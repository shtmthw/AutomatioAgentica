"""Audio treatment, unchanged from the previous production:

  * narration placed clip by clip at its cue time, levelled to -16 LUFS (measured in
    stereo, as the listener hears it), then a transparent look-ahead peak limiter
    at -1.5 dBFS (1 ms blocks, 5 ms look-ahead, 80 ms release);
  * synthesised ambient music at -33 LUFS, ducked 6 dB under the voice with a
    smoothed (Hann 0.6 s) envelope built from the known speech intervals;
  * 1.5 s fade at the end, ~1 dB of headroom.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from . import music
from .log import log
from .secrets import scrubbed_env

SR = 48000


def decode(path) -> np.ndarray:
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                                   "-f", "f32le", "-"], env=scrubbed_env())
    return np.frombuffer(raw, dtype=np.float32).copy()


def loudness(path) -> dict:
    """Integrated loudness (LUFS), loudness range and true peak (dBTP) via ffmpeg ebur128."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True, env=scrubbed_env()).stderr
    summary = err[err.rfind("Summary:"):] if "Summary:" in err else err

    def grab(pat):
        m = re.findall(pat, summary)
        return float(m[-1]) if m else None
    return {"integrated_lufs": grab(r"I:\s+(-?\d+(?:\.\d+)?) LUFS"), "lra": grab(r"LRA:\s+(-?\d+(?:\.\d+)?) LU"),
            "true_peak_dbtp": grab(r"Peak:\s+(-?\d+(?:\.\d+)?|-inf) dBFS")}


def lufs(path) -> float:
    v = loudness(path)["integrated_lufs"]
    if v is None:
        raise RuntimeError(f"could not measure loudness of {path}")
    return v


def limit(x: np.ndarray, ceiling_db: float = -1.5, lookahead: float = 0.005, release: float = 0.08) -> np.ndarray:
    """Transparent look-ahead peak limiter (1 ms blocks): only the few samples above
    the ceiling are turned down, instead of lowering the whole programme."""
    ceiling = 10 ** (ceiling_db / 20)
    blk = int(0.001 * SR)
    n = int(np.ceil(len(x) / blk))
    pad = np.pad(np.abs(x), (0, n * blk - len(x)))
    need = np.minimum(1.0, ceiling / np.maximum(pad.reshape(n, blk).max(axis=1), 1e-9))
    la = max(1, int(lookahead / 0.001))
    padded = np.pad(need, (la, la), constant_values=1.0)
    g = np.lib.stride_tricks.sliding_window_view(padded, 2 * la + 1).min(axis=1)
    coef = np.exp(-1.0 / (release / 0.001))
    out = np.empty_like(g)
    cur = 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else v + (cur - v) * coef
        out[i] = cur
    gain = np.interp(np.arange(n * blk), np.arange(n) * blk + blk / 2, out)[: len(x)]
    return (x * gain).astype(np.float32)


def place_voice(placements: list[tuple[float, Path, float, float]], total: float) -> tuple[np.ndarray, np.ndarray]:
    """Mono voice track + speech mask from (time, clip, speech_start, speech_end) placements."""
    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n, dtype=np.float32)
    speech = np.zeros(n, dtype=bool)
    for t, clip_path, s_start, s_end in placements:
        clip = decode(clip_path)
        a = int(round(t * SR))
        b = min(n, a + len(clip))
        if b > a:
            voice[a:b] += clip[: b - a]
        speech[int((t + s_start) * SR): int((t + s_end) * SR)] = True
    return voice, speech


def mix(voice: np.ndarray, speech: np.ndarray, total: float, settings, work: Path) -> dict:
    """Level the voice, duck the music under it, write mix.wav (+ stems) into `work`."""
    work.mkdir(parents=True, exist_ok=True)
    n = len(voice)
    vpath = work / "narration_raw.wav"
    sf.write(vpath, np.stack([voice, voice], axis=1), SR, subtype="FLOAT")
    gain_v = 10 ** ((settings.voice_lufs - lufs(vpath)) / 20)
    voice = voice * gain_v
    pre_peak = float(np.max(np.abs(voice)))
    voice = limit(voice, settings.limiter_db)
    vpath.unlink(missing_ok=True)
    log.info(f"  voice gain {20 * np.log10(gain_v):+.1f} dB, peak {20 * np.log10(max(pre_peak, 1e-9)):+.1f} dBFS "
             f"-> limited to {settings.limiter_db} dBFS")

    if settings.music == "none":
        m = np.zeros((n, 2), dtype=np.float32)
        gain_m = 0.0
    else:
        mpath = music.track(total + 1.0)
        m, msr = sf.read(mpath, dtype="float32")
        assert msr == SR
        m = np.pad(m, ((0, max(0, n - len(m))), (0, 0)))[:n]
        gain_m = 10 ** ((settings.music_lufs - lufs(mpath)) / 20)
        m = m * gain_m
        duck = np.where(speech, 10 ** (-settings.duck_db / 20), 1.0).astype(np.float32)
        win = int(0.6 * SR)
        kernel = np.hanning(win).astype(np.float32)
        kernel /= kernel.sum()
        duck = np.convolve(duck, kernel, mode="same").astype(np.float32)
        m = m * duck[:, None]

    out = m + voice[:, None]
    end = int(total * SR)
    out, m, voice = out[:end], m[:end], voice[:end]
    fo = min(int(1.5 * SR), end)
    fade = np.linspace(1, 0, fo, dtype=np.float32)
    out[-fo:] *= fade[:, None]
    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    scale = 0.89 / peak if peak > 0.89 else 1.0
    out *= scale
    mix_path = work / "mix.wav"
    sf.write(mix_path, out, SR, subtype="PCM_24")
    # stems exactly as they sit in the mix (for re-editing)
    v_stem = voice.copy()
    v_stem[-fo:] *= fade
    sf.write(work / "voice_stem.flac", v_stem * scale, SR, subtype="PCM_24", format="FLAC")
    if settings.music != "none":
        m[-fo:] *= fade[:, None]
        sf.write(work / "music_stem.flac", m * scale, SR, subtype="PCM_24", format="FLAC")
    log.info(f"  music gain {20 * np.log10(max(gain_m, 1e-9)):+.1f} dB, mix peak "
             f"{20 * np.log10(max(peak * scale, 1e-9)):.1f} dBFS")
    return {"mix": str(mix_path), "voice_stem": str(work / "voice_stem.flac"),
            "music_stem": str(work / "music_stem.flac") if settings.music != "none" else None,
            "voice_gain_db": round(20 * np.log10(gain_v), 2)}


def speech_frames(path, frame: float = 0.02, rel_db: float = -32.0) -> tuple[np.ndarray, float]:
    """Boolean speech activity per frame (RMS within rel_db of the loud frames) of a voice stem."""
    x = decode(path)
    hop = int(frame * SR)
    n = len(x) // hop
    if n == 0:
        return np.zeros(0, bool), frame
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    ref = np.percentile(rms[rms > 1e-5], 90) if np.any(rms > 1e-5) else 1.0
    return rms > ref * 10 ** (rel_db / 20), frame
