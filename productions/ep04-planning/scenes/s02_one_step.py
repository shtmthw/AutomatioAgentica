"""02 · Why one step at a time is not enough: the model picks only the next action; fine for a
small task, but on a big goal it forgets parts, works in the wrong order, and stops too early or
never; the cooking analogy; a person writes a list first."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *


def fail_tab(i, text):
    n = en(str(i), 22, RED, italic=False, weight=NORMAL)
    return Pill(VGroup(n, en(text, 18, FG)).arrange(RIGHT, buff=0.14), DIM, pad_x=0.2, pad_y=0.08)


def pot_icon(h=0.7, color=FG):
    body = RoundedRectangle(width=h * 1.3, height=h * 0.7, corner_radius=h * 0.12).set_stroke(color, 2).set_fill(PANEL, 1)
    lid = Line(LEFT * h * 0.75, RIGHT * h * 0.75).set_stroke(color, 2.2).next_to(body, UP, buff=0.04)
    knob = RoundedRectangle(width=h * 0.22, height=h * 0.1, corner_radius=0.03).set_stroke(color, 2).next_to(lid, UP, buff=0.02)
    handles = VGroup(Line(ORIGIN, LEFT * h * 0.18).set_stroke(color, 2).next_to(body, LEFT, buff=0),
                     Line(ORIGIN, RIGHT * h * 0.18).set_stroke(color, 2).next_to(body, RIGHT, buff=0))
    return VGroup(body, lid, knob, handles)


def flame(h=0.3, color=RED):
    f = VGroup(*[Triangle().scale_to_fit_height(h * s).set_stroke(color, 1.6).set_fill(color, 0.35) for s in (1.0, 0.7, 0.85)])
    f.arrange(RIGHT, buff=0.04)
    return f


def onion_icon(h=0.5, color=FG):
    c = Circle(radius=h / 2).set_stroke(color, 2)
    lines = VGroup(*[Arc(radius=h / 2 * r, start_angle=-PI / 2, angle=PI).set_stroke(color, 1.4, opacity=0.7)
                     .move_to(c.get_center() + RIGHT * h * 0.02 * i) for i, r in enumerate((0.7, 0.45))])
    knife = VGroup(Line(ORIGIN, RIGHT * h * 0.9).set_stroke(MUTED, 3),
                   RoundedRectangle(width=h * 0.45, height=h * 0.12, corner_radius=0.03).set_stroke(MUTED, 2))
    knife.arrange(RIGHT, buff=0).rotate(-0.5).next_to(c, UR, buff=-0.1)
    return VGroup(c, lines, knife)


def bowl_icon(h=0.5, color=TEAL):
    bowl = Arc(radius=h * 0.7, start_angle=PI, angle=PI).set_stroke(color, 2)
    rim = Line(bowl.get_left(), bowl.get_right()).set_stroke(color, 2)
    leaves = VGroup(*[Circle(radius=h * 0.16).set_stroke(color, 1.6).move_to(rim.get_center() + RIGHT * h * 0.3 * (i - 1)
                                                                            + UP * h * 0.12) for i in range(3)])
    return VGroup(bowl, rim, leaves)


class S02OneStep(VoiceScene):
    SECTION = "s02"

    def construct(self):
        self.show_chapter()
        W = 3.3
        msgs = [SizedCard("user", "Add a contact form…", width=W, height=0.3, size=12),
                ToolCallMsg("read_file", '"index.html"', width=W, size=12, height=0.3),
                SizedCard("tool", content=mono("<html> …", 11, FG), width=W, height=0.3),
                ToolCallMsg("edit_file", '"contact.html"', width=W, size=12, height=0.3)]
        VGroup(*msgs).arrange(DOWN, buff=0.07, aligned_edge=LEFT).move_to([-4.3, 0.3, 0])
        lab = caps("the conversation so far", 12, MUTED).next_to(VGroup(*msgs), UP, buff=0.18, aligned_edge=LEFT)
        model = ModelBox(2.0, 1.2, label_size=16).move_to([0.2, 0.3, 0])
        nxt = Pill(VGroup(caps("next action", 12, BLUE), mono("run_command", 15, FG)).arrange(RIGHT, buff=0.14), BLUE,
                   pad_x=0.2).move_to([4.35, 0.3, 0])
        a1 = arrow(VGroup(*msgs).get_right() + RIGHT * 0.15, model.in_port + LEFT * 0.1, color=MUTED, tip=0.12)
        a2 = arrow(model.out_port + RIGHT * 0.1, nxt.get_left() + LEFT * 0.1, color=MUTED, tip=0.12)
        one = caps("one step at a time", 14, FG).next_to(nxt, DOWN, buff=0.25)
        with self.say("s02_01") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(FadeIn(model, scale=0.94), run_time=0.5)
            self.wait_until(v.cue("each") - 0.3)
            self.play(FadeIn(lab), LaggedStart(*[FadeIn(m, shift=DOWN * 0.08) for m in msgs], lag_ratio=0.15), run_time=0.8)
            self.wait_until(v.cue("looks") - 0.3)
            self.play(GrowArrow(a1), send_anim(msgs, model), run_time=0.8)
            self.wait_until(v.cue("picks") - 0.3)
            self.play(GrowArrow(a2), FadeIn(nxt, shift=RIGHT * 0.15), run_time=0.5)
            self.play(FadeIn(one, shift=UP * 0.06), run_time=0.4)

        # small task: works well
        small = VGroup(SizedCard("user", "What port does the server use?", width=4.2, height=0.36, size=14),
                       ToolCallMsg("read_file", '"config.txt"', width=4.2, size=14, height=0.36),
                       SizedCard("tool", content=mono("port = 8080", 13, FG), width=4.2, height=0.36),
                       SizedCard("assistant", "The server uses port 8080.", width=4.2, height=0.36, size=14))
        small.arrange(DOWN, buff=0.08, aligned_edge=LEFT).move_to([0, -0.2, 0])
        small_tag = Pill(VGroup(I.check_icon(0.2, TEAL), caps("small task: works well", 13, TEAL)).arrange(RIGHT, buff=0.1),
                         TEAL, pad_x=0.18, pad_y=0.07).next_to(small, UP, buff=0.3)
        with self.say("s02_02") as v:
            self.wait_until(v.cue("small") - 0.4)
            self.play(*[FadeOut(m) for m in (lab, *msgs, a1, a2, nxt, one, model)], run_time=0.5)
            self.play(FadeIn(small_tag, shift=DOWN * 0.06), run_time=0.4)
            self.wait_until(v.cue("port") - 0.3)
            self.play(FadeIn(small[0], shift=DOWN * 0.08), run_time=0.4)
            self.wait_until(v.cue("read") - 0.3)
            self.play(FadeIn(small[1], shift=DOWN * 0.08), run_time=0.35)
            self.play(FadeIn(small[2], shift=DOWN * 0.08), run_time=0.35)
            self.wait_until(v.cue("answer") - 0.3)
            self.play(FadeIn(small[3], shift=DOWN * 0.08), run_time=0.4)

        tabs = VGroup(fail_tab(1, "forgets parts"), fail_tab(2, "wrong order"), fail_tab(3, "when is it finished?"))
        tabs.arrange(RIGHT, buff=0.35).move_to([0.6, 2.75, 0])
        big = caps("big goal", 14, RED).next_to(tabs, LEFT, buff=0.35)
        with self.say("s02_03") as v:
            self.wait_until(v.cue("big") - 0.3)
            self.play(FadeOut(small), FadeOut(small_tag), FadeIn(big), run_time=0.5)
            self.wait_until(v.cue("three") - 0.3)
            self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.08) for t in tabs], lag_ratio=0.25), run_time=0.9)

        def focus_tab(i):
            return [t.animate.set_opacity(1.0 if j == i else 0.35) for j, t in enumerate(tabs)]

        # 1. forgets parts of the goal
        parts = VGroup(*[Pill(VGroup(caps(f"part {i + 1}", 12, MUTED), en(t, 17, FG)).arrange(RIGHT, buff=0.12), FG,
                              pad_x=0.18, pad_y=0.07)
                         for i, t in enumerate(("form page", "save messages", "thank-you note"))]).arrange(RIGHT, buff=0.3)
        goal_lab = caps("goal", 13, FG)
        goal_g = VGroup(goal_lab, parts).arrange(RIGHT, buff=0.3).move_to([0, 1.65, 0])
        feed = Feed(-2.3, 1.0, -2.6, gap=0.06)
        with self.say("s02_04") as v:
            self.wait_until(v.cue("forgets") - 0.3)
            self.play(*focus_tab(0), FadeIn(goal_g, shift=DOWN * 0.08), run_time=0.6)
            self.wait_until(v.cue("grows") - 0.3)
            for i in range(10):
                c = (ToolCallMsg(("edit_file", "read_file")[i % 2], '"contact.html"', width=4.6, size=12, height=0.28)
                     if i % 2 == 0 else SizedCard("tool", content=VGroup(caps("part 1", 10, MUTED),
                                                                          code_block(1.6, 1, size=0.03, color=DIM)).arrange(
                         RIGHT, buff=0.2), width=4.6, height=0.28))
                self.play(*feed.push(c, shift=DOWN * 0.1), run_time=0.22)
                if i == 2:
                    self.play(glow(parts[0].frame, BLUE, 5), run_time=0.3)
            self.wait_until(v.cue("never") - 0.3)
            self.play(parts[1].animate.fade(0.75), parts[2].animate.fade(0.75), run_time=0.6)
            fg = VGroup(*[Pill(caps("forgotten", 11, RED), RED, pad_x=0.12, pad_y=0.04).next_to(p, DOWN, buff=0.1)
                          for p in parts[1:]])
            self.play(FadeIn(fg, shift=UP * 0.06), run_time=0.4)

        # 2. wrong order
        save_cards = VGroup(*[SizedCard("assistant", content=VGroup(caps("save messages", 10, BLUE),
                                                                    code_block(1.3, 1, size=0.03, color=BLUE, seed=i)).arrange(
            RIGHT, buff=0.2), width=3.6, height=0.32, dashed=True) for i in range(3)]).arrange(DOWN, buff=0.08)
        save_cards.move_to([-3.0, -0.2, 0])
        first = caps("written first", 12, MUTED).next_to(save_cards, UP, buff=0.18)
        look = SizedCard("tool", content=VGroup(caps("website", 10, TEAL), mono("uses a different setup", 12, FG)).arrange(
            RIGHT, buff=0.16), width=3.9, height=0.36).move_to([2.6, -0.2, 0])
        look_lab = caps("looked at later", 12, MUTED).next_to(look, UP, buff=0.18)
        trash = I.trash_icon(0.55, RED).move_to([-3.0, -2.1, 0])
        with self.say("s02_05") as v:
            self.wait_until(v.cue("order") - 0.3)
            self.play(*focus_tab(1), FadeOut(goal_g), FadeOut(fg), *feed.clear(), run_time=0.6)
            self.wait_until(v.cue("writes") - 0.3)
            self.play(FadeIn(first), LaggedStart(*[FadeIn(c, shift=DOWN * 0.08) for c in save_cards], lag_ratio=0.25),
                      run_time=0.9)
            self.wait_until(v.cue("looking") - 0.3)
            self.play(FadeIn(look_lab), FadeIn(look, shift=LEFT * 0.12), run_time=0.5)
            self.play(*[c.outline.animate.set_stroke(RED) for c in save_cards], run_time=0.4)
            self.wait_until(v.cue("thrown") - 0.4)
            self.play(FadeIn(trash, scale=0.8), run_time=0.3)
            self.play(LaggedStart(*[c.animate.move_to(trash).scale(0.2).set_opacity(0) for c in save_cards], lag_ratio=0.15),
                      FadeOut(first), run_time=0.9)

        # 3. stopping too early, or never
        la = LoopDiagram([-3.0, -0.35, 0], radius=1.0, node_w=0.96, node_h=0.42, name_size=14, meanings=False, goal=False)
        lb = LoopDiagram([3.0, -0.35, 0], radius=1.0, node_w=0.96, node_h=0.42, name_size=14, meanings=False, goal=False)
        early = Pill(VGroup(en("“Done!”", 18, RED), caps("too soon", 12, RED)).arrange(RIGHT, buff=0.12), RED, pad_x=0.18)
        early.move_to([-3.0, 1.55, 0])
        never = Pill(VGroup(en("polishing", 18, AMBER), en("∞", 22, AMBER, italic=False)).arrange(RIGHT, buff=0.12), AMBER,
                     pad_x=0.18).move_to([3.0, 1.55, 0])
        tb = Token(AMBER, 0.08).move_to(lb.nodes["decide"])
        ta = Token(RED, 0.08).move_to(la.nodes["decide"])
        with self.say("s02_06") as v:
            self.wait_until(v.cue("finished") - 0.3)
            self.play(*focus_tab(2), FadeOut(look), FadeOut(look_lab), FadeOut(trash), FadeIn(la), FadeIn(lb), run_time=0.6)
            self.wait_until(v.cue("soon") - 0.4)
            self.add(ta)
            self.play(MoveAlongPath(ta, la.leg("decide", "act")), run_time=0.4)
            self.play(FadeOut(ta, scale=0.5), FadeIn(early, shift=DOWN * 0.08), *la.all_dim(), run_time=0.4)
            self.wait_until(v.cue("forever") - 0.4)
            self.add(tb)
            self.play(FadeIn(never, shift=DOWN * 0.08), run_time=0.3)
            ring = Circle(radius=1.0).move_to(lb.center).rotate(PI / 2).flip(UP)
            for _ in range(2):
                self.play(MoveAlongPath(tb, ring), rate_func=linear, run_time=0.45)

        # analogy: cooking without a recipe
        pot = pot_icon(0.8).move_to([-3.6, -0.1, 0])
        fl = flame(0.32).next_to(pot, DOWN, buff=0.08)
        smoke = VGroup(*[Arc(radius=0.12, start_angle=-PI / 2, angle=PI).set_stroke(MUTED, 1.6).move_to(
            pot.get_top() + UP * (0.25 + 0.22 * i) + RIGHT * 0.08 * (-1) ** i) for i in range(3)])
        burn = caps("rice burning", 12, RED).next_to(fl, DOWN, buff=0.14)
        onion = onion_icon(0.75).move_to([0, -0.1, 0])
        chop = caps("chopping onions", 12, FG).move_to([0, -1.05, 0])
        bowl = bowl_icon(0.6).move_to([3.6, -0.1, 0])
        forgot = caps("salad: forgotten", 12, MUTED).move_to([3.6, -1.05, 0])
        busy = caps("busy the whole time", 13, AMBER).move_to([0, 1.3, 0])
        no_recipe = Pill(VGroup(paper(0.32, 0.4, 3), en("no recipe", 18, FG)).arrange(RIGHT, buff=0.12), DIM,
                         pad_x=0.18).move_to([0, 2.0, 0])
        cross = I.cross_icon(0.3, RED).move_to(no_recipe.label[0])
        with self.say("s02_07") as v:
            self.wait_until(v.cue("cooking") - 0.4)
            self.play(*[FadeOut(m) for m in (la, lb, early, never, tb, tabs, big)], run_time=0.5)
            self.play(FadeIn(no_recipe, shift=DOWN * 0.08), FadeIn(cross, scale=1.3), run_time=0.5)
            self.wait_until(v.cue("busy") - 0.3)
            self.play(FadeIn(busy), run_time=0.4)
            self.wait_until(v.cue("rice") - 0.3)
            self.play(FadeIn(pot, shift=UP * 0.08), FadeIn(fl), run_time=0.4)
            self.play(FadeIn(smoke, lag_ratio=0.3), FadeIn(burn), run_time=0.5)
            self.wait_until(v.cue("onions") - 0.3)
            self.play(FadeIn(onion, shift=UP * 0.08), FadeIn(chop), run_time=0.5)
            self.wait_until(v.cue("salad") - 0.3)
            bowl.fade(0.65)
            self.play(FadeIn(bowl, shift=UP * 0.08), FadeIn(forgot), run_time=0.5)

        lst = paper(1.5, 1.9, 5).move_to([-1.4, -0.2, 0])
        ticks = VGroup(*[I.check_icon(0.18, PLAN).move_to(lst[1 + i].get_left() + LEFT * 0.0) for i in range(5)])
        for i, t in enumerate(ticks):
            lst[1 + i].shift(RIGHT * 0.2)
        person = VGroup(I.user_icon(0.5, FG), caps("a person", 12, MUTED)).arrange(DOWN, buff=0.1).next_to(lst, LEFT, buff=0.6)
        agent = VGroup(I.chip(0.55, BLUE), caps("an agent", 12, BLUE)).arrange(DOWN, buff=0.1).move_to([2.2, -0.2, 0])
        same = arrow(lst.get_right() + RIGHT * 0.15, agent.get_left() + LEFT * 0.15, color=PLAN, tip=0.12)
        first_l = caps("a list first", 13, PLAN).next_to(lst, UP, buff=0.2)
        with self.say("s02_08") as v:
            self.wait_until(v.cue("person") - 0.3)
            self.play(*[FadeOut(m) for m in (pot, fl, smoke, burn, onion, chop, bowl, forgot, busy, no_recipe, cross)],
                      run_time=0.5)
            self.play(FadeIn(person, shift=RIGHT * 0.1), run_time=0.4)
            self.wait_until(v.cue("list") - 0.3)
            self.play(FadeIn(lst, shift=UP * 0.08), FadeIn(first_l), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(t, scale=1.3) for t in ticks], lag_ratio=0.2), run_time=0.8)
            self.wait_until(v.cue("agent") - 0.3)
            self.play(GrowArrow(same), FadeIn(agent, shift=LEFT * 0.1), run_time=0.6)
        self.clear_all(0.6)


def send_anim(msgs, model):
    b = bundle_copy(msgs, 0.3).move_to(VGroup(*msgs))
    return Succession(b.animate(run_time=0.5).move_to(model.in_port + LEFT * 0.2),
                      FadeOut(b, scale=0.3, run_time=0.3))
