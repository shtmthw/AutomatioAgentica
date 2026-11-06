"""
End-to-end build.

    python -m tools.build all                 # voice -> render -> assemble
    python -m tools.build voice               # (re)generate changed narration clips
    python -m tools.build render [s03 s05]    # render all / selected scenes at 1080p
    python -m tools.build assemble            # concat + audio mix + subtitles + final MP4

Outputs (in ./output):
    agentic_ai_intro_hi_1080p.mp4            final video (Hindi voice), English subtitles burned in
    agentic_ai_intro_hi_1080p_softsubs.mp4   same video, subtitles as a toggleable track
    agentic_ai_intro_hi_1080p.srt            subtitles (e.g. for YouTube upload)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import soundfile as sf

from agentic_video import config as C
from tools import music, subtitles, tts

SR = 48000
SCENE_DIR = C.BUILD / "scenes"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe_duration(path) -> float:
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(path)])
    return float(out.strip())


# ------------------------------------------------------------------ render
def render_one(mod: str, cls: str, sec: str) -> tuple[str, float]:
    path = C.ROOT / (mod.replace(".", "/") + ".py")
    media = C.RENDER_DIR / sec
    env = dict(os.environ, PYTHONPATH=str(C.ROOT))
    env.pop("AGENTIC_PREVIEW_AUDIO", None)
    t0 = time.time()
    log = C.BUILD / "logs" / f"{sec}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w") as fh:
        run([sys.executable, "-m", "manim", "-qh", "--frame_rate", str(C.FPS), "--disable_caching",
             "--progress_bar", "none", "--media_dir", str(media), "-o", cls, str(path), cls],
            env=env, cwd=C.ROOT, stdout=fh, stderr=subprocess.STDOUT)
    found = sorted(media.rglob(f"{cls}.mp4"), key=lambda p: p.stat().st_mtime)[-1]
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(found, SCENE_DIR / f"{sec}.mp4")
    return sec, time.time() - t0


def render(sections=None, jobs=4):
    todo = [s for s in C.SCENES if not sections or s[2] in sections]
    print(f"rendering {len(todo)} scene(s) at {C.WIDTH}x{C.HEIGHT}@{C.FPS} with {jobs} workers ...")
    with ThreadPoolExecutor(jobs) as ex:
        for sec, dt in ex.map(lambda s: render_one(*s), todo):
            print(f"  {sec} done in {dt:.0f}s")


# ------------------------------------------------------------------ audio
def decode(path) -> np.ndarray:
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                                   "-f", "f32le", "-"])
    return np.frombuffer(raw, dtype=np.float32)


def lufs(path) -> float:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    vals = re.findall(r"I:\s+(-?\d+(?:\.\d+)?) LUFS", err)
    return float(vals[-1])


def timeline():
    """Absolute start time of every scene and of every narration line."""
    manifest = json.loads(C.VOICE_MANIFEST.read_text())
    offset, scenes, lines = 0.0, [], []
    for _, _, sec in C.SCENES:
        vid = SCENE_DIR / f"{sec}.mp4"
        cues = json.loads((C.CUES_DIR / f"{sec}.json").read_text())
        dur = probe_duration(vid)
        if abs(dur - cues["duration"]) > 0.2:
            print(f"  warning: {sec} video {dur:.2f}s vs cue log {cues['duration']:.2f}s - re-render this scene")
        scenes.append((sec, offset, dur))
        for c in cues["cues"]:
            lines.append((offset + c["start"], manifest[c["key"]]))
        offset += dur
    return scenes, lines, offset


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
    g = np.lib.stride_tricks.sliding_window_view(padded, 2 * la + 1).min(axis=1)   # attack ahead of peaks
    coef = np.exp(-1.0 / (release / 0.001))
    out = np.empty_like(g)
    cur = 1.0
    for i, v in enumerate(g):                       # release: recover smoothly
        cur = v if v < cur else v + (cur - v) * coef
        out[i] = cur
    gain = np.interp(np.arange(n * blk), np.arange(n) * blk + blk / 2, out)[: len(x)]
    return (x * gain).astype(np.float32)


def build_audio(lines, total) -> str:
    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n, dtype=np.float32)
    speech = np.zeros(n, dtype=bool)
    for t, entry in lines:
        clip = decode(C.VOICE_DIR / entry["file"])
        a = int(round(t * SR))
        b = min(n, a + len(clip))
        voice[a:b] += clip[: b - a]
        s0, s1 = int((t + entry["speech_start"]) * SR), int((t + entry["speech_end"]) * SR)
        speech[s0:s1] = True
    return mix_voice(voice, speech, total)


def mix_voice(voice: np.ndarray, speech: np.ndarray, total: float, tag: str = "") -> str:
    """Level a mono narration track (SR, float32), duck the music under `speech`
    (bool mask, same length) and write build/mix{tag}.wav. Returns its path."""
    # measure as the listener hears it: the mono voice is duplicated to both stereo
    # channels, which BS.1770 counts as +3 dB compared with a mono measurement
    n = len(voice)
    vpath = C.BUILD / f"narration{tag}_raw.wav"
    sf.write(vpath, np.stack([voice, voice], axis=1), SR, subtype="FLOAT")
    gain_v = 10 ** ((C.VOICE_LUFS - lufs(vpath)) / 20)
    voice *= gain_v
    pre_peak = float(np.max(np.abs(voice)))
    voice = limit(voice, -1.5)
    print(f"  voice peak {20*np.log10(max(pre_peak,1e-9)):+.1f} dBFS -> limited to -1.5 dBFS")

    mpath = C.MUSIC_DIR / "ambient.wav"
    music.make(total + 1.0, mpath)
    m, msr = sf.read(mpath, dtype="float32")
    assert msr == SR
    m = np.pad(m, ((0, max(0, n - len(m))), (0, 0)))[:n]
    gain_m = 10 ** ((C.MUSIC_LUFS - lufs(mpath)) / 20)
    m *= gain_m

    # ducking envelope: smooth dip while the voice speaks
    duck = np.where(speech, 10 ** (-C.DUCK_DB / 20), 1.0).astype(np.float32)
    win = int(0.6 * SR)
    kernel = np.hanning(win).astype(np.float32)
    kernel /= kernel.sum()
    duck = np.convolve(duck, kernel, mode="same").astype(np.float32)
    m *= duck[:, None]

    mix = m + voice[:, None]
    # end exactly with the picture, short fade
    mix = mix[: int(total * SR)]
    fo = int(1.5 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = np.max(np.abs(mix))
    if peak > 0.89:  # keep ~1 dB of headroom
        mix *= 0.89 / peak
    out = C.BUILD / f"mix{tag}.wav"
    sf.write(out, mix, SR, subtype="PCM_24")
    print(f"  narration gain {20*np.log10(gain_v):+.1f} dB, music gain {20*np.log10(gain_m):+.1f} dB, peak {20*np.log10(max(peak,1e-9)):.1f} dBFS")
    return str(out)


# ------------------------------------------------------------------ assemble
def assemble():
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    scenes, lines, total = timeline()
    print(f"timeline: {len(scenes)} scenes, {total:.1f}s ({int(total//60)}:{total%60:04.1f})")

    concat_list = C.BUILD / "concat.txt"
    concat_list.write_text("".join(f"file '{(SCENE_DIR / f'{s}.mp4').as_posix()}'\n" for s, _, _ in scenes))
    video = C.BUILD / "video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-an", "-c", "copy", str(video)])

    print("mixing audio ...")
    mix = build_audio(lines, total)

    print("writing subtitles ...")
    raw = []
    for t, entry in lines:
        raw.extend(subtitles.line_cues(t, entry))
    raw.sort(key=lambda c: c[0])
    cues = subtitles.finalize(raw)
    srt = C.OUTPUT / f"{C.FINAL_NAME}.srt"
    ass = C.BUILD / "subs.ass"
    subtitles.write_srt(cues, srt)
    subtitles.write_ass(cues, ass)
    print(f"  {len(cues)} subtitle cues -> {srt.name}")

    final = C.OUTPUT / f"{C.FINAL_NAME}.mp4"
    print("encoding final video ...")
    vf = f"ass={ass.as_posix()}" if C.BURN_SUBTITLES else "null"
    run(["ffmpeg", "-v", "error", "-stats", "-y", "-i", str(video), "-i", mix,
         "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
         "-r", str(C.FPS), "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart",
         "-metadata", "title=Agentic AI - The Beginning", "-metadata:s:a:0", f"language={C.AUDIO_LANG}", str(final)])

    soft = C.OUTPUT / f"{C.FINAL_NAME}_softsubs.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", mix, "-i", str(srt),
         "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-c:s", "mov_text", "-metadata:s:s:0", f"language={C.SUB_LANG}", "-metadata:s:a:0", f"language={C.AUDIO_LANG}",
         "-t", f"{total:.3f}", "-movflags", "+faststart", str(soft)])
    print(f"done -> {final}  ({probe_duration(final):.1f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["all", "voice", "render", "assemble"])
    ap.add_argument("sections", nargs="*")
    ap.add_argument("-j", "--jobs", type=int, default=4)
    a = ap.parse_args()
    if a.step in ("all", "voice"):
        asyncio.run(tts.main())
    if a.step in ("all", "render"):
        render(a.sections, a.jobs)
    if a.step in ("all", "assemble"):
        assemble()
