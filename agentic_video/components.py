"""
Reusable diagram building blocks, styled after the reference video:
dotted rounded zones, thin-stroked cards, small labelled arrows, terminal /
editor / browser windows.
"""
from __future__ import annotations

import numpy as np
from manim import (
    Arrow, ArcBetweenPoints, Circle, CurvedArrow, DashedVMobject, Dot, Line, Mobject,
    Rectangle, RoundedRectangle, Text, Triangle, VGroup, VMobject,
    UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR, ORIGIN, PI, TAU,
)

from . import icons
from .style import (
    BG, PANEL, PANEL_2, FG, MUTED, DIM, FAINT, BLUE, TEAL, AMBER, RED, VIOLET,
    BODY, SMALL, TINY, STROKE, ZONE_STROKE, bn, en, mono, txt,
)


# ---------------------------------------------------------------- zones
class Zone(VGroup):
    """Dotted rounded region with a faint tinted fill and an optional label."""

    def __init__(self, width=4.0, height=3.0, color=MUTED, label=None, label_color=None,
                 label_size=30, radius=None, fill_opacity=0.045, dash=0.085, label_inside=True,
                 stroke_opacity=0.7, **kw):
        super().__init__(**kw)
        radius = radius if radius is not None else min(width, height) * 0.26
        shape = RoundedRectangle(width=width, height=height, corner_radius=radius)
        self.fill = shape.copy().set_stroke(width=0).set_fill(color, fill_opacity)
        perim = 2 * (width + height)
        outline = shape.copy().set_stroke(color, ZONE_STROKE, opacity=stroke_opacity).set_fill(opacity=0)
        self.outline = DashedVMobject(outline, num_dashes=max(12, int(perim / dash)), dashed_ratio=0.5)
        self.shape = shape.set_stroke(width=0).set_fill(opacity=0)  # invisible geometry reference
        self.add(self.shape, self.fill, self.outline)
        self.accent = color
        self.label = None
        if label is not None:
            lab = label if isinstance(label, Mobject) else txt(label, label_size, label_color or color)
            if label_inside:
                lab.next_to(shape.get_top(), DOWN, buff=0.2)
            else:
                lab.next_to(shape.get_top(), UP, buff=0.12)
            self.label = lab
            self.add(lab)

    def lit(self, opacity=0.13):
        """Animation: brighten the fill."""
        return self.fill.animate.set_fill(opacity=opacity)

    def unlit(self, opacity=0.045):
        return self.fill.animate.set_fill(opacity=opacity)


class Card(VGroup):
    """Thin-stroked rounded card, optionally with an icon and a title."""

    def __init__(self, width=1.6, height=1.0, color=BLUE, title=None, icon=None, title_size=24,
                 subtitle=None, radius=0.12, fill=PANEL, stroke_width=STROKE, **kw):
        super().__init__(**kw)
        self.frame = RoundedRectangle(width=width, height=height, corner_radius=radius)
        self.frame.set_stroke(color, stroke_width).set_fill(fill, 1)
        self.add(self.frame)
        self.accent = color
        head = VGroup()
        if icon is not None:
            head.add(icon)
        if title is not None:
            t = txt(title, title_size, FG)
            head.add(t)
        if len(head):
            head.arrange(RIGHT, buff=0.12)
            head.move_to(self.frame.get_top() + DOWN * (0.12 + head.height / 2))
            if subtitle is None and height < 0.9:
                head.move_to(self.frame)
        self.head = head
        self.add(head)
        if subtitle is not None:
            s = en(f"~ {subtitle} ~", 15, DIM)
            s.next_to(head, DOWN, buff=0.05)
            self.add(s)


class Pill(VGroup):
    def __init__(self, text, color=FG, size=SMALL, pad_x=0.22, pad_y=0.1, fill=PANEL,
                 stroke_opacity=0.9, text_color=None, icon=None, **kw):
        super().__init__(**kw)
        label = text if isinstance(text, Mobject) else txt(text, size, text_color or color)
        content = VGroup(icon, label).arrange(RIGHT, buff=0.12) if icon is not None else VGroup(label)
        h = max(content.height + 2 * pad_y, 0.38)
        self.frame = RoundedRectangle(width=content.width + 2 * pad_x, height=h, corner_radius=h / 2)
        self.frame.set_stroke(color, STROKE, opacity=stroke_opacity).set_fill(fill, 1)
        content.move_to(self.frame)
        self.label = label
        self.add(self.frame, content)


class Bubble(VGroup):
    """Chat bubble with a small tail. `side` is 'left' (tail bottom-left) or 'right'."""

    def __init__(self, text, color=MUTED, size=26, side="left", text_color=FG, pad=0.2, max_w=None, **kw):
        super().__init__(**kw)
        label = text if isinstance(text, Mobject) else bn(text, size, text_color)   # upright sentence
        if max_w and label.width > max_w:
            label.scale_to_fit_width(max_w)
        w, h = label.width + 2 * pad, label.height + 2 * pad * 0.85
        self.frame = RoundedRectangle(width=w, height=h, corner_radius=min(0.22, h / 2))
        self.frame.set_stroke(color, STROKE).set_fill(PANEL, 1)
        sgn = -1 if side == "left" else 1
        base = self.frame.get_bottom() + RIGHT * sgn * (w / 2 - 0.34)
        tail = VMobject().set_points_as_corners([
            base + LEFT * 0.1 + UP * 0.01, base + DOWN * 0.16 + RIGHT * sgn * 0.12, base + RIGHT * 0.1 + UP * 0.01,
        ]).set_stroke(color, STROKE).set_fill(PANEL, 1)
        mask = Line(base + LEFT * 0.085, base + RIGHT * 0.085).set_stroke(PANEL, STROKE * 1.6)
        label.move_to(self.frame)
        self.label = label
        self.add(self.frame, tail, mask, label)


# ---------------------------------------------------------------- arrows
def mono_char_width(size: float) -> float:
    return mono("M" * 20, size).width / 20


def mono_line(s: str, size: float, color=FG) -> Text:
    """Monospace line that preserves leading indentation (stored as .indent)."""
    stripped = s.lstrip(" ")
    t = mono(stripped if stripped else " ", size, color)
    t.indent = (len(s) - len(stripped)) * mono_char_width(size)
    return t


def arrow(start, end, color=FG, opacity=0.85, width=2.0, tip=0.13, buff=0.0):
    a = Arrow(np.array(start, dtype=float), np.array(end, dtype=float), buff=buff, stroke_width=width,
              tip_length=tip, max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=100,
              color=color)
    a.set_stroke(opacity=opacity)
    a.get_tip().set_fill(color, opacity)
    return a


def labeled_arrow(start, end, label=None, color=FG, label_color=MUTED, size=TINY + 1,
                  side=1, offset=0.2, **kw) -> VGroup:
    a = arrow(start, end, color=color, **kw)
    g = VGroup(a)
    if label:
        t = txt(label, size, label_color)
        v = np.array(end, dtype=float) - np.array(start, dtype=float)
        ang = np.arctan2(v[1], v[0])
        if ang > PI / 2:
            ang -= PI
        if ang < -PI / 2:
            ang += PI
        t.rotate(ang)
        normal = np.array([-np.sin(ang), np.cos(ang), 0])
        t.move_to(a.get_center() + normal * offset * side)
        g.add(t)
        g.label = t
    g.arrow = a
    return g


def curved_arrow(start, end, angle=-PI / 3, color=FG, opacity=0.85, width=2.0, tip=0.13):
    a = CurvedArrow(np.array(start, dtype=float), np.array(end, dtype=float), angle=angle,
                    stroke_width=width, color=color, tip_length=tip)
    a.set_stroke(opacity=opacity)
    a.get_tip().set_fill(color, opacity).set_stroke(width=0)
    return a


# ---------------------------------------------------------------- windows
class Window(VGroup):
    """Generic app window: rounded frame + title bar with three dots."""

    def __init__(self, width=4.0, height=2.6, title="", color=FAINT, title_color=DIM, bar=0.36, **kw):
        super().__init__(**kw)
        self.frame = RoundedRectangle(width=width, height=height, corner_radius=0.14)
        self.frame.set_stroke(color, 1.6).set_fill(PANEL, 1)
        top = self.frame.get_top()
        self.bar_h = bar
        sep = Line(top + DOWN * bar + LEFT * width / 2, top + DOWN * bar + RIGHT * width / 2).set_stroke(color, 1.2)
        dots = VGroup(*[Dot(radius=0.045, color=c) for c in ("#5a4a4d", "#5a564a", "#4a5a52")])
        dots.arrange(RIGHT, buff=0.09).move_to(self.frame.get_corner(UL) + RIGHT * 0.32 + DOWN * bar / 2)
        self.title = mono(title, 15, title_color).move_to(top + DOWN * bar / 2) if title else VGroup()
        self.add(self.frame, sep, dots, self.title)
        self.w, self.h = width, height

    @property
    def body_top_left(self):
        return self.frame.get_corner(UL) + DOWN * (self.bar_h + 0.2) + RIGHT * 0.22


class Terminal(Window):
    """Terminal window. Use `next_line()` to create a positioned text line (not yet added)."""

    def __init__(self, width=4.0, height=2.6, title="terminal", font_size=18, line_gap=1.55, **kw):
        super().__init__(width, height, title, **kw)
        self.fs = font_size
        self.line_h = font_size / 48 * 0.5 * line_gap
        self.n = 0

    def next_line(self, s: str, color=FG) -> Text:
        t = mono_line(s, self.fs, color)
        anchor = self.body_top_left + DOWN * self.n * self.line_h + RIGHT * t.indent
        t.move_to(anchor, aligned_edge=LEFT)
        t.set_y(anchor[1] - self.line_h * 0.35)
        self.n += 1
        return t

    def reset_cursor(self):
        self.n = 0


class Browser(Window):
    def __init__(self, width=3.6, height=2.0, url="", **kw):
        super().__init__(width, height, "", **kw)
        top = self.frame.get_top()
        self.url_box = RoundedRectangle(width=width * 0.62, height=0.22, corner_radius=0.11)
        self.url_box.set_stroke(FAINT, 1.2).set_fill(PANEL_2, 1).move_to(top + DOWN * self.bar_h / 2 + RIGHT * 0.25)
        self.add(self.url_box)
        self.url = self.make_url(url)
        self.add(self.url)

    @property
    def body_center(self):
        return self.frame.get_center() + DOWN * self.bar_h / 2

    def make_url(self, s):
        return mono(s, 15, MUTED).move_to(self.url_box)


class CodeEditor(Window):
    """Read-only code view with line numbers."""

    def __init__(self, width=5.0, height=3.4, title="", font_size=19, line_gap=1.65, **kw):
        super().__init__(width, height, title, **kw)
        self.fs = font_size
        self.line_h = font_size / 48 * 0.5 * line_gap
        self.lines = VGroup()
        self.numbers = VGroup()

    def line_pos(self, i):
        return self.body_top_left + DOWN * i * self.line_h

    def make_line(self, i, s, color=FG):
        """Return (number, text) mobjects for code line i (0-based), positioned."""
        y_anchor = self.line_pos(i)
        num = mono(str(i + 1), self.fs, DIM)
        num.move_to(y_anchor, aligned_edge=LEFT)
        code = mono_line(s, self.fs, color)
        code.move_to(y_anchor + RIGHT * (0.42 + code.indent), aligned_edge=LEFT)
        # vertical alignment: use the same row centre for both
        row_y = y_anchor[1] - self.line_h * 0.35
        num.set_y(row_y)
        code.set_y(row_y)
        return num, code

    def row_highlight(self, i, color=RED, opacity=0.14):
        y = self.line_pos(i)[1] - self.line_h * 0.35
        r = Rectangle(width=self.w - 0.12, height=self.line_h * 1.02)
        r.set_stroke(width=0).set_fill(color, opacity).move_to([self.frame.get_center()[0], y, 0])
        return r


# ---------------------------------------------------------------- agent marks
class AgentBadge(VGroup):
    """The agent as a small teal pill: ✦ agent"""

    def __init__(self, text="agent", size=22, color=TEAL, **kw):
        super().__init__(**kw)
        star = icons.spark_icon(0.26, color)
        label = en(text, size, color)
        content = VGroup(star, label).arrange(RIGHT, buff=0.1)
        h = 0.46
        self.frame = RoundedRectangle(width=content.width + 0.42, height=h, corner_radius=h / 2)
        self.frame.set_stroke(color, STROKE).set_fill(PANEL, 1)
        content.move_to(self.frame)
        self.star = star
        self.add(self.frame, content)


class Token(VGroup):
    """Glowing dot that travels around diagrams."""

    def __init__(self, color=TEAL, r=0.09, **kw):
        super().__init__(**kw)
        halo = VGroup(*[Circle(radius=r * k).set_stroke(width=0).set_fill(color, 0.10) for k in (3.2, 2.2)])
        core = Circle(radius=r).set_stroke(width=0).set_fill(color, 1)
        self.add(halo, core)


def chapter_tag(num: str, title: str) -> VGroup:
    n = bn(num, 22, DIM)
    bar = Line(UP * 0.16, DOWN * 0.16).set_stroke(FAINT, 2)
    t = bn(title, 22, MUTED)
    g = VGroup(n, bar, t).arrange(RIGHT, buff=0.18)
    g.to_corner(UL, buff=0.42)
    return g


def labeled_icon(icon: Mobject, label: str, sub: str | None = None, color=FG, size=24, sub_size=19) -> VGroup:
    """Icon with a label (and optional local-language meaning) underneath."""
    t = txt(label, size, color)
    g = VGroup(icon, t).arrange(DOWN, buff=0.14)
    if sub:
        s = bn(sub, sub_size, MUTED)
        s.next_to(t, DOWN, buff=0.06)
        g.add(s)
    return g


def dim(m: Mobject, opacity: float = 0.2):
    """Animation that fades a mobject to `opacity` while preserving zone styling."""
    from manim import AnimationGroup
    if isinstance(m, Zone):
        anims = [m.outline.animate.set_stroke(opacity=0.7 * opacity),
                 m.fill.animate.set_fill(opacity=0.045 * opacity)]
        if m.label is not None:
            anims.append(m.label.animate.set_opacity(opacity))
        return AnimationGroup(*anims)
    # fade() scales fill and stroke opacity multiplicatively, so outline-only
    # shapes (fill opacity 0) stay hollow instead of revealing a default fill.
    return m.animate.fade(1 - opacity)


def pulse(m: Mobject, scale: float = 1.07, run_time: float = 0.6):
    """Gentle there-and-back scale pulse that never recolours fills."""
    from manim import there_and_back
    return m.animate(rate_func=there_and_back, run_time=run_time).scale(scale)


def glow(m: VMobject, color: str, width: float = 6.0, run_time: float = 0.8):
    """Flash a thick outline copy of `m` in `color` that fades away."""
    from manim import FadeOut
    g = m.copy().set_fill(opacity=0).set_stroke(color, width, opacity=0.9)
    return FadeOut(g, scale=1.08, run_time=run_time)
