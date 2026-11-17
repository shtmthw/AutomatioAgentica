"""03 · What is a plan? A list of steps to reach a goal, written by the same model as an ordinary
assistant message in plain text; what changes is the first thing we ask; why it helps."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *


def definition(term, rest, color=PLAN, size=30):
    return VGroup(en(term, size + 2, color, italic=False, weight=NORMAL), en("=", size, MUTED, italic=False),
                  en(rest, size, FG)).arrange(RIGHT, buff=0.22)


class S03WhatIsPlan(VoiceScene):
    SECTION = "s03"

    def construct(self):
        self.show_chapter()
        d = definition("Plan", "a list of steps to reach a goal").move_to([0, 2.65, 0])
        with self.say("s03_01") as v:
            self.wait_until(v.cue("plan") - 0.3)
            self.play(FadeIn(d[0], shift=UP * 0.1), run_time=0.5)
            self.wait_until(v.cue("list") - 0.3)
            self.play(FadeIn(d[1]), FadeIn(d[2], shift=RIGHT * 0.1), run_time=0.6)

        sys_c = SizedCard("system", "Before acting, write a plan.", width=3.7, height=0.36, size=14)
        user_c = SizedCard("user", "Add a contact form… save every message… thank-you note.", width=3.7, height=0.5, size=13,
                           wrap=30)
        left = VGroup(sys_c, user_c).arrange(DOWN, buff=0.1, aligned_edge=LEFT).move_to([-4.85, -0.15, 0])
        model = ModelBox(1.9, 1.15, label_size=15).move_to([-1.3, -0.15, 0])
        a_in = arrow(left.get_right() + RIGHT * 0.12, model.in_port + LEFT * 0.08, color=MUTED, tip=0.12)
        # the plan as an ordinary assistant message
        lines = VGroup(*[VGroup(en(f"{i + 1}.", 17, MUTED, italic=False), bn(s, 17, FG)).arrange(RIGHT, buff=0.14)
                         for i, s in enumerate(STEPS)]).arrange(DOWN, buff=0.17, aligned_edge=LEFT)
        box_w, box_h = 5.6, lines.height + 0.75
        frame = RoundedRectangle(width=box_w, height=box_h, corner_radius=0.12).set_stroke(BLUE, 1.4, opacity=0.6)
        frame.set_fill(PANEL, 1)
        tag_box = RoundedRectangle(width=1.36, height=0.3, corner_radius=0.08).set_stroke(BLUE, 1.3).set_fill(BLUE, 0.14)
        tag = VGroup(tag_box, caps("assistant", 13, BLUE).move_to(tag_box))
        msg = VGroup(frame, tag)
        msg.move_to([3.55, -0.15, 0])
        tag.move_to(frame.get_corner(UL) + RIGHT * 0.8 + DOWN * 0.27)
        lines.move_to(frame.get_corner(UL) + RIGHT * (lines.width / 2 + 0.32) + DOWN * (lines.height / 2 + 0.55))
        plain = caps("plain text", 12, MUTED).next_to(frame, DOWN, buff=0.14, aligned_edge=RIGHT)
        a_out = arrow(model.out_port + RIGHT * 0.08, frame.get_left() + LEFT * 0.08, color=MUTED, tip=0.12)
        with self.say("s03_02") as v:
            self.wait_until(v.cue("goal") - 0.3)
            self.play(FadeIn(user_c, shift=RIGHT * 0.1), FadeIn(model, scale=0.94), run_time=0.6)
            self.wait_until(v.cue("first") - 0.3)
            self.play(FadeIn(sys_c, shift=RIGHT * 0.1), run_time=0.4)
            self.play(GrowArrow(a_in), send_anim([sys_c, user_c], model), run_time=0.8)
            self.wait_until(v.cue("replies") - 0.3)
            self.play(GrowArrow(a_out), FadeIn(msg, shift=RIGHT * 0.1), run_time=0.6)
            self.wait_until(v.cue("plain") - 0.3)
            self.play(FadeIn(plain), run_time=0.4)

        with self.say("s03_03") as v:
            for i, cue in enumerate(("one", "two", "three", "four", "five")):
                self.wait_until(v.cue(cue) - 0.25)
                self.play(FadeIn(lines[i], shift=RIGHT * 0.12), run_time=0.45)

        just = Pill(VGroup(I.check_icon(0.18, BLUE), caps("written by the model", 12, BLUE)).arrange(RIGHT, buff=0.1), BLUE,
                    pad_x=0.16, pad_y=0.06).next_to(frame, UP, buff=0.14, aligned_edge=RIGHT)
        with self.say("s03_04") as v:
            self.wait_until(v.cue("ordinary") - 0.3)
            self.play(glow(tag_box, BLUE, 5), glow(frame, BLUE, 4), run_time=0.6)
            self.wait_until(v.cue("model") - 0.3)
            self.play(FadeIn(just, shift=DOWN * 0.06), model.think(0.6), run_time=0.6)
            self.wait_until(v.cue("reply") - 0.3)
            self.play(pulse(plain, 1.15), run_time=0.5)

        ghost = VGroup(RoundedRectangle(width=1.55, height=0.62, corner_radius=0.1).set_stroke(MUTED, 1.4),
                       en("planning part", 15, MUTED)).arrange(ORIGIN)
        ghost[1].move_to(ghost[0])
        ghost_o = DashedVMobject(ghost[0], num_dashes=28).set_stroke(MUTED, 1.4)
        ghost = VGroup(ghost_o, ghost[1]).next_to(model, DOWN, buff=0.35)
        x = I.cross_icon(0.42, RED).move_to(ghost)
        same = Pill(caps("same model", 13, BLUE), BLUE, pad_x=0.16, pad_y=0.06).next_to(model, UP, buff=0.16)
        with self.say("s03_05") as v:
            self.wait_until(v.cue("special") - 0.3)
            self.play(FadeIn(ghost, shift=UP * 0.12), run_time=0.5)
            self.play(FadeIn(x, scale=1.3), run_time=0.35)
            self.wait_until(v.cue("same") - 0.3)
            self.play(FadeOut(ghost), FadeOut(x), FadeIn(same, shift=DOWN * 0.06), run_time=0.5)

        with self.say("s03_06") as v:
            self.wait_until(v.cue("changes") - 0.3)
            self.play(user_c.animate.fade(0.6), run_time=0.4)
            self.wait_until(v.cue("first") - 0.3)
            self.play(glow(sys_c.frame, FG, 5), pulse(sys_c, 1.05), run_time=0.6)
            self.wait_until(v.cue("before") - 0.3)
            ul = Underline(sys_c.body, buff=0.04).set_stroke(PLAN, 2.2)
            self.play(Create(ul), run_time=0.5)

        # why it helps
        def benefit(icon, text):
            return VGroup(icon, en(text, 19, FG)).arrange(RIGHT, buff=0.18)

        eye = eye_icon(0.28, PLAN)
        order_i = VGroup(*[Circle(radius=0.07).set_stroke(PLAN, 1.6) for _ in range(3)]).arrange(RIGHT, buff=0.12)
        tick_i = I.check_icon(0.28, PLAN)
        bens = VGroup(benefit(eye, "the whole job, at once"), benefit(order_i, "order decided first"),
                      benefit(tick_i, "finished = every step done")).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
        bens.move_to([-4.3, 0.1, 0])
        helps = caps("why it helps", 13, PLAN).next_to(bens, UP, buff=0.32, aligned_edge=LEFT)
        with self.say("s03_07") as v:
            self.wait_until(v.cue("helps") - 0.3)
            self.play(*[FadeOut(m) for m in (sys_c, user_c, ul, a_in, a_out, same, model)],
                      FadeIn(helps), run_time=0.6)
            self.wait_until(v.cue("whole") - 0.3)
            self.play(FadeIn(bens[0], shift=RIGHT * 0.1), run_time=0.45)
            self.play(LaggedStart(*[glow(l, PLAN, 3, 0.5) for l in lines], lag_ratio=0.12), run_time=0.8)
            self.wait_until(v.cue("forgotten") - 0.2)
            self.play(pulse(lines, 1.03), run_time=0.5)

        nums = VGroup(*[l[0] for l in lines])
        done_ticks = VGroup(*[I.check_icon(0.18, PLAN).next_to(l, RIGHT, buff=0.16) for l in lines])
        with self.say("s03_08") as v:
            self.wait_until(v.cue("order") - 0.3)
            self.play(FadeIn(bens[1], shift=RIGHT * 0.1), run_time=0.45)
            self.play(LaggedStart(*[n.animate.set_color(PLAN) for n in nums], lag_ratio=0.15), run_time=0.8)
            self.wait_until(v.cue("finished") - 0.3)
            self.play(FadeIn(bens[2], shift=RIGHT * 0.1), run_time=0.45)
            self.wait_until(v.cue("every") - 0.3)
            self.play(LaggedStart(*[FadeIn(t, scale=1.3) for t in done_ticks], lag_ratio=0.12), run_time=0.8)

        just_t = Pill(mono("just text", 22, FG), MUTED, pad_x=0.26, pad_y=0.1).move_to([-3.6, 0.0, 0])
        track = VGroup(*[Circle(radius=0.12).set_stroke(PLAN, 2).set_fill(BG, 1) for _ in range(5)]).arrange(RIGHT, buff=0.8)
        track.move_to([2.6, 0.0, 0])
        rail = Line(track[0].get_center(), track[-1].get_center()).set_stroke(PLAN, 2, opacity=0.5)
        tok = Token(TEAL, 0.1).move_to(track[0])
        on_track = caps("keeps the agent on track", 14, PLAN).next_to(VGroup(rail, track), DOWN, buff=0.3)
        with self.say("s03_09") as v:
            self.wait_until(v.cue("just") - 0.4)
            self.play(*[FadeOut(m) for m in (msg, lines, done_ticks, plain, just, bens, helps, d)], run_time=0.5)
            self.play(FadeIn(just_t, scale=0.92), run_time=0.5)
            self.wait_until(v.cue("track") - 0.5)
            self.play(Create(rail), FadeIn(track, lag_ratio=0.15), FadeIn(on_track), run_time=0.6)
            self.add(rail, track, tok)
            self.play(FadeIn(tok), run_time=0.2)
            for i in range(1, 5):
                self.play(tok.animate.move_to(track[i]), track[i - 1].animate.set_fill(PLAN, 0.6), run_time=0.3)
            self.play(track[4].animate.set_fill(PLAN, 0.6), run_time=0.2)
        self.clear_all(0.6)


def send_anim(msgs, model):
    b = bundle_copy(msgs, 0.3).move_to(VGroup(*msgs))
    return Succession(b.animate(run_time=0.5).move_to(model.in_port + LEFT * 0.2), FadeOut(b, scale=0.3, run_time=0.3))
