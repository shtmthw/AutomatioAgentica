"""06 · Technique 3: summarize old messages (compaction), step by step: the harness notices the
threshold, makes a separate call, the model writes the summary, the harness swaps the messages,
the meter drops. What a good summary keeps, why a summary is lossy, and the comparison table."""
from agentic_video.prelude import *
from memory_kit import *

CW_C = np.array([-4.6, -0.05, 0])
W = 3.08
RX = 2.55
SUMMARY = ["Goal: fix the crash, keep public function names", "Done: found bug in total(), fixed it",
           "Still to do: fix failing login test", 'Key facts: tests run with "run tests"; server port is 8080']


def thin(role, text=None, content=None, h=0.28, size=12, label=None, accent=None):
    return SizedCard(role, text, height=h, width=W, size=size, content=content, label=label, accent=accent)


def call(tool, arg):
    return ToolCallMsg(tool, arg, width=W, size=12, height=0.28)


def result(head, n, h, seed):
    body = VGroup(mono(head, 11, MUTED), code_block(1.5, n, size=0.033, color=DIM, seed=seed, gap=0.13)).arrange(
        DOWN, buff=0.08, aligned_edge=LEFT) if n else mono(head, 11, FG)
    return SizedCard("tool", content=body, height=h, width=W)


class S06Compaction(VoiceScene):
    SECTION = "s06"

    def construct(self):
        self.show_chapter()
        tech = technique_tag(3)
        head = en("Summarize old messages", 34, FG).move_to([RX, 2.62, 0])
        steps = StepTracker(5, AMBER).move_to([RX, 1.95, 0])
        ctx = LiveContext(CW_C, 3.4, 5.3)
        sysc = ctx.size(thin("system", "You are a coding agent."), 0.05)
        older = [ctx.size(thin("user", "Fix the crash. Keep the public function names.", size=11), 0.04),
                 ctx.size(call("read_file", '"math_utils.py"'), 0.02),
                 ctx.size(result("math_utils.py · lines 1–200", 3, 0.55, 1), 0.17),
                 ctx.size(thin("assistant", "Found the bug in total()."), 0.03),
                 ctx.size(call("edit_file", '"math_utils.py"'), 0.02),
                 ctx.size(result("File updated successfully", 0, 0.28, 2), 0.03),
                 ctx.size(thin("user", "Use simple words in error messages."), 0.03),
                 ctx.size(call("run_command", '"run tests"'), 0.02),
                 ctx.size(result("test log · 700 lines", 3, 0.6, 3), 0.30)]
        lossy = older[6]
        newest = [ctx.size(call("run_command", '"run login tests"'), 0.04),
                  ctx.size(result("2 login tests failed", 1, 0.32, 4), 0.08)]
        for c in [sysc] + older:
            ctx.place(c)

        with self.say("s06_01") as v:
            self.wait_until(v.cue("tech") - 0.3)
            self.play(FadeIn(tech, shift=DOWN * 0.08), run_time=0.5)
            self.wait_until(v.cue("summarize") - 0.3)
            self.play(FadeIn(head, shift=UP * 0.08), *ctx.appear(),
                      LaggedStart(*[FadeIn(c) for c in ctx.cards], lag_ratio=0.06), run_time=1.0)

        trash = VGroup(I.trash_icon(0.34, RED), I.cross_icon(0.22)).arrange(RIGHT, buff=0.12)
        no_throw = VGroup(trash, en("throw away", 22, MUTED)).arrange(RIGHT, buff=0.16).move_to([RX - 1.6, 0.8, 0])
        summ_p = Pill(VGroup(caps("summary", 13, AMBER), en("replace them", 22, FG)).arrange(RIGHT, buff=0.14), AMBER,
                      pad_x=0.22).move_to([RX + 1.7, 0.8, 0])
        term = VGroup(spaced("COMPACTION", 40, FG, tracking=0.3, weight=LIGHT),
                      en("= replacing old messages with a summary", 20, MUTED)).arrange(DOWN, buff=0.2)
        term.move_to([RX, -0.6, 0])
        with self.say("s06_02") as v:
            self.wait_until(v.cue("throwing") - 0.3)
            self.play(FadeIn(no_throw, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("summary") - 0.3)
            self.play(FadeIn(summ_p, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("compaction") - 0.3)
            self.play(FadeIn(term, shift=UP * 0.1), run_time=0.6)

        # ---- step 1: the harness notices
        mb = ctx.cw.meter_box
        y80 = mb.get_bottom()[1] + 0.04 + 0.8 * (ctx.cw.H - 0.08)
        thr = DashedLine([ctx.cw.frame.get_left()[0], y80, 0], [mb.get_right()[0] + 0.12, y80, 0],
                         dash_length=0.08).set_stroke(AMBER, 2)
        thr_lab = VGroup(caps("80%", 14, AMBER), caps("example", 11, MUTED)).arrange(DOWN, buff=0.04,
                                                                                    aligned_edge=LEFT)
        thr_lab.next_to(thr, RIGHT, buff=0.1)
        harness = Pill(VGroup(I.gear(0.26, AMBER), caps("harness", 14, AMBER)).arrange(RIGHT, buff=0.1), AMBER,
                       pad_x=0.18).move_to([-0.75, -0.2, 0])
        with self.say("s06_03") as v:
            self.wait_until(v.cue("step") - 0.4)
            self.play(FadeOut(no_throw), FadeOut(summ_p), FadeOut(term), FadeIn(steps), run_time=0.4)
            self.play(*steps.go(1), run_time=0.4)
            self.wait_until(v.cue("notices") - 0.3)
            self.play(FadeIn(harness, scale=0.9), run_time=0.4)
            self.wait_until(v.cue("threshold") - 0.4)
            self.play(Create(thr), FadeIn(thr_lab), run_time=0.6)
            self.wait_until(v.cue("pct") - 0.9)
            for c in newest:
                self.play(*ctx.add(c, shift=DOWN * 0.15), run_time=0.35)
            self.play(glow(harness.frame, AMBER, 6), glow(thr, AMBER, 5), run_time=0.6)

        # ---- step 2: a separate call with the older messages + one instruction
        model = ModelBox(2.3, 1.3).move_to([RX + 0.4, 0.55, 0])
        sep = model.badge("separate call", AMBER)
        instr = SizedCard("user", "Summarize the important points of this conversation so far.", height=0.5, width=4.4,
                          size=14, wrap=34, label="instruction", accent=AMBER)
        instr.move_to([RX + 0.4, -1.0, 0])
        olds = VGroup(*older)
        brace = Brace(olds, LEFT, buff=0.06).set_color(MUTED)
        with self.say("s06_04") as v:
            self.wait_until(v.cue("step") - 0.3)
            self.play(*steps.go(2), run_time=0.5)
            self.wait_until(v.cue("separate") - 0.4)
            self.play(FadeIn(model, scale=0.94), FadeIn(sep, shift=DOWN * 0.06), run_time=0.6)
            self.wait_until(v.cue("older") - 0.3)
            self.play(GrowFromCenter(brace), *[glow(c.frame, FG, 3) for c in older], run_time=0.6)
            b = bundle_copy(older, 0.35).move_to(olds)
            self.play(b.animate.move_to(model.in_port + LEFT * 0.35).scale(0.6), run_time=0.9)
            self.play(FadeOut(b, scale=0.4), run_time=0.3)
            self.wait_until(v.cue("instruction") - 0.3)
            self.play(FadeIn(instr, shift=UP * 0.1), run_time=0.5)

        # ---- step 3: the model writes the summary
        summ = SummaryCard(SUMMARY, width=W, size=11).set_z_index(1)
        ctx.size(summ, 0.08)
        draft = SummaryCard(SUMMARY, width=4.4, size=14).move_to([RX + 0.4, -1.15, 0])
        writes = caps("writes it", 13, BLUE).next_to(model, DOWN, buff=0.12)
        decides = VGroup(caps("decides when", 12, AMBER), caps("and what to replace", 12, AMBER)).arrange(
            DOWN, buff=0.04).next_to(harness, DOWN, buff=0.12)
        with self.say("s06_05") as v:
            self.wait_until(v.cue("step") - 0.3)
            self.play(*steps.go(3), instr.animate.move_to(model.in_port + LEFT * 0.4).scale(0.15).set_opacity(0),
                      run_time=0.6)
            self.remove(instr)
            self.wait_until(v.cue("writes") - 0.4)
            self.play(model.think(0.6), FadeIn(writes), run_time=0.6)
            self.play(FadeIn(draft, shift=DOWN * 0.15), run_time=0.6)
            self.wait_until(v.cue("when") - 0.3)
            self.play(FadeIn(decides[0], shift=UP * 0.05), glow(harness.frame, AMBER, 5), run_time=0.45)
            self.wait_until(v.cue("what") - 0.3)
            self.play(FadeIn(decides[1], shift=UP * 0.05), run_time=0.4)

        # ---- step 4: the harness swaps them (the older messages are now replaced by the summary)
        with self.say("s06_06") as v:
            self.wait_until(v.cue("step") - 0.3)
            self.play(*steps.go(4), FadeOut(sep), FadeOut(writes), run_time=0.5)
            self.wait_until(v.cue("swaps") - 0.3)
            self.play(draft.animate.scale(W / draft.width).move_to(
                [ctx.cw.frame.get_right()[0] + 1.05 + W / 2, 0.72, 0]), run_time=0.8)
            self.wait_until(v.cue("become") - 0.4)
            self.play(*[c.animate.fade(0.6) for c in older], glow(draft.frame, AMBER, 5), run_time=0.6)
            keep_sys = Pill(caps("stays on top", 12, MUTED), MUTED, pad_x=0.14, pad_y=0.05)
            keep_new = Pill(caps("newest: unchanged", 12, TEAL), TEAL, pad_x=0.14, pad_y=0.05)
            self.wait_until(v.cue("system") - 0.3)
            keep_sys.next_to(sysc, RIGHT, buff=0.75)
            self.play(glow(sysc.frame, FG, 5), FadeIn(keep_sys, shift=LEFT * 0.08), run_time=0.5)
            self.wait_until(v.cue("newest") - 0.3)
            keep_new.next_to(VGroup(*newest), RIGHT, buff=0.75)
            self.play(*[glow(c.frame, TEAL, 4) for c in newest], FadeIn(keep_new, shift=LEFT * 0.08), run_time=0.5)

        # ---- step 5: the meter drops, the loop continues
        loop_p = Pill(VGroup(I.loop_icon(0.26, TEAL), en("the loop continues", 20, FG)).arrange(RIGHT, buff=0.12), TEAL,
                      pad_x=0.2)
        with self.say("s06_07") as v:
            self.wait_until(v.cue("step") - 0.3)
            self.play(*steps.go(5), FadeOut(keep_sys), FadeOut(keep_new), FadeOut(brace), run_time=0.45)
            self.wait_until(v.cue("drops") - 0.8)
            i = ctx.cards.index(older[0])
            for c in older:
                ctx.cards.remove(c)
            ctx.cards.insert(i, summ)
            summ.move_to(ctx.slots()[i])
            self.play(*[c.animate.move_to(draft).scale(0.4).set_opacity(0) for c in older],
                      ReplacementTransform(draft, summ), run_time=0.8)
            self.remove(*older)
            self.play(*ctx.relayout(), run_time=0.6)
            self.play(glow(ctx.readout, TEAL, 4), pulse(ctx.readout, 1.25), run_time=0.5)
            self.wait_until(v.cue("continues") - 0.3)
            loop_p.move_to([RX + 0.4, -1.3, 0])
            self.play(FadeIn(loop_p, shift=UP * 0.08), model.think(0.5), run_time=0.5)

        # ---- what a good summary keeps
        big = SummaryCard(SUMMARY, width=6.4, size=19).move_to([RX + 0.2, -0.45, 0])
        keeps = caps("a good summary keeps", 14, MUTED).next_to(big, UP, buff=0.16, aligned_edge=LEFT)
        with self.say("s06_08") as v:
            self.play(FadeOut(model), FadeOut(loop_p), FadeOut(harness), FadeOut(decides), FadeOut(thr), FadeOut(thr_lab),
                      run_time=0.4)
            self.play(TransformFromCopy(summ, big), FadeIn(keeps), run_time=0.7)
            self.play(big.rows.animate.set_opacity(0.28), run_time=0.3)
            for name, k in (("goal", 0), ("done", 1), ("left", 2), ("facts", 3)):
                self.wait_until(v.cue(name) - 0.3)
                self.play(big.rows[k].animate.set_opacity(1.0), run_time=0.35)
                if name == "goal":
                    self.wait_until(v.cue("rules") - 0.2)
                    self.play(pulse(big.rows[0], 1.05), run_time=0.4)

        # ---- a summary is lossy
        ghost = SizedCard("user", "Use simple words in error messages.", height=0.32, width=4.4, size=15)
        ghost.move_to([RX + 0.2, 1.25, 0])
        g_lab = caps("an old message", 13, MUTED).next_to(ghost, UP, buff=0.1, aligned_edge=LEFT)
        lossy_p = Pill(caps("lossy", 15, RED), RED, pad_x=0.18).next_to(big, RIGHT, buff=0.2).shift(UP * 0.6)
        if lossy_p.get_right()[0] > 6.8:
            lossy_p.next_to(keeps, RIGHT, buff=2.3)
        with self.say("s06_09") as v:
            self.wait_until(v.cue("lossy") - 0.3)
            self.play(FadeIn(lossy_p, scale=0.9), run_time=0.4)
            self.wait_until(v.cue("simple") - 0.8)
            self.play(FadeIn(ghost, shift=DOWN * 0.1), FadeIn(g_lab), run_time=0.5)

        miss = VGroup(I.cross_icon(0.22), caps("not in the summary", 13, RED)).arrange(RIGHT, buff=0.1)
        miss.next_to(ghost, RIGHT, buff=0.2)
        if miss.get_right()[0] > 6.8:
            miss.next_to(g_lab, RIGHT, buff=0.4)
        answer = SizedCard("assistant", "TypeError: unsupported operand type(s) in total()", height=0.34, width=5.2,
                           size=13).move_to([RX + 0.2, -2.25, 0])
        no_simple = I.warn_icon(0.3, RED).next_to(answer, RIGHT, buff=0.15)
        with self.say("s06_10") as v:
            self.wait_until(v.cue("left") - 0.3)
            self.play(FadeIn(miss, shift=LEFT * 0.08), run_time=0.4)
            self.play(ghost.animate.fade(0.8), g_lab.animate.fade(0.8), run_time=0.8)
            self.wait_until(v.cue("sees") - 0.3)
            self.play(FadeOut(ghost), FadeOut(g_lab), FadeOut(miss), run_time=0.4)
            self.wait_until(v.cue("following") - 0.4)
            self.play(FadeIn(answer, shift=DOWN * 0.1), run_time=0.45)
            self.play(FadeIn(no_simple, scale=1.3), run_time=0.35)

        # ---- the comparison table
        cols = [0.0, 3.6, 6.2]
        hdr = VGroup(caps("technique", 15, MUTED), caps("saves space", 15, MUTED), caps("what you risk", 15, MUTED))
        rows_data = [("Small tool results", "Yes, early", "Missing a part you needed", TEAL),
                     ("Trimming", "Yes, a lot", "Losing old instructions completely", AMBER),
                     ("Summarizing", "Yes, a lot", "Losing small details", VIOLET)]
        x0, y0 = -5.6, 1.35
        for t, x in zip(hdr, cols):
            t.move_to([x0 + x, y0, 0], aligned_edge=LEFT)
        rule = Line([x0, y0 - 0.32, 0], [x0 + 11.8, y0 - 0.32, 0]).set_stroke(FAINT, 1.6)
        rows = []
        for i, (a, s, r, c) in enumerate(rows_data):
            y = y0 - 0.95 - i * 0.95
            num = en(str(i + 1), 24, c, italic=False, weight=NORMAL).move_to([x0 - 0.45, y, 0])
            ta = en(a, 26, FG).move_to([x0 + cols[0], y, 0], aligned_edge=LEFT)
            ts = VGroup(I.check_icon(0.22, TEAL), en(s, 24, FG)).arrange(RIGHT, buff=0.12).move_to(
                [x0 + cols[1], y, 0], aligned_edge=LEFT)
            tr = en(r, 24, RED if i == 1 else FG).move_to([x0 + cols[2], y, 0], aligned_edge=LEFT)
            sep_l = Line([x0, y - 0.47, 0], [x0 + 11.8, y - 0.47, 0]).set_stroke(FAINT, 1.0)
            rows.append(VGroup(num, ta, ts, tr, sep_l))
        table = VGroup(hdr, rule, *rows)
        with self.say("s06_11") as v:
            self.wait_until(v.cue("comparing") - 0.5)
            self.play(*[FadeOut(m) for m in self.mobjects if m not in (self.chapter, tech)], run_time=0.6)
            self.play(FadeIn(hdr, shift=DOWN * 0.06), Create(rule), run_time=0.5)
            self.wait_until(v.cue("small") - 0.3)
            self.play(FadeIn(rows[0][:3], shift=RIGHT * 0.1), FadeIn(rows[0][4]), run_time=0.5)
            self.wait_until(v.cue("miss") - 0.3)
            self.play(FadeIn(rows[0][3], shift=RIGHT * 0.1), run_time=0.4)

        with self.say("s06_12") as v:
            self.wait_until(v.cue("trimming") - 0.3)
            self.play(FadeIn(rows[1][:3], shift=RIGHT * 0.1), FadeIn(rows[1][4]), run_time=0.5)
            self.wait_until(v.cue("instructions") - 0.4)
            self.play(FadeIn(rows[1][3], shift=RIGHT * 0.1), run_time=0.4)

        with self.say("s06_13") as v:
            self.wait_until(v.cue("summarizing") - 0.3)
            self.play(FadeIn(rows[2][:3], shift=RIGHT * 0.1), FadeIn(rows[2][4]), run_time=0.5)
            self.wait_until(v.cue("details") - 0.4)
            self.play(FadeIn(rows[2][3], shift=RIGHT * 0.1), run_time=0.4)

        risk_box = SurroundingRectangle(VGroup(hdr[2], *[r[3] for r in rows]), color=RED, buff=0.16,
                                        corner_radius=0.1).set_stroke(width=1.8)
        loses = Pill(en("every technique loses something", 24, FG), RED, pad_x=0.28, pad_y=0.12).move_to([0, -2.38, 0])
        with self.say("s06_14") as v:
            self.wait_until(v.cue("loses") - 0.3)
            self.play(Create(risk_box), FadeIn(loses, shift=UP * 0.08), run_time=0.7)
            self.wait_until(v.cue("choosing") - 0.3)
            self.play(glow(risk_box, RED, 6), run_time=0.7)
        self.clear_all(0.6)
