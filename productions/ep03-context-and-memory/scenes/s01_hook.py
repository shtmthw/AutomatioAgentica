"""01 · The desk is full: recap of Episode 02 (model, harness, whole conversation on every call,
the limited context window), the hook (calls pile up until the window is full), the title card."""
from agentic_video.prelude import *
from memory_kit import *

CW_C = np.array([-4.15, -0.05, 0])


def thin(role, text=None, content=None, dashed=False, accent=None):
    return SizedCard(role, text, height=0.34, width=3.48, size=13, content=content, dashed=dashed, accent=accent)


class S01Hook(VoiceScene):
    SECTION = "s01"

    def construct(self):
        self.show_chapter()
        recap = Pill(en("last lesson · recap", 20, MUTED), DIM, pad_x=0.22).move_to([5.3, 3.0, 0])
        ctx = LiveContext(CW_C, 3.8, 5.3)
        hf = HarnessFrame(6.9, 4.7).move_to([2.95, -0.1, 0])
        model = ModelBox(2.5, 1.45).move_to([2.95, 0.55, 0])
        cards = [thin("system", "You are a coding agent."),
                 thin("user", "Why does total() crash?"),
                 ToolCallMsg("read_file", '"math_utils.py"', width=3.48, height=0.34)]
        for c, f in zip(cards, (0.06, 0.04, 0.04)):
            ctx.size(c, f)
            ctx.place(c)
        result = ctx.size(thin("tool", content=mono("def total(items): …", 12, FG)), 0.06)

        # ---- the Episode 02 picture
        with self.say("s01_01") as v:
            self.play(FadeIn(recap, shift=DOWN * 0.08), run_time=0.5)
            self.wait_until(v.cue("inside") - 0.6)
            self.play(FadeIn(hf), FadeIn(model, scale=0.94), LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in cards],
                                                                         lag_ratio=0.2), run_time=1.1)

        t_in = Pill(mono("text", 18, FG), FG, pad_x=0.16).move_to(model.in_port + LEFT * 0.95)
        t_out = Pill(mono("text", 18, BLUE), BLUE, pad_x=0.16).move_to(model.out_port + RIGHT * 0.95)
        a_in = arrow(t_in.get_right() + RIGHT * 0.05, model.in_port + LEFT * 0.05, color=MUTED, tip=0.1)
        a_out = arrow(model.out_port + RIGHT * 0.05, t_out.get_left() + LEFT * 0.05, color=MUTED, tip=0.1)
        cant = VGroup(I.file_icon(0.42, MUTED), I.terminal_icon(0.4, MUTED)).arrange(RIGHT, buff=0.3)
        cross = I.cross_icon(0.3).move_to(cant)
        cant_lab = caps("not on its own", 13, RED).next_to(cant, DOWN, buff=0.14)
        cant_g = VGroup(cant, cross, cant_lab).move_to([t_out.get_x() - 0.15, -0.5, 0])
        with self.say("s01_02") as v:
            self.wait_until(v.cue("only") - 0.3)
            self.play(FadeIn(t_in, shift=RIGHT * 0.2), GrowArrow(a_in), model.think(), run_time=0.6)
            self.wait_until(v.cue("writes") - 0.3)
            self.play(GrowArrow(a_out), FadeIn(t_out, shift=RIGHT * 0.2), run_time=0.5)
            self.wait_until(v.cue("open") - 0.3)
            self.play(FadeIn(cant, shift=UP * 0.08), run_time=0.4)
            self.play(FadeIn(cross, scale=1.3), FadeIn(cant_lab), run_time=0.4)

        jobs = VGroup(Pill(VGroup(I.loop_icon(0.26, AMBER), en("runs the loop", 19, FG)).arrange(RIGHT, buff=0.12), AMBER,
                           pad_x=0.18),
                      Pill(VGroup(I.wrench_icon(0.26, TEAL), en("executes the tools", 19, FG)).arrange(RIGHT, buff=0.12),
                           TEAL, pad_x=0.18)).arrange(RIGHT, buff=0.25)
        jobs.move_to([hf.frame.get_x(), -1.55, 0])
        with self.say("s01_03") as v:
            self.wait_until(v.cue("harness") - 0.3)
            self.play(glow(hf.frame, AMBER, 7), FadeIn(jobs[0], shift=UP * 0.08), FadeOut(cant_g), run_time=0.6)
            self.wait_until(v.cue("executes") - 0.3)
            self.play(FadeIn(jobs[1], shift=UP * 0.08), glow(cards[2].outline, BLUE, 4), run_time=0.5)
            self.wait_until(v.cue("adds") - 0.5)
            result.move_to(jobs[1].get_top() + UP * 0.45)
            self.play(FadeIn(result, shift=UP * 0.1), run_time=0.4)
            self.play(*ctx.add_quiet(result), run_time=0.7)

        list_lab = caps("message list", 15, MUTED).move_to(ctx.cw.label)
        badge = model.badge("call #3")
        with self.say("s01_04") as v:
            self.wait_until(v.cue("list") - 0.3)
            self.play(FadeIn(list_lab, shift=DOWN * 0.06), *[glow(c.frame if c.outline is None else c.outline, FG, 3)
                                                              for c in ctx.cards], run_time=0.6)
            self.wait_until(v.cue("every") - 0.3)
            self.play(FadeOut(t_in), FadeOut(a_in), FadeOut(t_out), FadeOut(a_out), FadeIn(badge, shift=DOWN * 0.06),
                      run_time=0.45)
            self.wait_until(v.cue("whole") - 0.35)
            b = bundle_copy(ctx.cards, 0.32).move_to(ctx.group())
            self.play(b.animate.move_to(model.in_port + LEFT * 0.3).scale(0.6), run_time=0.8)
            self.play(FadeOut(b, scale=0.4), model.think(0.5), run_time=0.5)

        with self.say("s01_05") as v:
            self.wait_until(v.cue("cw") - 0.35)
            self.play(FadeOut(list_lab), *ctx.appear(), run_time=0.6)
            self.wait_until(v.cue("limited") - 0.3)
            self.play(glow(ctx.cw.frame, FG, 6), run_time=0.6)

        # ---- the desk has a fixed size; the hook begins
        right = np.array([3.3, 0.0, 0])
        desk = VGroup(paper(0.7, 0.5, 3).rotate(0.06), en("the model's desk", 24, AMBER)).arrange(RIGHT, buff=0.22)
        desk.move_to(right + UP * 2.0)
        fixed = caps("fixed size", 15, MUTED).next_to(desk, DOWN, buff=0.14)
        with self.say("s01_06") as v:
            self.play(FadeOut(recap), FadeOut(jobs), FadeOut(badge), FadeOut(model), FadeOut(hf), run_time=0.6)
            self.wait_until(v.cue("desk") - 0.3)
            self.play(FadeIn(desk, shift=LEFT * 0.1), run_time=0.5)
            self.wait_until(v.cue("fixed") - 0.3)
            self.play(FadeIn(fixed), glow(ctx.cw.frame, AMBER, 6), run_time=0.6)

        steps = Pill(VGroup(I.loop_icon(0.28, FG), en("hundreds of steps", 22, FG)).arrange(RIGHT, buff=0.14), FG,
                     pad_x=0.24).move_to(right + UP * 0.9)
        counter = CallCounter(1).move_to(right + DOWN * 0.15)
        roles = ["assistant", "tool", "assistant", "tool", "user", "assistant", "tool", "assistant", "tool", "assistant",
                 "tool", "assistant", "tool", "assistant", "tool", "assistant", "tool", "assistant", "tool", "assistant"]
        texts = {"assistant": None, "tool": None, "user": "Also check the login."}

        def filler(role, h=0.23):
            if role == "assistant":
                return SizedCard("assistant", content=code_block(1.5, 1, size=0.035, color=BLUE, seed=len(ctx.cards)),
                                 height=h, width=3.48, dashed=True)
            if role == "tool":
                return SizedCard("tool", content=code_block(1.7, 1, size=0.035, color=TEAL, seed=len(ctx.cards) + 5),
                                 height=h, width=3.48)
            return SizedCard("user", texts["user"], height=h, width=3.48, size=12)

        stream = iter(roles)

        def drop(n, rt=0.2):
            """Eleven filler messages take the window from 20% to 91.5% (6.5% each): amber on
            "Amber", red on "Red"; the last tool result then fills what is left (100%)."""
            for _ in range(n):
                c = ctx.size(filler(next(stream)), 0.065)
                self.play(*ctx.add(c, shift=DOWN * 0.15), run_time=rt)

        with self.say("s01_07") as v:
            self.wait_until(v.cue("long") - 0.3)
            self.play(FadeIn(counter, shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("hundreds") - 0.3)
            self.play(FadeIn(steps, shift=LEFT * 0.1), run_time=0.5)
            drop(2, 0.3)

        with self.say("s01_08") as v:
            for name, n, k in (("c5", 5, 2), ("c20", 20, 2), ("c60", 60, 2)):
                self.wait_until(v.cue(name) - 0.2)
                self.play(*counter.to(n), run_time=0.3)
                drop(k, 0.16)
            self.wait_until(v.cue("adds") - 0.2)
            drop(1, 0.18)

        with self.say("s01_09") as v:
            self.wait_until(v.cue("climbs") - 0.2)
            drop(1, 0.25)
            self.wait_until(v.cue("red") - 0.3)
            drop(1, 0.25)
            self.wait_until(v.cue("full") - 0.4)
            last = SizedCard("tool", content=code_block(1.7, 1, size=0.035, color=TEAL, seed=11), height=ctx.free(),
                             width=3.48)
            ctx.size(last, 1.0 - ctx.level())            # the last result takes all the space that is left
            self.play(*ctx.add(last, shift=DOWN * 0.15), run_time=0.3)
            full = Pill(caps("context full", 16, RED), RED, pad_x=0.22).move_to(ctx.cw.label)
            self.play(ctx.cw.frame.animate.set_stroke(RED), FadeOut(ctx.cw.label), FadeIn(full, scale=0.9), run_time=0.4)
            # one more message tries to come in from the side and bounces off the full window
            extra = thin("assistant", content=code_block(1.5, 1, size=0.035, color=BLUE, seed=4), dashed=True).scale(0.8)
            extra.move_to([ctx.cw.meter_box.get_right()[0] + 0.12 + extra.width / 2, ctx.cards[-1].get_y(), 0])
            self.play(FadeIn(extra, shift=LEFT * 0.2), run_time=0.25)
            self.play(extra.animate.shift(LEFT * 0.35), rate_func=there_and_back, run_time=0.4)
            self.play(extra.animate.shift(RIGHT * 0.3).set_opacity(0), run_time=0.3)
            self.remove(extra)

        q1 = VGroup(caps("task: not finished", 16, MUTED), caps("desk: full", 16, RED)).arrange(DOWN, buff=0.16,
                                                                                               aligned_edge=LEFT)
        q1.move_to(right + DOWN * 1.25)
        now = en("Now what?", 46, FG).move_to(right + DOWN * 1.25)
        with self.say("s01_10") as v:
            self.wait_until(v.cue("finished") - 0.3)
            self.play(FadeOut(steps), counter.animate.move_to(right + UP * 0.9), FadeIn(q1[0], shift=UP * 0.06),
                      run_time=0.5)
            self.wait_until(v.cue("full") - 0.3)
            self.play(FadeIn(q1[1], shift=UP * 0.06), run_time=0.4)
            self.wait_until(v.cue("now") - 0.3)
            self.play(q1.animate.shift(UP * 0.85).fade(0.4), FadeIn(now, shift=UP * 0.1), run_time=0.6)

        keep = Pill(VGroup(I.loop_icon(0.28, TEAL), en("keep working?", 22, FG)).arrange(RIGHT, buff=0.14), TEAL, pad_x=0.24)
        rem = Pill(VGroup(Notebook(0.34, label=None, sub=None).icon, en("remember yesterday?", 22, FG)).arrange(RIGHT, buff=0.14),
                   MEMORY, pad_x=0.24)
        VGroup(keep, rem).arrange(DOWN, buff=0.3).move_to(right + DOWN * 1.35)
        with self.say("s01_11") as v:
            self.wait_until(v.cue("keep") - 0.3)
            self.play(FadeOut(q1), FadeOut(now), FadeOut(counter), FadeIn(keep, shift=LEFT * 0.1), run_time=0.55)
            self.wait_until(v.cue("remember") - 0.3)
            self.play(FadeIn(rem, shift=LEFT * 0.1), run_time=0.5)

        # ---- title card
        t1 = spaced("CONTEXT & MEMORY", 64, FG, tracking=0.32, weight=LIGHT)
        if t1.width > 12.0:
            t1.scale_to_fit_width(12.0)
        rule = Line(LEFT * 1.4, RIGHT * 1.4).set_stroke(FAINT, 1.6)
        sub = spaced("AGENTIC AI · EPISODE 03", 20, MUTED, tracking=0.6, weight=NORMAL)
        card = VGroup(t1, rule, sub).arrange(DOWN, buff=0.4).move_to(UP * 0.35)
        with self.say("s01_12") as v:
            self.wait_until(v.cue("title") - 0.7)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.6)
            self.play(FadeIn(t1, shift=UP * 0.12), run_time=0.9)
            self.play(Create(rule), FadeIn(sub, shift=UP * 0.06), run_time=0.7)
        self.wait(1.2)
        self.clear_all(0.6)
