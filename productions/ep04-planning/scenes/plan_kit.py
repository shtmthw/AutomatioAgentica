"""
Planning: reusable building blocks for lessons about agents that plan (first used in Episode 04,
"Planning"). Built on agentic_video/internals.py and Episode 03's memory_kit.py.

    PlanState      the single source of truth: goal, steps (id, text, status, new), numbering,
                   the current step. Pure data, no drawing.
    PlanPanel      cyan-outlined panel labelled PLAN: a GoalCard pinned at the top and one StepRow per
                   step, always drawn from its PlanState. It changes only through `apply()`, which needs
                   the update_plan tool call card that requested the change to be on screen.
    GoalCard       wide card with a GOAL tag and the user's goal in one line
    StepRow        status icon + number + short text (pending / active / done / removed / new)
    Spinner        the in-progress icon: a ring with a moving arc
    StepCounter    "STEP 2 OF 5", always computed from the PlanState it watches
    EvidenceLink   thin cyan curve from a done tick to the TOOL message that proves it
    ApprovalPrompt harness dialog: "Start with this plan?" with Approve / Change
    Feed           a message list that scrolls: old cards fade out at the top when it is full
    send_bundle    copies of the messages, the tool descriptions and the plan travel into the model

Kept next to this production's scenes (not in agentic_video/) so that adding it does not re-render
earlier productions. A later episode can copy it, or promote it into the shared library.
"""
from __future__ import annotations

import numpy as np
from manim import (Animation, AnimationGroup, LaggedStart, Succession, Transform, Arc, Circle, CubicBezier, Create, Dot, FadeIn, FadeOut, Line, NORMAL, PI,
                   Rectangle, RoundedRectangle, VGroup, VMobject, Write, DOWN, LEFT, RIGHT, UP, UL, UR, ORIGIN,
                   MoveAlongPath, there_and_back)

from agentic_video import icons as I
from agentic_video.components import Pill, Token, glow, pulse
from agentic_video.internals import caps, bundle_copy, dashed_outline
from agentic_video.style import AMBER, BG, BLUE, DIM, FAINT, FG, MUTED, PANEL, PANEL_2, RED, TEAL, VIOLET, bn, en, mono

PLAN = "#5ccbe4"         # the plan accent (cyan): the house TEAL already means TOOLS

PENDING, ACTIVE, DONE, REMOVED = "pending", "active", "done", "removed"


# ---------------------------------------------------------------- the single plan state
class PlanState:
    """Goal + ordered steps. Every number on screen (row numbers, the step counter) is derived from
    this object, so they can never disagree. Removed steps stay in the list (shown struck through)
    but get no number and do not count."""

    def __init__(self, goal: str, steps=(), ids=None):
        self.goal = goal
        self.steps: list[dict] = []
        for i, t in enumerate(steps):
            self.steps.append({"id": (ids[i] if ids else f"s{i + 1}"), "text": t, "status": PENDING, "new": False})

    def copy(self) -> "PlanState":
        c = PlanState(self.goal)
        c.steps = [dict(s) for s in self.steps]
        return c

    def get(self, sid: str) -> dict:
        for s in self.steps:
            if s["id"] == sid:
                return s
        raise KeyError(sid)

    def number(self, sid: str) -> int | None:
        n = 0
        for s in self.steps:
            if s["status"] != REMOVED:
                n += 1
            if s["id"] == sid:
                return n if s["status"] != REMOVED else None
        raise KeyError(sid)

    @property
    def total(self) -> int:
        return sum(1 for s in self.steps if s["status"] != REMOVED)

    @property
    def current(self) -> int | None:
        """Number of the step in progress; else the first pending one; else the last (all done)."""
        live = [s for s in self.steps if s["status"] != REMOVED]
        for st in (ACTIVE, PENDING):
            for i, s in enumerate(live):
                if s["status"] == st:
                    return i + 1
        return len(live) or None

    # changes (pure) ------------------------------------------------------------
    def set_status(self, sid, status):
        self.get(sid)["status"] = status

    def add(self, sid, text, before=None, status=PENDING):
        new = {"id": sid, "text": text, "status": status, "new": True}
        if before is None:
            self.steps.append(new)
        else:
            self.steps.insert([s["id"] for s in self.steps].index(before), new)

    def edit(self, sid, text):
        self.get(sid)["text"] = text


# ---------------------------------------------------------------- small pieces
def plan_icon(h=0.3, color=PLAN) -> VGroup:
    """Clipboard with three lines and two ticks."""
    w = h * 0.8
    board = RoundedRectangle(width=w, height=h, corner_radius=h * 0.1).set_stroke(color, 1.8).set_fill(PANEL, 1)
    clip = RoundedRectangle(width=w * 0.44, height=h * 0.16, corner_radius=h * 0.05).set_stroke(color, 1.6).set_fill(PANEL, 1)
    clip.move_to(board.get_top())
    rows = VGroup()
    for i in range(3):
        y = h * (0.16 - 0.22 * i)
        mark = (I.check_icon(h * 0.2, color) if i < 2 else Circle(radius=h * 0.05).set_stroke(color, 1.2))
        mark.move_to(board.get_center() + LEFT * w * 0.24 + UP * y)
        ln = Line(LEFT * w * 0.16, RIGHT * w * 0.2).set_stroke(color, 1.5, opacity=0.7)
        ln.move_to(board.get_center() + RIGHT * w * 0.1 + UP * y)
        rows.add(VGroup(mark, ln))
    return VGroup(board, clip, rows)


class Spinner(VGroup):
    """In-progress icon: a faint ring with a moving cyan arc (an updater turns it)."""

    def __init__(self, r=0.11, color=PLAN, speed=3.6, **kw):
        super().__init__(**kw)
        self.ring = Circle(radius=r).set_stroke(DIM, 1.6)
        self.arc = Arc(radius=r, start_angle=PI / 2, angle=-PI * 0.7).set_stroke(color, 3.0)
        self.add(self.ring, self.arc)
        self.add_updater(lambda m, dt: m.arc.rotate(-dt * speed, about_point=m.ring.get_center()))


def status_icon(status: str, r=0.11):
    if status == ACTIVE:
        return Spinner(r)
    if status == DONE:
        c = Circle(radius=r).set_stroke(PLAN, 1.8).set_fill(PLAN, 0.16)
        return VGroup(c, I.check_icon(r * 1.25, PLAN).move_to(c))
    ring = Circle(radius=r).set_stroke(MUTED if status == PENDING else DIM, 1.6)
    return VGroup(ring)


class StepRow(VGroup):
    """One plan step: status icon, number, text."""

    def __init__(self, num, text, status=PENDING, width=4.0, size=15, h=0.4, **kw):
        super().__init__(**kw)
        self.W, self.size, self.status = width, size, status
        self.bg = RoundedRectangle(width=width, height=h, corner_radius=0.08).set_stroke(width=0).set_fill(PLAN, 0)
        self.icon = status_icon(status).move_to(self.bg.get_left() + RIGHT * 0.22)
        self.num = self._num(num)
        self.text = bn(text, size, FG)
        avail = width - 0.85
        if self.text.width > avail:
            self.text.scale_to_fit_width(avail)
        self.text.move_to(self.bg.get_left() + RIGHT * 0.72, aligned_edge=LEFT)
        self.strike = None
        self.tag = None
        self.add(self.bg, self.icon, self.num, self.text)

    def _num(self, n):
        t = en(f"{n}" if n is not None else "–", self.size, MUTED, italic=False, weight=NORMAL)
        return t.move_to(self.bg.get_left() + RIGHT * 0.52)

    def icon_anims(self, status):
        old = self.icon
        new = status_icon(status).move_to(old)
        self.remove(old)
        self.add(new)
        self.icon = new
        self.status = status
        return [FadeOut(old, scale=0.7), FadeIn(new, scale=1.3)]

    def num_anims(self, n):
        old = self.num
        new = self._num(n)
        if old.text == new.text:
            return []
        self.remove(old)
        self.add(new)
        self.num = new
        return [FadeOut(old, shift=UP * 0.1), FadeIn(new, shift=UP * 0.1)]

    def strike_anims(self):
        self.strike = Line(self.text.get_left() + LEFT * 0.04, self.text.get_right() + RIGHT * 0.04)
        self.strike.set_stroke(MUTED, 2.0)
        self.add(self.strike)
        return [Create(self.strike), self.text.animate.fade(0.6), self.num.animate.fade(0.6), self.icon.animate.fade(0.6)]

    def new_tag(self):
        t = Pill(caps("new", 10, PLAN), PLAN, pad_x=0.1, pad_y=0.03)
        t.move_to(self.bg.get_right() + LEFT * (t.width / 2 + 0.06))
        return t


class GoalCard(VGroup):
    """Wide card: GOAL tag + the goal in one line."""

    def __init__(self, goal: str, width=4.2, size=14, color=PLAN, **kw):
        super().__init__(**kw)
        tag_box = RoundedRectangle(width=0.82, height=0.28, corner_radius=0.08).set_stroke(color, 1.3).set_fill(color, 0.16)
        tag = VGroup(tag_box, caps("goal", 11, color).move_to(tag_box))
        avail = width - tag_box.width - 0.42
        text = bn(goal, size, FG)
        if text.width > avail * 1.15:            # too long for one line: two balanced lines
            words = goal.split()
            best = min(range(1, len(words)), key=lambda i: max(len(" ".join(words[:i])), len(" ".join(words[i:]))))
            text = bn(" ".join(words[:best]) + "\n" + " ".join(words[best:]), size, FG)
        if text.width > avail:
            text.scale_to_fit_width(avail)
        h = max(0.46, text.height + 0.22)
        self.frame = RoundedRectangle(width=width, height=h, corner_radius=0.1).set_stroke(color, 1.5).set_fill(PANEL, 1)
        tag.move_to(self.frame.get_left() + RIGHT * (0.12 + tag_box.width / 2))
        text.next_to(tag, RIGHT, buff=0.16)
        self.tag, self.text = tag, text
        self.add(self.frame, tag, text)
        self.accent = color


# ---------------------------------------------------------------- the plan panel
class PlanPanel(VGroup):
    """The plan, kept by the harness: PLAN head, a pinned GoalCard, one StepRow per step.

    Drawn from `self.state` (a PlanState). The only way to change it on screen is

        panel.apply(scene, call_card, "status", "s1", ACTIVE)     # or "create", "add", "remove", "edit"

    which refuses to run unless `call_card` (the update_plan request) is on screen, then shows the
    harness applying the change: a token runs from the request to the panel, the panel flashes amber
    (the harness), and the rows, numbers and an attached StepCounter update together."""

    def __init__(self, state: PlanState, width=4.4, size=15, rows=6, row_h=0.4, gap=0.05, label="PLAN",
                 sub="kept by the harness", show_steps=True, empty=False, visible=None, lead=None, **kw):
        super().__init__(**kw)
        self.state = state.copy()
        self.W, self.size, self.row_h, self.gap = width, size, row_h, gap
        self.visible = visible            # show only these step ids (numbers still come from the state)
        self.lead = lead                  # optional note in the first row slot, e.g. "steps 1-4: done"
        head = VGroup(plan_icon(0.3), en(label, 19, PLAN, italic=False, weight=NORMAL)).arrange(RIGHT, buff=0.12)
        if sub:
            head.add(en(sub, 14, MUTED))
            head.arrange(RIGHT, buff=0.14)
        self.goal = GoalCard(self.state.goal, width - 0.3)
        body_h = rows * row_h + (rows - 1) * gap
        height = 0.22 + head.height + 0.16 + self.goal.height + 0.14 + body_h + 0.2
        self.frame = RoundedRectangle(width=width, height=height, corner_radius=0.18)
        self.frame.set_stroke(PLAN, 2.0).set_fill(PLAN, 0.035)
        self.base = self.frame.copy().set_stroke(width=0).set_fill(BG, 1)
        head.move_to(self.frame.get_corner(UL) + RIGHT * (head.width / 2 + 0.2) + DOWN * (head.height / 2 + 0.2))
        self.goal.next_to(head, DOWN, buff=0.16).set_x(self.frame.get_x())
        self.goal.next_to(head, DOWN, buff=0.16).set_x(self.frame.get_x())
        self.head = head
        self.rows: dict[str, StepRow] = {}
        self.tags: dict[str, Pill] = {}
        self.counter = None
        self.add(self.base, self.frame, head)
        self.goal_shown = not empty
        if not empty:
            self.add(self.goal)
        if lead is not None:
            lead.move_to(self.slot(0)).align_to(self.goal, LEFT).shift(RIGHT * 0.15)
            self.add(lead)
        if show_steps and not empty:
            for s in self._shown():
                self._make_row(s)
            self._layout(now=True)
            for s in self._shown():
                self.add(self.rows[s["id"]])

    # layout -----------------------------------------------------------------------
    @property
    def rows_top(self) -> float:
        return self.goal.get_bottom()[1] - 0.14

    def slot(self, i: int) -> np.ndarray:
        y = self.rows_top - self.row_h / 2 - i * (self.row_h + self.gap)
        return np.array([self.frame.get_x(), y, 0.0])

    def _make_row(self, s):
        r = StepRow(self.state.number(s["id"]), s["text"], s["status"], width=self.W - 0.3, size=self.size,
                    h=self.row_h)
        self.rows[s["id"]] = r
        return r

    def _shown(self):
        return [s for s in self.state.steps if self.visible is None or s["id"] in self.visible]

    def _layout(self, now=False):
        anims = []
        off = 1 if self.lead is not None else 0
        for i, s in enumerate(self._shown(), off):
            r = self.rows[s["id"]]
            if now:
                r.move_to(self.slot(i))
            else:
                anims.append(r.animate.move_to(self.slot(i)))
        return anims

    def row(self, sid: str) -> StepRow:
        return self.rows[sid]

    def row_by_number(self, n: int) -> StepRow:
        for s in self.state.steps:
            if self.state.number(s["id"]) == n:
                return self.rows[s["id"]]
        raise KeyError(n)

    def snapshot(self) -> VGroup:
        """A static copy of what the panel shows now (for bundles travelling into the model)."""
        c = self.copy()
        for m in c.get_family():
            m.clear_updaters()
        return c

    # changes ----------------------------------------------------------------------
    def apply(self, scene, call, op: str, *args, token=True, run_time=0.7, fast=False, **kw):
        fam = set()
        for m in scene.mobjects:
            fam.update(m.get_family())
        if call is None or call not in fam:
            raise RuntimeError("PlanPanel.apply: the plan may only change after an update_plan tool call is on screen")
        old_n = {s["id"]: self.state.number(s["id"]) for s in self.state.steps}
        anims = []
        for t in list(self.tags.values()):        # NEW tags last until the next change
            anims.append(FadeOut(t))
        self.tags.clear()
        for s in self.state.steps:
            s["new"] = False
        if op == "create":
            self.goal.next_to(self.head, DOWN, buff=0.16).set_x(self.frame.get_x())   # (not moved with an empty panel)
            steps = args[0]
            ids = kw.get("ids") or [f"s{i + 1}" for i in range(len(steps))]
            for sid, t in zip(ids, steps):
                self.state.steps.append({"id": sid, "text": t, "status": PENDING, "new": False})
            new_rows = [self._make_row(s) for s in self.state.steps]
            self._layout(now=True)
            if not self.goal_shown:
                self.goal_shown = True
                self.add(self.goal)
                anims.append(FadeIn(self.goal, shift=DOWN * 0.08))
        elif op == "status":
            sid, status = args
            self.state.set_status(sid, status)
            anims += self.rows[sid].icon_anims(status)
            if status == DONE:
                anims.append(glow(self.rows[sid].icon[0], PLAN, 6))
        elif op == "add":
            sid, text = args
            before = kw.get("before")
            status = kw.get("status", PENDING)
            demote = kw.get("demote")             # the previously active step goes back to pending
            if demote:
                self.state.set_status(demote, PENDING)
                anims += self.rows[demote].icon_anims(PENDING)
            self.state.add(sid, text, before=before, status=status)
            r = self._make_row(self.state.get(sid))
            i = [s["id"] for s in self._shown()].index(sid) + (1 if self.lead is not None else 0)
            r.move_to(self.slot(i))
            self._pending_layout = sid            # built after renumbering (see below)
            self.add(r)
            anims.append(FadeIn(r, shift=RIGHT * 0.25))
            tag = r.new_tag()
            room = tag.get_left()[0] - 0.08 - r.text.get_left()[0]
            if r.text.width > room:                 # leave room for the NEW tag
                left = r.text.get_left()
                r.text.scale_to_fit_width(room).move_to(left, aligned_edge=LEFT)
            self.tags[sid] = tag
            self.add(tag)
            anims.append(FadeIn(tag, scale=0.8))
        elif op == "remove":
            (sid,) = args
            self.state.set_status(sid, REMOVED)
            anims += self.rows[sid].strike_anims()
        elif op == "edit":
            sid, text = args
            self.state.edit(sid, text)
            r = self.rows[sid]
            nt = bn(text, self.size, FG)
            if nt.width > r.W - 0.85:
                nt.scale_to_fit_width(r.W - 0.85)
            nt.move_to(r.text, aligned_edge=LEFT)
            old = r.text
            r.remove(old)
            r.add(nt)
            r.text = nt
            anims += [FadeOut(old, shift=UP * 0.1), FadeIn(nt, shift=UP * 0.1)]
        else:
            raise ValueError(op)
        for s in self.state.steps:                # renumber every row from the state
            if op == "create" or s["id"] not in old_n or s["id"] not in self.rows:
                continue
            anims += self.rows[s["id"]].num_anims(self.state.number(s["id"]))
        if getattr(self, "_pending_layout", None):
            sid_new = self._pending_layout
            self._pending_layout = None
            anims += [a for a, s in zip(self._layout(), self._shown()) if s["id"] != sid_new]
        if self.counter is not None:
            anims += self.counter.update_from(self.state)
        # ---- play: the request travels to the panel, then the harness applies it
        if token:
            tok = Token(PLAN, 0.075).move_to(call.get_center())
            target = (np.array([self.frame.get_x(), self.rows_top - 0.9, 0.0]) if op == "create"
                      else self._target_point(op, args))
            path = Line(call.get_left() if call.get_x() > self.get_x() else call.get_right(), target)
            tok.move_to(path.get_start())
            edge = getattr(call, "outline", None) or getattr(call, "frame", None) or call
            scene.play(glow(edge, BLUE, 4, 0.5), FadeIn(tok, scale=0.5), run_time=0.08 if fast else 0.25)
            scene.play(MoveAlongPath(tok, path), run_time=0.2 if fast else 0.5)
            scene.remove(tok)
        if fast:
            run_time = min(run_time, 0.3)
        if op == "create":
            self.add(*new_rows)
            scene.play(glow(self.frame, AMBER, 7, run_time), *anims,
                       LaggedStart(*[FadeIn(r, shift=RIGHT * 0.15) for r in new_rows], lag_ratio=0.15),
                       run_time=max(run_time, 1.0))
            return
        if op == "add":
            r = self.rows[args[0]]
            scene.play(glow(self.frame, AMBER, 7, run_time), *anims, run_time=run_time)
            scene.play(glow(r.bg.copy().set_fill(opacity=0).set_stroke(PLAN, 1), PLAN, 8, 0.6),
                       r.bg.animate(rate_func=there_and_back).set_fill(PLAN, 0.22), run_time=0.7)
            return
        scene.play(glow(self.frame, AMBER, 7, run_time), *anims, run_time=run_time)

    def _target_point(self, op, args):
        sid = args[0]
        if sid in self.rows:
            return self.rows[sid].icon.get_center()
        return self.frame.get_center()


# ---------------------------------------------------------------- counter
class StepCounter(VGroup):
    """ "STEP 2 OF 5": always computed from a PlanState (attach it with `panel.counter = c`)."""

    def __init__(self, state: PlanState, color=PLAN, size=24, **kw):
        super().__init__(**kw)
        self.accent, self.size = color, size
        self.cur, self.tot = state.current, state.total
        self.frame = RoundedRectangle(width=2.5, height=0.52, corner_radius=0.26).set_stroke(color, 1.6).set_fill(PANEL, 1)
        self.text = self._text(self.cur, self.tot)
        self.add(self.frame, self.text)

    def _text(self, cur, tot):
        g = VGroup(caps("step", 15, MUTED), en(str(cur or "–"), self.size, self.accent, italic=False, weight=NORMAL),
                   caps("of", 15, MUTED), en(str(tot), self.size, FG, italic=False, weight=NORMAL)).arrange(RIGHT, buff=0.12)
        return g.move_to(self.frame)

    def update_from(self, state: PlanState) -> list:
        cur, tot = state.current, state.total
        anims = []
        if cur != self.cur:
            old, new = self.text[1], self._text(cur, tot)[1]
            new.move_to(old)
            self.text.submobjects[1] = new
            anims += [FadeOut(old, shift=UP * 0.12), FadeIn(new, shift=UP * 0.12)]
        if tot != self.tot:
            old, new = self.text[3], self._text(cur, tot)[3]
            new.move_to(old)
            self.text.submobjects[3] = new
            anims += [FadeOut(old, shift=UP * 0.12), FadeIn(new, shift=UP * 0.12), glow(self.frame, PLAN, 5)]
        self.cur, self.tot = cur, tot
        return anims


# ---------------------------------------------------------------- evidence
class EvidenceLink(VGroup):
    """Thin cyan curve from a done tick to the TOOL message that proves it, with end dots."""

    def __init__(self, tick, card, color=PLAN, bend=0.6, label=None, **kw):
        super().__init__(**kw)
        self.hl = self.ring = None
        if isinstance(tick, StepRow):             # the done row is highlighted, its tick ringed; the link leaves the row
            self.hl = tick.bg.copy().set_fill(color, 0.14).set_stroke(color, 1.4, opacity=0.9)
            self.ring = Circle(radius=tick.icon.width * 0.85).move_to(tick.icon).set_stroke(color, 2.0)
            tick = tick.bg
        a = tick.get_right() + RIGHT * 0.02
        if card.get_x() > tick.get_x():
            b = card.get_left() + LEFT * 0.03
            k = max(0.25, min(bend, abs(b[0] - a[0]) * 0.6))
            ca, cb = a + RIGHT * k, b + LEFT * k
        else:
            b = card.get_right() + RIGHT * 0.03
            ca, cb = a + RIGHT * bend, b + RIGHT * bend
        self.curve = CubicBezier(a, ca, cb, b).set_stroke(color, 2.4, opacity=0.95)
        self.dots = VGroup(Dot(a, radius=0.05, color=color), Dot(b, radius=0.05, color=color))
        self.add(*[m for m in (self.hl, self.ring) if m is not None], self.curve, self.dots)
        self.label = None
        if label:
            self.label = Pill(VGroup(I.check_icon(0.16, color), caps(label, 12, color)).arrange(RIGHT, buff=0.08), color,
                              pad_x=0.12, pad_y=0.04)
            self.label.move_to(self.curve.point_from_proportion(0.5) + UP * 0.22)
            self.add(self.label)

    def draw(self, run_time=0.8):
        anims = [Create(self.curve), FadeIn(self.dots)] + [FadeIn(m) for m in (self.hl, self.ring) if m is not None]
        if self.label is not None:
            anims.append(FadeIn(self.label, shift=UP * 0.06))
        return AnimationGroup(*anims, run_time=run_time)


# ---------------------------------------------------------------- approval
class ApprovalPrompt(VGroup):
    """Small harness dialog to the user: "Start with this plan?" with Approve / Change."""

    def __init__(self, question="Start with this plan?", width=3.6, **kw):
        super().__init__(**kw)
        head = VGroup(I.gear(0.24, AMBER), caps("harness", 12, AMBER), caps("asks", 12, MUTED)).arrange(RIGHT, buff=0.1)
        q = bn(question, 19, FG)
        self.approve = Pill(VGroup(I.check_icon(0.18, PLAN), en("Approve", 17, FG, italic=False)).arrange(RIGHT, buff=0.1),
                            PLAN, pad_x=0.18, pad_y=0.07)
        self.change = Pill(en("Change", 17, FG, italic=False), MUTED, pad_x=0.2, pad_y=0.07)
        btns = VGroup(self.approve, self.change).arrange(RIGHT, buff=0.22)
        body = VGroup(head, q, btns).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        width = max(width, body.width + 0.5)
        self.frame = RoundedRectangle(width=width, height=body.height + 0.44, corner_radius=0.16)
        self.frame.set_stroke(AMBER, 1.8).set_fill(PANEL, 1)
        body.move_to(self.frame)
        self.add(self.frame, body)

    def press(self, which="approve"):
        b = self.approve if which == "approve" else self.change
        c = PLAN if which == "approve" else FG
        return [b.frame.animate.set_fill(c, 0.3), glow(b.frame, c, 6), pulse(b, 1.08)]


# ---------------------------------------------------------------- scrolling message list
class Feed:
    """Message cards stacked top to bottom inside [top, bottom]. When a new card does not fit, the
    oldest cards fade out at the top and the rest move up."""

    def __init__(self, x_left, top, bottom, gap=0.07):
        self.x0, self.top, self.bottom, self.gap = x_left, top, bottom, gap
        self.cards: list = []

    def _targets(self, cards):
        out, y = [], self.top
        for c in cards:
            out.append(np.array([self.x0 + c.width / 2, y - c.height / 2, 0.0]))
            y -= c.height + self.gap
        return out

    def used(self, cards=None) -> float:
        cs = self.cards if cards is None else cards
        return sum(c.height for c in cs) + self.gap * max(0, len(cs) - 1)

    def push(self, card, shift=DOWN * 0.15) -> list:
        cards = self.cards + [card]
        gone = []
        while self.used(cards) > self.top - self.bottom and len(cards) > 1:
            gone.append(cards.pop(0))
        self.cards = cards
        tg = self._targets(cards)
        card.move_to(tg[-1])
        anims = [FadeOut(c, shift=UP * 0.3) for c in gone]
        anims += [c.animate.move_to(p) for c, p in zip(cards[:-1], tg[:-1])]
        anims.append(FadeIn(card, shift=shift))
        return anims

    def clear(self) -> list:
        cs, self.cards = self.cards, []
        return [FadeOut(c) for c in cs]

    def group(self) -> VGroup:
        return VGroup(*self.cards)


# ---------------------------------------------------------------- calling the model
def send_bundle(scene, model, parts, run_time=0.75, scale=0.3, think=True):
    """Shrunken copies of `parts` (message cards, tool descriptions, the plan panel...) travel into the
    model's input as one bundle. Pass the PlanPanel itself: its static snapshot is used."""
    copies = []
    for p in parts:
        c = p.snapshot() if isinstance(p, PlanPanel) else p.copy()
        for m in c.get_family():
            m.clear_updaters()
        copies.append(c)
    b = VGroup(*copies)
    targets = []
    for c in copies:
        t = c.copy().scale(scale)
        targets.append(t)
    tg = VGroup(*targets).arrange(DOWN, buff=0.04)
    tg.move_to(model.in_port + LEFT * (tg.width / 2 + 0.12))
    scene.add(b)
    scene.play(*[c.animate.become(t) for c, t in zip(copies, targets)], run_time=run_time)
    scene.play(*[c.animate.move_to(model.get_center()).scale(0.4).set_opacity(0) for c in copies],
               *([model.think(0.5)] if think else []), run_time=0.45)
    scene.remove(b, *copies)


def bundle_anim(model, parts, run_time=0.7, scale=0.28):
    """One animation (to play together with others): static copies of `parts` shrink, travel into the
    model's input and fade into it, while the model pulses."""
    copies = []
    for p in parts:
        c = p.snapshot() if isinstance(p, PlanPanel) else p.copy()
        for m in c.get_family():
            m.clear_updaters()
        copies.append(c)
    tg = VGroup(*[c.copy().scale(scale) for c in copies]).arrange(DOWN, buff=0.03)
    tg.move_to(model.in_port + LEFT * (tg.width / 2 + 0.1))
    seqs = []
    for c, t in zip(copies, tg):
        seqs.append(Succession(Transform(c, t, run_time=run_time * 0.6),
                               c.animate(run_time=run_time * 0.4).move_to(model.get_center()).scale(0.3).set_opacity(0)))
    return AnimationGroup(*seqs, model.think(run_time), _cleanup(copies))


class _cleanup(Animation):
    """Removes the bundle copies when the bundle animation ends."""

    def __init__(self, mobs, **kw):
        self.mobs = mobs
        super().__init__(VGroup(), **kw)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        scene.remove(*self.mobs)


def bundle_label(parts_text, color=MUTED):
    """Small "sent: messages + tools + plan" legend."""
    return caps(parts_text, 12, color)


def tool_desc_card(name="update_plan", desc="Creates or updates the list of steps for the current task", width=4.4,
                   size=13, new=False):
    """Compact tool description: name + one line; cyan when it is the plan tool."""
    color = PLAN if name == "update_plan" else TEAL
    n = mono(name, size + 1, color)
    head = VGroup(n)
    tag = None
    if new:
        tag = Pill(caps("new", 10, PLAN), PLAN, pad_x=0.1, pad_y=0.03)
        head.add(tag)
        head.arrange(RIGHT, buff=0.16)
    d = wrapped(desc, size - 1, MUTED, width - 0.4, font=bn)
    body = VGroup(head, d).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    if body.width > width - 0.4:
        body.scale_to_fit_width(width - 0.4)
    fr = RoundedRectangle(width=width, height=body.height + 0.24, corner_radius=0.08).set_stroke(color, 1.3, opacity=0.8)
    fr.set_fill(PANEL, 1)
    body.move_to(fr.get_left() + RIGHT * (body.width / 2 + 0.18))
    g = VGroup(fr, body)
    g.frame = fr
    g.tag = tag
    return g


def wrapped(text: str, size, color, max_w: float, font=None):
    """Text on one line, or on two (or more) balanced lines when it is wider than max_w; never shrunk
    unless a single word is wider than max_w."""
    font = font or mono
    one = font(text, size, color)
    if one.width <= max_w or " " not in text:
        if one.width > max_w:
            one.scale_to_fit_width(max_w)
        return one
    words = text.split(" ")
    for n in range(2, 5):                              # fewest lines that fit, as balanced as possible
        best = None
        import itertools
        for cut in itertools.combinations(range(1, len(words)), n - 1):
            idx = (0, *cut, len(words))
            lines = [" ".join(words[idx[k]:idx[k + 1]]) for k in range(n)]
            longest = max(len(x) for x in lines)
            if best is None or longest < best[0]:
                best = (longest, lines)
        g = VGroup(*[font(x, size, color) for x in best[1]]).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
        if g.width <= max_w:
            return g
    g.scale_to_fit_width(max_w)
    return g


CARD_TAG_W = 1.2                                      # SizedCard.TAG_W


def call_msg(tool: str, arg: str | None = None, width=4.2, size=12):
    """ASSISTANT message holding a tool call (dashed: only a request), always at `size`: when the
    call does not fit on one line, the argument goes on its own line(s) instead of shrinking."""
    from memory_kit import SizedCard, call_line
    avail = width - CARD_TAG_W - 0.36
    one = call_line(tool, arg, size)
    if one.width <= avail:
        content = one
    else:
        head = VGroup(mono(tool, size, BLUE), en("→", size + 2, MUTED)).arrange(RIGHT, buff=0.1)
        content = VGroup(head, wrapped(arg, size, FG, avail)).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return SizedCard("assistant", content=content, width=width, height=max(0.3, content.height + 0.14), dashed=True)


def res_msg(text: str, width=4.2, size=12, color=FG):
    """TOOL message with a short result, wrapped (not shrunk) when it is long."""
    from memory_kit import SizedCard
    avail = width - CARD_TAG_W - 0.36
    content = wrapped(text, size, color, avail)
    return SizedCard("tool", content=content, width=width, height=max(0.3, content.height + 0.14))


def tools_stack(width=3.0, size=12, plan=True):
    """The tool descriptions as a small stack of names (read_file, run_command, edit_file, update_plan)."""
    names = ["read_file", "run_command", "edit_file"] + (["update_plan"] if plan else [])
    rows = VGroup(*[mono(n, size, PLAN if n == "update_plan" else TEAL) for n in names]).arrange(DOWN, buff=0.07,
                                                                                               aligned_edge=LEFT)
    head = caps("tools", 11, TEAL)
    body = VGroup(head, rows).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
    fr = RoundedRectangle(width=max(width, body.width + 0.3), height=body.height + 0.24, corner_radius=0.1)
    fr.set_stroke(TEAL, 1.3, opacity=0.8).set_fill(PANEL, 1)
    body.move_to(fr)
    g = VGroup(fr, body)
    g.frame, g.rows = fr, rows
    return g


GOAL = "Add a contact form that saves every message and shows a thank-you note"
STEPS = ["Look at how the website is organized", "Create the contact form page", "Save each submitted message",
         "Show a thank-you note after sending", "Test the whole thing"]
NEW_STEP = "Create a file to store messages"


def plan_state(n=5) -> PlanState:
    return PlanState(GOAL, STEPS[:n])


def plan_call(input_text, width=4.2, size=12, height=0.3):
    """ASSISTANT tool-call message for update_plan: `update_plan → step 1: in progress` (wraps, never shrinks)."""
    return call_msg("update_plan", input_text, width=width, size=size)


def ok_tag(text="checked", color=PLAN):
    return Pill(VGroup(I.check_icon(0.18, color), caps(text, 13, color)).arrange(RIGHT, buff=0.1), color, pad_x=0.16,
                pad_y=0.06)


def bad_tag(text="said, not checked", color=RED):
    return Pill(VGroup(en("?", 18, color, italic=False, weight=NORMAL), caps(text, 13, color)).arrange(RIGHT, buff=0.1),
                color, pad_x=0.16, pad_y=0.06)
