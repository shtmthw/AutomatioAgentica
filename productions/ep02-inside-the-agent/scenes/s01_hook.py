"""01 · Who runs the loop? Recap of the Episode 01 loop, the hook, the title card."""
from agentic_video.prelude import *


class S01Hook(VoiceScene):
    SECTION = "s01"

    def construct(self):
        self.show_chapter()
        recap = Pill(en("last lesson · recap", 20, MUTED), DIM, pad_x=0.22).move_to([5.3, 3.0, 0])
        loop = LoopDiagram(center=[0, -0.45, 0])
        hub = en("agent loop", 26, MUTED).move_to(loop.center)
        tok = Token(TEAL, 0.085)

        def visit(a, b, rt=0.75):
            node = loop.nodes[b]
            self.play(MoveAlongPath(tok, loop.leg(a, b)), run_time=rt * 0.7)
            self.play(glow(node.zone.shape, node.accent, 6, rt * 0.5), pulse(node, 1.06, rt * 0.5),
                      run_time=rt * 0.5)

        # ---- the Episode 01 loop, fully lit
        with self.say("s01_01") as v:
            self.play(FadeIn(recap, shift=DOWN * 0.08), run_time=0.6)
            self.wait_until(v.cue("heart") - 0.5)
            self.play(LaggedStart(*[FadeIn(p, scale=0.94) for p in loop.parts_in_order()], lag_ratio=0.1),
                      run_time=1.5)
            self.add(loop)
            self.wait_until(v.cue("loop") - 0.3)
            self.play(*loop.all_lit(), FadeIn(hub, scale=0.95), run_time=0.8)

        with self.say("s01_02") as v:
            self.wait_until(v.cue("goal") - 0.3)
            tok.move_to(loop.goal.get_center())
            trail = loop.trail(tok)
            self.add(trail)
            self.play(FadeIn(tok, scale=0.5), glow(loop.goal.zone.shape, FG, 6), pulse(loop.goal, 1.06), run_time=0.6)
            self.wait_until(v.cue("decides") - 0.55)
            visit("goal", "decide")
            self.wait_until(v.cue("acts") - 0.55)
            visit("decide", "act")

        with self.say("s01_03") as v:
            self.wait_until(v.cue("observes") - 0.55)
            visit("act", "observe")
            self.wait_until(v.cue("evaluates") - 0.55)
            visit("observe", "evaluate")

        with self.say("s01_04") as v:
            self.wait_until(v.cue("repeats") - 0.5)
            self.play(MoveAlongPath(tok, loop.leg("evaluate", "decide")), glow(loop.arcs["ed"].line, VIOLET, 5),
                      pulse(loop.repeat, 1.15), run_time=0.8)
            self.play(pulse(loop.nodes["decide"], 1.06, 0.35), run_time=0.35)
            self.wait_until(v.cue("again") - 0.2)
            for _ in range(2):
                for a, b in (("decide", "act"), ("act", "observe"), ("observe", "evaluate"), ("evaluate", "decide")):
                    self.play(MoveAlongPath(tok, loop.leg(a, b), rate_func=linear), run_time=0.27)

        # ---- what we said the agent does
        def action(icon, text):
            return Pill(VGroup(icon, en(text, 28, TEAL)).arrange(RIGHT, buff=0.18), TEAL, pad_x=0.3, pad_y=0.14)

        reads = action(I.file_icon(0.36, TEAL), "reads files")
        runs = action(I.terminal_icon(0.32, TEAL), "runs commands")
        VGroup(reads, runs).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([3.2, 0.25, 0])
        loop_g = VGroup(loop, hub)
        with self.say("s01_05") as v:
            self.play(FadeOut(tok), FadeOut(trail), FadeOut(recap), loop_g.animate.scale(0.6).move_to([-3.9, -0.1, 0]),
                      run_time=0.9)
            self.remove(trail)
            self.wait_until(v.cue("reads") - 0.3)
            self.play(FadeIn(reads, shift=LEFT * 0.12), run_time=0.5)
            self.wait_until(v.cue("runs") - 0.3)
            self.play(FadeIn(runs, shift=LEFT * 0.12), run_time=0.5)

        # ---- but a model only produces text
        model = ModelBox(2.8, 1.7).move_to([3.0, 0.35, 0])
        out = Pill(mono("text", 22, FG), FG, pad_x=0.2)
        out.move_to(model.out_port + RIGHT * (out.width / 2 + 0.45))
        out_arrow = arrow(model.out_port + RIGHT * 0.05, out.get_left() + LEFT * 0.05, color=MUTED, tip=0.1)
        only = en("only text", 24, BLUE).next_to(model, DOWN, buff=0.32)
        with self.say("s01_06") as v:
            self.wait_until(v.cue("model") - 0.45)
            self.play(FadeOut(reads, shift=RIGHT * 0.1), FadeOut(runs, shift=RIGHT * 0.1), *loop.all_dim(),
                      hub.animate.set_opacity(0.3), FadeIn(model, scale=0.92), run_time=0.8)
            self.wait_until(v.cue("only") - 0.35)
            self.play(GrowArrow(out_arrow), FadeIn(out, shift=RIGHT * 0.3), model.think(), run_time=0.6)
            self.play(FadeIn(only, shift=UP * 0.08), run_time=0.4)

        # ---- zoom in: the model tries to "read a file" and cannot reach it
        big = ModelBox(5.6, 3.3, label_size=30).move_to([-1.3, 0.05, 0])
        big.content.move_to(big.frame.get_top() + DOWN * (big.content.height / 2 + 0.38))
        file_ic = I.file_icon(0.95, MUTED).move_to([4.35, 0.25, 0])
        file_lab = en("a file", 24, MUTED).next_to(file_ic, DOWN, buff=0.2)
        with self.say("s01_07") as v:
            self.wait_until(v.cue("zoom") - 0.35)
            self.play(FadeOut(loop_g), FadeOut(out), FadeOut(out_arrow), FadeOut(only),
                      ReplacementTransform(model, big), run_time=1.0)
            self.wait_until(v.cue("read") - 0.3)
            self.play(FadeIn(file_ic, shift=LEFT * 0.1), FadeIn(file_lab), run_time=0.5)

        act = Pill(mono("read the file", 24, FG), BLUE, pad_x=0.3, pad_y=0.14)
        act.move_to(big.frame.get_center() + DOWN * 0.62)
        home = act.get_center()
        edge_x = big.frame.get_right()[0]
        with self.say("s01_08") as v:
            self.wait_until(v.cue("words") - 0.3)
            self.play(FadeIn(act, scale=0.9), run_time=0.6)
            self.wait_until(v.cue("cant") - 1.2)
            self.play(act.animate.move_to([edge_x - 0.1 - act.width / 2, home[1], 0]), run_time=0.55,
                      rate_func=rush_into)
            self.play(big.frame.animate.set_stroke(RED), Flash([edge_x, home[1], 0], color=RED, line_length=0.18,
                                                               flash_radius=0.3), run_time=0.35)
            self.play(act.animate.move_to(home), big.frame.animate.set_stroke(BLUE), run_time=0.6, rate_func=rush_from)
            cross = I.cross_icon(0.42).move_to([edge_x + 0.55, home[1], 0])
            lock = I.lock_icon(0.36, MUTED).next_to(file_ic, RIGHT, buff=0.16)
            self.play(FadeIn(cross, scale=1.3), FadeIn(lock, scale=0.8), run_time=0.4)

        q = bn("A model only produces text… so who opens the file?", 34, FG).move_to([0, 2.62, 0])
        if q.width > 12.4:
            q.scale_to_fit_width(12.4)
        term = I.terminal_icon(0.8, MUTED).move_to([4.35, -1.75, 0])
        term_q = en("?", 44, AMBER).next_to(term, RIGHT, buff=0.22)
        file_q = en("?", 44, AMBER).next_to(lock, RIGHT, buff=0.18)
        with self.say("s01_09") as v:
            self.wait_until(v.cue("who") - 0.5)
            self.play(FadeIn(q, shift=DOWN * 0.1), FadeIn(file_q, scale=0.8), run_time=0.7)
            self.wait_until(v.cue("cmd") - 0.3)
            self.play(FadeIn(term, shift=LEFT * 0.1), FadeIn(term_q, scale=0.8), run_time=0.5)

        # ---- title card
        sub = spaced("EPISODE 02", 22, MUTED, tracking=0.6, weight=NORMAL)
        title = spaced("INSIDE THE AGENT", 64, FG, tracking=0.36, weight=LIGHT)
        if title.width > 12.0:
            title.scale_to_fit_width(12.0)
        rule = Line(LEFT * 1.6, RIGHT * 1.6).set_stroke(FAINT, 1.6)
        VGroup(sub, title, rule).arrange(DOWN, buff=0.42).move_to(UP * 0.2)
        with self.say("s01_10") as v:
            self.wait_until(v.cue("open") - 0.3)
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
            self.wait_until(v.cue("inside") - 0.6)
            self.play(FadeIn(title, shift=UP * 0.12), FadeIn(sub, shift=UP * 0.08), run_time=1.1)
            self.play(Create(rule), run_time=0.6)
        self.wait(1.4)
        self.clear_all(0.8)
