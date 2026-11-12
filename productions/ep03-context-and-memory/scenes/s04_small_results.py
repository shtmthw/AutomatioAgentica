"""04 · Technique 1: keep tool results small. Read only the needed part, search instead of reading
everything, and the harness shortens very long output (and says so with a placeholder line)."""
from agentic_video.prelude import *
from memory_kit import *

CW_C = np.array([-4.55, -0.05, 0])
W = 3.08
RX = 2.35


def sub(i, text):
    return VGroup(en(str(i), 26, AMBER, italic=False, weight=NORMAL), en(text, 26, FG)).arrange(RIGHT, buff=0.18)


def phase(word, color):
    return caps(word, 16, color)


def bars(n, seed, w=1.6, color=DIM):
    return code_block(w, n, size=0.033, color=color, seed=seed, gap=0.13)


class S04SmallResults(VoiceScene):
    SECTION = "s04"

    def construct(self):
        self.show_chapter()
        tech = technique_tag(1)
        head = en("Keep tool results small", 34, FG).move_to([RX, 2.6, 0])
        ctx = LiveContext(CW_C, 3.4, 5.3)
        base = [SizedCard("system", "You are a coding agent.", height=0.28, width=W, size=12),
                SizedCard("user", "Why does total() crash?", height=0.28, width=W, size=12)]
        ctx.size(base[0], 0.06)
        ctx.size(base[1], 0.04)
        for c in base:
            ctx.place(c)

        with self.say("s04_01") as v:
            self.wait_until(v.cue("tech") - 0.3)
            self.play(FadeIn(tech, shift=DOWN * 0.08), run_time=0.5)
            self.play(FadeIn(head, shift=UP * 0.08), *ctx.appear(), *[FadeIn(c) for c in base], run_time=0.7)

        gate = Pill(VGroup(I.gear(0.26, AMBER), en("don't add it in the first place", 22, FG)).arrange(RIGHT, buff=0.14),
                    AMBER, pad_x=0.24).move_to([RX, 1.0, 0])
        with self.say("s04_02") as v:
            self.wait_until(v.cue("cheapest") - 0.3)
            self.play(glow(ctx.cw.frame, TEAL, 5), run_time=0.6)
            self.wait_until(v.cue("not") - 0.3)
            self.play(FadeIn(gate, shift=UP * 0.08), run_time=0.5)

        # ---- 1. read only the part you need
        s1 = sub(1, "read only the needed part").move_to([RX, 1.85, 0])
        with self.say("s04_03") as v:
            self.wait_until(v.cue("first") - 0.3)
            self.play(FadeOut(gate), FadeIn(s1, shift=UP * 0.08), run_time=0.5)

        before = phase("before", RED).move_to([RX, 1.2, 0])
        req = ToolCallCard("read_file", 'path = "math_utils.py"', width=3.7, size=17).move_to([RX, 0.35, 0])
        call = ctx.size(ToolCallMsg("read_file", '"math_utils.py"', width=W, size=12, height=0.28), 0.01)
        huge = SizedCard("tool", content=VGroup(mono("math_utils.py · 5,000 lines", 11, MUTED), bars(18, 4)).arrange(
            DOWN, buff=0.1, aligned_edge=LEFT), height=3.55, width=W)
        ctx.size(huge, 0.74)
        with self.say("s04_04") as v:
            self.wait_until(v.cue("before") - 0.3)
            self.play(FadeIn(before), FadeIn(req, shift=DOWN * 0.1), run_time=0.5)
            self.play(*ctx.add(call, shift=LEFT * 0.3), run_time=0.45)
            self.wait_until(v.cue("whole") - 0.3)
            self.play(*ctx.add(huge, shift=DOWN * 0.3), run_time=0.8)
            self.play(glow(ctx.readout, AMBER, 4), pulse(ctx.readout, 1.25), run_time=0.5)

        after = phase("after", TEAL).move_to(before)
        inp = VGroup(mono('path = "math_utils.py"', 15, FG), mono("lines = 40–80", 15, TEAL)).arrange(DOWN, buff=0.08,
                                                                                                    aligned_edge=LEFT)
        req2 = ToolCallCard("read_file", inp, width=3.7, size=17).move_to([RX, 0.25, 0])
        call2 = ctx.size(ToolCallMsg("read_file", '"math_utils.py", 40–80', width=W, size=12, height=0.28), 0.01)
        small = SizedCard("tool", content=VGroup(mono("lines 40–80", 11, MUTED), bars(2, 6)).arrange(DOWN, buff=0.08,
                                                                                                    aligned_edge=LEFT),
                          height=0.55, width=W)
        ctx.size(small, 0.05)
        with self.say("s04_05") as v:
            self.wait_until(v.cue("after") - 0.4)
            self.play(*ctx.remove([huge, call], shift=RIGHT * 0.3), FadeOut(before), FadeIn(after), FadeOut(req),
                      run_time=0.5)
            self.play(*ctx.relayout(), run_time=0.4)
            self.wait_until(v.cue("lines") - 0.4)
            self.play(FadeIn(req2, shift=DOWN * 0.1), run_time=0.5)
            self.play(*ctx.add(call2, shift=LEFT * 0.3), run_time=0.4)
            self.wait_until(v.cue("small") - 0.3)
            self.play(*ctx.add(small, shift=DOWN * 0.2), run_time=0.5)

        # ---- 2. search instead of reading everything
        s2 = sub(2, "search instead of reading everything").move_to(s1)
        with self.say("s04_06") as v:
            self.wait_until(v.cue("second") - 0.3)
            self.play(*ctx.remove([call2, small], shift=RIGHT * 0.3), FadeOut(req2), FadeOut(after), FadeOut(s1),
                      run_time=0.45)
            self.play(*ctx.relayout(), FadeIn(s2, shift=UP * 0.08), run_time=0.45)

        files = VGroup(*[I.file_icon(0.42, MUTED) for _ in range(10)]).arrange(RIGHT, buff=0.18).move_to([RX, 0.5, 0])
        before2 = phase("before", RED).move_to([RX, 1.2, 0])
        many_call = ctx.size(ToolCallMsg("read_file", "× 10 files", width=W, size=12, height=0.28), 0.01)
        reads = [ctx.size(SizedCard("tool", content=bars(1, 20 + j, 1.4), height=0.27, width=W), 0.065) for j in range(10)]
        after2 = phase("after", TEAL).move_to(before2)
        req3 = ToolCallCard("run_command", 'search "total()"', width=3.7, size=17).move_to([RX, 0.35, 0])
        call3 = ctx.size(ToolCallMsg("run_command", 'search "total()"', width=W, size=12, height=0.28), 0.01)
        hits = VGroup(mono("math_utils.py · line 42", 11, FG), mono("report.py · line 7", 11, FG),
                      mono("test_math.py · line 15", 11, FG)).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
        found = ctx.size(SizedCard("tool", content=hits, height=0.62, width=W), 0.04)
        with self.say("s04_07") as v:
            self.wait_until(v.cue("before") - 0.3)
            self.play(FadeIn(before2), FadeIn(files, lag_ratio=0.1), run_time=0.6)
            self.play(*ctx.add(many_call, shift=LEFT * 0.3), run_time=0.35)
            self.wait_until(v.cue("ten") - 0.2)
            for j in range(10):
                self.play(files[j].animate.set_color(TEAL), *ctx.add(reads[j], shift=DOWN * 0.15), run_time=0.18)
            self.wait_until(v.cue("after") - 0.4)
            self.play(*ctx.remove(reads + [many_call], shift=RIGHT * 0.3), FadeOut(files), FadeOut(before2),
                      FadeIn(after2), run_time=0.5)
            self.play(*ctx.relayout(), run_time=0.35)
            self.wait_until(v.cue("search") - 0.3)
            self.play(FadeIn(req3, shift=DOWN * 0.1), *ctx.add(call3, shift=LEFT * 0.3), run_time=0.5)
            self.wait_until(v.cue("matching") - 0.3)
            self.play(*ctx.add(found, shift=DOWN * 0.2), run_time=0.5)

        # ---- 3. the harness shortens very long output
        s3 = sub(3, "the harness shortens long output").move_to(s1)
        with self.say("s04_08") as v:
            self.wait_until(v.cue("third") - 0.3)
            self.play(*ctx.remove([call3, found], shift=RIGHT * 0.3), FadeOut(req3), FadeOut(after2), FadeOut(s2),
                      run_time=0.45)
            self.play(*ctx.relayout(), FadeIn(s3, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("shortens") - 0.3)
            gear = Pill(VGroup(I.gear(0.24, AMBER), caps("harness", 13, AMBER)).arrange(RIGHT, buff=0.1), AMBER,
                        pad_x=0.16).move_to([RX + 2.6, 1.2, 0])
            self.play(FadeIn(gear, scale=0.9), run_time=0.4)

        call4 = ctx.size(ToolCallMsg("run_command", '"run tests"', width=W, size=12, height=0.28), 0.01)
        head_l = VGroup(mono("running 812 tests…", 11, FG), mono("test_math ✓  test_report ✓", 11, FG)).arrange(
            DOWN, buff=0.05, aligned_edge=LEFT)
        mid = bars(14, 31, 2.2)
        tail_l = VGroup(mono("FAILED test_login (2)", 11, RED), mono("810 passed, 2 failed", 11, FG)).arrange(
            DOWN, buff=0.05, aligned_edge=LEFT)
        long_body = VGroup(head_l, mid, tail_l).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        out_frame = RoundedRectangle(width=3.4, height=long_body.height + 0.36, corner_radius=0.1).set_stroke(TEAL, 1.4,
                                                                                                         opacity=0.6)
        out_frame.set_fill(PANEL, 1)
        out_lab = caps("tool result · thousands of lines", 12, TEAL).next_to(out_frame, UP, buff=0.1, aligned_edge=LEFT)
        long_out = VGroup(out_frame, long_body.move_to(out_frame)).move_to([RX + 0.1, -0.85, 0])
        out_lab.next_to(out_frame, UP, buff=0.1, aligned_edge=LEFT)
        b_top = SurroundingRectangle(head_l, color=TEAL, buff=0.06, corner_radius=0.05).set_stroke(width=1.6)
        b_end = SurroundingRectangle(tail_l, color=TEAL, buff=0.06, corner_radius=0.05).set_stroke(width=1.6)
        ph = PlaceholderCard("[output shortened: 4,800 more lines]", width=2.9, size=11)
        short_body = VGroup(head_l.copy(), ph, tail_l.copy()).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        short = ctx.size(SizedCard("tool", content=short_body, height=short_body.height + 0.26, width=W), 0.09)
        with self.say("s04_09") as v:
            self.play(*ctx.add(call4, shift=LEFT * 0.3), run_time=0.4)
            self.wait_until(v.cue("thousands") - 0.4)
            self.play(FadeIn(out_frame), FadeIn(long_body, shift=DOWN * 0.15), FadeIn(out_lab), run_time=0.7)
            self.wait_until(v.cue("beginning") - 0.3)
            self.play(Create(b_top), run_time=0.4)
            self.wait_until(v.cue("end") - 0.3)
            self.play(Create(b_end), run_time=0.4)
            self.wait_until(v.cue("note") - 0.5)
            ph_tmp = ph.copy().move_to(mid)
            self.play(FadeOut(b_top), FadeOut(b_end), mid.animate.stretch_to_fit_height(0.05).set_opacity(0),
                      FadeIn(ph_tmp, scale=0.9), run_time=0.7)
            self.remove(mid)
            short.move_to(long_out)
            self.play(FadeOut(out_frame), FadeOut(out_lab), FadeOut(head_l), FadeOut(tail_l), FadeOut(ph_tmp),
                      FadeIn(short), run_time=0.5)
            self.play(*ctx.add_from(short), run_time=0.8)

        tell = Pill(VGroup(I.warn_icon(0.26, AMBER), en("tell the model that text was cut", 21, FG)).arrange(RIGHT, buff=0.12),
                    AMBER, pad_x=0.22).move_to([RX - 0.4, 0.62, 0])
        with self.say("s04_10") as v:
            self.wait_until(v.cue("matters") - 0.3)
            self.play(glow(short.body[1].frame, AMBER, 6), pulse(short.body[1], 1.08), run_time=0.7)
            self.wait_until(v.cue("tell") - 0.3)
            self.play(FadeIn(tell, shift=UP * 0.08), run_time=0.5)

        def panel(title, color, x):
            fr = RoundedRectangle(width=4.0, height=2.75, corner_radius=0.14).set_stroke(color, 1.6).set_fill(color, 0.03)
            fr.move_to([x, -1.2, 0])
            t = caps(title, 14, color).next_to(fr.get_top(), DOWN, buff=0.16)
            m = ModelBox(1.6, 0.85, label_size=14).move_to(fr.get_center() + UP * 0.25)
            return VGroup(fr, t, m)

        p1 = panel("without the note", RED, RX - 2.15)
        p2 = panel("with the note", TEAL, RX + 2.15)
        wrong = SizedCard("assistant", "Only 2 tests fail. All done!", height=0.34, width=3.6, size=13)
        wrong.next_to(p1[2], DOWN, buff=0.25)
        qmark = en("?", 40, RED, italic=False, weight=NORMAL).next_to(p1[2], RIGHT, buff=0.25)
        seen = caps("thinks it saw everything", 12, MUTED).next_to(p1[2], UP, buff=0.12)
        ask = ToolCallMsg("run_command", '"show the cut part"', width=3.6, size=14, height=0.36)
        ask.next_to(p2[2], DOWN, buff=0.25)
        knows = caps("knows something is missing", 12, MUTED).next_to(p2[2], UP, buff=0.12)
        with self.say("s04_11") as v:
            self.wait_until(v.cue("without") - 0.4)
            self.play(FadeIn(p1), tell.animate.fade(0.6), FadeOut(s3), run_time=0.5)
            self.wait_until(v.cue("everything") - 0.3)
            self.play(FadeIn(seen), p1[2].think(), run_time=0.5)
            self.wait_until(v.cue("confidently") - 0.3)
            self.play(FadeIn(wrong, shift=DOWN * 0.1), run_time=0.45)
            self.play(FadeIn(qmark, scale=1.4), run_time=0.35)

        with self.say("s04_12") as v:
            self.wait_until(v.cue("with") - 0.4)
            self.play(FadeIn(p2), run_time=0.5)
            self.wait_until(v.cue("missing") - 0.3)
            self.play(FadeIn(knows), p2[2].think(), run_time=0.5)
            self.wait_until(v.cue("asks") - 0.3)
            self.play(FadeIn(ask, shift=DOWN * 0.1), run_time=0.45)
            self.play(glow(ask.frame, BLUE, 5), run_time=0.5)
        self.clear_all(0.6)
