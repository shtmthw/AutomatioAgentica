"""08 · Reality check - agents are powerful, not magic; they need boundaries."""
from agentic_video.prelude import *


class S08Reality(VoiceScene):
    SECTION = "s08"

    def construct(self):
        self.show_chapter()
        l1 = bn("AI agents are powerful,", 52, FG)
        l2 = bn("but they are not magic.", 52, AMBER)
        head = VGroup(l1, l2).arrange(DOWN, buff=0.3).move_to(UP * 0.25)
        with self.say("s08_01") as v:
            self.wait_until(v.word("ताकतवर") - 0.5)
            self.play(FadeIn(l1, shift=UP * 0.1), run_time=0.7)
            self.wait_until(v.word("जादू") - 0.4)
            self.play(FadeIn(l2, shift=UP * 0.1), run_time=0.7)

        # ---- four risks
        specs = [
            (I.fork_icon(0.55, AMBER), "can make wrong decisions"),
            (I.wrench_icon(0.55, AMBER), "can use tools incorrectly"),
            (I.trash_icon(0.55, RED), "can change or delete important data"),
            (I.loop_icon(0.55, AMBER), "can get stuck repeating itself"),
        ]
        rows = VGroup()
        for ic, t in specs:
            box = Zone(0.8, 0.8, ic[0].get_stroke_color() if hasattr(ic[0], "get_stroke_color") else AMBER,
                       None, radius=0.24, fill_opacity=0.05)
            ic.scale(0.88)
            ic.move_to(box.shape)
            rows.add(VGroup(VGroup(box, ic), bn(t, 34, FG)).arrange(RIGHT, buff=0.45))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([0, 0.2, 0])

        for i in range(4):
            with self.say(f"s08_0{i + 2}"):
                anims = [FadeIn(rows[i], shift=RIGHT * 0.12)]
                if i == 0:
                    anims.append(FadeOut(head, shift=UP * 0.15))
                self.play(*anims, run_time=0.6)
                ic = rows[i][0][1]
                if i == 0:
                    self.play(glow(ic, AMBER, 5), run_time=0.6)
                elif i == 1:
                    self.play(Rotate(ic, PI / 6, rate_func=there_and_back), run_time=0.6)
                    self.play(Rotate(ic, -PI / 6, rate_func=there_and_back), run_time=0.6)
                elif i == 2:
                    self.play(Wiggle(ic, scale_value=1.1, rotation_angle=0.06 * TAU), run_time=0.9)
                else:
                    self.play(Rotate(ic, -TAU, about_point=ic.get_center()), run_time=1.2)
                    self.play(Rotate(ic, -TAU, about_point=ic.get_center()), run_time=1.2)

        # ---- what keeps an agent safe
        guards = [("Permissions", TEAL), ("Safeguards", BLUE), ("Human oversight", AMBER)]
        pills = VGroup(*[Pill(en(e, 26, c), c, pad_x=0.34) for e, c in guards]).arrange(RIGHT, buff=0.35).move_to([0, 2.5, 0])
        with self.say("s08_06") as v:
            self.play(FadeOut(rows, shift=LEFT * 0.15), run_time=0.6)
            for i, w in enumerate(("Permission", "Safeguard", "निगरानी")):
                self.wait_until(v.word(w) - 0.3)
                self.play(FadeIn(pills[i], shift=DOWN * 0.1), run_time=0.5)

        # ---- the boundary
        bound = RoundedRectangle(width=6.8, height=3.7, corner_radius=0.34).set_stroke(TEAL, 2.4).set_fill(TEAL, 0.04)
        bound.move_to([-2.55, -0.4, 0])
        b_lab = VGroup(en("allowed", 26, TEAL), bn("· the agent may do these", 20, MUTED)).arrange(RIGHT, buff=0.1)
        b_lab.move_to(bound.get_corner(UL) + RIGHT * (b_lab.width / 2 + 0.35) + DOWN * 0.32)
        agent = AgentBadge(size=24).move_to([-4.65, -0.5, 0])
        allowed = VGroup(*[Pill(VGroup(bn(t, 24, FG), I.check_icon(0.23)).arrange(RIGHT, buff=0.14), TEAL, pad_y=0.1)
                           for t in ("read files", "run tests", "edit code")]).arrange(DOWN, buff=0.32)
        allowed.move_to([-1.5, -0.55, 0])
        blocked = VGroup(*[Pill(VGroup(I.lock_icon(0.28, MUTED), bn(t, 24, MUTED)).arrange(RIGHT, buff=0.14), DIM, pad_y=0.1)
                           for t in ("delete files", "send money", "change the database")]).arrange(DOWN, buff=0.32, aligned_edge=RIGHT)
        blocked.move_to([5.12, -0.55, 0])
        blocked.shift(RIGHT * (6.7 - blocked.get_right()[0]))   # keep a safe margin from the frame edge
        with self.say("s08_07") as v:
            self.play(Create(bound), FadeIn(b_lab), FadeIn(agent, scale=0.9), run_time=0.9)
            self.play(LaggedStart(*[FadeIn(a, shift=RIGHT * 0.1) for a in allowed], lag_ratio=0.2), run_time=0.8)
            self.wait_until(v.word("नहीं") - 0.3)
            self.play(LaggedStart(*[FadeIn(b, shift=LEFT * 0.1) for b in blocked], lag_ratio=0.2), run_time=0.8)
            self.wait_until(v.word("सीमा") - 0.3)
            self.play(glow(bound, TEAL, 6, 0.9), run_time=0.9)

        # the agent tries to step outside, the boundary stops it, a human decides
        tok = Token(TEAL, 0.08).move_to(agent.get_right() + RIGHT * 0.1)
        edge = np.array([bound.get_right()[0] - 0.12, blocked[0].get_y(), 0])
        gate = VGroup(RoundedRectangle(width=0.7, height=0.7, corner_radius=0.16).set_stroke(AMBER, 2.2).set_fill(PANEL, 1),
                      I.user_icon(0.42, AMBER)).move_to([bound.get_right()[0], edge[1], 0])
        gate_lab = bn("needs human\napproval", 22, AMBER).next_to(gate, RIGHT, buff=0.2)
        moral = bn("more power  =  more responsibility", 40, FG).move_to([0, 2.5, 0])
        with self.say("s08_08") as v:
            self.play(FadeIn(tok, scale=0.5), run_time=0.3)
            self.play(tok.animate.move_to(edge), run_time=0.9, rate_func=rush_into)
            self.play(bound.animate.set_stroke(RED), Flash(edge, color=RED, line_length=0.15, flash_radius=0.3),
                      run_time=0.4)
            self.play(tok.animate.move_to(edge + LEFT * 1.0), bound.animate.set_stroke(TEAL), run_time=0.6,
                      rate_func=rush_from)
            self.play(FadeIn(gate, scale=0.7), FadeIn(gate_lab, shift=DOWN * 0.08), run_time=0.7)
            self.wait_until(v.word("ज़िम्मेदारी") - 1.0)
            self.play(FadeOut(pills, shift=UP * 0.1), run_time=0.5)
            self.play(FadeIn(moral, shift=DOWN * 0.1), run_time=0.7)
        self.wait(0.6)
        self.clear_all(0.8)
