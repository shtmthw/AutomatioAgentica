"""
Inside the agent: reusable building blocks for lessons about how an agent works
(first used in Episode 02, "Inside an AI Agent").

    ModelBox       the AI model: text goes in on the left, comes out on the right
    HarnessFrame   the ordinary program around the model (amber frame + label)
    MessageCard    one message: coloured role tag (SYSTEM / USER / ASSISTANT / TOOL) + text
    MessageList    message cards stacked top to bottom, newest at the bottom
    ToolCard       a tool definition: NAME / DESCRIPTION / PARAMETERS
    ToolCallCard   a tool request written by the model (dashed blue: only a request)
    ContextWindow  a fixed-size container with a fill meter
    LoopDiagram    the Episode 01 agent loop (goal -> decide -> act -> observe -> evaluate)
    StepTracker    "step 3 of 9" with progress dots

Colours follow the house palette (style.py): MODEL = BLUE, HARNESS = AMBER,
TOOLS = TEAL (GREEN), errors = RED. Role tags: SYSTEM grey, USER white, ASSISTANT
blue, TOOL green. All components are plain VGroups; position them after building.
"""
from __future__ import annotations

import random
import textwrap

import numpy as np
from manim import (
    AnimationGroup, Arc, Circle, DashedVMobject, FadeIn, FadeOut, Line, Mobject, NORMAL, Polygon,
    Rectangle, RegularPolygon, ReplacementTransform, RoundedRectangle, VGroup, VMobject,
    UP, DOWN, LEFT, RIGHT, UR, ORIGIN, PI, TAU, there_and_back,
)

from . import icons
from .components import Pill, Zone, arrow, glow
from .style import (BG, PANEL, PANEL_2, FG, MUTED, DIM, FAINT, BLUE, TEAL, AMBER, VIOLET, RED, bn, en, mono, spaced)

__all__ = ["ROLE_COLORS", "wrap_text", "caps", "dashed_outline", "ModelBox", "HarnessFrame", "MessageCard",
           "MessageList", "bundle_copy", "ToolCard", "ToolCallCard", "meter_color", "ContextWindow",
           "LOOP_KEYS", "LOOP_COLORS", "LOOP_MEANINGS", "LoopNode", "LoopDiagram", "StepTracker",
           "shield_icon", "stop_icon", "pause_icon", "clock_icon", "coins_icon", "code_block", "paper"]

ROLE_COLORS = {"system": MUTED, "user": FG, "assistant": BLUE, "tool": TEAL}


def wrap_text(s: str, chars: int | None) -> str:
    return "\n".join(textwrap.wrap(s, chars)) if chars else s


def caps(s: str, size: float = 15, color: str = MUTED) -> VMobject:
    """Small upright uppercase label (role tags, row labels)."""
    return en(s.upper(), size, color, italic=False, weight=NORMAL)


def dashed_outline(shape: VMobject, color: str, width: float = 1.6, opacity: float = 0.95, dash: float = 0.09):
    perim = 2 * (shape.width + shape.height)
    src = shape.copy().set_stroke(color, width, opacity=opacity).set_fill(opacity=0)
    return DashedVMobject(src, num_dashes=max(16, int(perim / dash)), dashed_ratio=0.55)


# ---------------------------------------------------------------- the model
class ModelBox(VGroup):
    """Rounded blue box labelled AI MODEL (with the Episode 01 chip icon).
    Text enters at `in_port` (left) and leaves at `out_port` (right)."""

    def __init__(self, width=2.6, height=1.6, label="AI MODEL", color=BLUE, label_size=22, icon=True, **kw):
        super().__init__(**kw)
        self.frame = RoundedRectangle(width=width, height=height, corner_radius=min(0.24, height * 0.18))
        self.frame.set_stroke(color, 2.4).set_fill(PANEL, 1)
        self.tint = self.frame.copy().set_stroke(width=0).set_fill(color, 0.07)
        self.label = spaced(label, label_size, color, tracking=0.3, weight=NORMAL)
        parts = VGroup()
        self.icon = icons.chip(min(height * 0.4, 0.72), color) if icon else VGroup()
        if icon:
            parts.add(self.icon)
        parts.add(self.label)
        parts.arrange(DOWN, buff=0.14).move_to(self.frame)
        if parts.width > width * 0.84:
            parts.scale_to_fit_width(width * 0.84)
        if parts.height > height * 0.8:
            parts.scale_to_fit_height(height * 0.8)
        self.content = parts
        self.add(self.frame, self.tint, parts)
        self.accent = color

    @property
    def in_port(self):
        return self.frame.get_left()

    @property
    def out_port(self):
        return self.frame.get_right()

    def badge(self, text: str, color=None, size=17) -> Pill:
        """Small pill above the top-right corner, e.g. "call #2" (position recomputed on each call)."""
        c = color or self.accent
        p = Pill(en(text, size, c, italic=False, weight=NORMAL), c, pad_x=0.16, pad_y=0.06)
        p.move_to(self.frame.get_corner(UR) + LEFT * (p.width / 2 + 0.06) + UP * (p.height / 2 + 0.1))
        return p

    def reset_flash(self, run_time=0.8):
        """The model "forgets": a white flash, the content blanks and comes back."""
        return AnimationGroup(
            glow(self.frame, FG, 10, run_time),
            self.tint.animate(rate_func=there_and_back, run_time=run_time).set_fill(FG, 0.3),
            self.content.animate(rate_func=there_and_back, run_time=run_time).fade(0.85))

    def think(self, run_time=0.7):
        """Short "working" pulse."""
        return AnimationGroup(glow(self.frame, self.accent, 7, run_time),
                              self.tint.animate(rate_func=there_and_back, run_time=run_time).set_fill(self.accent, 0.22))


# ---------------------------------------------------------------- the harness
class HarnessFrame(VGroup):
    """Larger amber rounded frame around the model, labelled HARNESS (top-left, inside)."""

    def __init__(self, width=7.0, height=4.4, label="HARNESS", color=AMBER, label_size=20, fill_opacity=0.035,
                 sub=None, **kw):
        super().__init__(**kw)
        self.frame = RoundedRectangle(width=width, height=height, corner_radius=0.3)
        self.frame.set_stroke(color, 2.2).set_fill(color, fill_opacity)
        self.label = spaced(label, label_size, color, tracking=0.32, weight=NORMAL)
        head = VGroup(icons.gear(self.label.height * 1.35, color), self.label).arrange(RIGHT, buff=0.14)
        if sub:
            head.add(en(sub, label_size * 0.85, MUTED))
            head.arrange(RIGHT, buff=0.16)
        head.move_to(self.frame.get_corner(UP + LEFT) + RIGHT * (head.width / 2 + 0.32) + DOWN * (head.height / 2 + 0.26))
        self.head = head
        self.add(self.frame, head)
        self.accent = color

    def grow_from(self, mob: Mobject, run_time=1.1):
        """Animation: the frame grows out of `mob`'s outline, then the label fades in."""
        src = RoundedRectangle(width=mob.width, height=mob.height, corner_radius=0.24).move_to(mob)
        src.set_stroke(self.accent, 2.2).set_fill(self.accent, 0)
        return AnimationGroup(ReplacementTransform(src, self.frame), FadeIn(self.head, shift=DOWN * 0.08),
                              lag_ratio=0.55, run_time=run_time)


# ---------------------------------------------------------------- messages
class MessageCard(VGroup):
    """Horizontal card: coloured role tag on the left, short text (or `content`) on the right.
    `dashed=True` draws a dashed border (a request, not an action); `label` overrides the tag text."""

    TAG_W = 1.36

    def __init__(self, role: str, text: str | None = None, width=5.0, size=19, content: Mobject | None = None,
                 dashed=False, accent=None, text_color=FG, wrap=None, min_h=0.5, tag_size=14, label=None, **kw):
        super().__init__(**kw)
        c = ROLE_COLORS[role]
        self.role = role
        self.accent = accent or c
        tag_box = RoundedRectangle(width=self.TAG_W, height=0.3, corner_radius=0.08)
        tag_box.set_stroke(c, 1.3).set_fill(c, 0.14)
        tag_txt = caps(label or role, tag_size, c)
        if tag_txt.width > self.TAG_W - 0.16:
            tag_txt.scale_to_fit_width(self.TAG_W - 0.16)
        tag_txt.move_to(tag_box)
        self.tag = VGroup(tag_box, tag_txt)
        body = content if content is not None else bn(wrap_text(text or "", wrap), size, text_color)
        body_w = width - self.TAG_W - 0.42
        if body.width > body_w:
            body.scale_to_fit_width(body_w)
        h = max(min_h, body.height + 0.26)
        shape = RoundedRectangle(width=width, height=h, corner_radius=0.1)
        self.frame = shape.copy().set_stroke(self.accent, 1.4, opacity=0.6).set_fill(PANEL, 1)
        self.outline = None
        if dashed:
            self.frame.set_stroke(width=0)
            self.outline = dashed_outline(shape, self.accent, 1.7)
        self.tag.move_to(self.frame.get_left() + RIGHT * (0.12 + self.TAG_W / 2))
        body.next_to(self.tag, RIGHT, buff=0.18)
        self.body = body
        self.add(self.frame, *([self.outline] if self.outline else []), self.tag, body)


class MessageList:
    """Positions for message cards stacked top to bottom (newest at the bottom).

    The cards stay ordinary scene mobjects: `push()` positions a card and records it;
    animate it in yourself. `group()` is the whole list (e.g. to send it as a bundle)."""

    def __init__(self, top_left, gap=0.1):
        self.x0, self.y0 = float(top_left[0]), float(top_left[1])
        self.gap = gap
        self.cards: list = []

    @property
    def bottom(self) -> float:
        return self.cards[-1].get_bottom()[1] if self.cards else self.y0 + self.gap

    def next_point(self, card) -> np.ndarray:
        y = self.bottom - self.gap
        return np.array([self.x0 + card.width / 2, y - card.height / 2, 0.0])

    def place(self, card):
        card.move_to(self.next_point(card))
        return card

    def push(self, card):
        self.place(card)
        self.cards.append(card)
        return card

    def remove(self, card):
        self.cards.remove(card)

    def layout_targets(self) -> list:
        """(card, target centre) after removals, to animate the stack closing up."""
        out, y = [], self.y0
        for c in self.cards:
            out.append((c, np.array([self.x0 + c.width / 2, y - c.height / 2, 0.0])))
            y -= c.height + self.gap
        return out

    def group(self) -> VGroup:
        return VGroup(*self.cards)


def bundle_copy(mobs, scale=0.4) -> VGroup:
    """A shrunken copy of some cards (the whole conversation travelling as one bundle)."""
    return VGroup(*[m.copy() for m in mobs]).scale(scale)


# ---------------------------------------------------------------- tools
class ToolCard(VGroup):
    """A tool definition with three labelled rows: NAME, DESCRIPTION, PARAMETERS."""

    def __init__(self, name: str, description, params, width=5.2, value_size=20, label_size=14, color=TEAL,
                 label_w=1.75, pad=0.22, row_gap=0.22, **kw):
        super().__init__(**kw)
        vals = []
        for i, v in enumerate((name, description, params)):
            if isinstance(v, Mobject):
                vals.append(v)
            elif i == 0:
                vals.append(mono(v, value_size, FG))
            elif i == 1:
                vals.append(bn(v, value_size, FG))
            else:
                vals.append(mono(v, value_size - 1, FG))
        labs = [caps(t, label_size, color) for t in ("name", "description", "parameters")]
        avail = width - 2 * pad - label_w
        for v in vals:
            if v.width > avail:
                v.scale_to_fit_width(avail)
        row_h = [max(l.height, v.height) for l, v in zip(labs, vals)]
        height = sum(row_h) + row_gap * 2 + pad * 2
        self.frame = RoundedRectangle(width=width, height=height, corner_radius=0.14)
        self.frame.set_stroke(color, 1.8).set_fill(PANEL, 1)
        self.tint = self.frame.copy().set_stroke(width=0).set_fill(color, 0.05)
        x_lab = self.frame.get_left()[0] + pad
        x_val = x_lab + label_w
        y = self.frame.get_top()[1] - pad
        for l, v, h in zip(labs, vals, row_h):
            cy = y - h / 2
            l.move_to([x_lab, cy, 0], aligned_edge=LEFT)
            v.move_to([x_val, cy, 0], aligned_edge=LEFT)
            y -= h + row_gap
        self.labels = VGroup(*labs)
        self.values = VGroup(*vals)
        self.rows = [VGroup(l, v) for l, v in zip(labs, vals)]
        self.add(self.frame, self.tint, self.labels, self.values)
        self.accent = color


class ToolCallCard(VGroup):
    """A tool request produced by the model: TOOL + INPUT rows, dashed blue border."""

    def __init__(self, tool: str, input_text, width=4.2, size=19, color=BLUE, title="TOOL CALL", label_w=1.05,
                 pad=0.2, **kw):
        super().__init__(**kw)
        t_title = caps(title, 13, color)
        vals = [mono(tool, size, FG), input_text if isinstance(input_text, Mobject) else mono(input_text, size - 1, FG)]
        labs = [caps("tool", 14, color), caps("input", 14, color)]
        avail = width - 2 * pad - label_w
        for v in vals:
            if v.width > avail:
                v.scale_to_fit_width(avail)
        row_h = [max(l.height, v.height, 0.26) for l, v in zip(labs, vals)]
        height = t_title.height + 0.16 + sum(row_h) + 0.16 + 2 * pad
        shape = RoundedRectangle(width=width, height=height, corner_radius=0.14)
        self.frame = shape.copy().set_stroke(width=0).set_fill(PANEL, 1)
        self.tint = shape.copy().set_stroke(width=0).set_fill(color, 0.06)
        self.outline = dashed_outline(shape, color, 1.9)
        left = self.frame.get_left()[0] + pad
        top = self.frame.get_top()[1] - pad
        t_title.move_to([left, top - t_title.height / 2, 0], aligned_edge=LEFT)
        y = top - t_title.height - 0.16
        for l, v, h in zip(labs, vals, row_h):
            cy = y - h / 2
            l.move_to([left, cy, 0], aligned_edge=LEFT)
            v.move_to([left + label_w, cy, 0], aligned_edge=LEFT)
            y -= h + 0.16
        self.title = t_title
        self.labels = VGroup(*labs)
        self.values = VGroup(*vals)
        self.rows = [VGroup(l, v) for l, v in zip(labs, vals)]
        self.add(self.frame, self.tint, self.outline, t_title, self.labels, self.values)
        self.accent = color


# ---------------------------------------------------------------- context window
def meter_color(frac: float) -> str:
    return TEAL if frac < 0.6 else (AMBER if frac < 0.85 else RED)


class ContextWindow(VGroup):
    """Tall container (cards fill it top to bottom) with a thin fill meter on its right."""

    def __init__(self, width=3.4, height=4.8, label="CONTEXT WINDOW", color=FG, meter_gap=0.26, meter_w=0.17,
                 label_size=16, **kw):
        super().__init__(**kw)
        self.frame = RoundedRectangle(width=width, height=height, corner_radius=0.16)
        self.frame.set_stroke(color, 1.8, opacity=0.8).set_fill(PANEL_2, 0.55)
        self.label = spaced(label, label_size, MUTED, tracking=0.3, weight=NORMAL) if label else VGroup()
        if label:
            self.label.next_to(self.frame, UP, buff=0.16)
        self.meter_w, self.H = meter_w, height
        self.meter_box = RoundedRectangle(width=meter_w, height=height, corner_radius=meter_w / 2)
        self.meter_box.set_stroke(DIM, 1.3).set_fill(BG, 1)
        self.meter_box.move_to(self.frame.get_right() + RIGHT * (meter_gap + meter_w / 2))
        self.level = 0.0
        self.fill = self._fill_rect(0.0)
        self.add(self.frame, self.label, self.meter_box, self.fill)

    def _fill_rect(self, frac: float, color=None):
        inner = self.H - 0.08
        h = max(0.002, inner * min(1.0, frac))
        r = Rectangle(width=self.meter_w * 0.56, height=h).set_stroke(width=0)
        r.set_fill(color or meter_color(frac), 0.95 if frac > 0 else 0)
        r.move_to(self.meter_box.get_bottom() + UP * (0.04 + h / 2))
        return r

    def meter_to(self, frac: float, color=None):
        from manim import Transform
        self.level = frac
        return Transform(self.fill, self._fill_rect(frac, color))

    @property
    def inner_top_left(self):
        return self.frame.get_corner(UP + LEFT) + RIGHT * 0.18 + DOWN * 0.18


# ---------------------------------------------------------------- the agent loop (Episode 01)
LOOP_KEYS = ("decide", "act", "observe", "evaluate")
LOOP_COLORS = {"goal": FG, "decide": BLUE, "act": TEAL, "observe": AMBER, "evaluate": VIOLET, "done": TEAL}
LOOP_MEANINGS = {"goal": "instruction", "decide": "next step", "act": "use a tool", "observe": "the result",
                 "evaluate": "goal met?", "done": "answer"}
_ANG = {"decide": PI / 2, "act": 0.0, "observe": -PI / 2, "evaluate": PI}
_STATES = {"active": (1.0, 0.17, 1.0), "normal": (0.7, 0.045, 1.0), "dim": (0.22, 0.012, 0.3)}


class LoopNode(VGroup):
    def __init__(self, name, meaning, color, w, h, name_size, meaning_size):
        super().__init__()
        self.zone = Zone(w, h, color, None, radius=min(0.24, h / 3), fill_opacity=0.045)
        self.base = self.zone.shape.copy().set_stroke(width=0).set_fill(BG, 1)   # hides a token passing under
        self.name = en(name, name_size, color)
        self.meaning = bn(meaning, meaning_size, MUTED) if meaning else None
        lab = VGroup(self.name, *([self.meaning] if self.meaning else [])).arrange(DOWN, buff=0.03)
        if lab.width > w * 0.9:
            lab.scale_to_fit_width(w * 0.9)
        self.add(self.base, self.zone, lab)
        self.accent = color
        self.set_z_index(3)

    def state(self, s: str) -> list:
        o, f, t = _STATES[s]
        anims = [self.zone.outline.animate.set_stroke(opacity=o), self.zone.fill.animate.set_fill(opacity=f),
                 self.name.animate.set_opacity(t)]
        if self.meaning is not None:
            anims.append(self.meaning.animate.set_opacity(t))
        return anims


class _ArcArrow(VGroup):
    def __init__(self, line: VMobject, tip: VMobject, path: VMobject):
        super().__init__(line, tip, path)
        self.line, self.tip, self.path = line, tip, path

    def state(self, opacity: float) -> list:
        return [self.line.animate.set_stroke(opacity=opacity), self.tip.animate.set_fill(opacity=opacity)]


class LoopDiagram(VGroup):
    """The Episode 01 agent loop: four nodes on one true circle (decide, act, observe,
    evaluate), arrows as arc segments clipped at the node boxes, GOAL entering from above,
    optional DONE exit to the left, REPEAT label on the evaluate -> decide arc.

    Build it at the size you need (radius / node size / text sizes) instead of scaling it,
    so labels stay readable. `nodes[k]`, `arcs[k]` (da, ao, oe, ed), `leg(a, b)` gives
    the path a travelling Token takes between two stages."""

    def __init__(self, center=ORIGIN, radius=1.85, node_w=1.5, node_h=0.72, name_size=24, meaning_size=16,
                 meanings=True, goal=True, done=False, goal_gap=1.3, done_gap=2.3, repeat=True):
        super().__init__()
        self.c = np.array(center, dtype=float)
        self.R, self.nw, self.nh = radius, node_w, node_h

        def node(k):
            return LoopNode(k, LOOP_MEANINGS[k] if meanings else None, LOOP_COLORS[k], node_w, node_h,
                            name_size, meaning_size)

        self.nodes = {}
        for k in LOOP_KEYS:
            self.nodes[k] = node(k).move_to(self.ring_point(_ANG[k]))
        self.arcs = {"da": self._arc(PI / 2, 0.0), "ao": self._arc(0.0, -PI / 2), "oe": self._arc(-PI / 2, -PI),
                     "ed": self._arc(PI, PI / 2, VIOLET, 0.9)}
        self.add(*self.arcs.values(), *[self.nodes[k] for k in LOOP_KEYS])
        self.repeat = None
        if repeat:
            d = np.array([-0.7071, 0.7071, 0])
            self.repeat = en("repeat", max(14, name_size * 0.82), VIOLET).rotate(PI / 4)
            self.repeat.move_to(self.c + (radius + 0.22 + 0.2 * radius / 1.85) * d)
            self.add(self.repeat)
        self.goal = self.goal_arrow = self.goal_path = None
        if goal:
            self.goal = node("goal").move_to(self.ring_point(PI / 2) + UP * goal_gap)
            g_line = Line(self.goal.zone.shape.get_bottom() + DOWN * 0.06,
                          self.nodes["decide"].zone.shape.get_top() + UP * 0.08)
            self.goal_arrow = arrow(g_line.get_start(), g_line.get_end(), color=FG, tip=0.12)
            self.goal_path = g_line.set_stroke(opacity=0)
            self.nodes["goal"] = self.goal
            self.add(self.goal_arrow, self.goal_path, self.goal)
        self.done = self.done_arrow = self.done_path = None
        if done:
            e = self.nodes["evaluate"].zone.shape
            self.done = node("done").move_to(self.ring_point(PI) + LEFT * done_gap)
            d_line = Line(e.get_left() + LEFT * 0.1, self.done.zone.shape.get_right() + RIGHT * 0.1)
            self.done_arrow = arrow(d_line.get_start(), d_line.get_end(), color=TEAL, tip=0.12)
            self.done_path = d_line.set_stroke(opacity=0)
            self.nodes["done"] = self.done
            self.add(self.done_arrow, self.done_path, self.done)
        self.ring = Circle(radius=radius).move_to(self.c).set_stroke(opacity=0).set_fill(opacity=0)
        self.ring.rotate(PI / 2).flip(UP)         # start at the top (decide), run clockwise
        self.add(self.ring)
        # token paths run from node centre to node centre along the ring (continuous motion; the
        # token passes under the nodes), clockwise
        self.legs = {}
        for a, b in self._LEGS:
            delta = (_ANG[a] - _ANG[b]) % TAU
            self.legs[(a, b)] = Arc(radius=radius, start_angle=_ANG[a], angle=-delta, arc_center=self.c
                                    ).set_stroke(opacity=0)
        if goal:
            self.legs[("goal", "decide")] = Line(self.goal.get_center(), self.nodes["decide"].get_center()
                                                 ).set_stroke(opacity=0)
        if done:
            self.legs[("evaluate", "done")] = Line(self.nodes["evaluate"].get_center(), self.done.get_center()
                                                   ).set_stroke(opacity=0)
        self.add(*self.legs.values())

    # geometry ---------------------------------------------------------------
    def ring_point(self, a: float) -> np.ndarray:
        return self.c + self.R * np.array([np.cos(a), np.sin(a), 0.0])

    def _leave(self, a_node: float, direction: int, pad: float = 0.1) -> float:
        c = self.ring_point(a_node)
        hw, hh = self.nw / 2 + pad, self.nh / 2 + pad
        a = a_node
        while True:
            a += 0.002 * direction
            p = self.ring_point(a)
            if abs(p[0] - c[0]) > hw or abs(p[1] - c[1]) > hh:
                return a

    def _arc(self, a_from, a_to, color=MUTED, opacity=0.75):
        a0, a1 = self._leave(a_from, -1), self._leave(a_to, +1)
        path = Arc(radius=self.R, start_angle=a0, angle=a1 - a0, arc_center=self.c)
        line = path.copy().set_stroke(color, 1.9, opacity=opacity)
        line.add_tip(tip_length=0.13, tip_width=0.13)
        tip = line.pop_tips()[0]
        tip.set_fill(color, opacity).set_stroke(width=0)
        return _ArcArrow(line, tip, path.set_stroke(opacity=0))

    # paths --------------------------------------------------------------------
    _LEGS = {("decide", "act"): "da", ("act", "observe"): "ao", ("observe", "evaluate"): "oe",
             ("evaluate", "decide"): "ed"}

    def leg(self, a: str, b: str) -> VMobject:
        """Path for a travelling Token from stage a to stage b (centre to centre)."""
        return self.legs[(a, b)]

    def trail(self, tok: Mobject, color=TEAL, width=3.0, time=0.32):
        """A short fading tail behind a token (add it after the token is in place)."""
        from manim import TracedPath
        tr = TracedPath(tok.get_center, stroke_color=color, stroke_width=width, dissipating_time=time)
        tr.set_stroke(opacity=0.55)
        return tr

    @property
    def center(self) -> np.ndarray:
        return self.ring.get_center()

    # looks ----------------------------------------------------------------------
    def parts_in_order(self) -> list:
        """Mobjects in build order: goal, ring nodes, arcs (+ repeat), done."""
        out = []
        if self.goal is not None:
            out += [self.goal, self.goal_arrow]
        out += [self.nodes[k] for k in LOOP_KEYS]
        out += list(self.arcs.values())
        if self.repeat is not None:
            out.append(self.repeat)
        if self.done is not None:
            out += [self.done_arrow, self.done]
        return out

    def focus(self, key: str | None, dim_others=True) -> list:
        """Animations: `key` glows (active), the other stages dim (or return to normal)."""
        anims = []
        for k, n in self.nodes.items():
            if k == key:
                anims += n.state("active")
            else:
                anims += n.state("dim" if dim_others and key is not None else "normal")
        level = 0.28 if (dim_others and key is not None) else 0.75
        for a in self.arcs.values():
            anims += a.state(level)
        if key is not None:
            anims.append(glow(self.nodes[key].zone.shape, self.nodes[key].accent, 6, 0.7))
        return anims

    def all_lit(self) -> list:
        anims = []
        for n in self.nodes.values():
            anims += n.state("active")
        for a in self.arcs.values():
            anims += a.state(0.95)
        return anims

    def all_normal(self) -> list:
        return self.focus(None)

    def all_dim(self) -> list:
        anims = []
        for n in self.nodes.values():
            anims += n.state("dim")
        for a in self.arcs.values():
            anims += a.state(0.2)
        return anims


# ---------------------------------------------------------------- progress
class StepTracker(VGroup):
    """ "STEP 3 OF 9" with a row of progress dots."""

    def __init__(self, n=9, color=AMBER, dot_r=0.07, gap=0.2, **kw):
        super().__init__(**kw)
        self.n, self.accent, self.i = n, color, 0
        self.dots = VGroup(*[Circle(radius=dot_r).set_stroke(DIM, 1.5).set_fill(BG, 1) for _ in range(n)])
        self.dots.arrange(RIGHT, buff=gap)
        self.text = self._text(None)
        VGroup(self.text, self.dots).arrange(RIGHT, buff=0.32)
        self.add(self.text, self.dots)

    def _text(self, i: int | None) -> VGroup:
        num = en(str(i), 28, self.accent, italic=False, weight=NORMAL) if i else en("–", 28, DIM, italic=False)
        return VGroup(caps("step", 16, MUTED), num,
                      caps(f"of {self.n}", 16, DIM)).arrange(RIGHT, buff=0.11)

    def go(self, i: int) -> list:
        """Animations to step i (1-based)."""
        old, new = self.text, self._text(i).move_to(self.text, aligned_edge=LEFT)
        self.remove(old)
        self.add(new)
        self.text = new
        anims = [FadeOut(old, shift=UP * 0.08), FadeIn(new, shift=UP * 0.08)]
        for j, d in enumerate(self.dots):
            if j < i - 1:
                anims.append(d.animate.set_fill(MUTED, 0.55).set_stroke(MUTED, 1.5))
            elif j == i - 1:
                anims.append(d.animate.set_fill(self.accent, 1).set_stroke(self.accent, 1.5))
        self.i = i
        return anims


# ---------------------------------------------------------------- small icons
def shield_icon(h=0.6, color=AMBER, fill=PANEL) -> VGroup:
    w = h * 0.82
    pts = [UP * h / 2 + LEFT * w / 2, UP * h / 2 + RIGHT * w / 2, UP * h * 0.05 + RIGHT * w / 2,
           DOWN * h / 2, UP * h * 0.05 + LEFT * w / 2]
    s = Polygon(*pts).round_corners(radius=h * 0.12).set_stroke(color, 2.2).set_fill(fill, 1)
    return VGroup(s)


def stop_icon(h=0.5, color=RED) -> VGroup:
    o = RegularPolygon(8, start_angle=PI / 8).scale_to_fit_height(h).set_stroke(color, 2.2).set_fill(color, 0.85)
    bar = Rectangle(width=h * 0.52, height=h * 0.13).set_stroke(width=0).set_fill(BG, 1).move_to(o)
    return VGroup(o, bar)


def pause_icon(h=0.4, color=FG) -> VGroup:
    bars = VGroup(*[RoundedRectangle(width=h * 0.22, height=h, corner_radius=h * 0.06).set_stroke(width=0).set_fill(color, 1)
                    for _ in range(2)]).arrange(RIGHT, buff=h * 0.2)
    return bars


def clock_icon(h=0.4, color=FG) -> VGroup:
    c = Circle(radius=h / 2).set_stroke(color, 2.0)
    m = Line(ORIGIN, UP * h * 0.32).set_stroke(color, 2.0)
    hr = Line(ORIGIN, RIGHT * h * 0.22).set_stroke(color, 2.0)
    return VGroup(c, m, hr)


def coins_icon(h=0.4, color=AMBER) -> VGroup:
    g = VGroup()
    for i in range(3):
        e = RoundedRectangle(width=h * 0.9, height=h * 0.26, corner_radius=h * 0.13).set_stroke(color, 1.8).set_fill(PANEL, 1)
        e.shift(UP * i * h * 0.3)
        g.add(e)
    return g.move_to(ORIGIN)


def code_block(width=2.4, lines=4, size=0.05, color=MUTED, seed=7, gap=0.17) -> VGroup:
    """Abstract (unreadable) code: indented bars of varying length."""
    rnd = random.Random(seed)
    g = VGroup()
    for i in range(lines):
        indent = (0.0, 0.25, 0.25, 0.5, 0.25)[i % 5] * width * 0.4
        w = width * rnd.uniform(0.35, 0.8)
        ln = Line(ORIGIN, RIGHT * w).set_stroke(color, size * 60, opacity=0.75)
        ln.move_to([indent, -i * gap, 0], aligned_edge=LEFT)
        g.add(ln)
    return g.center()


def paper(width=1.0, height=0.7, lines=3, color=FG, fill=PANEL, line_color=MUTED) -> VGroup:
    """A sheet of paper / note with a few text lines."""
    sheet = RoundedRectangle(width=width, height=height, corner_radius=0.05).set_stroke(color, 1.6).set_fill(fill, 1)
    g = VGroup(sheet)
    for i in range(lines):
        frac = 0.75 if i < lines - 1 else 0.5
        y = height / 2 - 0.16 - i * (height - 0.28) / max(1, lines - 1) if lines > 1 else 0
        ln = Line(ORIGIN, RIGHT * width * frac).set_stroke(line_color, 2.2, opacity=0.8)
        ln.move_to([-width / 2 + 0.12, y, 0], aligned_edge=LEFT)
        g.add(ln)
    g.sheet = sheet
    return g
