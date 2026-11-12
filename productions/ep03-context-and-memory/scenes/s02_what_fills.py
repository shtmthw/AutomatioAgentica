"""02 · What is actually filling the context: sized message cards by type, one large file read
(20% -> 60%), the share of each type, and the same tall card sent again on every call."""
from agentic_video.prelude import *
from memory_kit import *

CW_C = np.array([-4.05, -0.05, 0])
W = 3.48
LX = -0.95                       # left edge of the label column


def tag(title, note, color):
    return VGroup(caps(title, 14, color), en(note, 19, MUTED)).arrange(RIGHT, buff=0.16)


class S02WhatFills(VoiceScene):
    SECTION = "s02"

    def construct(self):
        self.show_chapter()
        ctx = LiveContext(CW_C, 3.8, 5.3)
        labels = VGroup()

        def label_for(card, title, note, color):
            t = tag(title, note, color)
            t.move_to([LX + t.width / 2, card.get_y(), 0])
            labels.add(t)
            return t

        def drop(card, frac, title, note, color, rt=0.5):
            ctx.size(card, frac)
            ctx.place(card)
            lab = label_for(card, title, note, color)
            self.play(FadeIn(card, shift=DOWN * 0.2), *ctx.meter(), FadeIn(lab, shift=LEFT * 0.1), run_time=rt)

        with self.say("s02_01") as v:
            self.wait_until(v.cue("actually") - 0.4)
            self.play(*ctx.appear(), run_time=0.7)

        sysc = SizedCard("system", "You are a coding agent.", height=0.28, width=W, size=13)
        with self.say("s02_02") as v:
            self.wait_until(v.cue("system") - 0.3)
            drop(sysc, 0.06, "system", "small · always there", MUTED)

        tools = SizedCard("tool", content=VGroup(mono("read_file · run_command · edit_file", 11, FG)), height=0.34,
                          width=W, label="tool list")
        with self.say("s02_03") as v:
            self.wait_until(v.cue("tools") - 0.3)
            drop(tools, 0.08, "tool descriptions", "small · always there", TEAL)

        user = SizedCard("user", "Why does total() crash?", height=0.28, width=W, size=13)
        asst = SizedCard("assistant", "Let me look at the code.", height=0.28, width=W, size=13)
        with self.say("s02_04") as v:
            self.wait_until(v.cue("user") - 0.3)
            drop(user, 0.03, "user", "thin", FG, 0.45)
            self.wait_until(v.cue("assistant") - 0.3)
            drop(asst, 0.02, "assistant", "thin", BLUE, 0.45)
            self.wait_until(v.cue("thin") - 0.2)
            self.play(*[glow(c.frame, c.accent, 4) for c in (user, asst)], run_time=0.5)

        ghost = VGroup(RoundedRectangle(width=0.5, height=1.5, corner_radius=0.08).set_stroke(TEAL, 1.6)
                       .set_fill(TEAL, 0.08), RoundedRectangle(width=0.5, height=0.2, corner_radius=0.06)
                       .set_stroke(TEAL, 1.3).set_fill(TEAL, 0.08)).arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
        tall_lab = VGroup(ghost, tag("tool results", "often very tall", TEAL)).arrange(RIGHT, buff=0.3)
        tall_lab.move_to([LX + tall_lab.width / 2, -1.2, 0])
        with self.say("s02_05") as v:
            self.wait_until(v.cue("tool") - 0.3)
            self.play(FadeIn(tall_lab[1], shift=LEFT * 0.1), run_time=0.45)
            self.wait_until(v.cue("tall") - 0.4)
            self.play(GrowFromEdge(ghost[0], DOWN), FadeIn(ghost[1]), run_time=0.6)

        # ---- one large file read
        model = ModelBox(2.3, 1.3).move_to([5.1, 1.85, 0])
        req = ToolCallCard("read_file", 'path = "math_utils.py"', width=3.5, size=17).move_to([4.95, 0.25, 0])
        call = ToolCallMsg("read_file", '"math_utils.py"', width=W)
        with self.say("s02_06") as v:
            self.play(FadeOut(tall_lab), run_time=0.35)
            self.wait_until(v.cue("requests") - 0.4)
            self.play(FadeIn(model, scale=0.94), run_time=0.45)
            self.play(model.think(0.5), FadeIn(req, shift=DOWN * 0.15), run_time=0.55)
            self.wait_until(v.cue("large") - 0.3)
            ctx.size(call, 0.01)
            slot = ctx.next_point(call)
            ctx.cards.append(call)
            self.play(TransformFromCopy(req, call.move_to(slot)), *ctx.meter(), run_time=0.6)
            big_lab = VGroup(I.file_icon(0.4, MUTED), en("a large file", 20, MUTED)).arrange(RIGHT, buff=0.14)
            big_lab.next_to(req, DOWN, buff=0.25)
            self.play(FadeIn(big_lab, shift=UP * 0.06), run_time=0.4)

        body = VGroup(mono("math_utils.py · whole file", 11, MUTED), code_block(1.9, 9, size=0.035, color=DIM, seed=9,
                                                                               gap=0.13)).arrange(DOWN, buff=0.1,
                                                                                                  aligned_edge=LEFT)
        big = SizedCard("tool", content=body, height=1.6, width=W)
        ctx.size(big, 0.40)
        with self.say("s02_07") as v:
            self.wait_until(v.cue("adds") - 0.3)
            big.move_to([4.95, -1.42, 0])
            self.play(FadeOut(big_lab), FadeIn(big, shift=UP * 0.15), run_time=0.5)
            self.wait_until(v.cue("jumps") - 0.6)
            self.play(*ctx.add_from(big), FadeOut(req), run_time=0.8)
            lab = label_for(big, "tool result", "one message", TEAL)
            self.play(FadeIn(lab, shift=LEFT * 0.1), glow(ctx.readout, TEAL, 4), pulse(ctx.readout, 1.25), run_time=0.6)

        # ---- the share of each type
        shares = [("system", 6, MUTED), ("tools", 8, TEAL), ("user", 3, FG), ("assistant", 3, BLUE),
                  ("tool results", 40, TEAL)]
        total = sum(s for _, s, _ in shares)
        bw = 7.4
        bar = VGroup()
        for name, s, c in shares:
            seg = Rectangle(width=bw * s / total, height=0.42).set_stroke(BG, 2).set_fill(c, 0.85 if name == "tool results"
                                                                                              else 0.35)
            bar.add(seg)
        bar.arrange(RIGHT, buff=0).move_to([LX + bw / 2, -1.55, 0])
        legend = VGroup(*[VGroup(Square(0.16).set_stroke(width=0).set_fill(c, 0.85 if n == "tool results" else 0.4),
                                 en(n, 16, MUTED)).arrange(RIGHT, buff=0.08) for n, _, c in shares])
        legend.arrange(RIGHT, buff=0.3).next_to(bar, DOWN, buff=0.18, aligned_edge=LEFT)
        most = en("tool results: the largest part", 22, TEAL).next_to(bar[-1], UP, buff=0.18)
        with self.say("s02_08") as v:
            self.wait_until(v.cue("sort") - 0.3)
            self.play(labels.animate.fade(0.6), FadeOut(model), run_time=0.4)
            self.play(LaggedStart(*[GrowFromEdge(s, LEFT) for s in bar], lag_ratio=0.25), FadeIn(legend), run_time=1.2)
            self.wait_until(v.cue("most") - 0.3)
            self.play(FadeIn(most, shift=UP * 0.08), glow(bar[-1], TEAL, 6), run_time=0.6)

        # ---- sent again on every call
        model2 = ModelBox(2.3, 1.3).move_to([5.1, 1.85, 0])
        counter = CallCounter(12).next_to(model2, DOWN, buff=0.3)
        with self.say("s02_09") as v:
            self.wait_until(v.cue("remember") - 0.3)
            self.play(FadeOut(labels), FadeOut(most), bar.animate.fade(0.5), legend.animate.fade(0.5),
                      FadeIn(model2, scale=0.94), FadeIn(counter, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("sent") - 0.3)
            for n in (12, 13, 14):
                b = bundle_copy(ctx.cards, 0.3).move_to(ctx.group())
                anims = [] if n == 12 else counter.to(n)
                self.play(b.animate.move_to(model2.in_port + LEFT * 0.25).scale(0.5), glow(big.frame, TEAL, 6), *anims,
                          run_time=0.55)
                self.play(FadeOut(b, scale=0.4), model2.think(0.3), run_time=0.3)

        time_p = Pill(VGroup(clock_icon(0.3, FG), en("time", 22, FG)).arrange(RIGHT, buff=0.14), FG, pad_x=0.24)
        cost_p = Pill(VGroup(coins_icon(0.3, AMBER), en("cost", 22, FG)).arrange(RIGHT, buff=0.14), AMBER, pad_x=0.24)
        VGroup(time_p, cost_p).arrange(RIGHT, buff=0.35).move_to([5.1, -0.3, 0])
        again = VGroup(*[SizedCard("tool", content=code_block(0.5, 3, size=0.03, color=DIM, seed=k), height=0.55, width=1.6)
                         for k in range(3)]).arrange(RIGHT, buff=0.12).move_to([1.15, 0.25, 0])
        x3 = en("× every call", 20, TEAL).next_to(again, DOWN, buff=0.16)
        with self.say("s02_10") as v:
            self.wait_until(v.cue("paid") - 0.4)
            self.play(LaggedStart(*[TransformFromCopy(big, a) for a in again], lag_ratio=0.25), FadeIn(x3),
                      run_time=1.0)
            self.wait_until(v.cue("time") - 0.3)
            self.play(FadeIn(time_p, shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("cost") - 0.3)
            self.play(FadeIn(cost_p, shift=UP * 0.08), run_time=0.4)
        self.clear_all(0.6)
