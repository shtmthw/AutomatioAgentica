"""
Context & memory: reusable building blocks for lessons about long agent tasks
(first used in Episode 03, "Context and Memory"). Built on agentic_video/internals.py.

    SizedCard        a MessageCard whose height is proportional to how much text it holds
    SummaryCard      amber SUMMARY tag + 3-4 short bullet lines (replaces many older cards)
    PlaceholderCard  thin dimmed card: "[old tool result removed]", "[output shortened: ...]"
    NoteCard         small violet card: one saved note in one short line
    NotesBlock       violet "NOTES FROM MEMORY" block inside the context window
    Notebook         the memory store (violet notebook labelled MEMORY): files on disk
    LiveContext      a ContextWindow whose meter is always computed from the cards inside it
    CallCounter      "CALL #12" pill
    TechniqueTag     "TECHNIQUE 2 OF 3" with progress dots
    session_wipe     the session divider: a vertical line sweeps across and clears the given mobjects
    CheckedScene     VoiceScene + an overlap report (text/cards/pills of different objects that overlap
                     for more than OVERLAP_MIN seconds are printed to the render log as OVERLAP lines),
                     and a chapter tag that fades in with the first narration line instead of before it

Kept next to this production's scenes (not in agentic_video/) so that adding it does not
re-render or re-review earlier productions. A later episode can copy or import it, or
promote it into the shared library together with other library changes.
"""
from __future__ import annotations

from contextlib import contextmanager

import numpy as np
from manim import (MarkupText, Text, VMobject, AnimationGroup, DashedLine, FadeIn, FadeOut, FadeTransform, Line, NORMAL, Rectangle,
                   RoundedRectangle, Succession, Transform, VGroup, Wait, linear, DOWN, LEFT, RIGHT, UP, UL, UR)

from agentic_video import icons as I
from agentic_video.components import Pill, glow
from agentic_video.internals import (ROLE_COLORS, ContextWindow, caps, code_block, dashed_outline, wrap_text)
from agentic_video.voice import VoiceScene
from agentic_video.style import (AMBER, BG, BLUE, DIM, FAINT, FG, MUTED, PANEL, PANEL_2, RED, TEAL, VIOLET, bn,
                                 en, mono)

MEMORY = VIOLET          # the memory accent (notebook, notes)


def meter_color3(frac: float) -> str:
    """Episode 03 meter: teal, amber when the window is getting full, red when it is (almost) full."""
    return TEAL if frac < 0.65 else (AMBER if frac < 0.895 else RED)


# ---------------------------------------------------------------- cards
class SizedCard(VGroup):
    """A message card (same look as internals.MessageCard: coloured role tag + text) whose height
    is set by how much text it holds. Thin cards for short messages, tall cards for big tool
    results; tall cards get abstract, unreadable text bars under their first line."""

    TAG_W = 1.2

    def __init__(self, role: str, text: str | None = None, height: float = 0.3, width: float = 3.4, size: float = 13,
                 content=None, filler: bool | None = None, label=None, accent=None, dashed=False, tag_size=10.5,
                 text_color=FG, wrap=None, seed=3, **kw):
        super().__init__(**kw)
        c = ROLE_COLORS[role]
        self.role = role
        self.accent = accent or c
        avail_w = width - self.TAG_W - 0.36
        if content is None:
            head = bn(wrap_text(text or "", wrap), size, text_color) if text else None
            if filler is None:
                filler = height > 0.75
            if filler:
                n = max(2, int((height - 0.3 - (head.height + 0.1 if head is not None else 0)) / 0.15))
                bars = code_block(min(avail_w, 1.9), n, size=0.035, color=DIM, seed=seed, gap=0.15)
                content = VGroup(*([head] if head is not None else []), bars).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
            else:
                content = head if head is not None else VGroup()
        body = content
        if body.width > avail_w:
            body.scale_to_fit_width(avail_w)
        if body.height > max(height - 0.14, 0.1) and height > 0.75:
            body.stretch_to_fit_height(height - 0.2)
        h = max(height, body.height + 0.12, 0.2)
        tag_h = min(0.24, h - 0.06)
        tag_box = RoundedRectangle(width=self.TAG_W, height=tag_h, corner_radius=0.07).set_stroke(c, 1.2).set_fill(c, 0.14)
        tag_txt = caps(label or role, tag_size, c)
        if tag_txt.width > self.TAG_W - 0.14:
            tag_txt.scale_to_fit_width(self.TAG_W - 0.14)
        tag_txt.move_to(tag_box)
        self.tag = VGroup(tag_box, tag_txt)
        shape = RoundedRectangle(width=width, height=h, corner_radius=0.08)
        self.frame = shape.copy().set_stroke(self.accent, 1.3, opacity=0.6).set_fill(PANEL, 1)
        self.outline = None
        if dashed:
            self.frame.set_stroke(width=0)
            self.outline = dashed_outline(shape, self.accent, 1.5, dash=0.08)
        tall = h > 0.6
        if tall:
            self.tag.move_to(self.frame.get_corner(UL) + RIGHT * (0.09 + self.TAG_W / 2) + DOWN * (0.06 + tag_h / 2))
            body.move_to(self.frame.get_corner(UL) + RIGHT * (self.TAG_W + 0.2) + DOWN * 0.08, aligned_edge=UL)
        else:
            self.tag.move_to(self.frame.get_left() + RIGHT * (0.09 + self.TAG_W / 2))
            body.next_to(self.tag, RIGHT, buff=0.14)
        self.body = body
        self.add(self.frame, *([self.outline] if self.outline else []), self.tag, body)


def call_line(tool: str, arg: str | None = None, size: float = 13) -> VGroup:
    """`read_file → "config.txt"` as one compact line (tool call inside a message card)."""
    parts = [mono(tool, size, BLUE)]
    if arg is not None:
        parts += [en("→", size + 2, MUTED), mono(arg, size, FG)]
    return VGroup(*parts).arrange(RIGHT, buff=0.1)


def ToolCallMsg(tool: str, arg: str | None = None, width: float = 3.4, size: float = 13, height: float = 0.3):
    """ASSISTANT message holding a tool call (dashed: only a request)."""
    return SizedCard("assistant", content=call_line(tool, arg, size), width=width, height=height, dashed=True)


class SummaryCard(VGroup):
    """Compact card with an amber SUMMARY tag and 3-4 short bullet lines."""

    def __init__(self, bullets, width=3.4, size=13, color=AMBER, title="SUMMARY", min_h=0.0, **kw):
        super().__init__(**kw)
        tag_box = RoundedRectangle(width=1.36, height=0.3, corner_radius=0.08).set_stroke(color, 1.3).set_fill(color, 0.14)
        tag_t = caps(title, 11, color).move_to(tag_box)
        self.tag = VGroup(tag_box, tag_t)
        rows = VGroup()
        for b in bullets:
            dot = en("•", size + 2, color, italic=False)
            t = bn(b, size, FG)
            rows.add(VGroup(dot, t).arrange(RIGHT, buff=0.1, aligned_edge=UP))
        rows.arrange(DOWN, buff=0.09, aligned_edge=LEFT)
        avail = width - 0.36
        if rows.width > avail:
            rows.scale_to_fit_width(avail)
        h = max(min_h, self.tag.height + rows.height + 0.42)
        self.frame = RoundedRectangle(width=width, height=h, corner_radius=0.1).set_stroke(color, 1.6).set_fill(PANEL, 1)
        self.tint = self.frame.copy().set_stroke(width=0).set_fill(color, 0.05)
        self.tag.move_to(self.frame.get_corner(UL) + RIGHT * (0.12 + 0.68) + DOWN * 0.24)
        rows.next_to(self.tag, DOWN, buff=0.12, aligned_edge=LEFT).shift(RIGHT * 0.04)
        self.rows = rows
        self.add(self.frame, self.tint, self.tag, rows)
        self.accent = color
        self.role = "summary"


class PlaceholderCard(VGroup):
    """Thin, dimmed card: something was removed or shortened, and the model is told so."""

    def __init__(self, text="[old tool result removed]", width=3.4, size=12, height=0.3, color=MUTED, **kw):
        super().__init__(**kw)
        shape = RoundedRectangle(width=width, height=height, corner_radius=0.08)
        self.frame = shape.copy().set_stroke(width=0).set_fill(PANEL_2, 1)
        self.outline = dashed_outline(shape, DIM, 1.2, opacity=0.9, dash=0.07)
        self.label = mono(text, size, color)
        if self.label.width > width - 0.3:
            self.label.scale_to_fit_width(width - 0.3)
        self.label.move_to(self.frame)
        self.add(self.frame, self.outline, self.label)
        self.role = "placeholder"


class NoteCard(VGroup):
    """One saved note, one short line, violet."""

    def __init__(self, text: str, width=None, size=14, color=MEMORY, max_w=4.4, **kw):
        super().__init__(**kw)
        self.text = bn(text, size, FG)
        mark = RoundedRectangle(width=0.07, height=0.22, corner_radius=0.03).set_stroke(width=0).set_fill(color, 1)
        inner = VGroup(mark, self.text).arrange(RIGHT, buff=0.14)
        if width is None:
            width = min(max_w, inner.width + 0.36)
        if inner.width > width - 0.3:
            inner.scale_to_fit_width(width - 0.3)
        self.frame = RoundedRectangle(width=width, height=max(0.36, inner.height + 0.18), corner_radius=0.08)
        self.frame.set_stroke(color, 1.4).set_fill(PANEL, 1)
        self.tint = self.frame.copy().set_stroke(width=0).set_fill(color, 0.08)
        inner.move_to(self.frame.get_left() + RIGHT * (inner.width / 2 + 0.15))
        self.add(self.frame, self.tint, inner)
        self.accent = color


class NotesBlock(VGroup):
    """The saved notes placed into the context window: a violet block labelled NOTES FROM MEMORY."""

    def __init__(self, notes, width=3.4, size=12, color=MEMORY, title="NOTES FROM MEMORY", min_h=0.0, **kw):
        super().__init__(**kw)
        head = caps(title, 11, color)
        rows = VGroup(*[VGroup(RoundedRectangle(width=0.05, height=0.16, corner_radius=0.02).set_stroke(width=0)
                               .set_fill(color, 1), bn(n, size, FG)).arrange(RIGHT, buff=0.1) for n in notes])
        rows.arrange(DOWN, buff=0.07, aligned_edge=LEFT)
        body = VGroup(head, rows).arrange(DOWN, buff=0.1, aligned_edge=LEFT) if notes else VGroup(head)
        if body.width > width - 0.3:
            body.scale_to_fit_width(width - 0.3)
        h = max(min_h, body.height + 0.24)
        self.frame = RoundedRectangle(width=width, height=h, corner_radius=0.1).set_stroke(color, 1.5).set_fill(PANEL, 1)
        self.tint = self.frame.copy().set_stroke(width=0).set_fill(color, 0.1)
        body.move_to(self.frame.get_corner(UL) + RIGHT * (body.width / 2 + 0.15) + DOWN * (body.height / 2 + 0.12))
        self.head, self.rows = head, rows
        self.add(self.frame, self.tint, body)
        self.accent = color
        self.role = "notes"


class Notebook(VGroup):
    """The memory store: a violet notebook labelled MEMORY. Stands for ordinary files on disk,
    outside the model and outside the context window. Note cards are stacked under it."""

    def __init__(self, h=1.1, color=MEMORY, label="MEMORY", sub="files on disk", **kw):
        super().__init__(**kw)
        w = h * 0.8
        self.cover = RoundedRectangle(width=w, height=h, corner_radius=h * 0.07).set_stroke(color, 2.2).set_fill(PANEL, 1)
        self.tint = self.cover.copy().set_stroke(width=0).set_fill(color, 0.1)
        spine = Line(self.cover.get_corner(UL) + RIGHT * w * 0.18, self.cover.get_corner(DOWN + LEFT) + RIGHT * w * 0.18)
        spine.set_stroke(color, 1.6, opacity=0.8)
        rings = VGroup(*[RoundedRectangle(width=w * 0.2, height=h * 0.06, corner_radius=h * 0.03)
                         .set_stroke(color, 1.6).set_fill(BG, 1)
                         .move_to(self.cover.get_left() + UP * h * (0.3 - 0.2 * i) + RIGHT * w * 0.06) for i in range(4)])
        lines = VGroup(*[Line(LEFT * w * 0.22, RIGHT * w * 0.26).set_stroke(color, 1.6, opacity=0.55)
                         .move_to(self.cover.get_center() + RIGHT * w * 0.1 + UP * h * (0.18 - 0.14 * i)) for i in range(3)])
        self.icon = VGroup(self.cover, self.tint, spine, lines, rings)
        self.label = en(label, 20, color, italic=False, weight=NORMAL) if label else None
        parts = [self.icon] + ([self.label] if self.label is not None else [])
        self.sub = en(sub, 15, MUTED) if sub else None
        if self.sub is not None:
            parts.append(self.sub)
        VGroup(*parts).arrange(DOWN, buff=0.12)
        self.add(*parts)
        self.accent = color
        self.notes: list = []

    def lock(self, h=0.32):
        """Lock + eye icons for 'memory can hold private information'."""
        lk = I.lock_icon(h, self.accent).next_to(self.cover, RIGHT, buff=0.14).shift(UP * h * 0.6)
        eye = eye_icon(h * 1.1, self.accent).next_to(lk, DOWN, buff=0.12)
        return VGroup(lk, eye)


def eye_icon(h=0.3, color=FG) -> VGroup:
    from manim import ArcBetweenPoints, Circle
    w = h * 1.7
    top = ArcBetweenPoints(LEFT * w / 2, RIGHT * w / 2, angle=-1.6).set_stroke(color, 1.8)
    bot = ArcBetweenPoints(LEFT * w / 2, RIGHT * w / 2, angle=1.6).set_stroke(color, 1.8)
    pupil = Circle(radius=h * 0.2).set_stroke(color, 1.8).set_fill(color, 0.9)
    return VGroup(top, bot, pupil)


def pin_icon(h=0.22, color=MUTED) -> VGroup:
    from manim import Circle
    head = Circle(radius=h * 0.28).set_stroke(color, 1.6).set_fill(color, 0.85).shift(UP * h * 0.22)
    needle = Line(UP * h * 0.0, DOWN * h * 0.5).set_stroke(color, 1.8)
    return VGroup(needle, head)


# ---------------------------------------------------------------- the context window, measured from its cards
class LiveContext:
    """A ContextWindow plus the cards inside it. The meter (and its % readout) is always
    computed from the cards currently in the window, so it can never disagree with what is
    shown. Each card takes `card.tokens` units of space (default: its height plus the gap,
    so a window stacked full of default cards reads 100%); small readable cards may be given
    fewer units (`ctx.size(card, 0.05)` = 5% of the window).

        ctx = LiveContext(center, w, h)
        self.play(*ctx.appear())
        self.play(*ctx.add(card))                 # positions the card under the last one
        self.play(*ctx.remove([a, b]), *ctx.relayout())
        self.play(*ctx.replace(olds, summary), *ctx.relayout())
    """

    def __init__(self, center, width=3.8, height=5.3, label="CONTEXT WINDOW", pad=0.16, gap=0.05, label_size=15,
                 readout=True):
        self.cw = ContextWindow(width, height, label=label, label_size=label_size)
        self.cw.shift(np.array(center, dtype=float) - self.cw.frame.get_center())   # centre the frame, not frame+label
        self.cw.frame.set_z_index(-2)            # the tinted window fill stays behind its cards
        self.pad, self.gap = pad, gap
        self.cards: list = []
        self.card_w = width - 2 * pad
        self.readout = self._readout(0) if readout else None
        self.shown = 0

    # geometry --------------------------------------------------------------
    @property
    def top(self) -> float:
        return self.cw.frame.get_top()[1] - self.pad

    @property
    def x0(self) -> float:
        return self.cw.frame.get_left()[0] + self.pad

    @property
    def inner(self) -> float:
        return self.cw.frame.height - 2 * self.pad

    @property
    def capacity(self) -> float:
        return self.inner + self.gap

    def units(self, c) -> float:
        t = getattr(c, "tokens", None)
        return c.height + self.gap if t is None else t

    def size(self, card, frac: float):
        """Give `card` a share of the window (0.05 = 5 %), whatever its drawn height."""
        card.tokens = frac * self.capacity
        return card

    def level(self, cards=None) -> float:
        cs = self.cards if cards is None else cards
        return min(1.0, sum(self.units(c) for c in cs) / self.capacity)

    def used_height(self, cards=None) -> float:
        cs = self.cards if cards is None else cards
        return sum(c.height for c in cs) + self.gap * max(0, len(cs) - 1)

    def free(self) -> float:
        """Drawn height still free for one more card."""
        return self.inner - self.used_height() - (self.gap if self.cards else 0)

    def slots(self, cards=None) -> list:
        out, y = [], self.top
        for c in (self.cards if cards is None else cards):
            out.append(np.array([self.x0 + c.width / 2, y - c.height / 2, 0.0]))
            y -= c.height + self.gap
        return out

    def next_point(self, card) -> np.ndarray:
        y = self.top - (self.used_height() + self.gap if self.cards else 0)
        return np.array([self.x0 + card.width / 2, y - card.height / 2, 0.0])

    # readout -----------------------------------------------------------------
    def _readout(self, pct: int):
        c = meter_color3(pct / 100)
        t = en(f"{pct}%", 17, c, italic=False, weight=NORMAL)
        t.next_to(self.cw.meter_box, UP, buff=0.14)
        return t

    # animations --------------------------------------------------------------
    def meter(self):
        """List of animations: meter fill and % readout to the current level."""
        lv = self.level()
        anims = [self.cw.meter_to(lv, meter_color3(lv))]
        pct = int(round(lv * 100))
        if self.readout is not None and pct != self.shown:
            new = self._readout(pct)
            anims += [FadeOut(self.readout), FadeIn(new)]       # cross-fade: morphing digits looks garbled
            self.readout = new
            self.shown = pct
        return anims

    def add_quiet(self, card):
        """Card already on screen moves into its slot, without touching the (not yet shown) meter."""
        target = self.next_point(card)
        self.cards.append(card)
        return [card.animate.move_to(target)]

    def parts(self, label=True, readout=True):
        out = [self.cw.frame, self.cw.meter_box, self.cw.fill]
        if label and self.cw.label is not None:
            out.append(self.cw.label)
        if readout and self.readout is not None:
            out.append(self.readout)
        return out

    def appear(self, label=True):
        """Fade the window in; the meter then rises to what the cards already inside take."""
        lv = self.level()
        self.cw.fill.become(self.cw._fill_rect(lv, meter_color3(lv)))
        if self.readout is not None:
            self.readout.become(self._readout(int(round(lv * 100))))
            self.shown = int(round(lv * 100))
        return [FadeIn(m) for m in self.parts(label)]

    def frame_group(self) -> VGroup:
        return VGroup(*self.parts())

    def place(self, card):
        card.move_to(self.next_point(card))
        self.cards.append(card)
        return card

    def add(self, card, shift=DOWN * 0.25):
        self.place(card)
        return [FadeIn(card, shift=shift), *self.meter()]

    def add_from(self, card):
        """Card already on screen (e.g. arriving from outside): move it into its slot."""
        target = self.next_point(card)
        self.cards.append(card)
        return [card.animate.move_to(target), *self.meter()]

    def insert(self, i, card):
        """Insert a card at position i (e.g. notes right after the system message); returns
        its FadeIn plus the relayout of the cards below it."""
        self.cards.insert(i, card)
        card.move_to(self.slots()[i])
        return [FadeIn(card, shift=RIGHT * 0.2)] + [c.animate.move_to(p) for c, p in zip(self.cards, self.slots())
                                                    if c is not card] + self.meter()

    def relayout(self):
        return [c.animate.move_to(p) for c, p in zip(self.cards, self.slots())] + self.meter()

    def remove(self, cards, shift=LEFT * 0.5):
        for c in cards:
            self.cards.remove(c)
        return [FadeOut(c, shift=shift) for c in cards]

    def replace(self, olds, new):
        """Collapse `olds` into `new` (placed where the first old card was)."""
        i = self.cards.index(olds[0])
        for c in olds:
            self.cards.remove(c)
        self.cards.insert(i, new)
        pos = self.slots()[i]
        new.move_to(pos)
        return [*[c.animate.move_to(pos).scale(0.5).set_opacity(0) for c in olds], FadeIn(new, scale=0.95)]

    def swap(self, old, new):
        """Replace one card by another in place (e.g. a tool result by a placeholder)."""
        i = self.cards.index(old)
        self.cards[i] = new
        new.move_to(old.get_top() + DOWN * new.height / 2)
        return [FadeTransform(old, new)]

    def clear(self):
        cs, self.cards = self.cards, []
        return cs

    def group(self) -> VGroup:
        return VGroup(*self.cards)

    def resize(self, height: float, anchor=DOWN, stroke=None):
        """Animations: the window grows/shrinks to `height`, keeping its `anchor` edge in place.
        Cards are laid out again from the new top and the meter is recomputed."""
        f = self.cw.frame
        old_edge = f.get_edge_center(anchor)
        new_frame = f.copy().stretch_to_fit_height(height)
        new_frame.move_to(old_edge, aligned_edge=anchor)
        if stroke is not None:
            new_frame.set_stroke(stroke)
        mb = self.cw.meter_box
        new_mb = mb.copy().stretch_to_fit_height(height)
        new_mb.move_to([mb.get_x(), new_frame.get_y(), 0])
        anims = [Transform(f, new_frame), Transform(mb, new_mb)]
        if self.cw.label is not None:
            anims.append(self.cw.label.animate.next_to(new_frame, UP, buff=0.16))
        self.cw.H = height
        # cards and meter computed against the new geometry
        dy = new_frame.get_top()[1] - f.get_top()[1]
        y = new_frame.get_top()[1] - self.pad
        for c in self.cards:
            anims.append(c.animate.move_to([self.x0 + c.width / 2, y - c.height / 2, 0]))
            y -= c.height + self.gap
        lv = min(1.0, sum(self.units(c) for c in self.cards) / (height - 2 * self.pad + self.gap))
        inner = height - 0.08
        hh = max(0.002, inner * lv)
        r = Rectangle(width=self.cw.meter_w * 0.56, height=hh).set_stroke(width=0).set_fill(meter_color3(lv), 0.95)
        r.move_to(new_mb.get_bottom() + UP * (0.04 + hh / 2))
        anims.append(Transform(self.cw.fill, r))
        if self.readout is not None:
            pct = int(round(lv * 100))
            new = en(f"{pct}%", 17, meter_color3(lv), italic=False, weight=NORMAL).next_to(new_mb, UP, buff=0.14)
            anims += [FadeOut(self.readout), FadeIn(new)]
            self.readout = new
            self.shown = pct
        self.cw.level = lv
        return anims


# ---------------------------------------------------------------- counters
class CallCounter(VGroup):
    """ "CALL #12" in a small pill; `.to(n)` returns the animations."""

    def __init__(self, n=1, color=BLUE, size=20, **kw):
        super().__init__(**kw)
        self.accent, self.size = color, size
        self.frame = RoundedRectangle(width=1.95, height=0.5, corner_radius=0.25).set_stroke(color, 1.6).set_fill(PANEL, 1)
        self.word = caps("call", 15, MUTED)
        self.num = self._num(n)
        self._arrange()
        self.add(self.frame, self.word, self.num)
        self.n = n

    def _num(self, n):
        return en(f"#{n}", self.size, self.accent, italic=False, weight=NORMAL)

    def _arrange(self):
        g = VGroup(self.word, self.num).arrange(RIGHT, buff=0.14).move_to(self.frame)
        return g

    def to(self, n):
        new = self._num(n)
        new.move_to(self.num, aligned_edge=LEFT)
        old = self.num
        self.remove(old)
        self.add(new)
        self.num = new
        self.n = n
        return [FadeOut(old, shift=UP * 0.12), FadeIn(new, shift=UP * 0.12)]


class TechniqueTag(VGroup):
    """ "TECHNIQUE 1 OF 3" + three dots (the corner counter of sections 04-06)."""

    def __init__(self, i=1, n=3, color=AMBER, **kw):
        super().__init__(**kw)
        from manim import Circle
        self.accent = color
        self.text = VGroup(caps("technique", 15, MUTED), en(str(i), 26, color, italic=False, weight=NORMAL),
                           caps(f"of {n}", 15, DIM)).arrange(RIGHT, buff=0.11)
        self.dots = VGroup(*[Circle(radius=0.065).set_stroke(color if j < i else DIM, 1.5)
                             .set_fill(color if j == i - 1 else (MUTED if j < i else BG), 1 if j <= i - 1 else 1)
                             for j in range(n)]).arrange(RIGHT, buff=0.16)
        VGroup(self.text, self.dots).arrange(RIGHT, buff=0.3)
        self.add(self.text, self.dots)


def technique_tag(i: int):
    """TechniqueTag in its corner place (top right)."""
    t = TechniqueTag(i)
    t.move_to([6.75 - t.width / 2, 3.55, 0])
    return t


def label_tag(text: str, color=AMBER, size=17):
    """Small pill like 'TECHNIQUE 1' shown next to a card while a technique is active."""
    return Pill(caps(text, size - 3, color), color, pad_x=0.16, pad_y=0.07)


def unchanged_badge(model, color=BLUE):
    """ "UNCHANGED" label under a ModelBox."""
    p = Pill(VGroup(I.check_icon(0.2, color), caps("unchanged", 14, color)).arrange(RIGHT, buff=0.1), color,
             pad_x=0.16, pad_y=0.07)
    p.next_to(model, DOWN, buff=0.16)
    return p


# ---------------------------------------------------------------- session divider
def session_pill(n: int, color=MEMORY):
    return Pill(caps(f"session {n}", 15, color), color, pad_x=0.2, pad_y=0.08)


def session_wipe(scene, clear, text="SESSION 1 ENDS", run_time=1.6, color=MEMORY, y_top=3.05, y_bottom=-2.7):
    """The session divider: a vertical line with a label sweeps left to right across the
    frame; every mobject in `clear` fades out as the line passes it. Whatever is not in
    `clear` (the notebook) is untouched. Plays the animation on `scene`."""
    x0, x1 = -7.4, 7.4
    line = Line([x0, y_bottom, 0], [x0, y_top - 0.3, 0]).set_stroke(color, 3)
    glow_l = line.copy().set_stroke(color, 12, opacity=0.18)
    lab = Pill(caps(text, 14, color), color, pad_x=0.18, pad_y=0.07).move_to([x0, y_top, 0])
    bar = VGroup(glow_l, line, lab)
    anims = [bar.animate(rate_func=linear, run_time=run_time).shift(RIGHT * (x1 - x0))]
    for m in clear:
        frac = min(1.0, max(0.0, (m.get_center()[0] - x0) / (x1 - x0)))
        d = frac * run_time
        anims.append(Succession(Wait(run_time=max(0.001, d)), FadeOut(m, run_time=0.35)))
    scene.add(bar)
    scene.play(AnimationGroup(*anims))
    scene.remove(bar)


# ---------------------------------------------------------------- scene base with an overlap report
def _leaves(m, out):
    """Visible text and opaque shapes of `m` (texts are not split into glyphs)."""
    if isinstance(m, (Text, MarkupText)):
        fam = [s for s in m.family_members_with_points()]
        if fam and max(s.get_fill_opacity() for s in fam) > 0.2:
            pts = np.concatenate([s.points for s in fam])
            out.append(("text", m.text, pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max()))
        return
    if m.submobjects:
        for s in m.submobjects:
            _leaves(s, out)
    elif isinstance(m, VMobject) and len(m.points) and m.get_fill_opacity() > 0.4:
        x0, x1 = m.points[:, 0].min(), m.points[:, 0].max()
        y0, y1 = m.points[:, 1].min(), m.points[:, 1].max()
        if 0.01 < (x1 - x0) * (y1 - y0) < 6.5:
            out.append(("shape", type(m).__name__, x0, x1, y0, y1))


def _name(m) -> str:
    texts = [s.text for s in m.get_family() if isinstance(s, (Text, MarkupText))]
    return f"{type(m).__name__}[{texts[0][:28]!r}]" if texts else type(m).__name__


class CheckedScene(VoiceScene):
    OVERLAP_MIN = 0.6          # seconds an overlap must stay on screen to be reported
    SHRINK = 0.025             # boxes are shrunk a little: touching is not overlapping

    def setup(self):
        super().setup()
        self._ov_open = {}
        self._ov_found = []
        self._chapter_pending = False

    # the chapter tag fades in during the first line (no silent gap before the narration)
    def show_chapter(self):
        if self.chapter is not None:
            self._chapter_pending = True

    @contextmanager
    def say(self, key, gap=None):
        with super().say(key, gap) as v:
            if self._chapter_pending:
                self._chapter_pending = False
                self.play(FadeIn(self.chapter, shift=0.1 * RIGHT), run_time=0.45)
            yield v

    def play(self, *args, **kwargs):
        super().play(*args, **kwargs)
        self._ov_check()

    def _ov_pairs(self) -> dict:
        boxes = []
        for i, m in enumerate(self.mobjects):
            out = []
            _leaves(m, out)
            boxes += [(i, *b) for b in out]
        found = {}
        s = self.SHRINK
        for a in range(len(boxes)):
            ia, ka, la, ax0, ax1, ay0, ay1 = boxes[a]
            for b in range(a + 1, len(boxes)):
                ib, kb, lb, bx0, bx1, by0, by1 = boxes[b]
                if ia == ib or (ka == "shape" and kb == "shape"):
                    continue
                if ka != kb:                         # text on a panel drawn behind it = a label, not an overlap
                    (it, tbox), (ish, sbox) = ((ia, (ax0, ax1, ay0, ay1)), (ib, (bx0, bx1, by0, by1))) if ka == "text" \
                        else ((ib, (bx0, bx1, by0, by1)), (ia, (ax0, ax1, ay0, ay1)))
                    inside = (tbox[0] >= sbox[0] - 0.02 and tbox[1] <= sbox[1] + 0.02 and tbox[2] >= sbox[2] - 0.02
                              and tbox[3] <= sbox[3] + 0.02)
                    behind = (self.mobjects[ish].z_index, ish) < (self.mobjects[it].z_index, it)
                    if inside and behind:
                        continue
                w = min(ax1, bx1) - max(ax0, bx0) - 2 * s
                h = min(ay1, by1) - max(ay0, by0) - 2 * s
                if w > 0 and h > 0 and w * h > 0.002:
                    key = (_name(self.mobjects[ia]), f"{ka}:{la}", _name(self.mobjects[ib]), f"{kb}:{lb}")
                    found[key] = (round(float((max(ax0, bx0) + min(ax1, bx1)) / 2), 2),
                                  round(float((max(ay0, by0) + min(ay1, by1)) / 2), 2))
        return found

    def _ov_check(self):
        now = self.time
        cur = self._ov_pairs()
        for k, where in cur.items():
            self._ov_open.setdefault(k, (now, where))
        for k in list(self._ov_open):
            if k not in cur:
                t0, where = self._ov_open.pop(k)
                if now - t0 >= self.OVERLAP_MIN:
                    self._ov_found.append((t0, now, where, k))

    def tear_down(self):
        now = self.time
        for k, (t0, where) in self._ov_open.items():
            if now - t0 >= self.OVERLAP_MIN:
                self._ov_found.append((t0, now, where, k))
        for t0, t1, where, k in sorted(self._ov_found):
            print(f"OVERLAP\t{self.rt.section}\t{t0:.1f}-{t1:.1f}\t{where}\t{k[0]} {k[1]}\t<->\t{k[2]} {k[3]}",
                  flush=True)
        super().tear_down()


# Scene files do `from memory_kit import *` after the prelude, so their `VoiceScene` is the checked
# one (the pipeline's scene discovery looks for classes whose base is named VoiceScene).
_BaseVoiceScene = VoiceScene
VoiceScene = CheckedScene
