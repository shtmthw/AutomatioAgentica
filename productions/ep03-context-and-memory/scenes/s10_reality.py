"""10 · Reality check: memory can be wrong. Summaries lose details, notes go out of date (check
important facts again), notes can be wrong from the start, memory can hold private information."""
from agentic_video.prelude import *
from memory_kit import *

LX = -6.3
VX = 3.0          # centre of the visual on the right


def point(i, text, color):
    return VGroup(en(str(i), 26, color, italic=False, weight=NORMAL), en(text, 24, FG)).arrange(RIGHT, buff=0.2)


class S10Reality(VoiceScene):
    SECTION = "s10"

    def construct(self):
        self.show_chapter()
        head = VGroup(caps("reality check", 16, MUTED), en("memory isn't magic", 30, FG)).arrange(DOWN, buff=0.12,
                                                                                               aligned_edge=LEFT)
        head.move_to([LX + head.width / 2, 2.55, 0])
        pts = [point(1, "Summaries lose details", AMBER), point(2, "Notes can be out of date", RED),
               point(3, "Notes can be wrong from the start", RED), point(4, "Memory can hold private information", MEMORY)]
        for i, p in enumerate(pts):
            p.move_to([LX + p.width / 2, 1.3 - i * 0.95, 0])
        state = {"vis": VGroup()}

        def show(i, vis_anims=()):
            anims = [FadeIn(pts[i], shift=RIGHT * 0.12)]
            for j in range(i):
                anims.append(pts[j].animate.set_opacity(0.4))
            if len(state["vis"]):
                anims.append(FadeOut(state["vis"]))
            state["vis"] = VGroup()
            return anims

        with self.say("s10_01") as v:
            self.wait_until(v.cue("reality") - 0.3)
            self.play(FadeIn(head[0], shift=DOWN * 0.06), run_time=0.4)
            self.wait_until(v.cue("magic") - 0.4)
            self.play(FadeIn(head[1], shift=UP * 0.06), run_time=0.5)

        # 1. summaries lose details
        summ = SummaryCard(["Goal: fix the crash", "Done: fixed total()", "User wants simple error messages",
                            "Still to do: login test"], width=4.6, size=18).move_to([VX, 0.3, 0])
        with self.say("s10_02") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(*show(0), run_time=0.5)
            self.wait_until(v.cue("details") - 0.4)
            self.play(FadeIn(summ, shift=UP * 0.1), run_time=0.5)
            self.wait_until(v.cue("gone") - 0.5)
            self.play(summ.rows[2].animate.set_opacity(0.08), run_time=1.0)
            state["vis"] = VGroup(summ)

        # 2. notes can be out of date
        note = NoteCard("Server port is 8080", size=17).move_to([VX - 1.35, 1.3, 0])
        n_lab = caps("saved note", 12, MEMORY).next_to(note, UP, buff=0.1, aligned_edge=LEFT)
        cfg = VGroup(I.file_icon(0.42, MUTED), VGroup(mono("config.txt", 15, MUTED), mono("port = 9090", 17, FG)).arrange(
            DOWN, buff=0.06, aligned_edge=LEFT)).arrange(RIGHT, buff=0.16).move_to([VX + 1.75, 1.3, 0])
        c_lab = caps("now", 12, MUTED).next_to(cfg, UP, buff=0.1, aligned_edge=LEFT)
        with self.say("s10_03") as v:
            self.wait_until(v.cue("two") - 0.3)
            self.play(*show(1), run_time=0.5)
            self.wait_until(v.cue("p8080") - 0.4)
            self.play(FadeIn(note, shift=DOWN * 0.1), FadeIn(n_lab), run_time=0.5)
            self.wait_until(v.cue("p9090") - 0.4)
            self.play(FadeIn(cfg, shift=DOWN * 0.1), FadeIn(c_lab), run_time=0.5)
            act = SizedCard("assistant", "Connect to the server on port 8080.", height=0.36, width=4.6, size=15)
            act.move_to([VX, 0.0, 0])
            a1 = arrow(note.get_bottom() + DOWN * 0.05, act.get_top() + UP * 0.05 + LEFT * 1.0, color=MEMORY, tip=0.1)
            fail = SizedCard("tool", content=VGroup(I.cross_icon(0.18), mono("connection refused", 14, RED)).arrange(
                RIGHT, buff=0.1), height=0.36, width=4.6).move_to([VX, -0.55, 0])
            self.wait_until(v.cue("trusts") - 0.3)
            self.play(GrowArrow(a1), FadeIn(act, shift=DOWN * 0.08), run_time=0.6)
            self.wait_until(v.cue("mistake") - 0.3)
            self.play(FadeIn(fail, shift=DOWN * 0.08), glow(fail.frame, RED, 5), run_time=0.6)

        chk = ToolCallMsg("read_file", '"config.txt"', width=4.6, size=14, height=0.34).move_to([VX, -1.35, 0])
        chk_ok = VGroup(I.check_icon(0.22, TEAL), caps("check again", 13, TEAL)).arrange(RIGHT, buff=0.1)
        chk_ok.next_to(chk, DOWN, buff=0.14, aligned_edge=RIGHT)
        with self.say("s10_04") as v:
            self.wait_until(v.cue("check") - 0.3)
            self.play(FadeIn(chk, shift=DOWN * 0.08), run_time=0.45)
            self.play(FadeIn(chk_ok), glow(cfg[1], TEAL, 3), run_time=0.45)
            state["vis"] = VGroup(note, n_lab, cfg, c_lab, a1, act, fail, chk, chk_ok)

        # 3. wrong from the start
        bad = NoteCard("The crash is caused by login.py", size=17, color=RED).move_to([VX - 1.6, 0.9, 0])
        b_lab = caps("a wrong conclusion, saved", 12, RED).next_to(bad, UP, buff=0.1, aligned_edge=LEFT)
        sess = VGroup()
        for k in (2, 3, 4):
            s = VGroup(session_pill(k), NoteCard("…caused by login.py", size=12, color=RED),
                       I.warn_icon(0.24, RED)).arrange(DOWN, buff=0.14)
            sess.add(s)
        sess.arrange(RIGHT, buff=0.22).move_to([VX + 0.3, -1.05, 0])
        with self.say("s10_05") as v:
            self.wait_until(v.cue("three") - 0.3)
            self.play(*show(2), run_time=0.5)
            self.wait_until(v.cue("wrong") - 0.3)
            self.play(FadeIn(bad, shift=DOWN * 0.08), FadeIn(b_lab), run_time=0.5)
            self.wait_until(v.cue("repeated") - 0.3)
            self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.15) for s in sess], lag_ratio=0.3), run_time=1.0)
            state["vis"] = VGroup(bad, b_lab, sess)

        # 4. private information
        nb = Notebook(1.3).move_to([VX - 1.2, 0.3, 0])
        lk = nb.lock(0.4)
        see = Pill(VGroup(eye_icon(0.26, FG), en("see what is saved", 21, FG)).arrange(RIGHT, buff=0.12), FG, pad_x=0.22)
        dele = Pill(VGroup(I.trash_icon(0.28, RED), en("delete it", 21, FG)).arrange(RIGHT, buff=0.12), RED, pad_x=0.22)
        ctrl = VGroup(see, dele).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([VX + 1.9, 0.3, 0])
        with self.say("s10_06") as v:
            self.wait_until(v.cue("four") - 0.3)
            self.play(*show(3), run_time=0.5)
            self.wait_until(v.cue("private") - 0.4)
            self.play(FadeIn(nb, scale=0.9), run_time=0.5)
            self.play(FadeIn(lk, scale=0.8), run_time=0.4)
            self.wait_until(v.cue("see") - 0.3)
            self.play(FadeIn(see, shift=LEFT * 0.1), run_time=0.45)
            self.wait_until(v.cue("delete") - 0.3)
            self.play(FadeIn(dele, shift=LEFT * 0.1), run_time=0.45)
            state["vis"] = VGroup(nb, lk, ctrl)

        more = VGroup(en("more memory", 30, MUTED), en("≠", 34, MUTED), en("better", 30, MUTED)).arrange(RIGHT, buff=0.22)
        right = VGroup(en("the right information", 32, TEAL), en("at the right time", 32, TEAL)).arrange(RIGHT, buff=0.3)
        g = VGroup(more, right).arrange(DOWN, buff=0.45).move_to([0, -0.2, 0])
        with self.say("s10_07") as v:
            self.wait_until(v.cue("automatically") - 0.5)
            self.play(*[FadeOut(m) for m in (head, *pts, state["vis"])], run_time=0.6)
            self.play(FadeIn(more, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("right") - 0.3)
            self.play(FadeIn(right[0], shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("time") - 0.3)
            self.play(FadeIn(right[1], shift=UP * 0.08), run_time=0.5)
        self.wait(0.3)
        self.clear_all(0.6)
