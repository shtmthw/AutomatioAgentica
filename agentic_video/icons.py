"""
Minimal line icons built from manim primitives (no image assets).
Every function returns a VGroup centred on ORIGIN with the given height.
"""
from __future__ import annotations

import numpy as np
from manim import (
    Annulus, Arc, Circle, Dot, Ellipse, Line, Polygon, Rectangle, RoundedRectangle,
    VGroup, VMobject, Triangle, UP, DOWN, LEFT, RIGHT, ORIGIN, PI, TAU,
)

from .style import BG, PANEL, FG, BLUE, TEAL, AMBER, RED, MUTED, STROKE, mono


def _sw(h: float, base: float = 2.2) -> float:
    """Stroke width that scales mildly with icon size."""
    return max(1.4, min(3.2, base * (h / 0.5) ** 0.35))


def gear(h: float = 0.3, color: str = BLUE) -> VGroup:
    r = h / 2
    ring = Annulus(inner_radius=r * 0.30, outer_radius=r * 0.74, color=color, fill_opacity=1).set_stroke(width=0)
    teeth = VGroup()
    for i in range(8):
        t = Rectangle(width=r * 0.34, height=r * 0.42).set_fill(color, 1).set_stroke(width=0)
        t.move_to(UP * r * 0.80)
        t.rotate(i * TAU / 8, about_point=ORIGIN)
        teeth.add(t)
    return VGroup(teeth, ring)


def chip(h: float = 1.2, color: str = FG, fill: str = PANEL, pins: int = 3) -> VGroup:
    """Processor-style chip used for the AI model (echoes the reference CPU)."""
    s = h / 1.32
    sw = _sw(h, 2.6)
    body = RoundedRectangle(width=s, height=s, corner_radius=s * 0.16)
    body.set_stroke(color, sw).set_fill(fill, 1)
    pin_group = VGroup()
    for side in range(4):
        for i in range(pins):
            off = (i - (pins - 1) / 2) * s * 0.24
            ln = Line(UP * (s / 2 + s * 0.03) + RIGHT * off, UP * (s / 2 + s * 0.16) + RIGHT * off)
            ln.set_stroke(color, sw)
            ln.rotate(side * PI / 2, about_point=ORIGIN)
            pin_group.add(ln)
    inner = VGroup(
        RoundedRectangle(width=s * 0.62, height=s * 0.12, corner_radius=0.03).shift(DOWN * s * 0.12),
        RoundedRectangle(width=s * 0.28, height=s * 0.11, corner_radius=0.03).shift(DOWN * s * 0.30 + LEFT * s * 0.17),
        RoundedRectangle(width=s * 0.28, height=s * 0.11, corner_radius=0.03).shift(DOWN * s * 0.30 + RIGHT * s * 0.17),
    ).set_stroke(color, sw * 0.6, opacity=0.8)
    g = VGroup(pin_group, body, inner)
    g.body = body
    g.label_anchor = body.get_center() + UP * s * 0.2
    return g


def chip_labeled(h: float = 1.2, label: str = "model", color: str = FG, size: float | None = None) -> VGroup:
    from .style import en
    g = chip(h, color)
    t = en(label, size or h * 24, color)
    t.move_to(g.label_anchor)
    if t.width > g.body.width * 0.84:
        t.scale_to_fit_width(g.body.width * 0.84)
    g.add(t)
    g.text = t
    return g


def file_icon(h: float = 0.5, color: str = FG, lines: int = 3) -> VGroup:
    w = h * 0.78
    c = w * 0.32
    page = Polygon(
        [-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2 - c, 0],
        [w / 2 - c, h / 2, 0], [-w / 2, h / 2, 0],
    ).set_stroke(color, _sw(h)).set_fill(PANEL, 1)
    fold = VMobject().set_points_as_corners(
        [[w / 2 - c, h / 2, 0], [w / 2 - c, h / 2 - c, 0], [w / 2, h / 2 - c, 0]]
    ).set_stroke(color, _sw(h) * 0.8)
    txt_lines = VGroup(*[
        Line([-w * 0.28, h * (0.08 - 0.2 * i), 0], [w * (0.28 if i < lines - 1 else 0.05), h * (0.08 - 0.2 * i), 0])
        for i in range(lines)
    ]).set_stroke(color, _sw(h) * 0.7, opacity=0.6)
    return VGroup(page, fold, txt_lines)


def folder_icon(h: float = 0.4, color: str = AMBER) -> VGroup:
    w = h * 1.3
    shape = Polygon(
        [-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h * 0.32, 0], [-w * 0.02, h * 0.32, 0],
        [-w * 0.14, h / 2, 0], [-w / 2, h / 2, 0],
    ).set_stroke(color, _sw(h)).set_fill(color, 0.12)
    return VGroup(shape)


def terminal_icon(h: float = 0.5, color: str = FG) -> VGroup:
    w = h * 1.3
    frame = RoundedRectangle(width=w, height=h, corner_radius=h * 0.14).set_stroke(color, _sw(h)).set_fill(PANEL, 1)
    chev = VMobject().set_points_as_corners(
        [[-w * 0.30, h * 0.16, 0], [-w * 0.12, 0, 0], [-w * 0.30, -h * 0.16, 0]]
    ).set_stroke(color, _sw(h))
    under = Line([-w * 0.04, -h * 0.18, 0], [w * 0.24, -h * 0.18, 0]).set_stroke(color, _sw(h))
    return VGroup(frame, chev, under)


def globe_icon(h: float = 0.5, color: str = FG) -> VGroup:
    r = h / 2
    sw = _sw(h)
    g = VGroup(
        Circle(radius=r).set_stroke(color, sw),
        Ellipse(width=r * 0.95, height=2 * r).set_stroke(color, sw * 0.8),
        Line(LEFT * r, RIGHT * r).set_stroke(color, sw * 0.8),
        Line(LEFT * r * 0.86 + UP * r * 0.5, RIGHT * r * 0.86 + UP * r * 0.5).set_stroke(color, sw * 0.6),
        Line(LEFT * r * 0.86 + DOWN * r * 0.5, RIGHT * r * 0.86 + DOWN * r * 0.5).set_stroke(color, sw * 0.6),
    )
    return g


def database_icon(h: float = 0.5, color: str = FG) -> VGroup:
    w = h * 0.86
    e = h * 0.26
    sw = _sw(h)
    top = Ellipse(width=w, height=e).move_to(UP * (h / 2 - e / 2)).set_stroke(color, sw).set_fill(PANEL, 1)
    left = Line(top.get_left(), top.get_left() + DOWN * (h - e)).set_stroke(color, sw)
    right = Line(top.get_right(), top.get_right() + DOWN * (h - e)).set_stroke(color, sw)
    mid = Arc(radius=1, start_angle=PI, angle=PI).stretch_to_fit_width(w).stretch_to_fit_height(e / 2)
    mid.move_to(top.get_center() + DOWN * (h - e) / 2 + DOWN * e / 4).set_stroke(color, sw * 0.8)
    bot = Arc(radius=1, start_angle=PI, angle=PI).stretch_to_fit_width(w).stretch_to_fit_height(e / 2)
    bot.move_to(top.get_center() + DOWN * (h - e) + DOWN * e / 4).set_stroke(color, sw)
    return VGroup(left, right, mid, bot, top)


def api_icon(h: float = 0.5, color: str = FG) -> VGroup:
    frame = RoundedRectangle(width=h * 1.15, height=h, corner_radius=h * 0.22).set_stroke(color, _sw(h)).set_fill(PANEL, 1)
    braces = mono("{ }", size=h * 52, color=color).move_to(frame)
    return VGroup(frame, braces)


def user_icon(h: float = 0.5, color: str = FG) -> VGroup:
    sw = _sw(h)
    head = Circle(radius=h * 0.2).set_stroke(color, sw).move_to(UP * h * 0.24)
    body = Arc(radius=h * 0.36, start_angle=0, angle=PI).set_stroke(color, sw)
    body.move_to(DOWN * h * 0.30)
    base = Line(body.get_corner(DOWN + LEFT), body.get_corner(DOWN + RIGHT)).set_stroke(color, sw)
    return VGroup(head, body, base)


def target_icon(h: float = 0.5, color: str = FG) -> VGroup:
    r = h / 2
    sw = _sw(h)
    return VGroup(
        Circle(radius=r).set_stroke(color, sw),
        Circle(radius=r * 0.62).set_stroke(color, sw),
        Dot(radius=r * 0.22, color=color),
    )


def spark_icon(h: float = 0.4, color: str = TEAL) -> VGroup:
    """Four-point star: the agent's mark."""
    r = h / 2
    k = r * 0.28
    pts = []
    for i in range(8):
        a = PI / 2 + i * PI / 4
        rr = r if i % 2 == 0 else k
        pts.append([rr * np.cos(a), rr * np.sin(a), 0])
    return VGroup(Polygon(*pts).set_fill(color, 1).set_stroke(width=0))


def check_icon(h: float = 0.3, color: str = TEAL) -> VGroup:
    m = VMobject().set_points_as_corners([[-h * 0.45, 0, 0], [-h * 0.12, -h * 0.32, 0], [h * 0.48, h * 0.34, 0]])
    return VGroup(m.set_stroke(color, _sw(h, 3.2)))


def cross_icon(h: float = 0.3, color: str = RED) -> VGroup:
    a = h * 0.38
    return VGroup(
        Line([-a, -a, 0], [a, a, 0]).set_stroke(color, _sw(h, 3.2)),
        Line([-a, a, 0], [a, -a, 0]).set_stroke(color, _sw(h, 3.2)),
    )


def warn_icon(h: float = 0.4, color: str = AMBER) -> VGroup:
    tri = Triangle().set_stroke(color, _sw(h)).set_fill(color, 0.08)
    tri.stretch_to_fit_height(h).stretch_to_fit_width(h * 1.12).move_to(ORIGIN)
    bar = Line(UP * h * 0.14, DOWN * h * 0.12).set_stroke(color, _sw(h)).shift(DOWN * h * 0.02)
    dot = Dot(radius=h * 0.045, color=color).shift(DOWN * h * 0.27)
    return VGroup(tri, bar, dot)


def lock_icon(h: float = 0.4, color: str = MUTED) -> VGroup:
    body = RoundedRectangle(width=h * 0.78, height=h * 0.56, corner_radius=h * 0.08)
    body.set_stroke(color, _sw(h)).set_fill(color, 0.12).shift(DOWN * h * 0.22)
    shackle = Arc(radius=h * 0.24, start_angle=0, angle=PI).set_stroke(color, _sw(h))
    shackle.next_to(body, UP, buff=0).shift(DOWN * 0.001)
    return VGroup(shackle, body)


def loop_icon(h: float = 0.4, color: str = FG) -> VGroup:
    arc = Arc(radius=h / 2, start_angle=PI * 0.6, angle=-TAU * 0.82).set_stroke(color, _sw(h))
    arc.add_tip(tip_length=h * 0.28, tip_width=h * 0.28)
    arc.get_tip().set_fill(color, 1).set_stroke(width=0)
    return VGroup(arc)


def trash_icon(h: float = 0.4, color: str = RED) -> VGroup:
    sw = _sw(h)
    can = Polygon([-h * 0.3, h * 0.3, 0], [h * 0.3, h * 0.3, 0], [h * 0.24, -h * 0.5, 0], [-h * 0.24, -h * 0.5, 0])
    can.set_stroke(color, sw)
    lid = Line([-h * 0.42, h * 0.38, 0], [h * 0.42, h * 0.38, 0]).set_stroke(color, sw)
    knob = Line([-h * 0.1, h * 0.5, 0], [h * 0.1, h * 0.5, 0]).set_stroke(color, sw)
    ribs = VGroup(*[Line([x, h * 0.15, 0], [x * 0.85, -h * 0.35, 0]) for x in (-h * 0.11, h * 0.11)]).set_stroke(color, sw * 0.7)
    return VGroup(can, lid, knob, ribs)


def fork_icon(h: float = 0.4, color: str = AMBER) -> VGroup:
    """A path that splits in two: 'wrong decision'."""
    sw = _sw(h)
    stem = Line(DOWN * h / 2, ORIGIN).set_stroke(color, sw)
    a = Line(ORIGIN, [-h * 0.36, h * 0.46, 0]).set_stroke(color, sw)
    b = Line(ORIGIN, [h * 0.36, h * 0.46, 0]).set_stroke(color, sw)
    return VGroup(stem, a, b)


def wrench_icon(h: float = 0.4, color: str = AMBER) -> VGroup:
    sw = _sw(h)
    handle = Line([-h * 0.38, -h * 0.38, 0], [h * 0.12, h * 0.12, 0]).set_stroke(color, sw * 1.5)
    head = Arc(radius=h * 0.2, start_angle=-PI * 0.25, angle=PI * 1.5).set_stroke(color, sw * 1.2)
    head.move_to([h * 0.2, h * 0.2, 0])
    return VGroup(handle, head)


ICONS = {
    "filesystem": file_icon,
    "terminal": terminal_icon,
    "browser": globe_icon,
    "api": api_icon,
    "database": database_icon,
}
