"""02 · The model only produces text: text in / text out, and no memory between calls."""
from agentic_video.prelude import *


def note(s, color=FG, size=22):
    t = bn(s, size, FG)
    f = RoundedRectangle(width=t.width + 0.42, height=t.height + 0.3, corner_radius=0.1)
    f.set_stroke(color, 1.5).set_fill(PANEL, 1)
    t.move_to(f)
    return VGroup(f, t)


def no_pill(text):
    return Pill(VGroup(I.cross_icon(0.2), en(text, 24, MUTED)).arrange(RIGHT, buff=0.14), DIM, pad_x=0.26, pad_y=0.12)


class S02TextOnly(VoiceScene):
    SECTION = "s02"

    def feed(self, card, model, rt=0.9, extra=()):
        """The text travels into the model (a token along the input side), the model works."""
        tok = Token(card.accent if hasattr(card, "accent") else FG, 0.08).move_to(card.get_right())
        path = Line(card.get_right(), model.in_port + RIGHT * 0.1)
        self.play(FadeIn(tok, scale=0.5), glow(card[0], BLUE, 5, 0.4), run_time=0.25)
        self.play(MoveAlongPath(tok, path), run_time=rt * 0.55)
        self.play(FadeOut(tok, scale=0.5), model.think(rt * 0.45), *extra, run_time=rt * 0.45)

    def construct(self):
        self.show_chapter()
        model = ModelBox(2.8, 1.7).move_to([0, 0.35, 0])
        slots = [np.array([-2.6, 2.62, 0]), np.array([2.6, 2.62, 0])]
        f_dim = [Pill(caps(f"fact {i + 1}", 16, DIM), DIM, pad_x=0.3).move_to(slots[i]) for i in range(2)]
        f_lit = [Pill(VGroup(caps(f"fact {i + 1}", 15, BLUE), en(t, 23, FG)).arrange(RIGHT, buff=0.18), BLUE,
                      pad_x=0.26).move_to(slots[i]) for i, t in enumerate(("text in, text out", "no memory"))]

        with self.say("s02_01") as v:
            self.play(FadeIn(model, scale=0.92), run_time=0.7)
            self.wait_until(v.cue("facts") - 0.3)
            self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.08) for f in f_dim], lag_ratio=0.3), run_time=0.7)

        # ---- fact 1: text in, text out
        q = note("What is the capital of India?").move_to([-4.55, 0.35, 0])
        a = note("New Delhi.", BLUE).move_to([4.2, 0.35, 0])
        a_in = arrow(q.get_right() + RIGHT * 0.1, model.in_port + LEFT * 0.08, color=MUTED, tip=0.12)
        a_out = arrow(model.out_port + RIGHT * 0.08, a.get_left() + LEFT * 0.1, color=MUTED, tip=0.12)
        with self.say("s02_02") as v:
            self.wait_until(v.cue("inout") - 0.3)
            self.play(FadeTransform(f_dim[0], f_lit[0]), run_time=0.6)
            self.wait_until(v.cue("send") - 0.3)
            self.play(FadeIn(q, shift=RIGHT * 0.15), run_time=0.5)
            self.play(GrowArrow(a_in), run_time=0.4)
            self.feed(q, model, 0.8)
            self.wait_until(v.cue("back") - 0.3)
            self.play(GrowArrow(a_out), FadeIn(a, shift=RIGHT * 0.3), run_time=0.6)

        span = VGroup(Line([-6.2, -1.15, 0], [5.4, -1.15, 0]).set_stroke(BLUE, 1.6, opacity=0.7),
                      Line([-6.2, -1.0, 0], [-6.2, -1.3, 0]).set_stroke(BLUE, 1.6, opacity=0.7),
                      Line([5.4, -1.0, 0], [5.4, -1.3, 0]).set_stroke(BLUE, 1.6, opacity=0.7))
        call_lab = Pill(VGroup(caps("one call", 15, BLUE), en("= one round trip", 22, FG)).arrange(RIGHT, buff=0.16),
                        BLUE, pad_x=0.26).move_to([-0.4, -1.72, 0])
        tok = Token(BLUE, 0.08)
        trip = Line(q.get_right(), a.get_left())
        with self.say("s02_03") as v:
            self.wait_until(v.cue("trip") - 0.3)
            tok.move_to(trip.get_start())
            self.play(FadeIn(tok, scale=0.5), run_time=0.2)
            self.play(MoveAlongPath(tok, trip), run_time=1.0, rate_func=smooth)
            self.play(FadeOut(tok), Create(span), run_time=0.4)
            self.wait_until(v.cue("call") - 0.3)
            self.play(FadeIn(call_lab, shift=UP * 0.1), run_time=0.5)

        # ---- that's all it can do
        nos = VGroup(no_pill("no hands"), no_pill("no eyes"), no_pill("no connection")).arrange(RIGHT, buff=0.45)
        nos.move_to([0, -1.55, 0])
        with self.say("s02_04") as v:
            self.play(*[FadeOut(m) for m in (q, a, a_in, a_out, span, call_lab)], run_time=0.6)
            for i, w in enumerate(("hands", "eyes", "connection")):
                self.wait_until(v.cue(w) - 0.3)
                self.play(FadeIn(nos[i], shift=UP * 0.1), run_time=0.45)

        # ---- the world is behind a wall
        things = VGroup(*[VGroup(ic, en(t, 26, MUTED)).arrange(RIGHT, buff=0.3)
                          for ic, t in ((I.file_icon(0.62, MUTED), "files"), (I.terminal_icon(0.55, MUTED), "terminal"),
                                        (I.globe_icon(0.62, MUTED), "internet"))])
        things.arrange(DOWN, buff=0.55, aligned_edge=LEFT).move_to([4.25, 0.3, 0])
        wall = DashedLine([1.2, 2.15, 0], [1.2, -1.75, 0], dash_length=0.12).set_stroke(DIM, 3)
        wall_lab = en("wall", 20, DIM).next_to(wall, DOWN, buff=0.14)
        with self.say("s02_05") as v:
            self.play(FadeOut(nos, shift=DOWN * 0.1), model.animate.move_to([-3.0, 0.35, 0]), run_time=0.7)
            for i, w in enumerate(("files", "terminal", "internet")):
                self.wait_until(v.cue(w) - 0.3)
                self.play(FadeIn(things[i], shift=LEFT * 0.12), run_time=0.45)
            self.wait_until(v.cue("wall") - 0.4)
            self.play(Create(wall), FadeIn(wall_lab), run_time=0.7)
            self.wait_until(v.cue("cant") - 0.6)
            reach = [DashedLine(model.out_port + RIGHT * 0.1, [1.05, t.get_y(), 0], dash_length=0.08).set_stroke(BLUE, 1.8)
                     for t in things]
            self.play(*[Create(r) for r in reach], run_time=0.6)
            crosses = VGroup(*[I.cross_icon(0.3).move_to([1.2, t.get_y(), 0]) for t in things])
            self.play(FadeIn(crosses, scale=1.4), wall.animate.set_stroke(RED, opacity=0.7), run_time=0.4)
            self.play(wall.animate.set_stroke(DIM, opacity=1), run_time=0.4)

        # ---- fact 2: no memory
        with self.say("s02_06") as v:
            self.play(*[FadeOut(m) for m in (things, wall, wall_lab, crosses, *reach)],
                      model.animate.move_to([0, 0.35, 0]), run_time=0.7)
            self.wait_until(v.cue("remember") - 0.4)
            self.play(FadeTransform(f_dim[1], f_lit[1]), f_lit[0].animate.fade(0.6), run_time=0.6)

        u1 = MessageCard("user", "My name is Rahul.", width=3.95).move_to([-4.65, 0.35, 0])
        r1 = MessageCard("assistant", "Hello, Rahul!", width=3.5).move_to([4.75, 0.35, 0])
        badge1 = model.badge("call #1")
        with self.say("s02_07") as v:
            self.wait_until(v.cue("first") - 0.3)
            self.play(FadeIn(badge1, shift=DOWN * 0.08), run_time=0.4)
            self.wait_until(v.cue("msg") - 0.3)
            self.play(FadeIn(u1, shift=RIGHT * 0.15), run_time=0.5)
            self.feed(u1, model, 0.8)

        with self.say("s02_08") as v:
            self.wait_until(v.cue("reply") - 0.35)
            self.play(FadeIn(r1, shift=RIGHT * 0.3), run_time=0.55)

        blank = VGroup(paper(0.5, 0.62, lines=0), en("blank page", 24, MUTED)).arrange(RIGHT, buff=0.2)
        blank.next_to(model, DOWN, buff=0.45)
        with self.say("s02_09") as v:
            self.wait_until(v.cue("ends") - 0.3)
            self.play(FadeOut(u1, shift=DOWN * 0.2), FadeOut(r1, shift=DOWN * 0.2), FadeOut(badge1), run_time=0.6)
            self.wait_until(v.cue("keeps") - 0.3)
            self.play(model.reset_flash(0.9), run_time=0.9)
            self.wait_until(v.cue("fresh") - 0.3)
            self.play(FadeIn(blank, shift=UP * 0.1), run_time=0.5)

        u2 = MessageCard("user", "What is my name?", width=3.95).move_to([-4.65, 0.35, 0])
        r2 = MessageCard("assistant", "I don't know.", width=3.5).move_to([4.75, 0.35, 0])
        badge2 = model.badge("call #2")
        sep = caps("separate call", 15, DIM).next_to(badge2, LEFT, buff=0.3)
        with self.say("s02_10") as v:
            self.wait_until(v.cue("second") - 0.3)
            self.play(FadeOut(blank), FadeIn(badge2, shift=DOWN * 0.08), FadeIn(sep), run_time=0.5)
            self.wait_until(v.cue("msg") - 0.3)
            self.play(FadeIn(u2, shift=RIGHT * 0.15), run_time=0.5)
            self.feed(u2, model, 0.8)

        qm = en("?", 54, AMBER).next_to(model.frame, DOWN, buff=0.28)
        with self.say("s02_11") as v:
            self.wait_until(v.cue("reply") - 0.35)
            self.play(FadeIn(r2, shift=RIGHT * 0.3), FadeIn(qm, scale=0.7), run_time=0.55)

        indep = Pill(en("independent", 24, FG), FG, pad_x=0.3).move_to([0, -1.85, 0])
        sees = en("all it sees", 22, BLUE).next_to(u2, DOWN, buff=0.22)
        with self.say("s02_12") as v:
            self.wait_until(v.cue("independent") - 0.35)
            self.play(FadeIn(indep, shift=DOWN * 0.08), FadeOut(sep), run_time=0.5)
            self.wait_until(v.cue("now") - 0.35)
            self.play(glow(u2.frame, BLUE, 6), pulse(u2, 1.05), FadeIn(sees, shift=UP * 0.06), run_time=0.7)

        ghosts_vis = VGroup(MessageCard("user", "My name is Rahul.", width=3.95, dashed=True),
                            MessageCard("assistant", "Hello, Rahul!", width=3.95, dashed=True))
        ghosts_vis.arrange(DOWN, buff=0.12).move_to([-4.65, -1.75, 0])
        with self.say("s02_13") as v:
            self.wait_until(v.cue("earlier") - 0.35)
            earlier = caps("earlier conversation", 14, DIM).next_to(ghosts_vis, UP, buff=0.12)
            self.play(FadeIn(ghosts_vis, shift=UP * 0.1), FadeIn(earlier), FadeOut(sees), FadeOut(indep), run_time=0.6)
            self.play(ghosts_vis.animate.fade(0.6), run_time=0.4)
            not_sent = DashedLine(ghosts_vis.get_right() + RIGHT * 0.1, model.frame.get_corner(DL) + LEFT * 0.05,
                                  dash_length=0.07).set_stroke(DIM, 1.6)
            x = I.cross_icon(0.28).move_to(not_sent.get_center())
            self.play(Create(not_sent), run_time=0.5)
            self.play(FadeIn(x, scale=1.3), run_time=0.3)
            self.wait_until(v.cue("before") - 0.3)
            self.play(pulse(qm, 1.3), run_time=0.6)

        # ---- but chat apps do remember
        win = Window(7.2, 3.95, "chat").move_to([0, -0.42, 0])
        bubbles = [Bubble("My name is Rahul.", FG, 22, side="right"), Bubble("Hello, Rahul!", BLUE, 22, side="left"),
                   Bubble("What is my name?", FG, 22, side="right"), Bubble("Your name is Rahul.", BLUE, 22, side="left")]
        top = win.frame.get_top()[1] - win.bar_h - 0.42
        for i, b in enumerate(bubbles):
            x = win.frame.get_right()[0] - 0.35 - b.width / 2 if i % 2 == 0 else win.frame.get_left()[0] + 0.35 + b.width / 2
            b.move_to([x, top - i * 0.78, 0])
        ok = I.check_icon(0.34, TEAL).next_to(bubbles[3], RIGHT, buff=0.25)
        with self.say("s02_14") as v:
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.7)
            self.wait_until(v.cue("chatgpt") - 0.4)
            self.play(FadeIn(win, shift=UP * 0.1), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.08) for b in bubbles], lag_ratio=0.35), run_time=1.6)
            self.wait_until(v.cue("remember") - 0.3)
            self.play(glow(bubbles[3].frame, TEAL, 6), FadeIn(ok, scale=0.7), run_time=0.6)

        question = bn("So how do ChatGPT or Claude remember what you said earlier?", 32, FG).move_to([0, 2.55, 0])
        if question.width > 12.6:
            question.scale_to_fit_width(12.6)
        with self.say("s02_15") as v:
            self.play(FadeIn(question, shift=DOWN * 0.1), run_time=0.7)
        self.wait(1.8)
        self.clear_all(0.8)
