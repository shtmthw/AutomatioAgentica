"""03 · What is an AI agent? Definition + the five components."""
from agentic_video.prelude import *


def comp_label(name, meaning, color, size=28):
    return VGroup(en(name, size, color), bn(meaning, 20, MUTED)).arrange(DOWN, buff=0.06)


class S03Agent(VoiceScene):
    SECTION = "s03"

    def construct(self):
        self.show_chapter()
        star = I.spark_icon(0.9, TEAL)
        title = en("AI Agent", 88, TEAL)
        head = VGroup(star, title).arrange(RIGHT, buff=0.35).move_to(UP * 0.2)
        self.narrate("s03_01", FadeIn(head, shift=UP * 0.12), run_time=0.9)

        # ---- definition: a system that uses a model to pursue a goal
        sys_zone = Zone(3.2, 2.4, TEAL, "system", label_size=24).move_to([-3.6, 0.75, 0])
        m = I.chip_labeled(1.3, "model", BLUE).move_to(sys_zone.shape.get_center() + DOWN * 0.2)
        goal_ic = I.target_icon(0.95, FG)
        goal_g = VGroup(goal_ic, en("goal", 30, FG)).arrange(DOWN, buff=0.2).move_to([3.6, 0.75, 0])
        goal_g.shift(UP * (sys_zone.shape.get_center()[1] - goal_ic.get_center()[1]))
        a1 = arrow(sys_zone.shape.get_right() + RIGHT * 0.15, goal_ic.get_left() + LEFT * 0.25, color=TEAL)
        with self.say("s03_02") as v:
            self.play(head.animate.scale(0.45).move_to([0, 2.75, 0]), run_time=0.8)
            self.wait_until(v.word("System") - 0.3)
            self.play(FadeIn(sys_zone), run_time=0.6)
            self.wait_until(v.word("Model") - 0.3)
            self.play(FadeIn(m, scale=0.9), run_time=0.6)
            self.wait_until(v.word("लक्ष्य") - 0.4)
            self.play(GrowArrow(a1), FadeIn(goal_g, shift=LEFT * 0.1), run_time=0.8)

        steps = ["makes decisions", "acts with tools", "checks results", "plans the next step"]
        cols = [BLUE, TEAL, AMBER, VIOLET]
        pills = VGroup(*[Pill(t, c, size=24) for t, c in zip(steps, cols)]).arrange(RIGHT, buff=0.55)
        pills.move_to([0, -1.75, 0])
        if pills.width > 13.0:
            pills.scale_to_fit_width(13.0)
        links = VGroup(*[arrow(pills[i].get_right() + RIGHT * 0.06, pills[i + 1].get_left() + LEFT * 0.06,
                               color=DIM, tip=0.1) for i in range(3)])
        cues = ["फ़ैसले", "Tools", "नतीजे", "आगे"]
        with self.say("s03_03") as v:
            for i, w in enumerate(cues):
                self.wait_until(v.word(w) - 0.25)
                anims = [FadeIn(pills[i], shift=UP * 0.1)]
                if i:
                    anims.append(GrowArrow(links[i - 1]))
                self.play(*anims, run_time=0.45)

        # ---- five components
        nums = VGroup(*[bn(n, 40, DIM) for n in "12345"]).arrange(RIGHT, buff=0.9).move_to(UP * 0.2)
        five = bn("five basic parts", 36, FG).next_to(nums, UP, buff=0.6)
        with self.say("s03_04") as v:
            self.play(*[FadeOut(x) for x in (sys_zone, m, goal_g, a1, pills, links, head)], run_time=0.7)
            self.play(FadeIn(five, shift=UP * 0.1), LaggedStart(*[FadeIn(n, shift=UP * 0.1) for n in nums],
                                                                 lag_ratio=0.15), run_time=1.0)
        self.play(FadeOut(five), FadeOut(nums), run_time=0.5)

        # layout of the full diagram
        agent_zone = Zone(5.3, 3.5, TEAL, "agent", label_size=24).move_to([-1.75, 0.45, 0])
        env_zone = Zone(3.5, 3.5, AMBER, None).move_to([4.75, 0.45, 0])

        goal = VGroup(I.target_icon(0.62, FG), comp_label("goal", "what we want", FG)).arrange(DOWN, buff=0.14)
        goal.move_to([-5.95, 0.45, 0])
        a_goal = arrow(goal.get_right() + RIGHT * 0.08, agent_zone.shape.get_left() + LEFT * 0.05 + UP * 0.0)

        model = I.chip_labeled(1.3, "model", BLUE).move_to([-3.05, 0.6, 0])
        model_lab = bn("thinks & decides", 20, MUTED).next_to(model, DOWN, buff=0.18)

        tool_icons = VGroup(I.file_icon(0.42, TEAL), I.terminal_icon(0.38, TEAL), I.globe_icon(0.42, TEAL))
        tool_icons.arrange(DOWN, buff=0.2).move_to([-0.35, 0.6, 0])
        tools_lab = comp_label("tools", "ways to act", TEAL, 26).next_to(tool_icons, DOWN, buff=0.2)
        a_mt = arrow(model.get_right() + RIGHT * 0.1, tool_icons.get_left() + LEFT * 0.15 + DOWN * 0.0, color=MUTED)

        env_lab = comp_label("environment", "where it works", AMBER, 26).next_to(env_zone.shape.get_top(), DOWN, buff=0.18)
        env_items = VGroup(
            VGroup(I.folder_icon(0.42, AMBER), mono("project/", 16, MUTED)).arrange(DOWN, buff=0.1),
            VGroup(I.database_icon(0.46, AMBER), mono("data", 16, MUTED)).arrange(DOWN, buff=0.1),
            VGroup(I.globe_icon(0.46, AMBER), mono("web", 16, MUTED)).arrange(DOWN, buff=0.1),
            VGroup(I.terminal_icon(0.4, AMBER), mono("computer", 16, MUTED)).arrange(DOWN, buff=0.1),
        ).arrange_in_grid(2, 2, buff=(0.7, 0.35)).move_to(env_zone.shape.get_center() + DOWN * 0.35)
        act_y = UP * 0.6
        a_act = labeled_arrow(tool_icons.get_right() * RIGHT + RIGHT * 0.25 + act_y, env_zone.shape.get_left() * RIGHT + LEFT * 0.08 + act_y,
                              "act", color=TEAL, label_color=TEAL)

        fb_start = env_zone.shape.get_bottom() + DOWN * 0.08 + LEFT * 0.4
        fb_end = model.get_bottom() + DOWN * 0.62
        fb = ArcBetweenPoints(fb_start, fb_end, angle=-PI / 4)
        fb.set_stroke(VIOLET, 2.2)
        fb.add_tip(tip_length=0.14, tip_width=0.14)
        fb.get_tip().set_fill(VIOLET, 1).set_stroke(width=0)
        fb_lab = comp_label("feedback", "what comes back", VIOLET, 26).move_to([0.6, -2.42, 0])

        with self.say("s03_05") as v:
            self.wait_until(v.word("Goal") - 0.3)
            self.play(FadeIn(goal, shift=RIGHT * 0.1), run_time=0.7)
            self.play(pulse(goal[0], 1.12), run_time=0.6)

        with self.say("s03_06") as v:
            self.wait_until(v.word("Model") - 0.3)
            self.play(FadeIn(agent_zone), GrowArrow(a_goal), FadeIn(model, scale=0.9), run_time=0.9)
            self.wait_until(v.word("सोचने") - 0.3)
            self.play(FadeIn(model_lab, shift=UP * 0.08), glow(model.body, BLUE), run_time=0.7)

        with self.say("s03_07") as v:
            self.wait_until(v.word("Tools") - 0.3)
            self.play(GrowArrow(a_mt), LaggedStart(*[FadeIn(t, shift=LEFT * 0.1) for t in tool_icons], lag_ratio=0.2),
                      FadeIn(tools_lab), run_time=1.0)

        with self.say("s03_08") as v:
            self.wait_until(v.word("Environment") - 0.3)
            self.play(FadeIn(env_zone), FadeIn(env_lab), run_time=0.7)
            self.play(GrowArrow(a_act.arrow), FadeIn(a_act.label), run_time=0.6)
            self.wait_until(v.word("जैसे") - 0.2)
            self.play(LaggedStart(*[FadeIn(e, scale=0.9) for e in env_items], lag_ratio=0.25), run_time=1.2)

        token = Token(VIOLET, 0.07)
        with self.say("s03_09") as v:
            self.wait_until(v.word("Feedback") - 0.3)
            self.play(Create(fb), FadeIn(fb_lab, shift=UP * 0.08), run_time=1.0)
            self.wait_until(v.word("काम") - 0.2)
            token.move_to(a_act.arrow.get_start())
            path_act = Line(a_act.arrow.get_start(), a_act.arrow.get_end())
            self.play(MoveAlongPath(token.set_color(TEAL), path_act), run_time=0.8)
            self.play(env_zone.lit(0.11), run_time=0.3)
            self.play(token.animate.set_fill(VIOLET), env_zone.unlit(), run_time=0.2)
            fb_path = ArcBetweenPoints(fb_start, fb_end, angle=-PI / 4)
            self.play(MoveAlongPath(token, fb_path), run_time=1.2)
            self.play(FadeOut(token), glow(model.body, VIOLET), run_time=0.5)

        # ---- the model is only one part of the agent
        neq = VGroup(en("model", 30, BLUE), en("≠", 34, FG), en("agent", 30, TEAL)).arrange(RIGHT, buff=0.25)
        neq.move_to([1.55, 2.82, 0])
        with self.say("s03_10") as v:
            self.wait_until(v.word("Model") - 0.2)
            self.play(glow(model.body, BLUE), pulse(model, 1.08), run_time=0.8)
            self.wait_until(v.word("System") - 0.3)
            self.play(agent_zone.lit(0.12), run_time=0.7)
            self.wait_until(v.word("पूरा") - 0.3)
            self.play(FadeIn(neq, shift=DOWN * 0.1), run_time=0.7)
        self.clear_all(0.8)
