"""
Quick visual check of one scene.

    python -m tools.preview s03            # 480p render + contact sheet
    python -m tools.preview s03 --hq       # 1080p render + contact sheet

Writes build/preview/<section>.mp4 and build/preview/<section>_sheet.jpg,
which has one frame per narration line (taken late in the line, once its
animations have settled).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

from agentic_video import config as C


def render(section: str, quality: str = "l", audio: bool = False) -> "Path":
    mod, cls, _ = next(s for s in C.SCENES if s[2] == section)
    path = C.ROOT / (mod.replace(".", "/") + ".py")
    env = dict(os.environ, PYTHONPATH=str(C.ROOT))
    if audio:
        env["AGENTIC_PREVIEW_AUDIO"] = "1"
    media = C.BUILD / "preview_media"
    cmd = [sys.executable, "-m", "manim", f"-q{quality}", "--disable_caching", "--progress_bar", "none",
           "--media_dir", str(media), "-o", cls, str(path), cls]
    if quality == "h":
        cmd[3:3] = ["--frame_rate", str(C.FPS)]
    subprocess.run(cmd, check=True, env=env, cwd=C.ROOT)
    found = sorted(media.rglob(f"{cls}.mp4"), key=lambda p: p.stat().st_mtime)
    out = C.BUILD / "preview" / f"{section}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(found[-1], out)
    return out


def sheet(section: str, video) -> "Path":
    cues = json.loads((C.CUES_DIR / f"{section}.json").read_text())
    man = json.loads(C.VOICE_MANIFEST.read_text())
    times = [c["start"] + man[c["key"]]["speech_end"] * 0.92 for c in cues["cues"]]
    tmp = C.BUILD / "preview" / f"{section}_frames"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for i, t in enumerate(times):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=640:-1", str(tmp / f"{i:02d}.png")], check=True)
    cols = 3
    rows = (len(times) + cols - 1) // cols
    out = C.BUILD / "preview" / f"{section}_sheet.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", str(tmp / "%02d.png"),
                    "-vf", f"tile={cols}x{rows}:padding=4:color=0x333333", "-frames:v", "1", str(out)], check=True)
    print(f"{section}: {cues['duration']:.1f}s  sheet -> {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sections", nargs="+")
    ap.add_argument("--hq", action="store_true")
    ap.add_argument("--audio", action="store_true")
    a = ap.parse_args()
    for s in a.sections:
        v = render(s, "h" if a.hq else "l", a.audio)
        sheet(s, v)
