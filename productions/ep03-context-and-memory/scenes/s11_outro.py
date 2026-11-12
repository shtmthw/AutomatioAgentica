"""11 · Conclusion: the five summary lines (the recap of every topic), the open question that leads
to Episode 04 (planning), and the title card."""
from agentic_video.prelude import *
from memory_kit import *

LINES = [("The context window fills up, mostly with tool results.", TEAL),
         ("Context management means choosing what the model sees on each call.", FG),
         ("Keep tool results small, trim old messages, or summarize them. Each one loses something.", AMBER),
         ("Memory is text saved outside the context and brought back later.", MEMORY),
         ("The model never changes. Only the text it receives changes.", BLUE)]


def icon(i):
    if i == 0:
        bar = RoundedRectangle(width=0.14, height=0.42, corner_radius=0.07).set_stroke(DIM, 1.2)
        fill = Rectangle(width=0.08, height=0.3).set_stroke(width=0).set_fill(TEAL, 0.9)
        fill.move_to(bar.get_bottom() + UP * (0.04 + 0.15))
        return VGroup(bar, fill)
    if i == 1:
        return I.gear(0.36, AMBER)
    if i == 2:
        return VGroup(*[RoundedRectangle(width=0.42, height=h, corner_radius=0.03).set_stroke(c, 1.1).set_fill(c, 0.2)
                        for h, c in ((0.09, MUTED), (0.16, AMBER), (0.09, TEAL))]).arrange(DOWN, buff=0.04)
    if i == 3:
        return Notebook(0.42, label=None, sub=None).icon
    return I.chip(0.42, BLUE)


class S11Outro(VoiceScene):
    SECTION = "s11"

    def construct(self):
        self.show_chapter()
        rows = VGroup()
        for i, (t, c) in enumerate(LINES):
            num = en(str(i + 1), 26, c, italic=False, weight=NORMAL)
            slot = Rectangle(width=0.5, height=0.45).set_stroke(width=0).set_fill(opacity=0)
            ic = icon(i).move_to(slot)
            body = bn(t, 25, FG)
            rows.add(VGroup(num, VGroup(slot, ic), body).arrange(RIGHT, buff=0.26))
        rows.arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        if rows.width > 12.9:
            rows.scale_to_fit_width(12.9)
        rows.move_to([0, 0.2, 0])
        head = caps("what we learned today", 16, MUTED).next_to(rows, UP, buff=0.42, aligned_edge=LEFT)

        def show(i):
            return FadeIn(rows[i], shift=RIGHT * 0.12)

        with self.say("s11_01") as v:
            self.wait_until(v.cue("solved") - 0.3)
            self.play(FadeIn(head, shift=DOWN * 0.06), run_time=0.5)
            self.wait_until(v.cue("limited") - 0.3)
            self.play(show(0), run_time=0.6)
            self.wait_until(v.cue("choose") - 0.3)
            self.play(show(1), run_time=0.6)

        with self.say("s11_02") as v:
            self.wait_until(v.cue("small") - 0.4)
            self.play(show(2), run_time=0.6)

        with self.say("s11_03") as v:
            self.wait_until(v.cue("memory") - 0.4)
            self.play(show(3), run_time=0.6)

        with self.say("s11_04") as v:
            self.wait_until(v.cue("important") - 0.3)
            self.play(rows[:4].animate.fade(0.55), head.animate.fade(0.55), run_time=0.5)
            self.wait_until(v.cue("never") - 0.4)
            self.play(show(4), run_time=0.6)
            self.wait_until(v.cue("sees") - 0.3)
            self.play(glow(rows[4][1][1], BLUE, 5), pulse(rows[4], 1.03), run_time=0.6)

        # ---- the open question: one step at a time vs a big goal
        one = Pill(en("one step", 24, FG), BLUE, pad_x=0.26).move_to([-4.2, 0.6, 0])
        q = en("?", 40, MUTED).next_to(one, RIGHT, buff=0.5)
        with self.say("s11_05") as v:
            self.wait_until(v.cue("one") - 0.4)
            self.play(FadeOut(rows), FadeOut(head), run_time=0.5)
            self.wait_until(v.cue("step") - 0.3)
            self.play(FadeIn(one, shift=RIGHT * 0.1), FadeIn(q), run_time=0.5)

        goal = Pill(VGroup(I.target_icon(0.32, FG), en("build a whole app", 26, FG)).arrange(RIGHT, buff=0.14), FG, pad_x=0.3,
                    pad_y=0.14).move_to([1.8, 1.35, 0])
        steps = VGroup(*[Pill(VGroup(RoundedRectangle(width=0.2, height=0.2, corner_radius=0.04).set_stroke(MUTED, 1.4),
                                     en(s, 19, FG)).arrange(RIGHT, buff=0.1), DIM, pad_x=0.16)
                         for s in ("design", "screens", "data", "tests", "release")]).arrange(RIGHT, buff=0.18)
        steps.move_to([1.8, -0.35, 0])
        if steps.get_right()[0] > 6.7:
            steps.shift(LEFT * (steps.get_right()[0] - 6.7))
        links = VGroup(*[Line(goal.get_bottom() + DOWN * 0.05, s.get_top() + UP * 0.05).set_stroke(DIM, 1.4) for s in steps])
        track = caps("keep track", 14, AMBER).next_to(steps, DOWN, buff=0.3)
        with self.say("s11_06") as v:
            self.wait_until(v.cue("big") - 0.4)
            self.play(one.animate.fade(0.5), q.animate.fade(0.5), FadeIn(goal, scale=0.92), run_time=0.6)
            self.wait_until(v.cue("break") - 0.3)
            self.play(LaggedStart(*[AnimationGroup(Create(l), FadeIn(s, shift=DOWN * 0.1)) for l, s in zip(links, steps)],
                                  lag_ratio=0.2), run_time=1.2)
            self.wait_until(v.cue("track") - 0.3)
            ticks = VGroup(*[I.check_icon(0.16, TEAL).move_to(s[1][0][0]) for s in steps[:2]])
            self.play(FadeIn(track), FadeIn(ticks, lag_ratio=0.4), run_time=0.7)

        nxt = caps("next lesson", 18, AMBER)
        topic = en("Planning", 48, FG)
        g = VGroup(nxt, topic).arrange(DOWN, buff=0.22).move_to([0, -1.85, 0])
        with self.say("s11_07") as v:
            self.wait_until(v.cue("planning") - 0.9)
            self.play(VGroup(one, q, goal, steps, links, track, ticks).animate.shift(UP * 0.55).fade(0.3),
                      FadeIn(nxt, shift=UP * 0.08), run_time=0.6)
            self.play(FadeIn(topic, shift=UP * 0.1), run_time=0.7)

        # ---- title card (same style as Episodes 01 and 02)
        self.wait(0.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        t1 = spaced("AGENTIC AI", 84, FG, tracking=0.42, weight=LIGHT)
        rule = Line(LEFT * 1.6, RIGHT * 1.6).set_stroke(FAINT, 1.6)
        t2 = spaced("CONTEXT & MEMORY", 26, MUTED, tracking=0.75, weight=NORMAL)
        card = VGroup(t1, rule, t2).arrange(DOWN, buff=0.42).move_to(UP * 0.3)
        nxt2 = en("Next: Planning", 24, MUTED).next_to(card, DOWN, buff=0.7)
        self.play(FadeIn(t1, shift=UP * 0.12), run_time=1.4)
        self.play(Create(rule), FadeIn(t2, shift=UP * 0.08), run_time=1.0)
        self.wait(0.8)
        self.play(FadeIn(nxt2, shift=UP * 0.06), run_time=0.6)
        self.wait(2.0)
        self.play(FadeOut(card), FadeOut(nxt2), run_time=1.5)
        self.wait(0.8)
