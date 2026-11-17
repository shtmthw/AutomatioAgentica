"""06 · Working through the plan (the key section): the loop is unchanged; the plan is in front of
the model on every call. Plan step 1 in detail (pick, do, check, mark, move on), steps 2 and 3
quickly, then two versions of step 5: said, not checked vs checked with an evidence link."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *

PANEL_C = np.array([-4.65, 0.45, 0])
MODEL_C = np.array([-0.05, 2.35, 0])
LOOP_C = np.array([-0.05, -0.4, 0])
FEED_X, FEED_TOP, FEED_BOTTOM = 1.95, 2.75, -2.65
FW = 4.85
PHASES = ("pick", "do", "check", "mark", "move on")


def phase_row():
    pills = VGroup()
    for i, t in enumerate(PHASES):
        n = en(str(i + 1), 14, DIM, italic=False, weight=NORMAL)
        lab = en(t, 14, DIM)
        pills.add(Pill(VGroup(n, lab).arrange(RIGHT, buff=0.08), FAINT, pad_x=0.1, pad_y=0.04))
    return pills.arrange(RIGHT, buff=0.08)


def light(pills, i):
    anims = []
    for j, p in enumerate(pills):
        if j == i:
            anims += [p.frame.animate.set_stroke(PLAN, opacity=1).set_fill(PLAN, 0.14), p.label.animate.set_opacity(1)]
            anims += [p[1].animate.set_color(PLAN)]
        elif j < i:
            anims += [p.frame.animate.set_stroke(DIM).set_fill(PANEL, 1), p[1].animate.set_color(MUTED)]
        else:
            anims += [p.frame.animate.set_stroke(FAINT).set_fill(PANEL, 1), p[1].animate.set_color(DIM)]
    return anims


def tool_res(text, width=FW, size=12, color=FG, h=0.3):
    return res_msg(text, width=width, size=size, color=color)


def calln(tool, arg, width=FW):
    return call_msg(tool, arg, width=width, size=12)


class S06WorkPlan(VoiceScene):
    SECTION = "s06"

    def construct(self):
        self.show_chapter()
        panel = PlanPanel(plan_state(), width=4.2, size=14, rows=5, row_h=0.4).move_to(PANEL_C)
        counter = StepCounter(panel.state).move_to([LOOP_C[0], -2.45, 0])
        panel.counter = counter
        model = ModelBox(1.75, 0.9, label_size=14).move_to(MODEL_C)
        loop = LoopDiagram(LOOP_C, radius=1.18, node_w=1.08, node_h=0.46, name_size=16, meanings=False, goal=False)
        phases = phase_row().move_to([PANEL_C[0], -2.2, 0])
        feed = Feed(FEED_X, FEED_TOP, FEED_BOTTOM, gap=0.07)
        feed_lab = caps("message list", 11, DIM).move_to([FEED_X + FW / 2, 3.1, 0])

        with self.say("s06_01") as v:
            self.wait_until(v.cue("important") - 0.4)
            self.play(FadeIn(panel, shift=RIGHT * 0.1), run_time=0.6)
            self.wait_until(v.cue("works") - 0.4)
            self.play(LaggedStart(FadeIn(model, scale=0.94), FadeIn(loop), FadeIn(counter), FadeIn(feed_lab), lag_ratio=0.2),
                      run_time=0.9)

        same = Pill(VGroup(I.check_icon(0.16, BLUE), caps("unchanged", 11, BLUE)).arrange(RIGHT, buff=0.08), BLUE,
                    pad_x=0.12, pad_y=0.04).next_to(model, RIGHT, buff=0.15)
        one = caps("one action per call", 11, MUTED).next_to(model, DOWN, buff=0.1)
        with self.say("s06_02") as v:
            self.wait_until(v.cue("changed") - 0.3)
            self.play(*loop.all_lit(), run_time=0.4)
            self.wait_until(v.cue("loop") - 0.3)
            self.play(*loop.all_normal(), FadeIn(same, shift=LEFT * 0.06), run_time=0.5)
            self.wait_until(v.cue("one") - 0.3)
            self.play(FadeIn(one), model.think(0.5), run_time=0.5)

        u = SizedCard("user", "Add a contact form… thank-you note.", width=FW, height=0.3, size=12)
        with self.say("s06_03") as v:
            self.wait_until(v.cue("plan") - 0.6)
            self.play(*feed.push(u), run_time=0.4)
            self.play(bundle_anim(model, [panel, u], run_time=0.8), glow(panel.frame, PLAN, 6), run_time=0.8)
            self.wait_until(v.cue("every") - 0.3)
            self.play(bundle_anim(model, [panel, u], run_time=0.7), run_time=0.7)

        with self.say("s06_04") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(FadeIn(phases, shift=UP * 0.06), FadeOut(same), run_time=0.5)
            self.wait_until(v.cue("look") - 0.3)
            r1 = panel.row("s1")
            self.play(glow(r1.bg.copy().set_stroke(PLAN, 1), PLAN, 6), pulse(r1.text, 1.06), run_time=0.7)

        # 1. pick the next step
        c1 = plan_call("step 1: in progress", width=FW, size=12)
        with self.say("s06_05") as v:
            self.wait_until(v.cue("pick") - 0.3)
            self.play(*light(phases, 0), *loop.focus("decide"), run_time=0.5)
            self.wait_until(v.cue("reads") - 0.3)
            self.play(bundle_anim(model, [panel, *feed.cards], run_time=0.8), run_time=0.8)
            self.wait_until(v.cue("calls") - 0.3)
            self.play(*feed.push(c1, shift=LEFT * 0.15), run_time=0.4)
            self.wait_until(v.cue("applies") - 0.6)
            panel.apply(self, c1, "status", "s1", ACTIVE)

        # 2. do the work
        work = [(calln("run_command", '"list files"'), tool_res("index.html  pages/  css/")),
                (calln("read_file", '"index.html"'), tool_res("<a href=\"pages/about.html\"> …"))]
        with self.say("s06_06") as v:
            self.wait_until(v.cue("work") - 0.3)
            self.play(*light(phases, 1), run_time=0.4)
            for (call, res), cue in zip(work, ("run", "read")):
                self.wait_until(v.cue(cue) - 0.7)
                self.play(*loop.focus("decide"), bundle_anim(model, [panel, *feed.cards[-2:]], run_time=0.55), run_time=0.55)
                self.play(*feed.push(call, shift=LEFT * 0.15), *loop.focus("act"), run_time=0.4)
                self.play(*feed.push(res), *loop.focus("observe"), run_time=0.4)

        tok = Token(TEAL, 0.08).move_to(loop.nodes["decide"])
        with self.say("s06_07") as v:
            self.add(tok)
            for _ in range(2):
                for a, b, cue in (("decide", "act", "act"), ("act", "observe", "observe")):
                    self.play(MoveAlongPath(tok, loop.leg(a, b)), *loop.focus(b), run_time=0.45)
                self.play(MoveAlongPath(tok, Line(loop.nodes["observe"].get_center(), loop.nodes["decide"].get_center())
                                        .set_stroke(opacity=0)), *loop.focus("decide"), run_time=0.4)
            self.play(FadeOut(tok), run_time=0.2)

        knows = Pill(VGroup(I.check_icon(0.16, VIOLET), en("pages are kept in pages/", 13, FG)).arrange(RIGHT, buff=0.08),
                     VIOLET, pad_x=0.14, pad_y=0.05).move_to([LOOP_C[0], 1.3, 0])
        with self.say("s06_08") as v:
            self.wait_until(v.cue("check") - 0.3)
            self.play(*light(phases, 2), *loop.focus("evaluate"), run_time=0.5)
            self.wait_until(v.cue("knows") - 0.3)
            self.play(FadeIn(knows, scale=0.92), glow(feed.cards[-1].frame, TEAL, 4), run_time=0.5)

        c2 = plan_call("step 1: done", width=FW, size=12)
        with self.say("s06_09") as v:
            self.wait_until(v.cue("mark") - 0.3)
            self.play(*light(phases, 3), *loop.focus("decide"), FadeOut(knows), run_time=0.5)
            self.wait_until(v.cue("another") - 0.5)
            self.play(bundle_anim(model, [panel, *feed.cards[-2:]], run_time=0.55), run_time=0.55)
            self.play(*feed.push(c2, shift=LEFT * 0.15), run_time=0.4)
            self.wait_until(v.cue("tick") - 0.8)
            panel.apply(self, c2, "status", "s1", DONE)

        with self.say("s06_10") as v:
            self.wait_until(v.cue("move") - 0.3)
            self.play(*light(phases, 4), run_time=0.4)
            self.wait_until(v.cue("two") - 0.3)
            r2 = panel.row("s2")
            self.play(glow(r2.bg.copy().set_stroke(PLAN, 1), PLAN, 6), glow(counter.frame, PLAN, 5), run_time=0.6)

        # steps 2 and 3, quickly: in progress, work, check, done
        quick = {"s2": (calln("edit_file", '"contact.html"'), tool_res("File created.")),
                 "s3": (calln("edit_file", '"contact.html"'), tool_res("File updated."))}
        rhythm = VGroup(*[caps(t, 12, PLAN) for t in ("in progress", "work", "check", "done")]).arrange(RIGHT, buff=0.3)
        rhythm.move_to([LOOP_C[0], 1.25, 0])
        with self.say("s06_11") as v:
            self.wait_until(v.cue("steps") - 0.3)
            self.play(FadeOut(phases), FadeOut(one), run_time=0.25)
            for sid in ("s2", "s3"):
                call, res = quick[sid]
                ca = plan_call(f"step {sid[1]}: in progress", width=FW, size=12)
                self.play(bundle_anim(model, [panel], run_time=0.35), *feed.push(ca, shift=LEFT * 0.15), *loop.focus("decide"),
                          *([FadeIn(rhythm[0], shift=UP * 0.06)] if sid == "s2" else []), run_time=0.35)
                panel.apply(self, ca, "status", sid, ACTIVE, fast=True)
                self.play(bundle_anim(model, [panel], run_time=0.35), *feed.push(call, shift=LEFT * 0.15), *loop.focus("act"),
                          *([FadeIn(rhythm[1], shift=UP * 0.06)] if sid == "s2" else []), run_time=0.35)
                self.play(*feed.push(res), *loop.focus("evaluate"),
                          *([FadeIn(rhythm[2], shift=UP * 0.06)] if sid == "s2" else []), run_time=0.3)
                cd = plan_call(f"step {sid[1]}: done", width=FW, size=12)
                self.play(bundle_anim(model, [panel], run_time=0.35), *feed.push(cd, shift=LEFT * 0.15), *loop.focus("decide"),
                          *([FadeIn(rhythm[3], shift=UP * 0.06)] if sid == "s2" else []), run_time=0.35)
                panel.apply(self, cd, "status", sid, DONE, fast=True)

        # ---- two versions of step 5
        def mini_state():
            st = PlanState("Contact form", STEPS)
            for k in ("s1", "s2", "s3", "s4"):
                st.set_status(k, DONE)
            st.set_status("s5", ACTIVE)
            return st

        LX, RX = -3.5, 3.5
        divider = DashedLine([0, 2.85, 0], [0, -2.7, 0], dash_length=0.08).set_stroke(FAINT, 1.6)
        heads = VGroup(Pill(VGroup(I.cross_icon(0.18, RED), caps("wrong", 13, RED)).arrange(RIGHT, buff=0.08), RED, pad_x=0.16,
                            pad_y=0.05).move_to([LX, 2.75, 0]),
                       Pill(VGroup(I.check_icon(0.18, PLAN), caps("right", 13, PLAN)).arrange(RIGHT, buff=0.08), PLAN,
                            pad_x=0.16, pad_y=0.05).move_to([RX, 2.75, 0]))
        pw, mw = 2.9, 3.1

        def mini(x):
            lead = VGroup(I.check_icon(0.16, PLAN), caps("steps 1–4 done", 11, MUTED)).arrange(RIGHT, buff=0.1)
            return PlanPanel(mini_state(), width=pw, size=14, rows=2, row_h=0.44, sub=None, visible=["s5"],
                             lead=lead).move_to([x, 0.9, 0])

        pl, pr = mini(-5.4), mini(1.55)
        fl = Feed(-3.3, 2.2, -2.6, gap=0.08)
        fr = Feed(3.65, 2.2, -2.6, gap=0.08)
        with self.say("s06_12") as v:
            self.wait_until(v.cue("closer") - 0.4)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.6)
            self.wait_until(v.cue("two") - 0.3)
            self.play(Create(divider), FadeIn(heads, shift=DOWN * 0.06), FadeIn(pl), FadeIn(pr), run_time=0.7)
            self.wait_until(v.cue("five") - 0.3)
            self.play(glow(pl.row("s5").bg.copy().set_stroke(PLAN, 1), PLAN, 6),
                      glow(pr.row("s5").bg.copy().set_stroke(PLAN, 1), PLAN, 6), run_time=0.6)

        e1 = calln("edit_file", '"contact.html"', width=mw)
        e1r = tool_res("File updated.", width=mw)
        d1 = plan_call("step 5: done", width=mw, size=12)
        q = en("?", 24, RED, italic=False, weight=NORMAL)
        said = bad_tag("said, not checked")
        with self.say("s06_13") as v:
            self.wait_until(v.cue("edits") - 0.3)
            self.play(*fl.push(e1), run_time=0.4)
            self.play(*fl.push(e1r), run_time=0.35)
            self.wait_until(v.cue("marks") - 0.4)
            self.play(*fl.push(d1, shift=LEFT * 0.12), run_time=0.4)
            pl.apply(self, d1, "status", "s5", DONE, fast=True)
            self.wait_until(v.cue("no") - 0.3)
            q.next_to(pl.row("s5").text, RIGHT, buff=0.14)
            self.play(FadeIn(q, scale=1.4), pl.row("s5").icon.animate.set_opacity(0.55), run_time=0.4)
            self.wait_until(v.cue("said") - 0.3)
            said.next_to(pl, DOWN, buff=0.25)
            self.play(FadeIn(said, shift=UP * 0.06), run_time=0.4)

        t1 = calln("run_command", '"run tests"', width=mw)
        t1r = tool_res("All tests passed ✓", width=mw, color=TEAL)
        d2 = plan_call("step 5: done", width=mw, size=12)
        checked = ok_tag("checked")
        with self.say("s06_14") as v:
            self.wait_until(v.cue("calls") - 0.3)
            self.play(*fr.push(t1), run_time=0.4)
            self.wait_until(v.cue("result") - 0.3)
            self.play(*fr.push(t1r), run_time=0.4)
            self.wait_until(v.cue("only") - 0.3)
            self.play(*fr.push(d2, shift=LEFT * 0.12), run_time=0.4)
            pr.apply(self, d2, "status", "s5", DONE, fast=True)
            self.wait_until(v.cue("checked") - 0.6)
            link = EvidenceLink(pr.row("s5"), t1r, bend=0.5)
            self.play(link.draw(0.7), run_time=0.7)
            checked.next_to(pr, DOWN, buff=0.25)
            self.play(FadeIn(checked, shift=UP * 0.06), run_time=0.35)

        claim = Pill(caps("a claim by the model", 11, BLUE), BLUE, pad_x=0.12, pad_y=0.04)
        claim.next_to(said, DOWN, buff=0.15)
        proof = Pill(caps("the proof", 11, TEAL), TEAL, pad_x=0.12, pad_y=0.04)
        proof = Pill(VGroup(caps("tool result", 11, TEAL), en("=", 13, MUTED, italic=False), caps("the proof", 11, TEAL)).arrange(
            RIGHT, buff=0.08), TEAL, pad_x=0.12, pad_y=0.04)
        with self.say("s06_15") as v:
            self.wait_until(v.cue("claim") - 0.3)
            self.play(FadeIn(claim, shift=UP * 0.06), glow(pl.row("s5").icon[0], BLUE, 5), glow(pr.row("s5").icon[0], BLUE, 5),
                      run_time=0.5)
            self.wait_until(v.cue("proof") - 0.3)
            proof.next_to(fr.cards[-1], DOWN, buff=0.18, aligned_edge=LEFT)
            self.play(FadeIn(proof, shift=UP * 0.06), glow(t1r.frame, TEAL, 6), run_time=0.5)

        tie = Pill(VGroup(I.gear(0.2, AMBER), caps("every done tied to evidence", 11, AMBER)).arrange(RIGHT, buff=0.08), AMBER,
                   pad_x=0.12, pad_y=0.04)
        tie.next_to(checked, DOWN, buff=0.15)
        chk = Pill(caps("checkable steps", 12, PLAN), PLAN, pad_x=0.14, pad_y=0.05)
        with self.say("s06_16") as v:
            self.wait_until(v.cue("tie") - 0.3)
            self.play(Create(link.curve.copy().set_stroke(PLAN, 4, opacity=0.6)), FadeIn(tie, shift=UP * 0.05), run_time=0.6)
            self.wait_until(v.cue("checkable") - 0.3)
            chk.next_to(tie, DOWN, buff=0.12)
            if chk.get_bottom()[1] < -2.7:
                chk.next_to(tie, LEFT, buff=0.2)
            self.play(FadeIn(chk, scale=0.9), run_time=0.4)

        key = VGroup(en("Done", 54, FG, italic=False), en("=", 50, MUTED, italic=False),
                     en("checked", 54, PLAN, italic=False, weight=NORMAL)).arrange(RIGHT, buff=0.35).move_to([0, 0.5, 0])
        notj = VGroup(caps("not just", 16, MUTED), en("said", 28, MUTED)).arrange(RIGHT, buff=0.16).next_to(key, DOWN, buff=0.5)
        strike = Line(notj[1].get_left() + LEFT * 0.06, notj[1].get_right() + RIGHT * 0.06).set_stroke(RED, 2.4)
        with self.say("s06_17") as v:
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.5)
            self.wait_until(v.cue("checked") - 0.4)
            self.play(FadeIn(key, shift=UP * 0.1), run_time=0.6)
            self.wait_until(v.cue("said") - 0.3)
            self.play(FadeIn(notj), run_time=0.3)
            self.play(Create(strike), run_time=0.35)
        self.wait(0.8)
        self.clear_all(0.6)
