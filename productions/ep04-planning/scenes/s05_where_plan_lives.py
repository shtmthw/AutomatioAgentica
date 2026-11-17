"""05 · Where does the plan live? As an old message it is trimmed out of the context window and
lost; instead the harness gives the model an update_plan tool and keeps the plan in the PLAN PANEL,
sending it with every call. Why that is better (survives, current, visible to Rahul), and the
same pattern as memory."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *

HF_C = np.array([0.0, -0.05, 0])
PANEL_C = np.array([-4.45, -0.32, 0])
MODEL_C = np.array([-0.05, 1.45, 0])
FEED_X, FEED_TOP, FEED_BOTTOM = 2.35, 2.2, -2.5
FW = 4.15


def phase_dots(n=5, color=AMBER):
    dots = VGroup()
    for i in range(n):
        c = Circle(radius=0.17).set_stroke(DIM, 1.5).set_fill(BG, 1)
        t = en(str(i + 1), 15, DIM, italic=False, weight=NORMAL).move_to(c)
        dots.add(VGroup(c, t))
    dots.arrange(RIGHT, buff=0.16)
    lab = caps("how it works", 12, MUTED)
    return VGroup(lab, dots).arrange(RIGHT, buff=0.22)


def go_phase(tr, i, color=AMBER):
    anims = []
    for j, d in enumerate(tr[1]):
        if j < i:
            anims += [d[0].animate.set_stroke(MUTED).set_fill(MUTED, 0.25), d[1].animate.set_color(MUTED)]
        elif j == i:
            anims += [d[0].animate.set_stroke(color).set_fill(color, 0.25), d[1].animate.set_color(color)]
    return anims


def work_card(i):
    if i % 2 == 0:
        return ToolCallMsg(("read_file", "edit_file", "run_command")[i % 3], '"…"', width=FW, size=12, height=0.3)
    return SizedCard("tool", content=code_block(2.2, 1, size=0.032, color=TEAL, seed=i), width=FW, height=0.62)


class S05WherePlanLives(VoiceScene):
    SECTION = "s05"

    def construct(self):
        self.show_chapter()
        # ---- A. the plan as an old message is trimmed away
        ctx = LiveContext([-3.1, -0.15, 0], 4.3, 5.1, label="CONTEXT WINDOW", label_size=13)
        cw = 4.3 - 0.32
        # the meter is computed from the drawn height of the cards (LiveContext default), so it always matches the picture
        sysm = SizedCard("system", "You are a coding agent.", width=cw, height=0.3, size=12)
        user = SizedCard("user", "Add a contact form… thank-you note.", width=cw, height=0.3, size=12)
        plines = VGroup(*[bn(f"{i + 1}. {s}", 10.5, FG) for i, s in enumerate(STEPS)]).arrange(DOWN, buff=0.05,
                                                                                               aligned_edge=LEFT)
        planm = SizedCard("assistant", content=plines, width=cw, height=plines.height + 0.2, label="plan")
        with self.say("s05_01") as v:
            self.wait_until(v.cue("where") - 0.3)
            self.play(*ctx.appear(), run_time=0.6)
            self.play(*ctx.add(sysm), run_time=0.3)
            self.play(*ctx.add(user), run_time=0.3)
            self.wait_until(v.cue("assistant") - 0.3)
            self.play(*ctx.add(planm), run_time=0.5)
            self.wait_until(v.cue("early") - 0.2)
            self.play(glow(planm.frame, BLUE, 5), run_time=0.5)

        def filler(i):
            if i % 2 == 0:
                return SizedCard("assistant", content=code_block(1.8, 1, size=0.03, color=BLUE, seed=i), width=cw, height=0.22,
                                 dashed=True, tag_size=9)
            return SizedCard("tool", content=code_block(2.1, 1, size=0.03, color=TEAL, seed=i + 3), width=cw, height=0.22,
                             tag_size=9)

        with self.say("s05_02") as v:
            self.wait_until(v.cue("grows") - 0.3)
            for i in range(9):
                c = filler(i)
                self.play(*ctx.add(c, shift=DOWN * 0.12), run_time=0.24)
            self.wait_until(v.cue("fills") - 0.3)
            for i in range(2):
                c = filler(9 + i)
                self.play(*ctx.add(c, shift=DOWN * 0.12), run_time=0.3)

        gone = Pill(VGroup(I.warn_icon(0.24, RED), caps("the plan is gone", 14, RED)).arrange(RIGHT, buff=0.1), RED, pad_x=0.2,
                    pad_y=0.07).move_to([2.3, 1.95, 0])
        model = ModelBox(1.8, 1.05, label_size=15).move_to([3.4, 0.35, 0])
        wander = VMobject().set_points_smoothly([model.get_bottom() + DOWN * 0.1, [2.4, -0.9, 0], [3.9, -1.4, 0],
                                                 [2.9, -2.1, 0], [4.7, -2.3, 0]])
        wander = DashedVMobject(wander.set_stroke(AMBER, 2), num_dashes=22)
        lost_q = en("?", 34, AMBER, italic=False).move_to([5.1, -2.2, 0])
        drift = caps("drifts", 13, AMBER).next_to(lost_q, UP, buff=0.12)
        with self.say("s05_03") as v:
            self.wait_until(v.cue("trimmed") - 0.3)
            self.play(*ctx.remove([user], shift=LEFT * 0.6), *ctx.relayout(), run_time=0.6)
            self.wait_until(v.cue("slides") - 0.3)
            self.play(*ctx.remove([planm], shift=LEFT * 0.8), run_time=0.9)
            self.play(*ctx.relayout(), run_time=0.4)
            self.wait_until(v.cue("gone") - 0.3)
            self.play(FadeIn(gone, scale=0.9), FadeIn(model, scale=0.94), run_time=0.4)
            self.wait_until(v.cue("drifts") - 0.6)
            self.play(Create(wander), FadeIn(lost_q), FadeIn(drift), run_time=0.8)

        # ---- B. the harness keeps the plan and gives the model a tool for it
        hf = HarnessFrame(13.7, 5.45, label_size=17).move_to(HF_C)
        panel = PlanPanel(PlanState(GOAL, []), width=4.25, size=14, rows=6, row_h=0.38, empty=True).move_to(PANEL_C)
        model2 = ModelBox(2.0, 1.15, label_size=16).move_to(MODEL_C)
        not_msg = caps("not just another old message", 13, MUTED).move_to([2.2, -1.5, 0])
        with self.say("s05_04") as v:
            self.wait_until(v.cue("shouldn") - 0.4)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.6)
            self.play(FadeIn(not_msg), run_time=0.3)
            self.wait_until(v.cue("harness") - 0.3)
            self.play(FadeIn(hf), FadeIn(model2, scale=0.94), FadeOut(not_msg), run_time=0.7)
            self.wait_until(v.cue("tool") - 0.3)
            self.play(FadeIn(panel, shift=RIGHT * 0.1), run_time=0.6)

        tr = phase_dots().move_to([4.4, 3.05, 0])
        feed = Feed(FEED_X, FEED_TOP, FEED_BOTTOM, gap=0.08)
        u = SizedCard("user", "Add a contact form to my website. It should save every message and show a thank-you note.",
                      width=FW, height=0.5, size=12, wrap=44)
        tools = tools_stack(2.6, 13, plan=False).move_to([-0.05, -0.35, 0])
        upd = tool_desc_card("update_plan", width=3.9, size=14, new=True).move_to([-0.05, -1.7, 0])
        with self.say("s05_05") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(FadeIn(tr, shift=DOWN * 0.06), *go_phase(tr, 0), run_time=0.5)
            self.wait_until(v.cue("goal") - 0.3)
            self.play(*feed.push(u), run_time=0.5)
            self.wait_until(v.cue("passes") - 0.3)
            self.play(FadeIn(tools, shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("tools") - 0.3)
            send_bundle(self, model2, [u, tools], run_time=0.6)

        new_rows = VGroup(*tools.rows, mono("update_plan", 13, PLAN))
        with self.say("s05_06") as v:
            self.wait_until(v.cue("new") - 0.3)
            self.play(FadeIn(upd, shift=UP * 0.1), run_time=0.5)
            self.play(glow(upd.frame, PLAN, 6), run_time=0.5)
            self.wait_until(v.cue("creates") - 0.2)
            self.play(Circumscribe(upd[1][1], color=PLAN, stroke_width=1.4, buff=0.04, time_width=0.6), run_time=1.0)
            self.wait_until(v.cue("example") - 0.3)
            ex = Pill(caps("example name", 11, MUTED), DIM, pad_x=0.12, pad_y=0.04).next_to(upd, DOWN, buff=0.1)
            self.play(FadeIn(ex, shift=UP * 0.05), run_time=0.4)

        inp = VGroup(*[bn(f"{i + 1}. {s}", 11, FG) for i, s in enumerate(STEPS)]).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
        call = ToolCallCard("update_plan", inp, width=FW, size=14, label_w=0.95)
        with self.say("s05_07") as v:
            self.wait_until(v.cue("two") - 0.3)
            self.play(*go_phase(tr, 1), model2.think(0.6), run_time=0.5)
            self.wait_until(v.cue("call") - 0.3)
            self.play(*feed.push(call, shift=LEFT * 0.15), run_time=0.6)
            self.wait_until(v.cue("tool") - 0.2)
            self.play(glow(call.values[0], BLUE, 4), run_time=0.4)
            self.wait_until(v.cue("input") - 0.2)
            self.play(LaggedStart(*[glow(l, BLUE, 3, 0.4) for l in inp], lag_ratio=0.12), run_time=0.8)

        with self.say("s05_08") as v:
            self.wait_until(v.cue("three") - 0.3)
            self.play(*go_phase(tr, 2), glow(hf.frame, AMBER, 5), run_time=0.5)
            self.wait_until(v.cue("goal") - 0.4)
            panel.apply(self, call, "create", STEPS)
            self.wait_until(v.cue("none") - 0.3)
            self.play(LaggedStart(*[glow(panel.row(f"s{i + 1}").icon[0], MUTED, 4, 0.5) for i in range(5)], lag_ratio=0.1),
                      run_time=0.8)

        saved = SizedCard("tool", "Plan saved.", width=FW, height=0.32, size=13)
        with self.say("s05_09") as v:
            self.wait_until(v.cue("four") - 0.3)
            self.play(*go_phase(tr, 3), run_time=0.4)
            self.wait_until(v.cue("saved") - 0.4)
            self.play(*feed.push(saved), run_time=0.5)

        sent = caps("sent on every call", 12, MUTED).next_to(model2, UP, buff=0.14)
        legend = VGroup(*[Pill(caps(t, 11, c), c, pad_x=0.12, pad_y=0.04) for t, c in
                          (("messages", FG), ("tools", TEAL), ("plan", PLAN))]).arrange(RIGHT, buff=0.12)
        legend.next_to(model2, RIGHT, buff=0.25).shift(UP * 0.0)
        legend.move_to([-0.05, 0.45, 0])
        with self.say("s05_10") as v:
            self.wait_until(v.cue("five") - 0.3)
            self.play(*go_phase(tr, 4), FadeIn(sent), run_time=0.4)
            self.wait_until(v.cue("messages") - 0.3)
            self.play(FadeIn(legend[0], shift=UP * 0.05), run_time=0.25)
            self.wait_until(v.cue("tools") - 0.3)
            self.play(FadeIn(legend[1], shift=UP * 0.05), run_time=0.25)
            self.wait_until(v.cue("plan") - 0.4)
            self.play(FadeIn(legend[2], shift=UP * 0.05), run_time=0.25)
            send_bundle(self, model2, [*feed.cards, VGroup(tools, upd), panel], run_time=0.8)

        # ---- C. why this is better
        whys = VGroup(*[Pill(VGroup(en(str(i + 1), 15, PLAN, italic=False, weight=NORMAL), en(t, 16, FG)).arrange(RIGHT, buff=0.1),
                             PLAN, pad_x=0.16, pad_y=0.06) for i, t in enumerate(("it survives", "always current",
                                                                                   "Rahul sees it"))])
        whys.arrange(RIGHT, buff=0.2).move_to([3.6, 3.05, 0])
        untouched = Pill(VGroup(I.check_icon(0.18, PLAN), caps("untouched", 12, PLAN)).arrange(RIGHT, buff=0.08), PLAN,
                         pad_x=0.14, pad_y=0.05)
        untouched.next_to(panel.frame, UP, buff=0.08, aligned_edge=RIGHT)
        with self.say("s05_11") as v:
            self.wait_until(v.cue("better") - 0.3)
            self.play(FadeOut(tr), FadeOut(legend), FadeOut(sent), run_time=0.4)
            self.wait_until(v.cue("survives") - 0.3)
            self.play(FadeIn(whys[0], shift=DOWN * 0.06), run_time=0.4)
            self.wait_until(v.cue("trimmed") - 0.3)
            for i in range(6):
                self.play(*feed.push(work_card(i)), run_time=0.3)
            self.wait_until(v.cue("untouched") - 0.3)
            self.play(FadeIn(untouched, scale=0.9), glow(panel.frame, PLAN, 6), run_time=0.5)
            self.wait_until(v.cue("separately") - 0.3)
            self.play(glow(hf.frame, AMBER, 5), pulse(panel, 1.02), run_time=0.6)

        screen = Window(3.9, 3.3, "Rahul's screen", color=DIM).move_to([4.45, -0.6, 0])
        mini = panel.snapshot().scale(0.62).move_to(screen.get_center() + DOWN * 0.15)
        rah = VGroup(I.user_icon(0.36, FG), en("Rahul", 15, FG)).arrange(RIGHT, buff=0.1).next_to(screen, UP, buff=0.12)
        with self.say("s05_12") as v:
            self.wait_until(v.cue("current") - 0.3)
            self.play(FadeIn(whys[1], shift=DOWN * 0.06), run_time=0.4)
            self.wait_until(v.cue("latest") - 0.3)
            send_bundle(self, model2, [panel], run_time=0.6, scale=0.35)
            self.wait_until(v.cue("rahul") - 0.4)
            self.play(FadeIn(whys[2], shift=DOWN * 0.06), *feed.clear(), run_time=0.5)
            self.play(FadeIn(screen), FadeIn(rah, shift=DOWN * 0.06), run_time=0.5)
            self.wait_until(v.cue("progress") - 0.4)
            self.play(TransformFromCopy(panel, mini), run_time=0.8)

        nb = Notebook(0.85, sub="memory").move_to([-0.05, -1.25, 0])
        same = VGroup(caps("same idea", 13, VIOLET), en("saved outside, sent back in", 17, FG)).arrange(DOWN, buff=0.08)
        same.move_to([-0.05, 0.25, 0])
        a_p = arrow(panel.frame.get_right() + UP * 1.3 + RIGHT * 0.05, model2.in_port + LEFT * 0.08, color=PLAN, tip=0.12)
        with self.say("s05_13") as v:
            self.wait_until(v.cue("pattern") - 0.4)
            self.play(FadeOut(tools), FadeOut(upd), FadeOut(ex), FadeOut(untouched), run_time=0.4)
            self.wait_until(v.cue("remember") - 0.3)
            self.play(model2.reset_flash(0.7), run_time=0.7)
            self.wait_until(v.cue("keeps") - 0.3)
            self.play(glow(panel.frame, PLAN, 6), run_time=0.5)
            self.wait_until(v.cue("back") - 0.3)
            self.play(GrowArrow(a_p), run_time=0.5)
            self.wait_until(v.cue("memory") - 0.4)
            self.play(FadeIn(nb, shift=UP * 0.08), FadeIn(same, shift=UP * 0.06), run_time=0.6)
        self.wait(0.6)
        self.clear_all(0.6)
