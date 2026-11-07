"""01 · Introduction - an AI that explains vs. an agent that acts."""
from agentic_video.prelude import *


class S01Intro(VoiceScene):
    SECTION = "s01"

    def construct(self):
        # ---------------------------------------------------- the error
        term = Terminal(5.8, 1.7, "terminal", font_size=22).scale(1.25).move_to([0, 0.4, 0])
        with self.say("s01_01") as v:
            self.play(FadeIn(term, shift=UP * 0.12), run_time=0.8)
            l1 = term.next_line("$ python app.py")
            self.play(AddTextLetterByLetter(l1, run_time=0.9))
            self.wait_until(v.cue("error") - 0.2)
            l2 = term.next_line("ZeroDivisionError", RED)
            self.play(FadeIn(l2, shift=RIGHT * 0.1), run_time=0.4)
            self.play(Indicate(l2, color=RED, scale_factor=1.06), run_time=0.8)
        self.attach(term, l1, l2)

        # ---------------------------------------------------- scenario A
        zone_a = Zone(6.2, 5.35, BLUE, "AI").move_to([-3.55, 0.2, 0])
        zone_b = Zone(6.2, 5.35, TEAL, "AI Agent").move_to([3.55, 0.2, 0])
        user_a = I.user_icon(0.5, MUTED).move_to([-6.05, 1.35, 0])
        ask_a = Bubble("What does this error mean?", size=24, side="left")
        ask_a.next_to(user_a, RIGHT, buff=0.22).shift(UP * 0.26)

        with self.say("s01_02") as v:
            self.play(
                FadeIn(zone_a),
                term.animate.scale(0.76 / 1.25).move_to([-3.55, -1.36, 0]),
                run_time=1.0,
            )
            self.show_chapter()
            self.wait_until(v.cue("ask") - 0.3)
            self.play(FadeIn(user_a, shift=UP * 0.1), FadeIn(ask_a, shift=UP * 0.1), run_time=0.6)

        model_a = I.chip_labeled(0.9, "AI", BLUE).move_to([-1.1, -0.05, 0])
        answer = Bubble("It is dividing by zero,\nso the program stops.",
                        size=21, side="right", color=BLUE)
        answer.next_to(model_a, LEFT, buff=0.25).shift(UP * 0.3)
        with self.say("s01_03"):
            self.play(FadeIn(model_a, scale=0.9), run_time=0.6)
            self.play(pulse(model_a, 1.08), glow(model_a.body, BLUE), run_time=0.6)
            self.play(FadeIn(answer, shift=LEFT * 0.1), run_time=0.7)

        still = bn("the problem is still there", 20, AMBER).next_to(term, DOWN, buff=0.14)
        with self.say("s01_04") as v:
            self.wait_until(v.cue("fix") - 0.2)
            self.play(Indicate(l2, color=RED, scale_factor=1.08), run_time=0.8)
            self.play(FadeIn(still, shift=UP * 0.08), pulse(user_a, 1.12), run_time=0.7)

        # ---------------------------------------------------- scenario B
        self.narrate("s01_05", FadeIn(zone_b), run_time=0.9)

        user_b = I.user_icon(0.5, MUTED).move_to([1.05, 1.35, 0])
        ask_b = Bubble("Find the error, understand why,\nand fix it.", size=21, side="left", color=TEAL)
        ask_b.next_to(user_b, RIGHT, buff=0.22).shift(UP * 0.26)
        with self.say("s01_06"):
            self.play(FadeIn(user_b, shift=UP * 0.1), FadeIn(ask_b, shift=UP * 0.1), run_time=0.7)

        names = ["app.py", "stats.py", "test.py"]
        files = VGroup()
        for i, n in enumerate(names):
            ic = I.file_icon(0.5, MUTED)
            lab = mono(n, 15, MUTED).next_to(ic, DOWN, buff=0.1)
            files.add(VGroup(ic, lab).move_to([2.25 + i * 1.3, 0.05, 0]))
        tb = Terminal(5.8, 2.0, "terminal", font_size=22).scale(0.76).move_to([3.55, -1.5, 0])
        agent = AgentBadge().scale(0.85)

        def over(f):
            return f[0].get_top() + UP * 0.28

        with self.say("s01_07") as v:
            self.play(LaggedStart(*[FadeIn(f, shift=UP * 0.08) for f in files], lag_ratio=0.15),
                      FadeIn(tb), run_time=0.8)
            agent.move_to(over(files[0]))
            self.play(FadeIn(agent, scale=0.8), run_time=0.4)
            self.play(files[0][0].animate.set_stroke(TEAL), run_time=0.3)
            self.play(agent.animate.move_to(over(files[1])), files[0][0].animate.set_stroke(MUTED),
                      files[1][0].animate.set_stroke(TEAL), run_time=0.6)
            self.wait_until(v.cue("commands") - 0.3)
            self.play(agent.animate.move_to(tb.get_top() + UP * 0.12 + RIGHT * 1.3),
                      files[1][0].animate.set_stroke(MUTED), run_time=0.6)
            r1 = tb.next_line("$ run tests")
            self.play(AddTextLetterByLetter(r1, run_time=0.6))

        with self.say("s01_08") as v:
            r2 = tb.next_line("✗ ZeroDivisionError", RED)
            self.play(FadeIn(r2, shift=RIGHT * 0.08), run_time=0.4)
            self.play(Indicate(r2, color=RED, scale_factor=1.06), run_time=0.5)
            self.wait_until(v.cue("fix") - 0.3)
            self.play(agent.animate.move_to(over(files[1])), run_time=0.6)
            self.play(files[1][0].animate.set_stroke(AMBER), Flash(files[1][0], color=AMBER, line_length=0.12,
                      flash_radius=0.45), run_time=0.6)
            self.wait_until(v.cue("check") - 0.3)
            self.play(agent.animate.move_to(tb.get_top() + UP * 0.12 + RIGHT * 1.3),
                      files[1][0].animate.set_stroke(TEAL), run_time=0.6)
            r3 = tb.next_line("✓ all tests passed", TEAL)
            self.play(FadeIn(r3, shift=RIGHT * 0.08), run_time=0.4)
        self.attach(tb, r1, r2, r3)

        # ---------------------------------------------------- the contrast
        content_a = VGroup(user_a, ask_a, model_a, answer, term, still)
        content_b = VGroup(user_b, ask_b, files, tb, agent)
        cap_a = Pill(bn("gives information", 38, BLUE), BLUE, pad_x=0.4, pad_y=0.18).move_to(zone_a.shape)
        cap_b = Pill(bn("takes action", 38, TEAL), TEAL, pad_x=0.4, pad_y=0.18).move_to(zone_b.shape)
        with self.say("s01_09") as v:
            self.play(dim(content_a, 0.22), FadeIn(cap_a, scale=0.9), run_time=0.8)
            self.wait_until(v.cue("second") - 0.2)
            self.play(dim(content_b, 0.22), FadeIn(cap_b, scale=0.9), run_time=0.8)

        title = en("Agentic AI", 84, FG).move_to(UP * 0.35)
        how = bn("How?", 40, AMBER).next_to(title, DOWN, buff=0.45)
        with self.say("s01_10") as v:
            self.wait_until(v.cue("agentic") - 0.6)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.6)
            self.play(Write(title), run_time=1.0)
            self.wait_until(v.cue("how") - 0.2)
            self.play(FadeIn(how, shift=UP * 0.1), run_time=0.6)
        self.clear_all(0.8)
