"""
Programmatically synthesised background music: a slow, warm ambient pad with
sparse soft bell notes. Deterministic (fixed seed), so rebuilding gives the
same track.

    python -m tools.music 540        # write assets/music/ambient.wav, 540 s long
"""
from __future__ import annotations

import sys

import numpy as np
import soundfile as sf

from agentic_video import config as C

SR = 48000
BPM = 66
CHORD_SECONDS = 8 * 60 / BPM          # two bars of 4/4 per chord (~7.3 s)

# Am9 - Fmaj7 - Cadd9 - G6  (MIDI notes)
PROGRESSION = [
    [45, 52, 60, 67, 71],
    [41, 48, 57, 64, 67],
    [48, 55, 62, 64, 67],
    [43, 50, 59, 64, 69],
]


def midi_hz(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def pad(duration: float, rng: np.random.Generator) -> np.ndarray:
    n = int(duration * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2), dtype=np.float32)
    n_chords = int(np.ceil(duration / CHORD_SECONDS)) + 1
    xfade = 2.6
    for ci in range(n_chords):
        notes = PROGRESSION[ci % len(PROGRESSION)]
        t0 = ci * CHORD_SECONDS - xfade / 2
        t1 = t0 + CHORD_SECONDS + xfade
        a, b = max(0, int(t0 * SR)), min(n, int(t1 * SR))
        if a >= b:
            continue
        tt = t[a:b]
        # raised-cosine envelope for smooth crossfades between chords
        env = np.ones_like(tt)
        rise = np.clip((tt - t0) / xfade, 0, 1)
        fall = np.clip((t1 - tt) / xfade, 0, 1)
        env *= 0.5 - 0.5 * np.cos(np.pi * np.minimum(rise, fall))
        for k, note in enumerate(notes):
            f = midi_hz(note)
            amp = 0.16 if k == 0 else 0.085
            amp *= 1.0 / (1 + 0.15 * k)
            for ch, det in enumerate((-0.0016, 0.0016)):
                ph = rng.uniform(0, 2 * np.pi)
                v = np.sin(2 * np.pi * f * (1 + det) * tt + ph)
                v += 0.18 * np.sin(2 * np.pi * 2 * f * (1 + det) * tt + ph * 1.3)
                v += 0.05 * np.sin(2 * np.pi * 3 * f * tt + ph * 0.7)
                out[a:b, ch] += (amp * env * v).astype(np.float32)
    # slow breathing movement
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.045 * t)
    out *= lfo[:, None].astype(np.float32)
    return out


def bells(duration: float, rng: np.random.Generator) -> np.ndarray:
    n = int(duration * SR)
    out = np.zeros((n, 2), dtype=np.float32)
    beat = 60 / BPM
    tail = int(3.0 * SR)
    tt = np.arange(tail) / SR
    t = 4 * beat
    while t < duration - 3:
        ci = int(t // CHORD_SECONDS)
        notes = PROGRESSION[ci % len(PROGRESSION)]
        note = notes[rng.integers(2, len(notes))] + 12
        f = midi_hz(note)
        env = np.exp(-tt * 1.6) * (1 - np.exp(-tt * 60))
        v = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2.01 * f * tt) * np.exp(-tt * 3)
        v *= env * 0.07
        pan = rng.uniform(0.3, 0.7)
        a = int(t * SR)
        b = min(n, a + tail)
        out[a:b, 0] += (v[: b - a] * (1 - pan)).astype(np.float32)
        out[a:b, 1] += (v[: b - a] * pan).astype(np.float32)
        t += beat * rng.choice([2, 3, 4, 4, 6])
    return out


def reverb(x: np.ndarray, seconds: float = 2.4, mix: float = 0.35, seed: int = 7) -> np.ndarray:
    """Overlap-add FFT convolution with a decaying-noise impulse response."""
    rng = np.random.default_rng(seed)
    m = int(seconds * SR)
    ir_t = np.arange(m) / SR
    ir = rng.standard_normal((m, 2)) * np.exp(-ir_t * 3.0)[:, None]
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    block = 1 << 18
    nfft = 1 << int(np.ceil(np.log2(block + m)))
    IR = np.fft.rfft(ir, nfft, axis=0)
    wet = np.zeros((len(x) + m, 2), dtype=np.float32)
    for s in range(0, len(x), block):
        seg = x[s:s + block]
        y = np.fft.irfft(np.fft.rfft(seg, nfft, axis=0) * IR, nfft, axis=0)[: len(seg) + m]
        wet[s:s + len(y)] += y.astype(np.float32)
    return (1 - mix) * x + mix * wet[: len(x)]


def lowpass(x: np.ndarray, cutoff: float = 2600.0) -> np.ndarray:
    """One-pole low-pass applied in the frequency domain (gentle, warm)."""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / cutoff) ** 2)
    return np.fft.irfft(X * H[:, None], len(x), axis=0).astype(np.float32)


def make(duration: float, path=None) -> str:
    rng = np.random.default_rng(2026)
    x = pad(duration, rng) + bells(duration, rng)
    x = reverb(x)
    x = lowpass(x)
    # fades
    fi, fo = int(3 * SR), int(5 * SR)
    x[:fi] *= np.linspace(0, 1, fi)[:, None]
    x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    x /= np.max(np.abs(x)) / 0.89
    path = path or (C.MUSIC_DIR / "ambient.wav")
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, x, SR, subtype="PCM_16")
    return str(path)


if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 540.0
    print(make(dur))
