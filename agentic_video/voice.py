"""
Voice-synchronised scene base class.

    with self.say("s02_05") as v:          # starts narration line s02_05
        self.play(FadeIn(a))               # animations run while it plays
        self.wait_until(v.word("Input"))   # jump to the moment a word is spoken
        self.play(Indicate(b))
    # on exit the scene waits until the line has finished (+ a short gap)

Each scene writes build/cues/<section>.json with the exact start time of every
line inside the scene. The build step uses these to place the audio clips and
the subtitles, so picture, voice and subtitles always line up.

Set AGENTIC_PREVIEW_AUDIO=1 to also embed the voice in the scene's own video
(handy when previewing a single scene).
"""
from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager

from manim import Scene, FadeIn, FadeOut, RIGHT, config as mconfig

from . import config as C
from .components import chapter_tag
from .narration import SECTIONS
from .style import BG


def _norm(s: str) -> str:
    return re.sub(r"[^\w\u0900-\u09ff]", "", s).lower()


class Line:
    def __init__(self, scene: "VoiceScene", key: str, data: dict, start: float):
        self.scene, self.key, self.data, self.start = scene, key, data, start
        self.duration = data["speech_end"]
        self.end = start + self.duration
        self.words = data["words"]

    def word(self, needle: str, nth: int = 1, end: bool = False) -> float:
        """Absolute scene time at which `needle` is spoken (nth occurrence).
        Words respelled by the pronunciation dictionary are found too
        (e.g. word("AI") finds the spoken "एआई")."""
        from .pronunciation import apply as pronounce
        for cand in dict.fromkeys([needle, pronounce(needle)]):
            n = _norm(cand)
            count = 0
            for off, dur, w in self.words:
                if n and n in _norm(w):
                    count += 1
                    if count == nth:
                        return self.start + off + (dur if end else 0.0)
        raise KeyError(f"word {needle!r} not found in {self.key}: {[w for *_, w in self.words]}")

    def at(self, frac: float) -> float:
        """Absolute time at a fraction of the spoken line."""
        return self.start + self.duration * frac

    @property
    def remaining(self) -> float:
        return max(0.0, self.end - self.scene.time)


class VoiceScene(Scene):
    SECTION = ""
    SHOW_CHAPTER = True

    def setup(self):
        mconfig.background_color = BG
        self.camera.background_color = BG
        self.manifest = json.loads(C.VOICE_MANIFEST.read_text())
        self.cues: list[dict] = []
        self.preview_audio = os.environ.get("AGENTIC_PREVIEW_AUDIO") == "1"
        self.chapter = None
        if self.SHOW_CHAPTER and self.SECTION in SECTIONS:
            num, title = SECTIONS[self.SECTION]["chapter"]
            self.chapter = chapter_tag(num, title)

    # --- time helpers -------------------------------------------------
    @property
    def time(self) -> float:
        return self.renderer.time

    def wait_until(self, t: float, min_wait: float = 0.0):
        dt = t - self.time
        if dt > 1 / C.FPS:
            self.wait(dt)
        elif min_wait > 0:
            self.wait(min_wait)

    # --- narration ----------------------------------------------------
    @contextmanager
    def say(self, key: str, gap: float | None = None):
        if key not in self.manifest:
            raise KeyError(f"{key} missing from voice manifest - run `python -m tools.build voice`")
        data = self.manifest[key]
        start = self.time
        if self.preview_audio:
            self.add_sound(str(C.VOICE_DIR / data["file"]))
        line = Line(self, key, data, start)
        self.cues.append({"key": key, "start": round(start, 4), "text": data["text"]})
        yield line
        self.wait_until(line.end + (C.LINE_GAP if gap is None else gap))

    def narrate(self, key: str, *anims, gap=None, run_time=None, **play_kw):
        """Shortcut: play animations at the start of a line and wait it out."""
        with self.say(key, gap=gap) as v:
            if anims:
                self.play(*anims, run_time=run_time or min(1.2, max(0.4, v.duration * 0.5)), **play_kw)
        return v

    # --- scene lifecycle ---------------------------------------------
    def show_chapter(self):
        if self.chapter is not None:
            self.play(FadeIn(self.chapter, shift=0.1 * RIGHT), run_time=0.6)

    def attach(self, parent, *children):
        """After introducing `children` with an animation, make them part of `parent`
        so that later moves / fades of the parent carry them along."""
        for c in children:
            self.remove(c)
            parent.add(c)

    def clear_all(self, run_time=0.7, keep=()):
        mobs = [m for m in self.mobjects if m not in keep]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)

    def tear_down(self):
        C.CUES_DIR.mkdir(parents=True, exist_ok=True)
        out = {"section": self.SECTION, "duration": round(self.time, 4), "fps": C.FPS, "cues": self.cues}
        (C.CUES_DIR / f"{self.SECTION}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
