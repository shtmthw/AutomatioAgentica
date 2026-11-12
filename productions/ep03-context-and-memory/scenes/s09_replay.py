"""09 · Full replay: one long task across two sessions. Context window on the left, the model and a
call counter in the middle, the notebook on the right; a label shows the active technique."""
from agentic_video.prelude import *
from memory_kit import *

CW_C = np.array([-3.95, -0.03, 0])
W = 3.88
MX = 1.05
MODEL_C = np.array([MX, 1.55, 0])
NB_C = np.array([4.9, 1.75, 0])
NOTE_X = 4.9


def thin(role, text=None, content=None, h=0.28, size=12, wrap=None):
    return SizedCard(role, text, height=h, width=W, size=size, content=content, wrap=wrap)


def call(tool, arg):
    return ToolCallMsg(tool, arg, width=W, size=12, height=0.28)


def note_slot(i):
    return np.array([NOTE_X, 0.6 - i * 0.72, 0])


class S09Replay(VoiceScene):
    SECTION = "s09"

    def construct(self):
        self.show_chapter()
        ctx = LiveContext(CW_C, 4.2, 5.3)
        model = ModelBox(2.1, 1.15, label_size=19).move_to(MODEL_C)
        counter = CallCounter(1).move_to([MX, 0.55, 0])
        nb = Notebook(0.8).move_to(NB_C)
        state = {"tech": None, "session": None}

        def set_tech(n, text):
            p = Pill(VGroup(caps(f"technique {n}", 13, AMBER), en(text, 19, FG)).arrange(RIGHT, buff=0.12), AMBER,
                     pad_x=0.2).move_to([MX, -0.3, 0])
            old = state["tech"]
            state["tech"] = p
            return [FadeIn(p, shift=UP * 0.08)] + ([FadeOut(old)] if old is not None else [])

        def set_session(n):
            p = session_pill(n).move_to([MX, 2.75, 0])
            old = state["session"]
            state["session"] = p
            return [FadeIn(p, shift=DOWN * 0.08)] + ([FadeOut(old)] if old is not None else [])

        def step(n=None):
            anims = [model.think(0.4)]
            if n is not None:
                anims += counter.to(n)
            return anims

        def add(card, frac, rt=0.4, n=None):
            ctx.size(card, frac)
            self.play(*ctx.add(card, shift=DOWN * 0.15), *step(n), run_time=rt)
            return card

        # ---- set up
        with self.say("s09_01") as v:
            self.wait_until(v.cue("together") - 0.4)
            self.play(*ctx.appear(), FadeIn(model, scale=0.95), FadeIn(counter), FadeIn(nb), run_time=0.8)
            self.wait_until(v.cue("two") - 0.3)
            self.play(glow(nb.cover, MEMORY, 4), run_time=0.5)

        # ---- session 1
        with self.say("s09_02") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(*set_session(1), run_time=0.4)
            add(thin("system", "You are a coding agent."), 0.03, 0.35)
            self.wait_until(v.cue("fix") - 0.3)
            add(thin("user", "Fix all failing tests in this project. Don't rename public functions.", h=0.3, wrap=48),
                0.03, 0.5)

        long_out = SizedCard("tool", content=VGroup(mono("running tests…", 11, FG), code_block(2.4, 13, size=0.033, color=DIM,
                                                                                             seed=5, gap=0.13),
                                                     mono("6 failed, 2 passed", 11, RED)).arrange(DOWN, buff=0.1,
                                                                                                  aligned_edge=LEFT),
                             height=2.3, width=3.6).move_to([MX, -1.3, 0])
        short = SizedCard("tool", content=VGroup(mono("running tests…", 11, FG),
                                                 PlaceholderCard("[output shortened: 2,300 more lines]", width=2.4, size=10,
                                                                 height=0.26),
                                                 mono("6 failed, 2 passed", 11, RED)).arrange(DOWN, buff=0.06,
                                                                                              aligned_edge=LEFT),
                          height=0.7, width=W)
        ctx.size(short, 0.08)
        with self.say("s09_03") as v:
            self.wait_until(v.cue("run") - 0.3)
            add(call("run_command", '"run tests"'), 0.01, 0.4, n=2)
            self.wait_until(v.cue("long") - 0.3)
            self.play(FadeIn(long_out, shift=UP * 0.1), run_time=0.5)
            self.wait_until(v.cue("shortens") - 0.3)
            short.move_to(long_out)
            self.play(FadeTransform(long_out, short), run_time=0.6)
            self.play(*ctx.add_from(short), run_time=0.6)
            self.wait_until(v.cue("one") - 0.3)
            self.play(*set_tech(1, "keep results small"), run_time=0.4)

        with self.say("s09_04") as v:
            self.wait_until(v.cue("read") - 0.3)
            add(call("read_file", '"math_utils.py", lines 40–80'), 0.01, 0.4, n=3)
            add(thin("tool", content=VGroup(mono("lines 40–80", 11, MUTED), code_block(1.5, 1, size=0.033, color=DIM)).arrange(
                RIGHT, buff=0.2)), 0.03, 0.35)
            self.wait_until(v.cue("again") - 0.3)
            self.play(pulse(state["tech"], 1.1), run_time=0.4)

        with self.say("s09_05") as v:
            self.wait_until(v.cue("edit") - 0.3)
            add(call("edit_file", '"math_utils.py"'), 0.01, 0.4, n=4)
            self.wait_until(v.cue("updated") - 0.3)
            add(thin("tool", "File updated successfully"), 0.01, 0.35)

        # ---- many more calls
        with self.say("s09_06") as v:
            self.wait_until(v.cue("on") - 0.3)
            self.play(FadeOut(state["tech"]), run_time=0.3)
            state["tech"] = None
            n_bars = 12
            free = ctx.free()
            h = min(0.09, (free - (n_bars - 1) * ctx.gap - 0.02) / n_bars)
            per = (0.80 - ctx.level()) / n_bars
            nums = np.linspace(6, 40, n_bars).astype(int)
            for j in range(n_bars):
                col = (BLUE, TEAL)[j % 2]
                bar = RoundedRectangle(width=W * (0.75 + 0.25 * ((j * 7) % 5) / 5), height=h, corner_radius=min(0.03, h / 2))
                bar.set_stroke(col, 1, opacity=0.8).set_fill(col, 0.25)
                ctx.size(bar, per)
                ctx.place(bar)
                bar.move_to([ctx.x0 + bar.width / 2, bar.get_y(), 0])
                self.play(FadeIn(bar, shift=DOWN * 0.08), *ctx.meter(), *counter.to(int(nums[j])), run_time=0.2)
            self.wait_until(v.cue("pct") - 0.3)
            self.play(glow(ctx.readout, AMBER, 4), pulse(ctx.readout, 1.25), run_time=0.5)

        with self.say("s09_07") as v:
            self.wait_until(v.cue("compaction") - 0.3)
            self.play(glow(ctx.cw.frame, AMBER, 6), run_time=0.5)
            self.wait_until(v.cue("three") - 0.3)
            self.play(*set_tech(3, "compaction"), run_time=0.4)
            summ = SummaryCard(["Goal: fix all failing tests,\ndon't rename public functions",
                                "Done: total() fixed, 6 of 8 tests pass", "Still to do: 2 login tests"], width=W, size=13)
            kept = ctx.units(ctx.cards[0]) + ctx.units(ctx.cards[-1]) + ctx.units(ctx.cards[-2])
            ctx.size(summ, 0.25 - kept / ctx.capacity)          # system + summary + 2 newest = 25 %
            self.wait_until(v.cue("summary") - 0.5)
            olds = ctx.cards[1:-2]
            self.play(*ctx.replace(olds, summ), run_time=0.8)
            self.remove(*olds)
            self.wait_until(v.cue("drops") - 0.5)
            self.play(*ctx.relayout(), run_time=0.6)
            self.play(glow(ctx.readout, TEAL, 4), pulse(ctx.readout, 1.25), run_time=0.5)

        note1 = NoteCard("Login tests fail: wrong port in config.txt.\nNot fixed yet.", width=3.2, size=12)
        note2 = NoteCard("Progress: 6 of 8 tests pass. Next: fix port\nin config.txt, then run tests.", width=3.2, size=12)
        with self.say("s09_08") as v:
            self.wait_until(v.cue("fail") - 0.3)
            self.play(FadeOut(state["tech"]), run_time=0.3)
            state["tech"] = None
            self.wait_until(v.cue("save") - 0.4)
            c = add(call("save_note", '"Login tests fail: wrong port…"'), 0.01, 0.4, n=41)
            note1.move_to([MX, -1.35, 0])
            self.play(FadeIn(note1, scale=0.9), run_time=0.3)
            self.play(note1.animate.move_to(note_slot(0)), run_time=0.8)
            add(thin("tool", "Note saved."), 0.01, 0.3)

        with self.say("s09_09") as v:
            self.wait_until(v.cue("stop") - 0.5)
            add(thin("user", "Let's stop for today."), 0.01, 0.4)
            self.wait_until(v.cue("save") - 0.3)
            c = add(call("save_note", '"Progress: 6 of 8 tests pass…"'), 0.01, 0.4, n=42)
            self.wait_until(v.cue("progress") - 0.3)
            note2.move_to([MX, -1.35, 0])
            self.play(FadeIn(note2, scale=0.9), run_time=0.3)
            self.play(note2.animate.move_to(note_slot(1)), run_time=0.8)
            self.wait_until(v.cue("next") - 0.3)
            self.play(glow(note2.frame, MEMORY, 6), pulse(note2, 1.05), run_time=0.6)
            add(thin("tool", "Note saved."), 0.01, 0.3)

        with self.say("s09_10") as v:
            self.wait_until(v.cue("ends") - 0.4)
            cards = ctx.clear()
            extra = [state["session"]]
            state["session"] = None
            session_wipe(self, cards + extra, text="SESSION 1 ENDS")
            self.play(*ctx.meter(), *counter.to(1), run_time=0.4)
            self.wait_until(v.cue("keeps") - 0.3)
            self.play(glow(note1.frame, MEMORY, 5), glow(note2.frame, MEMORY, 5), run_time=0.6)

        # ---- session 2
        block = NotesBlock(["Login tests fail: wrong port in config.txt. Not fixed yet.",
                            "Progress: 6 of 8 pass. Next: fix port in config.txt, then run tests."], width=W, size=11)
        with self.say("s09_11") as v:
            self.wait_until(v.cue("two") - 0.3)
            self.play(*set_session(2), run_time=0.4)
            add(thin("system", "You are a coding agent."), 0.02, 0.35)
            self.wait_until(v.cue("loads") - 0.4)
            tmp = VGroup(note1.copy(), note2.copy())
            self.play(tmp.animate.move_to(ctx.next_point(block)).scale(0.8), run_time=0.8)
            ctx.size(block, 0.03)
            ctx.place(block)
            self.play(FadeTransform(tmp, block), *ctx.meter(), run_time=0.5)
            self.wait_until(v.cue("pct") - 0.3)
            self.play(glow(ctx.readout, TEAL, 4), pulse(ctx.readout, 1.25), run_time=0.5)

        with self.say("s09_12") as v:
            self.wait_until(v.cue("continue") - 0.3)
            add(thin("user", "Continue from yesterday."), 0.01, 0.4)

        port = SizedCard("tool", content=VGroup(mono("port = ", 12, FG), mono("8800", 12, RED), mono(", host = localhost", 12, FG)
                                                ).arrange(RIGHT, buff=0.04), height=0.28, width=W)
        with self.say("s09_13") as v:
            self.wait_until(v.cue("read") - 0.3)
            add(call("read_file", '"config.txt"'), 0.01, 0.4, n=2)
            self.wait_until(v.cue("port") - 0.3)
            add(port, 0.01, 0.4)
            self.wait_until(v.cue("wrong") - 0.3)
            link = CurvedArrow(block.frame.get_right() + RIGHT * 0.04, port.frame.get_right() + RIGHT * 0.04, angle=-1.4,
                               color=MEMORY, stroke_width=2.2, tip_length=0.12)
            self.play(Create(link), glow(port.frame, RED, 5), run_time=0.6)

        with self.say("s09_14") as v:
            self.wait_until(v.cue("edit") - 0.3)
            add(call("edit_file", '"config.txt"'), 0.01, 0.35, n=3)
            add(thin("tool", "File updated successfully"), 0.01, 0.3)
            self.wait_until(v.cue("run") - 0.3)
            add(call("run_command", '"run tests"'), 0.01, 0.35, n=4)
            self.wait_until(v.cue("passed") - 0.4)
            ok = thin("tool", content=VGroup(mono("All 8 tests passed", 12, TEAL), I.check_icon(0.18, TEAL)).arrange(
                RIGHT, buff=0.1))
            add(ok, 0.01, 0.4)

        final = SizedCard("assistant", "All tests pass now. The last two failed because config.txt had the\n"
                                       "wrong port. No public functions were renamed.", height=0.46, width=W, size=11)
        fa = Pill(caps("final answer · no tool call", 12, BLUE), BLUE, pad_x=0.16, pad_y=0.06).move_to([MX + 0.6, -0.3, 0])
        big_final = SizedCard("assistant", "All tests pass now. The last two failed\nbecause config.txt had the wrong port.\n"
                                           "No public functions were renamed.", height=0.9, width=4.9, size=15)
        big_final.move_to([MX + 0.6, -1.15, 0])
        with self.say("s09_15") as v:
            self.wait_until(v.cue("answer") - 0.4)
            add(final, 0.02, 0.5, n=5)
            self.play(FadeIn(fa, shift=UP * 0.06), TransformFromCopy(final, big_final), run_time=0.6)
            self.wait_until(v.cue("functions") - 0.3)
            chk = I.check_icon(0.26, TEAL).next_to(final, RIGHT, buff=0.75)
            self.play(glow(final.frame, TEAL, 5), glow(big_final.frame, TEAL, 5), FadeIn(chk, scale=1.3), run_time=0.6)

        p1 = Pill(VGroup(caps("rule", 13, AMBER), en("survived compaction: kept in the summary", 18, FG)).arrange(RIGHT, buff=0.12),
                  AMBER, pad_x=0.2)
        p2 = Pill(VGroup(caps("progress", 13, MEMORY), en("survived the session: saved to memory", 18, FG)).arrange(
            RIGHT, buff=0.12), MEMORY, pad_x=0.2)
        surv = VGroup(p1, p2).arrange(DOWN, buff=0.2, aligned_edge=LEFT).move_to([MX + 1.3, -1.55, 0])
        head = caps("what survived", 14, MUTED).next_to(surv, UP, buff=0.16, aligned_edge=LEFT)
        with self.say("s09_16") as v:
            self.wait_until(v.cue("survived") - 0.3)
            self.play(FadeOut(fa), FadeOut(big_final), FadeIn(head), run_time=0.4)
            self.wait_until(v.cue("rule") - 0.3)
            self.play(FadeIn(p1, shift=UP * 0.08), run_time=0.45)

        same = unchanged_badge(model)
        with self.say("s09_17") as v:
            self.wait_until(v.cue("progress") - 0.3)
            self.play(FadeIn(p2, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("memory") - 0.3)
            self.play(glow(nb.cover, MEMORY, 5), FadeOut(counter), FadeIn(same, shift=UP * 0.06), run_time=0.6)
        self.wait(0.3)
        self.clear_all(0.6)
