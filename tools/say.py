"""
Hear how the narrator will say something, in seconds, without rebuilding.

    .venv/bin/python -m tools.say "आपने एक AI Agent से कहा"
    .venv/bin/python -m tools.say "ए आई" "एआई" "ए-आई"      # compare spellings
    .venv/bin/python -m tools.say --raw "AI"                  # ignore the dictionary

Each sample is written to output/samples/ and the spoken text is printed.
The pronunciation dictionary (agentic_video/pronunciation.py) is applied
unless --raw is given.
"""
from __future__ import annotations

import argparse
import asyncio
import re

from agentic_video import config as C
from agentic_video.pronunciation import apply as pronounce
from tools.tts import synth


async def main(texts: list[str], raw: bool) -> None:
    out_dir = C.OUTPUT / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, text in enumerate(texts, 1):
        spoken = text if raw else pronounce(text)
        slug = re.sub(r"[^\w\u0900-\u09ff-]+", "_", text).strip("_")[:40] or f"sample{i}"
        path = out_dir / f"{i:02d}_{slug}{'_raw' if raw else ''}.mp3"
        await synth(spoken, path)
        print(f"{path}\n    spoken as: {spoken}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("texts", nargs="+")
    ap.add_argument("--raw", action="store_true", help="don't apply the pronunciation dictionary")
    a = ap.parse_args()
    asyncio.run(main(a.texts, a.raw))
