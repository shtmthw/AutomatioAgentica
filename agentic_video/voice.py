"""
Voice-synchronised scene base class (language-agnostic).

    with self.say("s02_05") as v:            # starts narration line s02_05
        self.play(FadeIn(a))                 # animations run while it plays
        self.wait_until(v.cue("input") - 0.2)  # jump to the word after the {input} marker
        self.play(Indicate(b))
    # on exit the scene waits until the line has finished (+ a short gap)

The same scene is rendered once per language: `self.say`/`v.cue` read the timings of
whichever language is being rendered (see agentic_video/runtime.py). Cue markers are
written into every language's narration text (`... a {input}input ...`), so cues
never depend on words of one language. `v.word("Input")` still works for words that
occur in every language, but markers are preferred.

Each render writes a cue log (line start times, scene duration, layout lint) that the
pipeline uses to place the audio and the subtitles, so picture, voice and subtitles
always line up. A scene must say every line of its section exactly once, in order;
this is checked when the render finishes.
"""
from __future__ import annotations

import json
import re
from contextlib import contextmanager

import numpy as np
from manim import FadeIn, FadeOut, RIGHT, Scene, Text, VMobject, config as mconfig

from . import runtime
from .components import chapter_tag
from .style import BG, SAFE_BOTTOM


def _norm(s: str) -> str:
    return re.sub(r"[^\wऀ-৿]", "", s).lower()


class Line:
    def __init__(self, scene: "VoiceScene", key: str, data: dict, start: float):
        self.scene, self.key, self.data, self.start = scene, key, data, start
        self.duration = data["speech_end"]
        self.end = start + self.duration
        self.words = data["words"]

    def cue(self, name: str, end: bool = False) -> float:
        """Absolute scene time of the word that follows marker {name} in this line."""
        marks = self.data.get("markers", {})
        if name not in marks:
            raise KeyError(f"marker {{{name}}} not in line {self.key} ({self.scene.rt.lang}); "
                           f"markers here: {sorted(marks)}; text: {self.data.get('display')!r}")
        t = marks[name]
        if end:
            for off, dur, _ in self.words:
                if off >= t - 1e-6:
                    return self.start + off + dur
        return self.start + t

    def word(self, needle: str, nth: int = 1, end: bool = False) -> float:
        """Absolute scene time at which `needle` is spoken (nth occurrence). Only safe for
        words present in every language's narration; prefer markers and cue().
        Words respelled by the pronunciation dictionary are found too."""
        table = self.scene.rt.pronunciation
        cands = [needle]
        if table:
            spoken = needle
            for w in sorted(table, key=len, reverse=True):
                spoken = re.sub(rf"(?<![A-Za-z0-9]){re.escape(w)}(?![A-Za-z0-9])", table[w], spoken)
            cands.append(spoken)
        for cand in dict.fromkeys(cands):
            n = _norm(cand)
            count = 0
            for off, dur, w in self.words:
                if n and n in _norm(w):
                    count += 1
                    if count == nth:
                        return self.start + off + (dur if end else 0.0)
        raise KeyError(f"word {needle!r} not spoken in {self.key} ({self.scene.rt.lang}): "
                       f"{[w for *_, w in self.words]} - use a {{marker}} instead")

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
        self.rt = runtime.load()
        if self.SECTION and self.SECTION != self.rt.section:
            raise RuntimeError(f"{type(self).__name__}.SECTION={self.SECTION!r} but the pipeline is rendering "
                               f"section {self.rt.section!r}")
        mconfig.background_color = BG
        self.camera.background_color = BG
        self.manifest = self.rt.lines
        self.cues: list[dict] = []
        self.lint: list[dict] = []
        self._lint_seen: set = set()
        self.preview_audio = self.rt.preview_audio
        self.chapter = None
        if self.SHOW_CHAPTER and self.rt.chapter:
            num, title = self.rt.chapter
            self.chapter = chapter_tag(num, title)

    # --- time helpers -------------------------------------------------
    @property
    def time(self) -> float:
        return self.renderer.time

    def wait_until(self, t: float, min_wait: float = 0.0):
        dt = t - self.time
        if dt > 1 / self.rt.fps:
            self.wait(dt)
        elif min_wait > 0:
            self.wait(min_wait)

    # --- narration ----------------------------------------------------
    @contextmanager
    def say(self, key: str, gap: float | None = None):
        if key not in self.manifest:
            raise KeyError(f"{key} is not a narration line of this production ({self.rt.lang}); "
                           f"lines of {self.rt.section}: {self.rt.expected_keys}")
        data = self.manifest[key]
        start = self.time
        if self.preview_audio:
            self.add_sound(str(self.rt.clip(key)))
        line = Line(self, key, data, start)
        self.cues.append({"key": key, "start": round(start, 4), "text": data.get("subtitle", "")})
        yield line
        self.wait_until(line.end + (self.rt.line_gap if gap is None else gap))
        if self.rt.lint:
            self._check_layout(key)

    def narrate(self, key: str, *anims, gap=None, run_time=None, **play_kw):
        """Shortcut: play animations at the start of a line and wait it out."""
        with self.say(key, gap=gap) as v:
            if anims:
                self.play(*anims, run_time=run_time or min(1.2, max(0.4, v.duration * 0.5)), **play_kw)
        return v

    # --- layout lint --------------------------------------------------
    def _check_layout(self, key: str):
        """Flag visible content outside the frame or below the subtitle safe line."""
        hw, hh = mconfig.frame_width / 2, mconfig.frame_height / 2
        tol = 0.04
        for m in self.mobjects:
            pts = [s.points for s in m.get_family() if isinstance(s, VMobject) and len(s.points)
                   and (s.get_fill_opacity() > 0.05 or (s.get_stroke_width() > 0 and s.get_stroke_opacity() > 0.05))]
            if not pts:
                continue
            allp = np.concatenate(pts)
            (x0, y0), (x1, y1) = allp[:, :2].min(axis=0), allp[:, :2].max(axis=0)
            if x1 - x0 > 0.9 * 2 * hw and y1 - y0 > 0.9 * 2 * hh:
                continue                       # full-frame veil / background
            issue = None
            if x0 < -hw - tol or x1 > hw + tol or y1 > hh + tol or y0 < -hh - tol:
                issue = "outside the frame"
            elif y0 < SAFE_BOTTOM - 0.05 and m is not self.chapter:
                issue = "below the safe area (subtitles are shown there)"
            if issue:
                texts = [t.text for t in m.get_family() if isinstance(t, Text)][:2]
                ident = (type(m).__name__, tuple(texts), issue)
                if ident in self._lint_seen:
                    continue
                self._lint_seen.add(ident)
                self.lint.append({"line": key, "t": round(self.time, 2), "issue": issue,
                                  "mobject": type(m).__name__, "texts": texts,
                                  "bounds": [round(float(v), 2) for v in (x0, y0, x1, y1)]})

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
        got = [c["key"] for c in self.cues]
        ok = got == self.rt.expected_keys if self.rt.expected_keys else True
        out = {"section": self.rt.section, "lang": self.rt.lang, "duration": round(self.time, 4),
               "fps": self.rt.fps, "cues": self.cues, "lint": self.lint, "complete": ok}
        self.rt.cues_out.parent.mkdir(parents=True, exist_ok=True)
        self.rt.cues_out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        if not ok:
            missing = [k for k in self.rt.expected_keys if k not in got]
            extra = [k for k in got if k not in self.rt.expected_keys]
            raise RuntimeError(f"{type(self).__name__} must say every line of {self.rt.section} once, in order. "
                               f"missing={missing} extra={extra} order={got}")
