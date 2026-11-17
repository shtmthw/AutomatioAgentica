"""10 · Reality check: plans are not magic. A plan can be wrong; a tick is not proof; small tasks do
not need a plan; the model can drift from its own plan. A plan makes the work visible."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *


def point_tag(i, n=4):
    t = VGroup(caps("reality check", 13, MUTED), en(str(i), 22, AMBER, italic=False, weight=NORMAL),
               caps(f"of {n}", 13, DIM)).arrange(RIGHT, buff=0.1)
    return t.move_to([6.75 - t.width / 2, 3.05, 0])


WRONG_STEPS = ["Look at how the website is organized", "Create a contact list page", "Add each contact to the list",
               "Sort the list by name", "Test the whole thing"]


def all_done(goal):
    st = PlanState(goal, WRONG_STEPS)
    for s in st.steps:
        s["status"] = DONE
    return st


class S10Reality(VoiceScene):
    SECTION = "s10"

    def construct(self):
        self.show_chapter()
        title = VGroup(en("Plans are useful,", 34, FG), en("but not magic.", 34, AMBER)).arrange(DOWN, buff=0.18)
        with self.say("s10_01") as v:
            self.wait_until(v.cue("reality") - 0.3)
            self.play(FadeIn(title[0], shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("magic") - 0.4)
            self.play(FadeIn(title[1], shift=UP * 0.08), run_time=0.5)

        tag = [point_tag(1)]
        wrong = PlanPanel(all_done("Add a contact list to my website"), width=5.0, size=15, rows=5, row_h=0.4, sub=None)
        wrong.move_to([-2.4, -0.1, 0])
        mark = Pill(VGroup(I.cross_icon(0.18, RED), caps("wrong goal", 12, RED)).arrange(RIGHT, buff=0.08), RED, pad_x=0.14,
                    pad_y=0.05).next_to(wrong.goal, RIGHT, buff=0.25)
        asked = Pill(VGroup(caps("rahul meant", 11, MUTED), en("a contact form", 16, FG)).arrange(RIGHT, buff=0.1), DIM,
                     pad_x=0.14, pad_y=0.05).next_to(mark, DOWN, buff=0.2, aligned_edge=LEFT)
        review = VGroup(I.user_icon(0.4, FG), eye_icon(0.26, PLAN), caps("human review helps", 12, PLAN)).arrange(RIGHT, buff=0.14)
        review.next_to(asked, DOWN, buff=0.45, aligned_edge=LEFT)
        with self.say("s10_02") as v:
            self.wait_until(v.cue("wrong") - 0.4)
            self.play(FadeOut(title), FadeIn(tag[0]), run_time=0.4)
            self.wait_until(v.cue("misunderstands") - 0.3)
            self.play(FadeIn(wrong, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("neat") - 0.3)
            self.play(LaggedStart(*[glow(wrong.row(f"s{i + 1}").icon[0], PLAN, 4, 0.4) for i in range(5)], lag_ratio=0.12),
                      run_time=0.8)
            self.play(FadeIn(mark, shift=LEFT * 0.08), FadeIn(asked, shift=LEFT * 0.06), wrong.goal.frame.animate.set_stroke(RED),
                      run_time=0.5)
            self.wait_until(v.cue("review") - 0.3)
            self.play(FadeIn(review, shift=UP * 0.06), run_time=0.5)

        row = StepRow(5, "Test the whole thing", DONE, width=3.95, size=19, h=0.56).move_to([-1.2, 0.3, 0])
        frame5 = SurroundingRectangle(row, buff=0.12, corner_radius=0.12).set_stroke(PLAN, 1.4, opacity=0.7)
        q = en("?", 30, RED, italic=False, weight=NORMAL).move_to(row.icon.get_corner(UR) + UR * 0.13)
        gap = DashedLine(frame5.get_right() + RIGHT * 0.1, frame5.get_right() + RIGHT * 1.9, dash_length=0.08)
        gap.set_stroke(DIM, 1.8)
        miss = VGroup(RoundedRectangle(width=1.5, height=0.42, corner_radius=0.08).set_stroke(DIM, 1.4),
                      caps("no evidence", 12, MUTED))
        miss[1].move_to(miss[0])
        miss.next_to(gap, RIGHT, buff=0.1)
        no_link = VGroup(gap, miss)
        with self.say("s10_03") as v:
            self.wait_until(v.cue("tick") - 0.4)
            self.play(*[FadeOut(m) for m in (wrong, mark, asked, review, tag[0])], run_time=0.4)
            tag[0] = point_tag(2)
            self.play(FadeIn(tag[0]), FadeIn(row, shift=UP * 0.08), FadeIn(frame5, shift=UP * 0.08), run_time=0.5)
            self.play(FadeIn(no_link), run_time=0.4)
            self.wait_until(v.cue("isn") - 0.4)
            self.play(FadeIn(q, scale=1.4), run_time=0.3)
            for _ in range(2):
                self.play(q.animate.set_opacity(0.2), run_time=0.2)
                self.play(q.animate.set_opacity(1), run_time=0.2)

        tiny = SizedCard("user", "What port does the server use?", width=4.4, height=0.42, size=16).move_to([0, -1.7, 0])
        heavy = VGroup(*[StepRow(i + 1, t, width=4.6, size=15, h=0.4)
                         for i, t in enumerate(("Understand the question", "Plan the search", "Open the config file",
                                                "Read the port", "Check the answer"))]).arrange(DOWN, buff=0.05)
        heavy.move_to([0, 0.55, 0])
        hbox = SurroundingRectangle(heavy, buff=0.14, corner_radius=0.12).set_stroke(PLAN, 1.5)
        slow = Pill(VGroup(clock_icon(0.24, AMBER), caps("slower, adds nothing", 12, AMBER)).arrange(RIGHT, buff=0.1), AMBER,
                    pad_x=0.14, pad_y=0.05).next_to(hbox, RIGHT, buff=0.3)
        with self.say("s10_04") as v:
            self.wait_until(v.cue("small") - 0.4)
            self.play(*[FadeOut(m) for m in (row, frame5, q, no_link, tag[0])], run_time=0.4)
            tag[0] = point_tag(3)
            self.play(FadeIn(tag[0]), run_time=0.3)
            self.wait_until(v.cue("port") - 0.4)
            self.play(FadeIn(tiny, shift=UP * 0.08), run_time=0.45)
            self.play(Create(hbox), LaggedStart(*[FadeIn(r, shift=DOWN * 0.15) for r in heavy], lag_ratio=0.15), run_time=1.0)
            self.play(tiny.animate.shift(DOWN * 0.08).fade(0.3), run_time=0.3)
            self.wait_until(v.cue("slower") - 0.3)
            self.play(FadeIn(slow, shift=LEFT * 0.06), run_time=0.4)

        st = plan_state()
        st.set_status("s1", DONE)
        st.set_status("s2", DONE)
        st.set_status("s3", ACTIVE)
        panel = PlanPanel(st, width=4.4, size=14, rows=5, row_h=0.38, sub=None).move_to([-3.6, -0.1, 0])
        off = SizedCard("assistant", content=call_line("edit_file", '"footer.css"', 14), width=3.7, height=0.4, dashed=True)
        off.move_to([3.6, -1.4, 0])
        path = VMobject().set_points_smoothly([panel.row("s3").bg.get_right() + RIGHT * 0.1, [0.8, 0.2, 0], [1.6, -0.9, 0],
                                               off.get_left() + LEFT * 0.1])
        path = DashedVMobject(path.set_stroke(AMBER, 2), num_dashes=20)
        unrel = caps("unrelated file", 12, AMBER).next_to(off, UP, buff=0.12)
        less = Pill(caps("less likely, not impossible", 12, MUTED), DIM, pad_x=0.14, pad_y=0.05).move_to([3.6, 1.6, 0])
        with self.say("s10_05") as v:
            self.wait_until(v.cue("drift") - 0.4)
            self.play(*[FadeOut(m) for m in (tiny, heavy, hbox, slow, tag[0])], run_time=0.4)
            tag[0] = point_tag(4)
            self.play(FadeIn(tag[0]), FadeIn(panel, shift=RIGHT * 0.08), run_time=0.5)
            self.play(Create(path), run_time=0.8)
            self.play(FadeIn(off, shift=LEFT * 0.08), FadeIn(unrel), run_time=0.4)
            self.wait_until(v.cue("less") - 0.3)
            self.play(FadeIn(less, shift=DOWN * 0.06), run_time=0.4)

        right = VGroup(I.cross_icon(0.26, MUTED), en("a plan doesn't make the agent right", 24, MUTED)).arrange(RIGHT, buff=0.16)
        vis = VGroup(eye_icon(0.34, PLAN), en("it makes the work visible", 28, FG)).arrange(RIGHT, buff=0.2)
        both = VGroup(VGroup(I.chip(0.42, BLUE), caps("the agent", 11, BLUE)).arrange(DOWN, buff=0.08),
                      VGroup(I.user_icon(0.42, FG), caps("the human", 11, FG)).arrange(DOWN, buff=0.08)).arrange(RIGHT, buff=0.8)
        catch = caps("catch mistakes earlier", 13, PLAN)
        col = VGroup(right, vis, both, catch).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        with self.say("s10_06") as v:
            self.wait_until(v.cue("right") - 0.5)
            self.play(*[FadeOut(m) for m in (panel, off, path, unrel, less, tag[0])], run_time=0.4)
            self.play(FadeIn(right, shift=UP * 0.06), run_time=0.4)
            self.wait_until(v.cue("visible") - 0.3)
            self.play(FadeIn(vis, shift=UP * 0.06), run_time=0.5)
            self.wait_until(v.cue("both") - 0.3)
            self.play(FadeIn(both, shift=UP * 0.06), run_time=0.5)
            self.wait_until(v.cue("mistakes") - 0.3)
            self.play(FadeIn(catch), run_time=0.4)
        self.wait(0.4)
        self.clear_all(0.6)
