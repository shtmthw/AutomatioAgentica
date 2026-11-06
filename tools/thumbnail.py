"""Render the YouTube thumbnail: output/thumbnail.png (1920x1080) and thumbnail.jpg (1280x720, <2 MB)."""
import os
import shutil
import subprocess
import sys

from agentic_video import config as C

if __name__ == "__main__":
    media = C.BUILD / "thumb_media"
    env = dict(os.environ, PYTHONPATH=str(C.ROOT))
    subprocess.run([sys.executable, "-m", "manim", "-qh", "-s", "--disable_caching", "--progress_bar", "none",
                    "--media_dir", str(media), "-o", "thumbnail", str(C.ROOT / "scenes" / "thumbnail.py"), "Thumbnail"],
                   check=True, env=env, cwd=C.ROOT, stdout=subprocess.DEVNULL)
    png = sorted(media.rglob("thumbnail*.png"), key=lambda p: p.stat().st_mtime)[-1]
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    shutil.copy(png, C.OUTPUT / "thumbnail.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(C.OUTPUT / "thumbnail.png"), "-vf", "scale=1280:720",
                    "-q:v", "2", str(C.OUTPUT / "thumbnail.jpg")], check=True)
    print(C.OUTPUT / "thumbnail.png", "\n" + str(C.OUTPUT / "thumbnail.jpg"))
