"""09 · Full replay: the hook's task done properly. Plan Panel left, message list centre, model, loop
and step counter right, a small context meter in the corner. Every model call carries the plan;
every plan change follows an update_plan call; done steps get evidence links."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *

PANEL_C = np.array([-4.8, 0.4, 0])
FEED_X, FEED_TOP, FEED_BOTTOM = -2.55, 2.75, -2.65
FW = 4.85
MODEL_C = np.array([4.3, 2.35, 0])
LOOP_C = np.array([4.3, -0.15, 0])


class Meter(VGroup):
    """Small context-window meter for the corner."""

    def __init__(self, h=2.2, w=0.2, **kw):
        super().__init__(**kw)
        self.h, self.w = h, w
        self.box = RoundedRectangle(width=w, height=h, corner_radius=w / 2).set_stroke(DIM, 1.3).set_fill(BG, 1)
        self.fill = self._rect(0.1)
        self.lab = caps("context", 10, MUTED).next_to(self.box, DOWN, buff=0.1)
        self.add(self.box, self.fill, self.lab)

    def _rect(self, f):
        hh = max(0.01, (self.h - 0.06) * f)
        r = Rectangle(width=self.w * 0.55, height=hh).set_stroke(width=0).set_fill(meter_color3(f), 0.95)
        return r.move_to(self.box.get_bottom() + UP * (0.03 + hh / 2))

    def to(self, f):
        return Transform(self.fill, self._rect(f))


def calln(tool, arg):
    return call_msg(tool, arg, width=FW, size=12)


def res(text, color=FG):
    return res_msg(text, width=FW, size=12, color=color)


class S09Replay(VoiceScene):
    SECTION = "s09"

    def construct(self):
        self.show_chapter()
        panel = PlanPanel(PlanState(GOAL, []), width=4.0, size=13, rows=6, row_h=0.38, empty=True).move_to(PANEL_C)
        model = ModelBox(1.75, 0.9, label_size=14).move_to(MODEL_C)
        loop = LoopDiagram(LOOP_C, radius=1.05, node_w=0.98, node_h=0.42, name_size=14, meanings=False, goal=False)
        counter = StepCounter(PlanState(GOAL, STEPS)).move_to([LOOP_C[0], -2.2, 0])
        meter = Meter().move_to([6.6, -0.2, 0])
        feed = Feed(FEED_X, FEED_TOP, FEED_BOTTOM, gap=0.07)
        lvl = {"v": 0.1, "loop": False}

        def focus(stage):
            return loop.focus(stage) if lvl["loop"] else []

        def bump(d):
            lvl["v"] = min(0.95, lvl["v"] + d)
            return meter.to(lvl["v"])

        def ask_model(card, stage="act", extra=()):
            """A model call (the plan travels in with it) that produces `card`."""
            self.play(bundle_anim(model, [panel], run_time=0.45), *focus(stage), *feed.push(card, shift=LEFT * 0.12),
                      bump(0.025), *extra, run_time=0.45)

        def result(card, stage="observe"):
            self.play(*feed.push(card), *focus(stage), bump(0.03), run_time=0.35)

        def plan(text, op, *args, extra=(), **kw):
            c = plan_call(text, width=FW, size=12)
            ask_model(c, "decide", extra)
            panel.apply(self, c, op, *args, fast=True, **kw)
            return c

        with self.say("s09_01") as v:
            self.wait_until(v.cue("replay") - 0.4)
            self.play(FadeIn(panel, shift=RIGHT * 0.1), FadeIn(model, scale=0.94), FadeIn(meter), run_time=0.7)
            self.wait_until(v.cue("everything") - 0.3)
            self.play(glow(panel.frame, PLAN, 5), run_time=0.5)

        u = SizedCard("user", "Add a contact form to my website. It should save every message and show a thank-you note.",
                      width=FW, height=0.5, size=12, wrap=42)
        prompt = ApprovalPrompt(width=3.4).move_to(LOOP_C)
        with self.say("s09_02") as v:
            self.wait_until(v.cue("asks") - 0.3)
            self.play(*feed.push(u), run_time=0.45)
            self.wait_until(v.cue("calls") - 0.5)
            plan("five steps", "create", STEPS)
            self.wait_until(v.cue("approval") - 0.3)
            self.play(FadeIn(prompt, scale=0.92), run_time=0.45)
            self.wait_until(v.cue("approves") - 0.3)
            self.play(*prompt.press("approve"), run_time=0.45)
            self.play(FadeOut(prompt), FadeIn(loop), FadeIn(counter), run_time=0.5)
            lvl["loop"] = True
            panel.counter = counter

        with self.say("s09_03") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(glow(panel.row("s1").bg.copy().set_stroke(PLAN, 1), PLAN, 5), run_time=0.4)
            self.wait_until(v.cue("progress") - 0.6)
            plan("step 1: in progress", "status", "s1", ACTIVE)
            self.wait_until(v.cue("list") - 0.5)
            ask_model(calln("run_command", '"list files"'))
            result(res("index.html  pages/  css/"))
            self.wait_until(v.cue("read") - 0.5)
            ask_model(calln("read_file", '"index.html"'))
            result(res("<a href=\"pages/about.html\"> …"), "evaluate")
            self.wait_until(v.cue("done") - 0.9)
            plan("step 1: done", "status", "s1", DONE)

        with self.say("s09_04") as v:
            self.wait_until(v.cue("two") - 0.8)
            plan("step 2: in progress", "status", "s2", ACTIVE)
            self.wait_until(v.cue("edit") - 0.5)
            ask_model(calln("edit_file", '"contact.html"'))
            self.wait_until(v.cue("created") - 0.3)
            r2 = res("File created.")
            result(r2, "evaluate")
            self.wait_until(v.cue("done") - 0.9)
            plan("step 2: done", "status", "s2", DONE)
            self.wait_until(v.cue("evidence") - 0.4)
            link = EvidenceLink(panel.row("s2"), r2, bend=0.4)
            self.play(link.draw(0.6), run_time=0.6)
            self.wait(0.4)
            self.play(FadeOut(link), run_time=0.3)

        with self.say("s09_05") as v:
            self.wait_until(v.cue("three") - 0.8)
            plan("step 3: in progress", "status", "s3", ACTIVE)
            self.wait_until(v.cue("search") - 0.5)
            ask_model(calln("run_command", '"search for storage"'))
            self.wait_until(v.cue("no") - 0.3)
            result(res("No storage found in this project.", AMBER), "evaluate")

        ask = SizedCard("assistant", "A simple file, or a database?", width=FW, height=0.3, size=12)
        ans = SizedCard("user", "A simple file is fine.", width=FW, height=0.3, size=12)
        pause = pause_icon(0.26, AMBER).next_to(model, LEFT, buff=0.2)
        with self.say("s09_06") as v:
            self.wait_until(v.cue("asks") - 0.5)
            ask_model(ask, "decide")
            self.play(FadeIn(pause, scale=0.8), run_time=0.3)
            self.wait_until(v.cue("fine") - 0.3)
            self.play(*feed.push(ans), FadeOut(pause), run_time=0.4)
            self.wait_until(v.cue("adds") - 0.6)
            plan("add before step 3: " + NEW_STEP, "add", "n1", NEW_STEP, before="s3", status=ACTIVE, demote="s3")

        with self.say("s09_07") as v:
            self.wait_until(v.cue("edit") - 0.5)
            ask_model(calln("edit_file", '"messages.txt"'))
            result(res("File created."), "evaluate")
            self.wait_until(v.cue("done") - 0.9)
            plan("step 3: done", "status", "n1", DONE)

        with self.say("s09_08") as v:
            self.wait_until(v.cue("back") - 0.8)
            plan("step 4: in progress", "status", "s3", ACTIVE)
            self.wait_until(v.cue("edit") - 0.5)
            ask_model(calln("edit_file", '"contact.html"'))
            result(res("File updated."), "evaluate")
            self.wait_until(v.cue("done") - 0.9)
            plan("step 4: done", "status", "s3", DONE)

        survives = Pill(VGroup(I.check_icon(0.18, PLAN), caps("the plan survives", 12, PLAN)).arrange(RIGHT, buff=0.08), PLAN,
                        pad_x=0.14, pad_y=0.05).next_to(panel, DOWN, buff=0.18)
        with self.say("s09_09") as v:
            self.wait_until(v.cue("fills") - 0.4)
            for i in range(4):
                c = SizedCard(("assistant", "tool")[i % 2], content=code_block(1.8, 1, size=0.03,
                                                                               color=(BLUE, TEAL)[i % 2], seed=i),
                              width=FW, height=0.28, dashed=(i % 2 == 0))
                self.play(*feed.push(c), meter.to(0.6 + 0.07 * i), run_time=0.25)
            lvl["v"] = 0.81
            self.wait_until(v.cue("collapse") - 0.3)
            old = feed.cards[:-2]
            summary = SummaryCard(["goal: contact form", "steps 1–4 done; file: messages.txt", "next: thank-you note"],
                                  width=FW, size=11)
            summary.move_to([FEED_X + FW / 2, FEED_TOP - summary.height / 2, 0])
            keep = feed.cards[-2:]
            feed.cards = [summary] + keep
            tg = feed._targets(feed.cards)
            self.play(*[c.animate.move_to(summary).scale(0.3).set_opacity(0) for c in old], FadeIn(summary, scale=0.95),
                      *[c.animate.move_to(p) for c, p in zip(keep, tg[1:])], meter.to(0.3), run_time=0.9)
            self.remove(*old)
            lvl["v"] = 0.3
            self.wait_until(v.cue("plan") - 0.3)
            self.play(glow(panel.frame, PLAN, 7), run_time=0.6)
            self.wait_until(v.cue("survives") - 0.3)
            self.play(FadeIn(survives, shift=UP * 0.06), run_time=0.4)

        with self.say("s09_10") as v:
            self.wait_until(v.cue("next") - 0.8)
            plan("step 5: in progress", "status", "s4", ACTIVE, extra=[FadeOut(survives)])
            self.wait_until(v.cue("edit") - 0.5)
            ask_model(calln("edit_file", '"contact.html"'))
            result(res("File updated."), "evaluate")
            self.wait_until(v.cue("done") - 0.9)
            plan("step 5: done", "status", "s4", DONE)

        with self.say("s09_11") as v:
            self.wait_until(v.cue("last") - 0.8)
            plan("step 6: in progress", "status", "s5", ACTIVE)
            self.wait_until(v.cue("tests") - 0.5)
            ask_model(calln("run_command", '"run tests"'))
            self.wait_until(v.cue("fails") - 0.3)
            fail = res_msg("1 test failed: message not saved when the name is empty", width=FW, size=12, color=RED)
            result(fail, "evaluate")
            self.play(glow(fail.frame, RED, 5), run_time=0.4)

        stays = Pill(caps("still in progress", 11, AMBER), AMBER, pad_x=0.12, pad_y=0.04)
        with self.say("s09_12") as v:
            self.wait_until(v.cue("stays") - 0.3)
            stays.next_to(panel, DOWN, buff=0.18)
            self.play(FadeIn(stays, shift=UP * 0.05), glow(panel.row("s5").icon[0], AMBER, 5), run_time=0.5)
            self.wait_until(v.cue("fixes") - 0.5)
            ask_model(calln("edit_file", '"contact.html"'))
            result(res("File updated."))
            self.wait_until(v.cue("runs") - 0.5)
            ask_model(calln("run_command", '"run tests"'))

        with self.say("s09_13") as v:
            self.wait_until(v.cue("all") - 0.3)
            ok = res("All tests passed ✓", TEAL)
            result(ok, "evaluate")
            self.wait_until(v.cue("done") - 0.9)
            self.play(FadeOut(stays), run_time=0.2)
            plan("step 6: done", "status", "s5", DONE)
            self.wait_until(v.cue("evidence") - 0.4)
            link2 = EvidenceLink(panel.row("s5"), ok, bend=0.4)
            self.play(link2.draw(0.6), run_time=0.6)

        final = SizedCard("assistant", "The contact form is ready. It saves every message to messages.txt and shows a thank-you "
                          "note. All tests pass.", width=FW, height=0.62, size=12, wrap=44)
        notool = Pill(caps("final answer · no tool call", 11, BLUE), BLUE, pad_x=0.12, pad_y=0.04)
        with self.say("s09_14") as v:
            self.wait_until(v.cue("final") - 0.5)
            self.play(FadeOut(link2), run_time=0.2)
            self.play(bundle_anim(model, [panel], run_time=0.4), *loop.focus("evaluate"), run_time=0.4)
            self.play(*feed.push(final), run_time=0.45)
            notool.next_to(model, DOWN, buff=0.12)
            self.play(FadeIn(notool, shift=UP * 0.05), *loop.all_normal(), run_time=0.4)

        items = ["Form page", "Saves every message", "Thank-you note"]
        rows = VGroup()
        for t in items:
            box = RoundedRectangle(width=0.42, height=0.42, corner_radius=0.08).set_stroke(TEAL, 1.5)
            rows.add(VGroup(bn(t, 21, FG), VGroup(box, I.check_icon(0.26, TEAL).move_to(box))))
        lw = max(r[0].width for r in rows)
        for i, r in enumerate(rows):
            r[0].move_to([0, -i * 0.66, 0], aligned_edge=LEFT)
            r[1].move_to([lw + 0.6, -i * 0.66, 0])
        head = caps("what rahul asked for", 13, MUTED).next_to(rows, UP, buff=0.3, aligned_edge=LEFT)
        check = VGroup(head, rows).move_to([FEED_X + FW / 2, 0.1, 0])
        veil = BackgroundRectangle(VGroup(*feed.cards), color=BG, fill_opacity=0.92, buff=0.1)
        with self.say("s09_15") as v:
            self.wait_until(v.cue("form") - 0.6)
            self.play(FadeIn(veil), FadeIn(head), run_time=0.4)
            for i, cue in enumerate(("form", "saves", "thank")):
                self.wait_until(v.cue(cue) - 0.2)
                self.play(FadeIn(rows[i][0], shift=RIGHT * 0.08), FadeIn(rows[i][1][0]), run_time=0.25)
                self.play(FadeIn(rows[i][1][1], scale=1.4), run_time=0.25)

        def attempt(x, ticks, with_plan, label):
            m = ModelBox(2.0, 1.15, label_size=15).move_to([x, 1.0, 0])
            same = Pill(caps("same model", 12, BLUE), BLUE, pad_x=0.14, pad_y=0.05).next_to(m, UP, buff=0.15)
            marks = VGroup()
            for ok in ticks:
                marks.add(I.check_icon(0.3, TEAL) if ok else I.cross_icon(0.3, RED))
            marks.arrange(RIGHT, buff=0.35).next_to(m, DOWN, buff=0.45)
            lab = caps(label, 13, MUTED).next_to(marks, DOWN, buff=0.3)
            g = VGroup(m, same, marks, lab)
            if with_plan:
                p = VGroup(plan_icon(0.5), caps("+ a plan", 12, PLAN)).arrange(DOWN, buff=0.08).next_to(m, RIGHT, buff=0.35)
                g.add(p)
            return g

        left = attempt(-3.4, [True, False, False], False, "the first attempt")
        right = attempt(3.0, [True, True, True], True, "with a plan")
        with self.say("s09_16") as v:
            self.wait_until(v.cue("same") - 0.4)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.5)
            self.play(FadeIn(left, shift=UP * 0.08), FadeIn(right, shift=UP * 0.08), run_time=0.7)
            self.wait_until(v.cue("smarter") - 0.3)
            self.play(glow(left[0].frame, BLUE, 5), glow(right[0].frame, BLUE, 5), run_time=0.6)
            self.wait_until(v.cue("view") - 0.4)
            self.play(glow(right[4][0][0], PLAN, 6), pulse(right[4], 1.1), run_time=0.7)
        self.wait(0.4)
        self.clear_all(0.6)
