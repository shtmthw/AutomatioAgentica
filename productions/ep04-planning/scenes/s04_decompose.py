"""04 · Breaking a big goal into good steps: decomposition; good steps are small, clear and
checkable (bad -> good each time); a way to see each step is finished; order; the right size."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *


def step_card(text, color, width=5.2, size=18):
    t = bn(text, size, FG)
    fr = RoundedRectangle(width=max(width, t.width + 0.5), height=0.56, corner_radius=0.1).set_stroke(color, 1.6)
    fr.set_fill(PANEL, 1)
    t.move_to(fr)
    return VGroup(fr, t)


def verdict(ok: bool, text):
    c = PLAN if ok else RED
    icon = I.check_icon(0.2, c) if ok else I.cross_icon(0.2, c)
    return VGroup(icon, caps(text, 12, c)).arrange(RIGHT, buff=0.1)


class S04Decompose(VoiceScene):
    SECTION = "s04"

    def construct(self):
        self.show_chapter()
        d = VGroup(en("Decomposition", 32, PLAN, italic=False, weight=NORMAL), en("=", 30, MUTED, italic=False),
                   en("breaking a big goal into smaller steps", 28, FG)).arrange(RIGHT, buff=0.2).move_to([0, 2.65, 0])
        goal = GoalCard(GOAL, 7.6, size=17).move_to([0, 1.0, 0])
        with self.say("s04_01") as v:
            self.wait_until(v.cue("breaking") - 0.3)
            self.play(FadeIn(goal, scale=0.95), run_time=0.6)
            self.wait_until(v.cue("decomposition") - 0.3)
            self.play(FadeIn(d, shift=DOWN * 0.08), run_time=0.6)

        rows = VGroup(*[StepRow(i + 1, s, width=5.6, size=17, h=0.42) for i, s in enumerate(STEPS)])
        rows.arrange(DOWN, buff=0.06).move_to([0, -1.05, 0])
        sx = rows[0].icon.get_left()[0] - 0.36
        spine = Line([sx, goal.get_bottom()[1], 0], [sx, rows[-1].icon.get_y(), 0]).set_stroke(PLAN, 1.6, opacity=0.6)
        branches = VGroup(*[Line([sx, r.icon.get_y(), 0], r.icon.get_left() + LEFT * 0.06).set_stroke(PLAN, 1.6, opacity=0.6)
                            for r in rows])
        links = VGroup(spine, branches)
        with self.say("s04_02") as v:
            self.wait_until(v.cue("five") - 0.4)
            self.play(Create(spine), run_time=0.5)
            self.play(LaggedStart(*[AnimationGroup(Create(l), FadeIn(r, shift=RIGHT * 0.12)) for l, r in zip(branches, rows)],
                                  lag_ratio=0.18), run_time=1.1)
            self.wait_until(v.cue("good") - 0.3)
            self.play(FadeOut(links), *[r.animate.fade(0.5) for r in rows], run_time=0.5)
            self.wait_until(v.cue("three") - 0.3)
            crit = VGroup(*[Pill(VGroup(en(str(i + 1), 18, PLAN, italic=False, weight=NORMAL), en(t, 18, FG)).arrange(RIGHT, buff=0.12),
                                 PLAN, pad_x=0.2, pad_y=0.07) for i, t in enumerate(("small", "clear", "checkable"))])
            crit.arrange(RIGHT, buff=0.3).move_to([0, 0.1, 0])
            self.play(FadeOut(rows), goal.animate.fade(0.7), LaggedStart(*[FadeIn(c, shift=UP * 0.08) for c in crit],
                                                                       lag_ratio=0.25), run_time=0.9)

        # bad -> good, three times
        cases = [("s04_03", "small", "Build the form and everything it needs", "too big",
                  "Create the contact form page", "one clear piece of work", ("bad", "good")),
                 ("s04_04", "clear", "Handle the messages", "could mean anything",
                  "Save each submitted message", "says exactly what to do", ("bad", "good")),
                 ("s04_05", "checkable", "Make sure it works well", "can't be checked",
                  "Run the tests and confirm they pass", "can be checked", ("bad", "good"))]
        crit_top = [c.copy() for c in crit]
        current = []
        for i, (key, name, bad, bad_v, good, good_v, (cb, cg)) in enumerate(cases):
            b = step_card(bad, RED).move_to([-3.25, -0.7, 0])
            g = step_card(good, PLAN).move_to([3.25, -0.7, 0])
            for card in (b, g):
                if card.width > 6.2:
                    card.scale_to_fit_width(6.2)
            bv = verdict(False, bad_v).next_to(b, DOWN, buff=0.16)
            gv = verdict(True, good_v).next_to(g, DOWN, buff=0.16)
            ar = arrow(b.get_right() + RIGHT * 0.12, g.get_left() + LEFT * 0.12, color=MUTED, tip=0.12)
            with self.say(key) as v:
                self.wait_until(v.cue(name) - 0.35)
                anims = [FadeOut(m) for m in current]
                if i == 0:
                    anims += [crit.animate.scale(0.8).move_to([0, 1.25, 0]), FadeOut(goal)]
                anims += [c.animate.set_opacity(1.0 if j == i else 0.3) for j, c in enumerate(crit)]
                self.play(*anims, run_time=0.5)
                self.play(glow(crit[i].frame, PLAN, 5), run_time=0.4)
                self.wait_until(v.cue(cb) - 0.3)
                self.play(FadeIn(b, shift=UP * 0.08), run_time=0.45)
                self.play(FadeIn(bv), run_time=0.3)
                self.wait_until(v.cue(cg) - 0.3)
                self.play(GrowArrow(ar), FadeIn(g, shift=LEFT * 0.12), run_time=0.5)
                self.play(FadeIn(gv), run_time=0.3)
            current = [b, g, bv, gv, ar]

        file_ok = VGroup(I.file_icon(0.55, TEAL), I.check_icon(0.24, PLAN)).arrange(RIGHT, buff=0.12)
        file_l = caps("a file that exists", 12, MUTED).next_to(file_ok, DOWN, buff=0.14)
        test_ok = VGroup(I.terminal_icon(0.5, TEAL), mono("all tests passed", 14, TEAL)).arrange(RIGHT, buff=0.14)
        test_l = caps("a test that passes", 12, MUTED).next_to(test_ok, DOWN, buff=0.14)
        ev = VGroup(VGroup(file_ok, file_l), VGroup(test_ok, test_l)).arrange(RIGHT, buff=1.6).move_to([0, -2.05, 0])
        see = Pill(VGroup(eye_icon(0.22, PLAN), caps("a way to see it's finished", 13, PLAN)).arrange(RIGHT, buff=0.12), PLAN,
                   pad_x=0.18, pad_y=0.07)
        with self.say("s04_06") as v:
            self.wait_until(v.cue("see") - 0.4)
            self.play(FadeOut(crit), run_time=0.4)
            see.move_to([0, -1.3, 0])
            self.play(FadeOut(current[2]), FadeOut(current[3]), run_time=0.3)
            self.play(FadeIn(see, shift=UP * 0.06), run_time=0.4)
            self.wait_until(v.cue("file") - 0.3)
            self.play(FadeIn(ev[0], shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("test") - 0.3)
            self.play(FadeIn(ev[1], shift=UP * 0.08), run_time=0.5)

        # order
        orows = VGroup(*[StepRow(i + 1, s, width=5.0, size=17, h=0.46) for i, s in enumerate(STEPS)])
        orows.arrange(DOWN, buff=0.16).move_to([-0.2, -0.2, 0])

        def side_arrow(a, b, color=PLAN):
            """Arc on the left of the status circles, from step a down into step b."""
            p0 = orows[a].icon.get_left() + LEFT * 0.07
            p1 = orows[b].icon.get_left() + LEFT * 0.07
            for ang in (PI / 1.6, -PI / 1.6):
                arr = CurvedArrow(p0, p1, angle=ang, color=color, tip_length=0.13).set_stroke(width=2.2)
                if arr.point_from_proportion(0.5)[0] < p0[0] - 0.05:
                    return arr
            return arr

        a12 = side_arrow(0, 1)
        a13 = side_arrow(0, 2)
        before = caps("comes before", 12, PLAN).next_to(a13, LEFT, buff=0.16)
        last = Pill(caps("last", 12, PLAN), PLAN, pad_x=0.14, pad_y=0.05).next_to(orows[4].text, RIGHT, buff=0.3)
        with self.say("s04_07") as v:
            self.wait_until(v.cue("order") - 0.4)
            self.play(*[FadeOut(m) for m in (*current, see, ev, crit)], run_time=0.5)
            self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.08) for r in orows], lag_ratio=0.1), run_time=0.8)
            self.wait_until(v.cue("looking") - 0.3)
            self.play(glow(orows[0].bg.copy().set_stroke(PLAN, 1), PLAN, 6), Create(a12), run_time=0.6)
            self.play(Create(a13), FadeIn(before), run_time=0.6)
            self.wait_until(v.cue("testing") - 0.3)
            self.play(FadeIn(last, shift=LEFT * 0.08), glow(orows[4].bg.copy().set_stroke(PLAN, 1), PLAN, 6), run_time=0.6)

        wrong = SizedCard("assistant", content=VGroup(caps("save messages", 10, RED),
                                                      code_block(1.0, 1, size=0.03, color=RED)).arrange(RIGHT, buff=0.16),
                          width=2.9, height=0.34, dashed=True, accent=RED)
        wrong.move_to([4.6, 1.85, 0])
        wl = caps("from before: written first", 11, RED).next_to(wrong, UP, buff=0.12)
        first_p = Pill(caps("first", 12, PLAN), PLAN, pad_x=0.14, pad_y=0.05).next_to(orows[0].text, RIGHT, buff=0.3)
        with self.say("s04_08") as v:
            self.wait_until(v.cue("remember") - 0.3)
            self.play(FadeIn(wrong, shift=LEFT * 0.1), FadeIn(wl), run_time=0.5)
            self.play(Wiggle(wrong, scale_value=1.05, rotation_angle=0.03), run_time=0.6)
            self.wait_until(v.cue("first") - 0.4)
            self.play(wrong.animate.scale(0.75).move_to(orows[2].text.get_right() + RIGHT * 1.2).set_opacity(0), FadeOut(wl),
                      glow(orows[0].bg.copy().set_stroke(PLAN, 1), PLAN, 8), FadeIn(first_p, shift=LEFT * 0.08), run_time=0.8)

        # the right size: a three-position slider
        track = Line([-3.2, 1.7, 0], [3.2, 1.7, 0]).set_stroke(DIM, 3)
        stops = VGroup(*[Dot(track.point_from_proportion(p), radius=0.07, color=DIM) for p in (0, 0.5, 1)])
        names = VGroup(caps("too little", 13, RED), caps("about right", 13, PLAN), caps("too much", 13, RED))
        for nm, s in zip(names, stops):
            nm.next_to(s, UP, buff=0.18)
        knob = Circle(radius=0.15).set_stroke(FG, 2).set_fill(PANEL, 1).move_to(stops[0])
        slider = VGroup(track, stops, names)
        one = StepRow(1, "Build the contact form.", width=4.6, size=17, h=0.46).move_to([0, 0.3, 0])
        same_as = VGroup(caps("= the goal again", 13, RED), I.cross_icon(0.2, RED)).arrange(RIGHT, buff=0.1)
        same_as.next_to(one, DOWN, buff=0.22)
        with self.say("s04_09") as v:
            self.wait_until(v.cue("size") - 0.4)
            self.play(*[FadeOut(m) for m in (orows, a12, a13, before, last, first_p)], run_time=0.5)
            self.play(Create(track), FadeIn(stops), FadeIn(names), FadeIn(knob), run_time=0.6)
            self.wait_until(v.cue("little") - 0.3)
            self.play(FadeIn(one, shift=UP * 0.08), glow(stops[0], RED, 5), run_time=0.5)
            self.wait_until(v.cue("repeats") - 0.3)
            self.play(FadeIn(same_as, shift=UP * 0.06), run_time=0.4)

        tiny_txt = ["open file", "move cursor", "type a letter", "type a letter", "save file", "scroll down", "open folder",
                    "read line 1", "read line 2", "move cursor", "type a letter", "close file"] * 4
        tiny = VGroup(*[Pill(en(t, 11, MUTED), DIM, pad_x=0.08, pad_y=0.02) for t in tiny_txt[:40]])
        tiny.arrange_in_grid(rows=8, cols=5, buff=(0.12, 0.08)).move_to([0, -0.45, 0])
        if tiny.width > 11.5:
            tiny.scale_to_fit_width(11.5)
        forty = Pill(caps("40 tiny steps", 13, RED), RED, pad_x=0.14, pad_y=0.05).move_to([5.3, 0.95, 0])
        with self.say("s04_10") as v:
            self.wait_until(v.cue("much") - 0.4)
            self.play(FadeOut(one), FadeOut(same_as), knob.animate.move_to(stops[2]), run_time=0.6)
            self.wait_until(v.cue("forty") - 0.3)
            self.play(LaggedStart(*[FadeIn(t, scale=0.8) for t in tiny], lag_ratio=0.03), FadeIn(forty), run_time=1.6)
            self.wait_until(v.cue("wasteful") - 0.3)
            self.play(glow(forty.frame, RED, 5), run_time=0.4)
            self.wait_until(v.cue("breaks") - 0.3)
            self.play(LaggedStart(*[AnimationGroup(t.frame.animate.set_stroke(RED), t.label.animate.set_color(RED),
                                                   t.animate.shift(DOWN * 0.08)) for t in tiny[12:22]],
                                  lag_ratio=0.05), run_time=0.8)
            self.play(Wiggle(tiny[12:22], scale_value=1.02, rotation_angle=0.04), run_time=0.6)

        right = VGroup(*[StepRow(i + 1, s, width=5.6, size=16, h=0.4) for i, s in enumerate(STEPS)]).arrange(DOWN, buff=0.05)
        right.move_to([0, -0.45, 0])
        five = caps("5–7 meaningful steps", 13, PLAN).next_to(right, DOWN, buff=0.2)
        with self.say("s04_11") as v:
            self.wait_until(v.cue("about") - 0.4)
            self.play(FadeOut(tiny), FadeOut(forty), knob.animate.move_to(stops[1]).set_stroke(PLAN), run_time=0.6)
            self.wait_until(v.cue("five") - 0.3)
            self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.08) for r in right], lag_ratio=0.12), FadeIn(five),
                      glow(stops[1], PLAN, 6), run_time=1.0)
        self.clear_all(0.6)
