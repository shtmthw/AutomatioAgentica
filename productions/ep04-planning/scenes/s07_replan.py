"""07 · Replanning: the plan is a best guess written before the work began. On step 3 a search finds
no storage; the model asks update_plan to add a step (the harness applies it: 6 steps). A choice it
should not make alone: it asks Rahul. A step that would be removed. Add / change / remove: a guide,
not a script. Two failures: never replanning, always replanning."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *

PANEL_C = np.array([-4.65, 0.5, 0])
MODEL_C = np.array([-0.05, 2.35, 0])
FEED_X, FEED_TOP, FEED_BOTTOM = 2.5, 2.75, -2.65
FW = 4.25


def calln(tool, arg, width=FW):
    return call_msg(tool, arg, width=width, size=12)


def start_state():
    st = plan_state()
    st.set_status("s1", DONE)
    st.set_status("s2", DONE)
    st.set_status("s3", ACTIVE)
    return st


class S07Replan(VoiceScene):
    SECTION = "s07"

    def construct(self):
        self.show_chapter()
        panel = PlanPanel(start_state(), width=4.2, size=14, rows=6, row_h=0.38).move_to(PANEL_C)
        counter = StepCounter(panel.state).move_to([PANEL_C[0], -2.25, 0])
        panel.counter = counter
        model = ModelBox(1.75, 0.9, label_size=14).move_to(MODEL_C)
        feed = Feed(FEED_X, FEED_TOP, FEED_BOTTOM, gap=0.08)

        truth = VGroup(caps("remember", 12, MUTED), bn("The plan was written", 20, FG), bn("before the work began.", 20, FG))
        truth.arrange(DOWN, buff=0.1).move_to([0, 0.55, 0])
        guess = Pill(caps("a best guess", 13, AMBER), AMBER, pad_x=0.16, pad_y=0.06).move_to([0, -0.6, 0])
        news = VGroup(*[SizedCard("tool", content=code_block(1.2, 1, size=0.03, color=TEAL, seed=i), width=2.0, height=0.26)
                        for i in range(3)]).arrange(DOWN, buff=0.08).move_to([0, -1.6, 0])
        news_l = caps("new facts", 11, TEAL).next_to(news, DOWN, buff=0.1)
        with self.say("s07_01") as v:
            self.wait_until(v.cue("written") - 0.5)
            self.play(FadeIn(panel, shift=RIGHT * 0.1), FadeIn(counter), FadeIn(model, scale=0.94), run_time=0.7)
            self.play(FadeIn(truth, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("looked") - 0.3)
            self.play(glow(panel.frame, PLAN, 5), run_time=0.5)
            self.wait_until(v.cue("guess") - 0.3)
            self.play(FadeIn(guess, scale=0.9), run_time=0.4)
            self.wait_until(v.cue("tool") - 0.3)
            self.play(LaggedStart(*[FadeIn(n, shift=UP * 0.1) for n in news], lag_ratio=0.2), FadeIn(news_l), run_time=0.8)

        d = VGroup(en("Replanning", 26, PLAN, italic=False, weight=NORMAL),
                   bn("changing the plan because of", 17, FG), bn("what the agent has learned", 17, FG))
        d.arrange(DOWN, buff=0.1).move_to([0, 0.2, 0])
        dbox = SurroundingRectangle(d, buff=0.22, corner_radius=0.14).set_stroke(PLAN, 1.6)
        with self.say("s07_02") as v:
            self.wait_until(v.cue("changing") - 0.3)
            self.play(FadeOut(truth), FadeOut(guess), FadeOut(news), FadeOut(news_l), run_time=0.4)
            self.play(FadeIn(d[1:], shift=UP * 0.06), run_time=0.5)
            self.wait_until(v.cue("replanning") - 0.3)
            self.play(FadeIn(d[0], shift=DOWN * 0.06), Create(dbox), run_time=0.6)

        s1 = calln("run_command", '"search for where data is stored"')
        r1 = res_msg("No storage found in this project.", width=FW, size=12, color=AMBER)
        with self.say("s07_03") as v:
            self.wait_until(v.cue("three") - 0.3)
            self.play(FadeOut(d), FadeOut(dbox), glow(panel.row("s3").bg.copy().set_stroke(PLAN, 1), PLAN, 6),
                      glow(counter.frame, PLAN, 5), run_time=0.6)
            self.wait_until(v.cue("calls") - 0.6)
            self.play(bundle_anim(model, [panel], run_time=0.55), run_time=0.55)
            self.play(*feed.push(s1, shift=LEFT * 0.15), run_time=0.4)

        assumed = Pill(VGroup(I.warn_icon(0.18, AMBER), caps("assumed a place to save", 11, AMBER)).arrange(RIGHT, buff=0.08),
                       AMBER, pad_x=0.12, pad_y=0.04)
        with self.say("s07_04") as v:
            self.wait_until(v.cue("result") - 0.3)
            self.play(*feed.push(r1), run_time=0.4)
            self.play(glow(r1.frame, AMBER, 5), run_time=0.5)
            self.wait_until(v.cue("assumed") - 0.3)
            assumed.move_to([0, -0.3, 0])
            arr = arrow(assumed.get_left() + LEFT * 0.05, panel.row("s3").bg.get_right() + RIGHT * 0.1, color=AMBER, tip=0.1)
            self.play(FadeIn(assumed, shift=LEFT * 0.08), GrowArrow(arr), run_time=0.5)

        c_add = plan_call("add before step 3: " + NEW_STEP, width=FW, size=12)
        with self.say("s07_05") as v:
            self.wait_until(v.cue("calls") - 0.6)
            self.play(bundle_anim(model, [panel, *feed.cards[-2:]], run_time=0.55), FadeOut(assumed), FadeOut(arr),
                      run_time=0.55)
            self.play(*feed.push(c_add, shift=LEFT * 0.15), run_time=0.4)
            self.wait_until(v.cue("create") - 0.3)
            self.play(glow(c_add.outline, BLUE, 5), run_time=0.5)

        with self.say("s07_06") as v:
            self.wait_until(v.cue("applies") - 0.5)
            panel.apply(self, c_add, "add", "n1", NEW_STEP, before="s3", status=ACTIVE, demote="s3")
            self.wait_until(v.cue("six") - 0.3)
            self.play(glow(counter.frame, PLAN, 6), pulse(counter, 1.08), run_time=0.6)
            self.wait_until(v.cue("continues") - 0.3)
            self.play(bundle_anim(model, [panel], run_time=0.6), run_time=0.6)

        # a choice the agent should not make alone
        opt_a = VGroup(I.file_icon(0.55, TEAL), en("a simple file", 17, FG)).arrange(DOWN, buff=0.12)
        opt_b = VGroup(VGroup(I.database_icon(0.55, AMBER), I.gear(0.3, AMBER)).arrange(RIGHT, buff=0.08),
                       en("a database", 17, FG), caps("needs new software", 10, AMBER)).arrange(DOWN, buff=0.1)
        opts = VGroup(opt_a, opt_b).arrange(RIGHT, buff=0.7, aligned_edge=UP).move_to([0, -0.3, 0])
        orr = en("or", 16, MUTED).move_to(opts.get_center() + UP * 0.25)
        alone = caps("not the agent's call alone", 12, MUTED).next_to(opts, UP, buff=0.35)
        with self.say("s07_07") as v:
            self.wait_until(v.cue("alone") - 0.3)
            self.play(FadeIn(alone), run_time=0.4)
            self.wait_until(v.cue("file") - 0.3)
            self.play(FadeIn(opt_a, shift=UP * 0.08), FadeIn(orr), run_time=0.45)
            self.wait_until(v.cue("database") - 0.3)
            self.play(FadeIn(opt_b, shift=UP * 0.08), run_time=0.45)

        ask = SizedCard("assistant", "Should I store messages in a simple file, or set up a database?", width=FW, height=0.5,
                        size=12, wrap=40)
        no_call = caps("a question, not a tool call", 10, BLUE).next_to(model, DOWN, buff=0.1)
        with self.say("s07_08") as v:
            self.wait_until(v.cue("asks") - 0.6)
            self.play(bundle_anim(model, [panel, *feed.cards[-2:]], run_time=0.55), run_time=0.55)
            self.wait_until(v.cue("should") - 0.3)
            self.play(*feed.push(ask, shift=LEFT * 0.15), FadeIn(no_call), run_time=0.5)

        pause = pause_icon(0.3, AMBER).next_to(model, LEFT, buff=0.2)
        paused = caps("paused", 11, AMBER).next_to(pause, DOWN, buff=0.08)
        rahul = VGroup(I.user_icon(0.3, FG), en("Rahul", 13, FG)).arrange(RIGHT, buff=0.08)
        ans = SizedCard("user", "A simple file is fine.", width=FW, height=0.3, size=12)
        with self.say("s07_09") as v:
            self.wait_until(v.cue("pauses") - 0.3)
            self.play(FadeIn(pause, scale=0.8), FadeIn(paused), FadeOut(no_call), run_time=0.4)
            self.wait_until(v.cue("rahul") - 0.3)
            self.play(*feed.push(ans), run_time=0.45)
            rahul.next_to(ans, LEFT, buff=0.15)
            self.play(FadeIn(rahul, shift=RIGHT * 0.06), run_time=0.3)
            self.wait_until(v.cue("simple") - 0.2)
            self.play(glow(opt_a[0], TEAL, 6), opt_b.animate.fade(0.7), FadeOut(pause), FadeOut(paused), run_time=0.6)

        # a step that is not needed (a "what if")
        wi = Pill(caps("what if", 12, MUTED), DIM, pad_x=0.14, pad_y=0.05)
        mini = PlanPanel(panel.state, width=4.2, size=13, rows=1, row_h=0.4, sub=None, visible=["s4"]).move_to([0, -1.0, 0])
        hyp = VGroup(I.check_icon(0.18, MUTED), bn("site already shows a thank-you note", 13, MUTED)).arrange(RIGHT, buff=0.1)
        c_rm = plan_call("remove step 5", width=3.2, size=12)
        with self.say("s07_10") as v:
            self.wait_until(v.cue("if") - 0.4)
            self.play(*[FadeOut(m) for m in (opts, orr, alone, rahul)], run_time=0.4)
            wi.move_to([0, 1.25, 0])
            hyp.next_to(wi, DOWN, buff=0.15)
            self.play(FadeIn(wi), FadeIn(hyp, shift=UP * 0.05), FadeIn(mini, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("ask") - 0.3)
            c_rm.next_to(mini, UP, buff=0.18)
            self.play(FadeIn(c_rm, shift=DOWN * 0.08), run_time=0.4)
            self.wait_until(v.cue("remove") - 0.3)
            mini.apply(self, c_rm, "remove", "s4", fast=True)

        ops = VGroup(*[Pill(VGroup(en(sym, 20, PLAN, italic=False, weight=NORMAL), en(t, 17, FG)).arrange(RIGHT, buff=0.1), PLAN,
                            pad_x=0.18, pad_y=0.06) for sym, t in (("+", "add"), ("~", "change"), ("−", "remove"))])
        ops.arrange(RIGHT, buff=0.2).move_to([0, 0.6, 0])
        guide = Pill(VGroup(I.check_icon(0.2, PLAN), en("a guide", 22, FG)).arrange(RIGHT, buff=0.12), PLAN, pad_x=0.22)
        script = Pill(VGroup(I.cross_icon(0.2, RED), en("a script", 22, MUTED)).arrange(RIGHT, buff=0.12), RED, pad_x=0.22)
        gs = VGroup(guide, script).arrange(DOWN, buff=0.18).move_to([0, -0.9, 0])
        with self.say("s07_11") as v:
            self.wait_until(v.cue("add") - 0.4)
            self.play(*[FadeOut(m) for m in (wi, hyp, mini, c_rm)], run_time=0.4)
            for i, cue in enumerate(("add", "change", "remove")):
                self.wait_until(v.cue(cue) - 0.2)
                self.play(FadeIn(ops[i], shift=UP * 0.06), run_time=0.3)
            self.wait_until(v.cue("guide") - 0.3)
            self.play(FadeIn(guide, shift=UP * 0.06), run_time=0.4)
            self.wait_until(v.cue("script") - 0.3)
            self.play(FadeIn(script, shift=UP * 0.06), run_time=0.4)

        # two failures to avoid
        divider = DashedLine([0, 2.6, 0], [0, -2.6, 0], dash_length=0.08).set_stroke(FAINT, 1.6)
        h1 = VGroup(caps("never replanning", 15, RED)).move_to([-3.5, 2.55, 0])
        h2 = VGroup(caps("always replanning", 15, RED)).move_to([3.5, 2.55, 0])
        avoid = caps("avoid", 13, MUTED).move_to([0, 3.0, 0])
        path_l = VGroup(*[Circle(radius=0.11).set_stroke(PLAN, 1.8) for _ in range(4)]).arrange(RIGHT, buff=0.7)
        path_l.move_to([-4.0, 0.0, 0])
        rail = Line(path_l[0].get_center(), path_l[-1].get_center() + RIGHT * 0.9).set_stroke(PLAN, 2, opacity=0.5)
        wall = VGroup(*[Rectangle(width=0.32, height=0.22).set_stroke(RED, 1.5).set_fill(RED, 0.15) for _ in range(12)])
        wall.arrange_in_grid(rows=6, cols=2, buff=0.02).move_to([-1.3, 0.0, 0])
        tok = Token(TEAL, 0.1).move_to(path_l[0])
        broken = caps("broken plan", 11, MUTED).next_to(path_l, DOWN, buff=0.25)
        with self.say("s07_12") as v:
            self.wait_until(v.cue("avoid") - 0.4)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.5)
            self.play(Create(divider), FadeIn(avoid), run_time=0.4)
            self.wait_until(v.cue("never") - 0.3)
            self.play(FadeIn(h1, shift=DOWN * 0.06), FadeIn(path_l), Create(rail), FadeIn(broken), FadeIn(wall), FadeIn(tok),
                      run_time=0.6)
            self.wait_until(v.cue("wall") - 1.2)
            self.play(tok.animate.move_to(wall.get_left() + LEFT * 0.12), run_time=1.0, rate_func=rush_into)
            self.play(Wiggle(wall, scale_value=1.03), tok.animate.set_color(RED), run_time=0.5)

        papers = VGroup(*[paper(0.9, 1.1, 4).rotate(0.08 * (i - 1)) for i in range(3)])
        for i, pp in enumerate(papers):
            pp.move_to([3.1 + 0.12 * i, 0.3 - 0.06 * i, 0])
        bar = RoundedRectangle(width=3.0, height=0.2, corner_radius=0.1).set_stroke(DIM, 1.4).move_to([3.5, -1.25, 0])
        prog = caps("progress: 0", 11, RED).next_to(bar, DOWN, buff=0.12)
        rew = caps("rewritten again", 11, AMBER).next_to(papers, UP, buff=0.2)
        with self.say("s07_13") as v:
            self.wait_until(v.cue("always") - 0.3)
            self.play(FadeIn(h2, shift=DOWN * 0.06), FadeIn(papers[0]), Create(bar), FadeIn(prog), run_time=0.5)
            self.wait_until(v.cue("rewrites") - 0.3)
            self.play(FadeIn(rew), run_time=0.3)
            for i in range(1, 3):
                self.play(FadeIn(papers[i], shift=DOWN * 0.15), papers[i - 1].animate.fade(0.6), run_time=0.4)
            self.wait_until(v.cue("progress") - 0.3)
            self.play(glow(bar, RED, 5), Wiggle(prog), run_time=0.6)
        self.wait(0.4)
        self.clear_all(0.6)
