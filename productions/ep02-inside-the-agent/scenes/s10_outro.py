"""10 · Conclusion: the five summary lines (recap of every topic), the problem that is left,
what's next, and the title card."""
from agentic_video.prelude import *

LINES = [("A model only reads text and writes text.", BLUE),
         ("The harness is the program around the model that runs the loop.", AMBER),
         ("The whole conversation is sent to the model as messages on every call.", FG),
         ("The model requests a tool; the harness runs it.", TEAL),
         ("The context window is limited, so what to keep and what to drop matters.", RED)]


def icon(i):
    if i == 0:
        return I.chip(0.42, BLUE)
    if i == 1:
        return I.gear(0.36, AMBER)
    if i == 2:
        return VGroup(*[RoundedRectangle(width=0.42, height=0.09, corner_radius=0.03).set_stroke(c, 1.1).set_fill(c, 0.2)
                        for c in (MUTED, FG, BLUE)]).arrange(DOWN, buff=0.04)
    if i == 3:
        return I.wrench_icon(0.36, TEAL)
    bar = RoundedRectangle(width=0.14, height=0.42, corner_radius=0.07).set_stroke(DIM, 1.2)
    fill = Rectangle(width=0.08, height=0.36).set_stroke(width=0).set_fill(RED, 0.9).move_to(bar)
    return VGroup(bar, fill)


class S10Outro(VoiceScene):
    SECTION = "s10"

    def construct(self):
        self.show_chapter()
        rows = VGroup()
        for i, (t, c) in enumerate(LINES):
            num = en(str(i + 1), 26, c, italic=False, weight=NORMAL)
            ic = icon(i)
            slot = Rectangle(width=0.5, height=0.45).set_stroke(width=0).set_fill(opacity=0)
            ic.move_to(slot)
            body = bn(t, 27, FG)
            rows.add(VGroup(num, VGroup(slot, ic), body).arrange(RIGHT, buff=0.26))
        rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        if rows.width > 12.8:
            rows.scale_to_fit_width(12.8)
        rows.move_to([0, 0.25, 0])
        head = caps("what we saw inside the agent", 16, MUTED).next_to(rows, UP, buff=0.45, aligned_edge=LEFT)

        def show(i):
            return FadeIn(rows[i], shift=RIGHT * 0.12)

        with self.say("s10_01") as v:
            self.wait_until(v.cue("inside") - 0.3)
            self.play(FadeIn(head, shift=DOWN * 0.06), run_time=0.5)

        with self.say("s10_02") as v:
            self.play(show(0), run_time=0.6)
            self.wait_until(v.cue("decisions") - 0.3)
            self.play(glow(rows[0][1][1], BLUE, 5), run_time=0.5)

        with self.say("s10_03") as v:
            self.wait_until(v.cue("harness") - 0.3)
            self.play(show(1), run_time=0.6)

        with self.say("s10_04") as v:
            self.wait_until(v.cue("whole") - 0.3)
            self.play(show(2), run_time=0.6)
            self.wait_until(v.cue("time") - 0.2)
            self.play(show(3), run_time=0.6)

        with self.say("s10_05") as v:
            self.wait_until(v.cue("problem") - 0.3)
            self.play(rows[:4].animate.fade(0.55), head.animate.fade(0.55), run_time=0.5)   # fade keeps outline icons hollow
            self.wait_until(v.cue("limited") - 0.3)
            self.play(show(4), run_time=0.6)
            self.play(glow(rows[4][1][1], RED, 6), run_time=0.5)

        # ---- the problem that is left
        cw = ContextWindow(2.6, 3.7, label=None).move_to([0, -0.05, 0])
        top = cw.frame.get_top()[1] - 0.14
        roles = ["system", "user", "assistant", "tool", "assistant", "tool", "assistant", "tool", "assistant", "tool"]
        bars = VGroup(*[RoundedRectangle(width=2.25, height=0.24, corner_radius=0.05).set_stroke(ROLE_COLORS[r], 1.2)
                        .set_fill(ROLE_COLORS[r], 0.18) for r in roles]).arrange(DOWN, buff=0.08)
        bars.move_to([cw.frame.get_x() - 0.0, top - bars.height / 2, 0])
        n_fit = len(roles)
        with self.say("s10_06") as v:
            self.wait_until(v.cue("work") - 0.4)
            self.play(FadeOut(rows), FadeOut(head), FadeIn(cw), run_time=0.6)
            self.wait_until(v.cue("pile") - 0.4)
            for k in range(n_fit):
                self.play(FadeIn(bars[k], shift=DOWN * 0.15), cw.meter_to((k + 1) / n_fit * 0.97), run_time=0.17)
            self.wait_until(v.cue("space") - 0.3)
            self.play(cw.meter_to(1.0), cw.frame.animate.set_stroke(RED), glow(cw.frame, RED, 6), run_time=0.6)

        q1 = Pill(en("big tasks?", 24, FG), FG, pad_x=0.26).move_to([-4.2, 0.9, 0])
        keep = VGroup(*[I.check_icon(0.22, TEAL).next_to(bars[k], RIGHT, buff=0.12) for k in (0, 1, 7)])
        let_go = [bars[k] for k in (2, 3, 4, 5)]
        q2 = Pill(en("what to remember?", 24, TEAL), TEAL, pad_x=0.26).move_to([4.2, 0.9, 0])
        q3 = Pill(en("what to let go?", 24, MUTED), MUTED, pad_x=0.26).move_to([4.2, -0.2, 0])
        with self.say("s10_07") as v:
            self.wait_until(v.cue("big") - 0.3)
            self.play(FadeIn(q1, shift=RIGHT * 0.1), run_time=0.45)
            self.wait_until(v.cue("remember") - 0.3)
            self.play(FadeIn(q2, shift=LEFT * 0.1), FadeIn(keep, scale=0.8), run_time=0.5)
            self.wait_until(v.cue("let") - 0.3)
            self.play(FadeIn(q3, shift=LEFT * 0.1), *[b.animate.set_stroke(opacity=0.15).set_fill(opacity=0.03) for b in let_go],
                      cw.meter_to(0.62), cw.frame.animate.set_stroke(FG), run_time=0.7)

        nxt = caps("next lesson", 18, AMBER)
        topic = en("Context Management & Memory", 40, FG)
        g = VGroup(nxt, topic).arrange(DOWN, buff=0.25).move_to([0, -2.05, 0])
        with self.say("s10_08") as v:
            self.wait_until(v.cue("next") - 0.3)
            self.play(VGroup(cw, bars, keep).animate.scale(0.8).shift(UP * 0.55), q1.animate.shift(UP * 0.3),
                      q2.animate.shift(UP * 0.3), q3.animate.shift(UP * 0.3), FadeIn(nxt, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("cm") - 0.3)
            self.play(FadeIn(topic, shift=UP * 0.1), run_time=0.7)

        # ---- title card (same style as Episode 01)
        self.wait(0.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        t1 = spaced("AGENTIC AI", 84, FG, tracking=0.42, weight=LIGHT)
        rule = Line(LEFT * 1.6, RIGHT * 1.6).set_stroke(FAINT, 1.6)
        t2 = spaced("INSIDE THE AGENT", 26, MUTED, tracking=0.75, weight=NORMAL)
        card = VGroup(t1, rule, t2).arrange(DOWN, buff=0.42).move_to(UP * 0.3)
        nxt2 = en("Next: Context & Memory", 24, MUTED).next_to(card, DOWN, buff=0.7)
        self.play(FadeIn(t1, shift=UP * 0.12), run_time=1.4)
        self.play(Create(rule), FadeIn(t2, shift=UP * 0.08), run_time=1.0)
        self.wait(0.8)
        self.play(FadeIn(nxt2, shift=UP * 0.06), run_time=0.6)
        self.wait(2.0)
        self.play(FadeOut(card), FadeOut(nxt2), run_time=1.5)
        self.wait(0.8)
