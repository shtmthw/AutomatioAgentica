"""11 · Conclusion: the five summary lines (the recap of the lesson), what stayed the same, the open
question that leads to Episode 05 (agents working together), and the title card."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *

LINES = [("One step at a time fails on big goals.", RED),
         ("A plan is a list of steps, written by the model as plain text.", PLAN),
         ("The harness keeps the plan and sends it on every call.", AMBER),
         ("Done means checked, not just said.", TEAL),
         ("A plan is a guide. It changes when the agent learns something new.", PLAN)]


def icon(i):
    if i == 0:
        return VGroup(Circle(radius=0.07).set_stroke(RED, 1.6), en("?", 18, RED, italic=False)).arrange(RIGHT, buff=0.08)
    if i == 1:
        return plan_icon(0.4)
    if i == 2:
        return I.gear(0.36, AMBER)
    if i == 3:
        return I.check_icon(0.34, TEAL)
    return VGroup(*[en(s, 18, PLAN, italic=False, weight=NORMAL) for s in ("+", "~", "−")]).arrange(RIGHT, buff=0.08)


class S11Outro(VoiceScene):
    SECTION = "s11"

    def construct(self):
        self.show_chapter()
        rows = VGroup()
        for i, (t, c) in enumerate(LINES):
            num = en(str(i + 1), 26, c, italic=False, weight=NORMAL)
            slot = Rectangle(width=0.55, height=0.45).set_stroke(width=0).set_fill(opacity=0)
            ic = icon(i).move_to(slot)
            body = bn(t, 24, FG)
            rows.add(VGroup(num, VGroup(slot, ic), body).arrange(RIGHT, buff=0.26))
        rows.arrange(DOWN, buff=0.38, aligned_edge=LEFT)
        if rows.width > 12.9:
            rows.scale_to_fit_width(12.9)
        rows.move_to([0, 0.15, 0])
        head = caps("what we learned today", 16, MUTED).next_to(rows, UP, buff=0.4, aligned_edge=LEFT)

        def show(i):
            return FadeIn(rows[i], shift=RIGHT * 0.12)

        with self.say("s11_01") as v:
            self.wait_until(v.cue("today") - 0.3)
            self.play(FadeIn(head, shift=DOWN * 0.06), show(0), run_time=0.6)

        with self.say("s11_02") as v:
            self.wait_until(v.cue("list") - 0.4)
            self.play(show(1), run_time=0.6)
            self.wait_until(v.cue("harness") - 0.3)
            self.play(show(2), run_time=0.6)

        with self.say("s11_03") as v:
            self.wait_until(v.cue("checks") - 0.4)
            self.play(show(3), run_time=0.6)
            self.wait_until(v.cue("changes") - 0.4)
            self.play(show(4), run_time=0.6)

        trio = VGroup(VGroup(I.chip(0.55, BLUE), caps("model", 12, BLUE)).arrange(DOWN, buff=0.1),
                      VGroup(I.gear(0.5, AMBER), caps("harness", 12, AMBER)).arrange(DOWN, buff=0.1),
                      VGroup(I.loop_icon(0.5, VIOLET), caps("loop", 12, VIOLET)).arrange(DOWN, buff=0.1)).arrange(RIGHT, buff=0.9)
        same = Pill(caps("unchanged", 13, MUTED), DIM, pad_x=0.16, pad_y=0.05)
        plus = en("+", 40, PLAN, italic=False)
        extra = VGroup(plan_icon(0.55), caps("one more piece of text", 12, PLAN)).arrange(DOWN, buff=0.1)
        grp = VGroup(trio, plus, extra).arrange(RIGHT, buff=0.7).move_to([0, -0.1, 0])
        same.next_to(trio, UP, buff=0.35)
        with self.say("s11_04") as v:
            self.wait_until(v.cue("same") - 0.3)
            self.play(FadeOut(rows), FadeOut(head), run_time=0.5)
            for i, cue in enumerate(("model", "harness", "loop")):
                self.wait_until(v.cue(cue) - 0.25)
                self.play(FadeIn(trio[i], shift=UP * 0.08), run_time=0.35)
            self.play(FadeIn(same), run_time=0.3)
            self.wait_until(v.cue("text") - 0.4)
            self.play(FadeIn(plus), FadeIn(extra, shift=LEFT * 0.08), run_time=0.5)

        st = plan_state()
        mini = PlanPanel(st, width=4.4, size=14, rows=5, row_h=0.38, sub=None).move_to([-3.6, -0.1, 0])
        big = StepRow(3, "Save each submitted message", width=4.2, size=14, h=0.38)
        huge = RoundedRectangle(width=5.4, height=4.0, corner_radius=0.2).set_stroke(PLAN, 1.6, opacity=0.8).move_to([3.4, -0.1, 0])
        huge_lab = caps("a huge job by itself", 12, PLAN).next_to(huge, UP, buff=0.12)
        sub = VGroup(*[RoundedRectangle(width=4.4, height=0.28, corner_radius=0.06).set_stroke(DIM, 1.2) for _ in range(8)])
        sub.arrange(DOWN, buff=0.12).move_to(huge)
        with self.say("s11_05") as v:
            self.wait_until(v.cue("one") - 0.4)
            self.play(FadeOut(grp), FadeOut(same), FadeIn(mini, shift=RIGHT * 0.08), run_time=0.6)
            self.play(glow(mini.row("s3").bg.copy().set_stroke(PLAN, 1), PLAN, 6), run_time=0.5)
            self.wait_until(v.cue("huge") - 0.4)
            big.move_to(mini.row("s3"))
            self.play(TransformFromCopy(mini.row("s3").bg.copy().set_stroke(PLAN, 1.4), huge), FadeIn(huge_lab), run_time=0.8)
            self.wait_until(v.cue("whole") - 0.3)
            self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.06) for s in sub], lag_ratio=0.08), run_time=0.9)

        a1 = VGroup(I.chip(0.6, BLUE), caps("agent", 12, BLUE)).arrange(DOWN, buff=0.1).move_to([-3.6, 0.2, 0])
        a2 = VGroup(I.chip(0.6, BLUE), caps("another agent", 12, BLUE)).arrange(DOWN, buff=0.1).move_to([3.4, 0.2, 0])
        hand = StepRow(3, "Save each submitted message", width=3.9, size=14, h=0.38).move_to([-0.1, 1.0, 0])
        go = Arrow(a1.get_right() + UP * 0.25, a2.get_left() + UP * 0.25, buff=0.15, stroke_width=2, tip_length=0.14).set_color(PLAN)
        back = Arrow(a2.get_left() + DOWN * 0.25, a1.get_right() + DOWN * 0.25, buff=0.15, stroke_width=2,
                     tip_length=0.14).set_color(TEAL)
        res = caps("result?", 12, TEAL).next_to(back, DOWN, buff=0.12)
        q = en("?", 46, MUTED, italic=False).move_to([0, -1.6, 0])
        with self.say("s11_06") as v:
            self.wait_until(v.cue("hand") - 0.4)
            self.play(*[FadeOut(m) for m in (mini, huge, huge_lab, sub)], FadeIn(a1), run_time=0.5)
            hand.move_to(a1.get_top() + UP * 0.4)
            self.play(FadeIn(hand), run_time=0.3)
            self.play(hand.animate.move_to([-0.1, 1.0, 0]), GrowArrow(go), run_time=0.6)
            self.wait_until(v.cue("another") - 0.3)
            self.play(FadeIn(a2, shift=LEFT * 0.08), hand.animate.move_to(a2.get_top() + UP * 0.4), run_time=0.6)
            self.wait_until(v.cue("wait") - 0.3)
            self.play(GrowArrow(back), FadeIn(res), FadeIn(q), run_time=0.6)

        nxt = caps("next lesson", 18, AMBER)
        topic = en("Agents Working Together", 44, FG)
        g = VGroup(nxt, topic).arrange(DOWN, buff=0.22).move_to([0, -1.75, 0])
        with self.say("s11_07") as v:
            self.wait_until(v.cue("next") - 0.4)
            self.play(VGroup(a1, a2, hand, go, back, res).animate.shift(UP * 0.5).fade(0.3), FadeOut(q),
                      FadeIn(nxt, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("together") - 0.6)
            self.play(FadeIn(topic, shift=UP * 0.1), run_time=0.7)

        # ---- title card (same style as Episodes 01-03)
        self.wait(0.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        t1 = spaced("AGENTIC AI", 84, FG, tracking=0.42, weight=LIGHT)
        rule = Line(LEFT * 1.6, RIGHT * 1.6).set_stroke(FAINT, 1.6)
        t2 = spaced("PLANNING", 26, MUTED, tracking=0.75, weight=NORMAL)
        card = VGroup(t1, rule, t2).arrange(DOWN, buff=0.42).move_to(UP * 0.3)
        nxt2 = en("Next: Agents Working Together", 24, MUTED).next_to(card, DOWN, buff=0.7)
        self.play(FadeIn(t1, shift=UP * 0.12), run_time=1.4)
        self.play(Create(rule), FadeIn(t2, shift=UP * 0.08), run_time=1.0)
        self.wait(0.8)
        self.play(FadeIn(nxt2, shift=UP * 0.06), run_time=0.6)
        self.wait(2.0)
        self.play(FadeOut(card), FadeOut(nxt2), run_time=1.5)
        self.wait(0.8)
