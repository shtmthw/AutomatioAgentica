"""02 · Understanding AI models - input -> model -> output."""
import random

from agentic_video.prelude import *


def data_grid(rows=12, cols=12, size=0.075, gap=0.11, color=BLUE):
    g = VGroup()
    for r in range(rows):
        for c in range(cols):
            sq = Square(size).set_stroke(color, 1.0, opacity=0.75).set_fill(color, 0.15)
            sq.move_to([c * gap, -r * gap, 0])
            g.add(sq)
    return g.center()


def text_bars(n=9, width=2.2, gap=0.17, color=MUTED, seed=3):
    rnd = random.Random(seed)
    g = VGroup()
    for i in range(n):
        w = width * rnd.uniform(0.45, 1.0)
        ln = Line(ORIGIN, RIGHT * w).set_stroke(color, 3, opacity=0.7)
        ln.move_to([0, -i * gap, 0], aligned_edge=LEFT)
        g.add(ln)
    return g.center()


class S02Model(VoiceScene):
    SECTION = "s02"

    def construct(self):
        self.show_chapter()
        model = I.chip_labeled(2.2, "AI Model", BLUE, size=34).move_to([0.9, 0.3, 0])

        with self.say("s02_01") as v:
            self.wait_until(v.word("Model") - 0.4)
            self.play(FadeIn(model, scale=0.92), run_time=0.8)

        # ---- learns from a lot of data
        grid = data_grid().move_to([-4.0, 0.45, 0])
        grid_lab = bn("a huge amount of data", 24, MUTED).next_to(grid, DOWN, buff=0.3)
        with self.say("s02_02") as v:
            self.wait_until(v.word("बहुत") - 0.3)
            self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in grid], lag_ratio=0.004),
                      FadeIn(grid_lab), run_time=1.2)
            self.wait_until(v.word("सीखा") - 0.6)
            flow = grid.copy()
            self.play(LaggedStart(*[s.animate.move_to(model.body.get_center()).set_opacity(0) for s in flow],
                                  lag_ratio=0.004), pulse(model, 1.06, run_time=1.6), glow(model.body, BLUE, run_time=1.6),
                      run_time=1.6)
            self.remove(flow)

        # ---- large language model
        full = en("Large Language Model", 40, FG, t2c={"L": BLUE, "M": BLUE}).move_to([0.9, -1.55, 0])
        llm_t = en("LLM", 34, BLUE).move_to(model.text)
        with self.say("s02_03") as v:
            self.wait_until(v.word("Large") - 0.2)
            self.play(FadeIn(full, shift=UP * 0.1), run_time=0.7)
            self.wait_until(v.word("LLM") - 0.3)
            self.play(Transform(model.text, llm_t), Indicate(full, color=BLUE, scale_factor=1.04), run_time=0.8)

        # ---- learned from text: questions, explanations, answers
        bars = text_bars().move_to(grid)
        bars_lab = bn("countless texts", 24, MUTED).next_to(bars, DOWN, buff=0.3)
        labels = ["questions", "explanations", "answers"]
        cue_words = ["सवाल", "समझाते", "जवाब"]       # the matching spoken words
        pills = VGroup(*[Pill(t, BLUE, size=24) for t in labels]).arrange(DOWN, buff=0.28).move_to([4.6, 0.3, 0])
        with self.say("s02_04") as v:
            self.play(ReplacementTransform(grid, bars), FadeTransform(grid_lab, bars_lab), run_time=1.0)
            for i, w in enumerate(cue_words):
                self.wait_until(v.word(w) - 0.25)
                self.play(FadeIn(pills[i], shift=LEFT * 0.15), run_time=0.45)

        # ---- the pipeline: input -> model -> output
        z_in = Zone(3.5, 2.6, FG, "input", label_size=28).move_to([-4.75, 0.35, 0])
        z_out = Zone(3.5, 2.6, TEAL, "output", label_size=28).move_to([4.75, 0.35, 0])
        q_card = Card(3.05, 1.02, FG, fill=PANEL, stroke_width=1.4)
        q_card.add(bn("What is the capital\nof India?", 22).move_to(q_card.frame))
        q_card.move_to(z_in.shape.get_center() + DOWN * 0.25)
        a_in = arrow(z_in.shape.get_right() + RIGHT * 0.12, [-1.1, 0.35, 0])
        a_out = arrow([1.1, 0.35, 0], z_out.shape.get_left() + LEFT * 0.12)

        with self.say("s02_05") as v:
            self.play(*[FadeOut(m) for m in (bars, bars_lab, pills, full)],
                      model.animate.scale(0.72).move_to([0, 0.35, 0]), run_time=0.9)
            self.play(FadeIn(z_in), FadeIn(z_out), GrowArrow(a_in), GrowArrow(a_out), run_time=0.9)
            self.wait_until(v.word("लिखकर") - 0.3)
            self.play(FadeIn(q_card, shift=UP * 0.12), run_time=0.6)
            self.wait_until(v.word("Input") - 0.2)
            self.play(Indicate(z_in.label, color=FG, scale_factor=1.15), run_time=0.7)

        with self.say("s02_06") as v:
            mover = q_card.copy()
            self.play(mover.animate.scale(0.3).move_to(model.body).set_opacity(0), run_time=1.0)
            self.remove(mover)
            self.play(pulse(model, 1.07), glow(model.body, BLUE), run_time=0.8)

        # ---- context
        ctx = Zone(5.2, 1.22, AMBER, None, radius=0.28, fill_opacity=0.06).move_to([0, 2.4, 0])
        ctx_lab = VGroup(en("context", 24, AMBER), bn("= what it can see", 22, AMBER)).arrange(RIGHT, buff=0.15)
        ctx_lab.next_to(ctx.shape.get_top(), DOWN, buff=0.12)
        ctx_q = bn("What is the capital of India?", 23, FG)
        ctx_more = VGroup(Line(ORIGIN, RIGHT * 0.75), Line(ORIGIN, RIGHT * 0.45)).arrange(RIGHT, buff=0.12)
        ctx_more.set_stroke(DIM, 3)
        ctx_body = VGroup(ctx_q, ctx_more).arrange(RIGHT, buff=0.25).next_to(ctx_lab, DOWN, buff=0.14)
        if ctx_body.width > 4.85:
            ctx_body.scale_to_fit_width(4.85)
        link = DashedLine(ctx.shape.get_bottom(), model.body.get_top() + UP * 0.2, dash_length=0.06).set_stroke(AMBER, 1.6)
        with self.say("s02_07") as v:
            self.play(FadeIn(ctx), Create(link), run_time=0.7)
            self.play(FadeIn(ctx_body, shift=DOWN * 0.08), run_time=0.6)
            self.wait_until(v.word("Context") - 0.2)
            self.play(FadeIn(ctx_lab, shift=DOWN * 0.08), ctx.lit(0.12), run_time=0.6)

        a_card = Card(3.05, 1.02, TEAL, fill=PANEL, stroke_width=1.4)
        a_card.add(bn("The capital of India\nis New Delhi.", 22).move_to(a_card.frame))
        a_card.move_to(z_out.shape.get_center() + DOWN * 0.25)
        with self.say("s02_08") as v:
            self.play(pulse(model, 1.06), glow(model.body, BLUE), run_time=0.6)
            start = a_card.copy().scale(0.3).move_to(model.body).set_opacity(0)
            self.play(Transform(start, a_card), run_time=0.9)
            self.remove(start)
            self.add(a_card)
            self.wait_until(v.word("Output") - 0.2)
            self.play(Indicate(z_out.label, color=TEAL, scale_factor=1.12), run_time=0.7)

        # ---- examples
        ex = VGroup(*[Pill(en(n, 28, BLUE), BLUE, pad_x=0.32) for n in ("GPT", "Claude", "Gemini")])
        ex.arrange(RIGHT, buff=0.3).move_to([0, -1.75, 0])
        with self.say("s02_09") as v:
            for i, n in enumerate(("GPT", "Claude", "Gemini")):
                self.wait_until(v.word(n) - 0.2)
                self.play(FadeIn(ex[i], shift=UP * 0.1), run_time=0.4)

        # ---- a model alone only produces text
        f_ic = I.file_icon(0.6, MUTED).move_to([-1.5, -1.85, 0])
        t_ic = I.terminal_icon(0.55, MUTED).move_to([1.5, -1.85, 0])
        l_f = DashedLine(model.body.get_bottom() + DOWN * 0.2 + LEFT * 0.2, f_ic.get_top() + UP * 0.08, dash_length=0.07).set_stroke(DIM, 1.6)
        l_t = DashedLine(model.body.get_bottom() + DOWN * 0.2 + RIGHT * 0.2, t_ic.get_top() + UP * 0.08, dash_length=0.07).set_stroke(DIM, 1.6)
        x_f = I.cross_icon(0.32).move_to(l_f.get_center())
        x_t = I.cross_icon(0.32).move_to(l_t.get_center())
        with self.say("s02_10") as v:
            self.wait_until(v.word("सिर्फ़") - 0.3)
            self.play(FadeOut(ex), pulse(a_card, 1.05), glow(a_card.frame, TEAL), run_time=0.8)
            self.wait_until(v.word("File") - 0.4)
            self.play(FadeIn(f_ic), Create(l_f), run_time=0.5)
            self.play(FadeIn(x_f, scale=1.4), run_time=0.35)
            self.wait_until(v.word("प्रोग्राम") - 0.3)
            self.play(FadeIn(t_ic), Create(l_t), run_time=0.5)
            self.play(FadeIn(x_t, scale=1.4), run_time=0.35)

        q = en("?", 120, AMBER).move_to([3.0, -1.6, 0])
        with self.say("s02_11") as v:
            others = [m for m in self.mobjects if m not in (model, self.chapter)]
            self.play(*[dim(m, 0.18) for m in others], run_time=0.8)
            self.play(FadeIn(q, scale=0.8), run_time=0.6)
        self.clear_all(0.8)
