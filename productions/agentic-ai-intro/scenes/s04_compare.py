"""04 · Chatbot vs AI agent - a straight line vs. a loop."""
from agentic_video.prelude import *


def timeline(steps, x0, y0, gap, color, size=26):
    """Dots joined by a thin line, each with a local-language label."""
    dots, labels = VGroup(), VGroup()
    for i, s in enumerate(steps):
        d = Dot([x0, y0 - i * gap, 0], radius=0.075, color=color)
        t = bn(s, size, FG).next_to(d, RIGHT, buff=0.3)
        dots.add(d)
        labels.add(t)
    rail = Line(dots[0].get_center(), dots[-1].get_center()).set_stroke(color, 1.6, opacity=0.45)
    return dots, labels, rail


class S04Compare(VoiceScene):
    SECTION = "s04"

    def construct(self):
        self.show_chapter()
        zl = Zone(6.0, 5.3, BLUE, "chatbot", label_size=30).move_to([-3.6, 0.15, 0])
        zr = Zone(6.0, 5.3, TEAL, "agent", label_size=30).move_to([3.6, 0.15, 0])
        self.narrate("s04_01", LaggedStart(FadeIn(zl), FadeIn(zr), lag_ratio=0.3), run_time=1.0)

        # ---- chatbot: three steps, then done
        c_steps = ["gets a question", "writes an answer", "returns the answer"]
        cd, cl, crail = timeline(c_steps, -6.0, 1.85, 0.95, BLUE, size=30)
        end = VGroup(Square(0.16).set_fill(BLUE, 1).set_stroke(width=0))
        end.move_to(cd[-1].get_center() + DOWN * 0.95)
        end_lab = bn("done", 30, MUTED).next_to(end, RIGHT, buff=0.3)
        end_rail = Line(cd[-1].get_center(), end.get_center()).set_stroke(BLUE, 1.6, opacity=0.45)
        ctok = Token(BLUE, 0.075).move_to(cd[0])

        for i in range(3):
            with self.say(f"s04_0{i + 2}"):
                anims = [FadeIn(cd[i], scale=0.5), FadeIn(cl[i], shift=RIGHT * 0.1)]
                if i == 0:
                    anims.append(FadeIn(ctok))
                else:
                    anims += [Create(Line(cd[i - 1].get_center(), cd[i].get_center()).set_stroke(BLUE, 1.6, opacity=0.45)),
                              ctok.animate.move_to(cd[i])]
                self.play(*anims, run_time=0.6)
                if i == 2:
                    self.wait(0.5)
                    self.play(Create(end_rail), ctok.animate.move_to(end), FadeIn(end), run_time=0.6)
                    self.play(FadeIn(end_lab, shift=RIGHT * 0.1), FadeOut(ctok), run_time=0.4)

        # ---- agent: goal -> plan -> tool -> act -> observe -> repeat
        a_steps = ["gets a goal", "works out what to do", "picks the right tool", "takes action",
                   "checks the result", "goal reached?"]
        ad, al, arail = timeline(a_steps, 1.2, 1.95, 0.7, TEAL, size=28)
        segs = [Line(ad[i].get_center(), ad[i + 1].get_center()).set_stroke(TEAL, 1.6, opacity=0.45) for i in range(5)]
        atok = Token(TEAL, 0.075).move_to(ad[0])
        for i in range(5):
            with self.say(f"s04_0{i + 5}") as v:
                anims = [FadeIn(ad[i], scale=0.5), FadeIn(al[i], shift=RIGHT * 0.1)]
                if i == 0:
                    anims.append(FadeIn(atok))
                else:
                    anims += [Create(segs[i - 1]), atok.animate.move_to(ad[i])]
                self.play(*anims, run_time=0.6)

        # loop arc from the check back to "decide what to do"
        x_loop = 5.75
        loop = VGroup()
        l1 = Line(al[5].get_right() + RIGHT * 0.2, [x_loop, ad[5].get_y(), 0])
        l2 = Line([x_loop, ad[5].get_y(), 0], [x_loop, ad[1].get_y(), 0])
        l3 = arrow([x_loop, ad[1].get_y(), 0], al[1].get_right() + RIGHT * 0.2, color=TEAL, opacity=0.8)
        for l in (l1, l2):
            l.set_stroke(TEAL, 1.8, opacity=0.8)
        loop.add(l1, l2, l3)
        rep = en("repeat", 20, TEAL).rotate(PI / 2).next_to(l2, RIGHT, buff=0.12)
        done = Pill(bn("goal reached", 22, TEAL), TEAL)
        done.move_to([1.85 + done.width / 2, -2.18, 0])
        human = Pill(bn("ask a human", 22, AMBER), AMBER).next_to(done, RIGHT, buff=0.3)
        exit_l = arrow(ad[5].get_center() + DOWN * 0.12, done.get_left() + LEFT * 0.08, color=TEAL)

        with self.say("s04_10") as v:
            self.play(FadeIn(ad[5], scale=0.5), FadeIn(al[5], shift=RIGHT * 0.1), Create(segs[4]),
                      atok.animate.move_to(ad[5]), run_time=0.6)
            self.play(Create(l1), Create(l2), GrowArrow(l3), FadeIn(rep), run_time=0.8)
            # one trip around the loop
            path = VMobject().set_points_as_corners([ad[5].get_center(), [x_loop, ad[5].get_y(), 0],
                                                     [x_loop, ad[1].get_y(), 0], ad[1].get_center()])
            self.play(MoveAlongPath(atok, path), run_time=1.2)
            for i in range(2, 6):
                self.play(atok.animate.move_to(ad[i]), run_time=0.28)
            self.wait_until(v.cue("or") - 0.4)
            self.play(GrowArrow(exit_l), FadeIn(done, shift=DOWN * 0.08), run_time=0.6)
            self.wait_until(v.cue("human") - 0.2)
            self.play(FadeIn(human, shift=DOWN * 0.08), run_time=0.5)
            self.play(atok.animate.move_to(done.get_left() + LEFT * 0.15), run_time=0.6)

        # ---- same interface, different abilities
        def chat_window(color, label):
            w = Window(4.6, 2.4, "chat", color=FAINT).move_to([0, 0, 0])
            q = Bubble("Do this task for me", size=20, side="right", color=MUTED)
            q.move_to(w.frame.get_corner(UR) + LEFT * (q.width / 2 + 0.25) + DOWN * 0.85)
            a = VGroup(*[Line(ORIGIN, RIGHT * w_).set_stroke(DIM, 3) for w_ in (2.6, 2.0, 1.2)]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            a.move_to(w.frame.get_corner(DL) + RIGHT * (a.width / 2 + 0.35) + UP * 0.6)
            tag = en(label, 28, color).next_to(w, UP, buff=0.18)
            return VGroup(w, q, a, tag)

        cw = chat_window(BLUE, "chatbot").move_to([-3.6, 0.85, 0])
        aw = chat_window(TEAL, "agent").move_to([3.6, 0.85, 0])
        eq = en("=", 54, MUTED).move_to([0, 0.75, 0])
        same = bn("look the same", 22, MUTED).next_to(eq, DOWN, buff=0.15)
        with self.say("s04_11") as v:
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.7)
            self.play(FadeIn(cw, shift=UP * 0.1), FadeIn(aw, shift=UP * 0.1), run_time=0.8)
            self.play(FadeIn(eq), FadeIn(same), run_time=0.5)

        tool_ics = VGroup(I.file_icon(0.5, TEAL), I.terminal_icon(0.45, TEAL), I.globe_icon(0.5, TEAL), I.database_icon(0.5, TEAL))
        tool_ics.arrange(RIGHT, buff=0.55).move_to([3.6, -1.35, 0])
        wires = VGroup(*[Line(aw[0].frame.get_bottom(), t.get_top() + UP * 0.08).set_stroke(TEAL, 1.4, opacity=0.6) for t in tool_ics])
        can = bn("can take action", 26, TEAL).next_to(tool_ics, DOWN, buff=0.3)
        only = bn("only answers", 26, BLUE).move_to([-3.6, can.get_y(), 0])
        with self.say("s04_12") as v:
            self.wait_until(v.cue("difference") - 0.4)
            self.play(FadeOut(eq), FadeOut(same), run_time=0.4)
            self.play(LaggedStart(*[Create(w) for w in wires], lag_ratio=0.1),
                      LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in tool_ics], lag_ratio=0.12), run_time=1.0)
            self.play(FadeIn(can, shift=UP * 0.08), FadeIn(only, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("goal") - 0.3)
            self.play(LaggedStart(*[glow(t, TEAL, 4) for t in tool_ics], lag_ratio=0.12), pulse(can, 1.06), run_time=1.0)
        self.clear_all(0.8)
