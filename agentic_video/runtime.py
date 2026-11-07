"""Render-time settings for scenes, handed over by the pipeline.

`python -m automatio` renders every scene once per language. For each render it
writes a small JSON file and points AA_RUNTIME at it:

    {"lang": "hi", "section": "s05", "manifest": ".../voice/hi/manifest.json",
     "cues_out": ".../cues.json", "chapter": ["05", "How does an agent work?"],
     "line_gap": 0.35, "fps": 30, "expected_keys": ["s05_01", ...],
     "preview_audio": false, "pronunciation": {"AI": "एआई"}, "lint": true}

Scenes never read files or settings themselves; everything language-specific
comes from here, so one scene file serves every language version.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Runtime:
    def __init__(self, data: dict):
        self.data = data
        self.lang: str = data["lang"]
        self.section: str = data["section"]
        man = json.loads(Path(data["manifest"]).read_text(encoding="utf-8"))
        self.lines: dict = man["lines"]
        self.cues_out = Path(data["cues_out"])
        self.chapter = data.get("chapter")
        self.line_gap = float(data.get("line_gap", 0.35))
        self.fps = int(data.get("fps", 30))
        self.expected_keys = list(data.get("expected_keys", []))
        self.preview_audio = bool(data.get("preview_audio", False))
        self.pronunciation = dict(data.get("pronunciation", {}))
        self.lint = bool(data.get("lint", True))

    def clip(self, key: str) -> Path:
        p = Path(self.lines[key]["file"])
        return p if p.is_absolute() else ROOT / p


def load() -> Runtime:
    p = os.environ.get("AA_RUNTIME")
    if not p:
        raise RuntimeError(
            "AA_RUNTIME is not set: scenes are rendered through the pipeline, e.g.\n"
            "    python -m automatio preview <production> <section>\n"
            "    python -m automatio run <production>")
    return Runtime(json.loads(Path(p).read_text(encoding="utf-8")))
