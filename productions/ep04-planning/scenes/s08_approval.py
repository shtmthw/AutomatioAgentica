"""08 · Showing the plan to a human first: the harness shows an approval prompt before any other
tool runs; Rahul adds a missing step, then approves. Without approval vs with approval (two
timelines). Human oversight, chosen by the harness developer."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *

PANEL_C = np.array([-4.65, 0.35, 0])
MODEL_C = np.array([-0.05, 2.35, 0])
FW = 4.25
EMAIL = "Email Rahul when someone writes"


def toggle(on=True, color=PLAN):
    track = RoundedRectangle(width=0.62, height=0.32, corner_radius=0.16).set_stroke(color if on else DIM, 1.6)
    track.set_fill(color if on else PANEL, 0.25 if on else 1)
    knob = Circle(radius=0.11).set_stroke(width=0).set_fill(color if on else MUTED, 1)
    knob.move_to(track.get_right() + LEFT * 0.17 if on else track.get_left() + RIGHT * 0.17)
    return VGroup(track, knob)


class S08Approval(VoiceScene):
    SECTION = "s08"

    def construct(self):
        self.show_chapter()
        # cost of fixing a mistake over time
        axis = Arrow([-5.0, -1.4, 0], [5.0, -1.4, 0], buff=0, stroke_width=2, tip_length=0.16).set_color(DIM)
        curve = VMobject().set_points_smoothly([[-4.8, -1.2, 0], [-1.5, -1.0, 0], [1.5, -0.2, 0], [4.6, 1.6, 0]])
        curve.set_stroke(RED, 3)
        before = Dot([-4.8, -1.2, 0], radius=0.1, color=PLAN)
        cheap = Pill(caps("before any work: cheapest fix", 12, PLAN), PLAN, pad_x=0.14, pad_y=0.05).move_to([-3.6, -0.45, 0])
        late = caps("cost of fixing it later", 12, RED).move_to([3.0, 1.75, 0])
        tlab = caps("time", 11, MUTED).next_to(axis, DOWN, buff=0.12, aligned_edge=RIGHT)
        with self.say("s08_01") as v:
            self.wait_until(v.cue("cheapest") - 0.4)
            self.play(GrowArrow(axis), FadeIn(tlab), Create(curve), FadeIn(late), run_time=1.0)
            self.wait_until(v.cue("before") - 0.3)
            self.play(FadeIn(before, scale=1.5), FadeIn(cheap, shift=UP * 0.06), run_time=0.5)

        panel = PlanPanel(PlanState(GOAL, []), width=4.2, size=14, rows=6, row_h=0.38, empty=True).move_to(PANEL_C)
        model = ModelBox(1.75, 0.9, label_size=14).move_to(MODEL_C)
        feed = Feed(2.5, 2.75, -2.65, gap=0.08)
        u = SizedCard("user", "Add a contact form… thank-you note.", width=FW, height=0.3, size=12)
        c1 = plan_call("five steps", width=FW, size=12)
        prompt = ApprovalPrompt().move_to([-0.05, 0.1, 0])
        with self.say("s08_02") as v:
            self.wait_until(v.cue("goal") - 0.4)
            self.play(*[FadeOut(m) for m in (axis, tlab, curve, late, before, cheap)], run_time=0.4)
            self.play(FadeIn(panel), FadeIn(model, scale=0.94), *feed.push(u), run_time=0.6)
            self.wait_until(v.cue("writes") - 0.5)
            self.play(bundle_anim(model, [panel, u], run_time=0.5), run_time=0.5)
            self.play(*feed.push(c1, shift=LEFT * 0.15), run_time=0.4)
            panel.apply(self, c1, "create", STEPS, fast=True)
            self.wait_until(v.cue("before") - 0.3)
            stop = VGroup(I.lock_icon(0.26, AMBER), caps("no other tool yet", 11, AMBER)).arrange(RIGHT, buff=0.08)
            stop.next_to(model, DOWN, buff=0.15)
            self.play(FadeIn(stop), run_time=0.4)
            self.wait_until(v.cue("start") - 0.4)
            self.play(FadeIn(prompt, scale=0.92), FadeOut(stop), run_time=0.5)

        rahul = VGroup(I.user_icon(0.3, FG), en("Rahul", 13, FG)).arrange(RIGHT, buff=0.08)
        u2 = SizedCard("user", "Also send me an email when someone writes.", width=FW, height=0.3, size=12)
        c2 = plan_call("add before step 5: " + EMAIL, width=FW, size=12)
        begins = Pill(VGroup(I.loop_icon(0.22, TEAL), caps("loop begins", 12, TEAL)).arrange(RIGHT, buff=0.08), TEAL,
                      pad_x=0.14, pad_y=0.05)
        with self.say("s08_03") as v:
            self.wait_until(v.cue("spots") - 0.3)
            self.play(LaggedStart(*[glow(panel.row(f"s{i + 1}").bg.copy().set_stroke(MUTED, 1), FG, 3, 0.4) for i in range(5)],
                                  lag_ratio=0.12), run_time=0.8)
            self.wait_until(v.cue("also") - 0.4)
            self.play(prompt.change.frame.animate.set_stroke(FG), run_time=0.2)
            self.play(*feed.push(u2), run_time=0.4)
            rahul.next_to(u2, LEFT, buff=0.15)
            self.play(FadeIn(rahul, shift=RIGHT * 0.05), run_time=0.3)
            self.wait_until(v.cue("calls") - 0.5)
            self.play(bundle_anim(model, [panel, u2], run_time=0.5), run_time=0.5)
            self.play(*feed.push(c2, shift=LEFT * 0.15), run_time=0.4)
            panel.apply(self, c2, "add", "e1", EMAIL, before="s5", fast=True)
            self.wait_until(v.cue("approves") - 0.3)
            self.play(*prompt.press("approve"), run_time=0.5)
            self.wait_until(v.cue("loop") - 0.3)
            begins.next_to(prompt, DOWN, buff=0.25)
            self.play(FadeIn(begins, shift=UP * 0.06), prompt.animate.fade(0.5), run_time=0.5)

        # two timelines
        def timeline(y, label, color):
            ticks = VGroup(*[RoundedRectangle(width=0.13, height=0.3, corner_radius=0.03).set_stroke(width=0).set_fill(TEAL, 0.6)
                             for _ in range(30)]).arrange(RIGHT, buff=0.06)
            ticks.move_to([0.9, y, 0])
            lab = caps(label, 13, color).next_to(ticks, LEFT, buff=0.35)
            return VGroup(lab, ticks)

        t1 = timeline(1.0, "without approval", RED)
        t2 = timeline(-1.2, "with approval", PLAN)
        c60 = caps("call 60", 11, MUTED).next_to(t1[1], UP, buff=0.12, aligned_edge=RIGHT)
        miss = Pill(caps("email part missing!", 11, RED), RED, pad_x=0.12, pad_y=0.04).next_to(t1[1], RIGHT, buff=0.15)
        if miss.get_right()[0] > 6.85:
            miss.next_to(t1[1], DOWN, buff=0.12, aligned_edge=RIGHT)
        redo = caps("much of it redone", 11, RED).next_to(t1[1], DOWN, buff=0.12, aligned_edge=LEFT)
        caught = Pill(caps("gap caught here", 11, PLAN), PLAN, pad_x=0.12, pad_y=0.04).next_to(t2[1][0], UP, buff=0.14)
        mark = Triangle().scale(0.09).rotate(PI).set_stroke(width=0).set_fill(PLAN, 1).next_to(t2[1][0], UP, buff=0.02)
        with self.say("s08_04") as v:
            self.wait_until(v.cue("without") - 0.4)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.5)
            self.play(FadeIn(t1[0]), LaggedStart(*[FadeIn(b) for b in t1[1]], lag_ratio=0.04), run_time=0.9)
            self.wait_until(v.cue("sixty") - 0.3)
            self.play(FadeIn(c60), FadeIn(miss, shift=LEFT * 0.06), run_time=0.4)
            self.wait_until(v.cue("redone") - 0.3)
            self.play(LaggedStart(*[b.animate.set_fill(RED, 0.6) for b in t1[1][8:]], lag_ratio=0.03), FadeIn(redo), run_time=0.8)
            self.wait_until(v.cue("with") - 0.3)
            self.play(FadeIn(t2[0]), FadeIn(mark), FadeIn(caught, shift=DOWN * 0.05), run_time=0.5)
            self.wait_until(v.cue("first") - 0.3)
            self.play(LaggedStart(*[FadeIn(b) for b in t2[1]], lag_ratio=0.03), run_time=0.9)

        shield = shield_icon(0.7, AMBER)
        ho = VGroup(shield, en("human oversight", 22, FG)).arrange(RIGHT, buff=0.2).move_to([-3.3, 0.9, 0])
        hcard = HarnessFrame(5.0, 1.9, label_size=15).move_to([2.9, 0.8, 0])
        row = VGroup(en("ask for approval", 17, FG), toggle(True)).arrange(RIGHT, buff=0.4)
        row.move_to(hcard.frame.get_center() + DOWN * 0.15)
        dev = caps("set by its developer", 11, MUTED).next_to(hcard, DOWN, buff=0.12)
        small = VGroup(caps("small, low-risk task", 12, MUTED), en("→", 18, MUTED), toggle(False),
                       caps("skip", 12, MUTED)).arrange(RIGHT, buff=0.16).move_to([2.9, -1.4, 0])
        with self.say("s08_05") as v:
            self.wait_until(v.cue("oversight") - 0.4)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.5)
            self.play(FadeIn(ho, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("choice") - 0.3)
            self.play(FadeIn(hcard), FadeIn(row, shift=UP * 0.06), run_time=0.6)
            self.wait_until(v.cue("developer") - 0.3)
            self.play(FadeIn(dev), glow(hcard.frame, AMBER, 5), run_time=0.5)
            self.wait_until(v.cue("small") - 0.3)
            self.play(FadeIn(small, shift=UP * 0.06), run_time=0.5)
        self.wait(0.4)
        self.clear_all(0.6)
