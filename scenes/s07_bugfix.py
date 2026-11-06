"""07 · Practical example - an agent finds and fixes a crash."""
from agentic_video.prelude import *

ORIG = ["def average(nums):", "    total = sum(nums)", "    return total / len(nums)"]
INSERT = ["    if len(nums) == 0:", "        return 0"]
PHASE_COL = {"decide": BLUE, "act": TEAL, "observe": AMBER, "evaluate": VIOLET}
PHASE_ANG = {"decide": PI / 2, "act": 0, "observe": -PI / 2, "evaluate": PI}
BN_NUM = "0123456789"


class S07BugFix(VoiceScene):
    SECTION = "s07"

    # ------------------------------------------------------------ loop widget
    def build_widget(self):
        c = np.array([6.45, 2.72, 0])
        r = 0.25
        self.w_ring = Circle(radius=r).move_to(c).set_stroke(FAINT, 1.6)
        self.w_dots = {k: Dot(c + r * np.array([np.cos(a), np.sin(a), 0]), radius=0.055, color=PHASE_COL[k]).set_opacity(0.35)
                       for k, a in PHASE_ANG.items()}
        self.w_phase = en("ready", 22, MUTED).move_to([5.95, 2.86, 0], aligned_edge=RIGHT)
        self.w_loop = self.loop_label(0)
        self.cur_phase = None
        return VGroup(self.w_ring, *self.w_dots.values(), self.w_phase, self.w_loop)

    def loop_label(self, n):
        g = VGroup(en("loop", 18, DIM), bn(BN_NUM[n], 22, FG)).arrange(RIGHT, buff=0.1)
        return g.move_to([5.95, 2.55, 0], aligned_edge=RIGHT)

    def phase(self, key, loop=None, color=None):
        anims = []
        if self.cur_phase:
            anims.append(self.w_dots[self.cur_phase].animate.set_opacity(0.35).scale(1 / 1.7))
        anims.append(self.w_dots[key].animate.set_opacity(1).scale(1.7))
        self.cur_phase = key
        new_phase = en(key, 22, color or PHASE_COL[key]).move_to(self.w_phase, aligned_edge=RIGHT)
        anims.append(FadeTransform(self.w_phase, new_phase))
        self.w_phase = new_phase
        if loop is not None:
            nl = self.loop_label(loop)
            anims.append(FadeTransform(self.w_loop, nl))
            self.w_loop = nl
        return anims

    # ------------------------------------------------------------ scene
    def construct(self):
        self.show_chapter()
        env = Zone(3.0, 4.2, AMBER, "project", label_size=24).move_to([-5.35, -0.02, 0])
        editor = CodeEditor(4.9, 2.4, "", font_size=17).move_to([-1.05, 0.88, 0])
        ed_title = mono("editor", 15, DIM).move_to(editor.frame.get_top() + DOWN * editor.bar_h / 2)
        term = Terminal(5.1, 4.2, "terminal", font_size=17).move_to([4.25, -0.02, 0])
        with self.say("s07_01"):
            self.play(LaggedStart(FadeIn(env), FadeIn(editor), FadeIn(ed_title), FadeIn(term), lag_ratio=0.2), run_time=1.2)

        user = I.user_icon(0.42, MUTED).move_to([-6.55, 2.7, 0])
        req = bn("“The program is crashing. Find the cause and fix it.”", 24, FG)
        req.next_to(user, RIGHT, buff=0.2)
        agent = AgentBadge().scale(0.8).move_to([3.7, 2.72, 0])
        widget = self.build_widget()
        pos = {"env": [-4.4, 2.08, 0], "editor": [0.6, 2.08, 0], "term": [5.85, 2.08, 0]}
        with self.say("s07_02") as v:
            self.play(FadeIn(user, shift=RIGHT * 0.1), FadeIn(req, shift=RIGHT * 0.1), run_time=0.8)
            self.wait_until(v.word("ढूँढकर") - 0.3)
            self.play(FadeIn(agent, scale=0.8), FadeIn(widget), run_time=0.7)

        # the program, explained for non-programmers
        ex1 = VGroup(mono("average([4, 8, 6])", 18, FG), en("→", 24, MUTED), mono("6", 18, TEAL)).arrange(RIGHT, buff=0.22)
        ex2 = bn("average = total ÷ how many numbers", 20, MUTED)
        note = VGroup(ex1, ex2).arrange(DOWN, buff=0.18).move_to([-1.05, -1.45, 0])
        with self.say("s07_03") as v:
            self.wait_until(v.word("औसत") - 0.5)
            self.play(FadeIn(note, shift=UP * 0.1), run_time=0.7)

        # ---- loop 1: list files
        tree_items = [("calculator/", 0, True), ("main.py", 1, False), ("stats.py", 1, False),
                      ("test_stats.py", 1, False), ("README.md", 1, False)]
        tree = VGroup()
        for i, (name, depth, is_dir) in enumerate(tree_items):
            ic = I.folder_icon(0.24, AMBER) if is_dir else I.file_icon(0.3, MUTED, lines=2)
            row = VGroup(ic, mono(name, 16, FG if is_dir else MUTED)).arrange(RIGHT, buff=0.14)
            row.move_to([-6.6 + depth * 0.32, 1.25 - i * 0.52, 0], aligned_edge=LEFT)
            tree.add(row)
        with self.say("s07_04") as v:
            self.play(*self.phase("decide", 1), run_time=0.5)
            self.play(agent.animate.move_to(pos["env"]), *self.phase("act"), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.08) for r in tree], lag_ratio=0.18), run_time=1.1)
            self.play(*self.phase("observe"), env.lit(0.1), run_time=0.5)

        # ---- loop 2: open stats.py
        stats = tree[2]
        code = [editor.make_line(i, s) for i, s in enumerate(ORIG)]
        st_title = mono("stats.py", 15, MUTED).move_to(ed_title)
        with self.say("s07_05") as v:
            self.play(*self.phase("decide", 2), env.unlit(), run_time=0.5)
            self.wait_until(v.word("stats") - 0.3)
            self.play(stats[1].animate.set_color(TEAL), stats[0].animate.set_stroke(TEAL), glow(stats, TEAL, 4), run_time=0.6)
            self.wait_until(v.word("खोलकर") - 0.4)
            self.play(agent.animate.move_to(pos["editor"]), *self.phase("act"), FadeTransform(ed_title, st_title), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(VGroup(*c), shift=RIGHT * 0.08) for c in code], lag_ratio=0.3), run_time=1.0)
            self.wait_until(v.word("पढ़ा") - 0.3)
            self.play(*self.phase("observe"), run_time=0.5)

        # ---- loop 3: run the tests
        with self.say("s07_06") as v:
            self.play(*self.phase("decide", 3), run_time=0.4)
            self.wait_until(v.word("Terminal") - 0.3)
            self.play(agent.animate.move_to(pos["term"]), *self.phase("act"), run_time=0.7)
            cmd = term.next_line("$ python -m pytest")
            self.play(AddTextLetterByLetter(cmd, run_time=0.9))

        out = [("test_stats.py ..F", MUTED), ("FAILED test_empty_list", RED), ("ZeroDivisionError:", RED),
               ("  division by zero", RED)]
        out_m = [term.next_line(s, c) for s, c in out]
        with self.say("s07_07") as v:
            self.play(*self.phase("observe"), FadeIn(out_m[0]), run_time=0.5)
            self.wait_until(v.word("फ़ेल") - 0.3)
            self.play(FadeIn(out_m[1], shift=RIGHT * 0.08), run_time=0.4)
            self.wait_until(v.word("Zero") - 0.3)
            self.play(FadeIn(out_m[2], shift=RIGHT * 0.08), FadeIn(out_m[3], shift=RIGHT * 0.08), run_time=0.5)
            self.play(Indicate(out_m[2], color=RED, scale_factor=1.06), run_time=0.7)

        # ---- loop 4: investigate, then edit
        hl = editor.row_highlight(2, RED, 0.16)
        bug1 = VGroup(mono("average([ ])", 18, FG), en("→", 24, MUTED), mono("0 / 0", 18, RED)).arrange(RIGHT, buff=0.22)
        bug2 = bn("empty list → divide by zero!", 20, RED)
        bug = VGroup(bug1, bug2).arrange(DOWN, buff=0.18).move_to(note)
        with self.say("s07_08") as v:
            self.play(*self.phase("evaluate", color=RED), run_time=0.5)
            self.play(*self.phase("decide", 4), run_time=0.4)
            self.wait_until(v.word("लिस्ट") - 0.4)
            self.play(FadeIn(hl), FadeTransform(note, bug), run_time=0.7)
            self.wait_until(v.word("शून्य") - 0.2)
            self.play(Indicate(code[2][1], color=RED, scale_factor=1.05), run_time=0.7)

        shift = DOWN * editor.line_h * 2
        new_code = [editor.make_line(i + 1, s, TEAL) for i, s in enumerate(INSERT)]
        new_nums = [mono(str(i + 1), editor.fs, DIM).move_to(code[0][0]).shift(DOWN * editor.line_h * i)
                    for i in range(1, 5)]
        add_hl = VGroup(editor.row_highlight(1, TEAL, 0.12), editor.row_highlight(2, TEAL, 0.12))
        fix_note = bn("if the list is empty, return 0 first", 21, TEAL).move_to(bug)
        with self.say("s07_09") as v:
            self.play(agent.animate.move_to(pos["editor"]), *self.phase("act"), run_time=0.7)
            self.play(FadeOut(hl), FadeOut(code[1][0]), FadeOut(code[2][0]),
                      code[1][1].animate.shift(shift), code[2][1].animate.shift(shift), run_time=0.7)
            self.play(FadeIn(add_hl), *[FadeIn(n) for n in new_nums],
                      LaggedStart(*[FadeIn(c[1], shift=RIGHT * 0.1) for c in new_code], lag_ratio=0.3), run_time=0.9)
            self.wait_until(v.word("खाली") - 0.3)
            self.play(FadeTransform(bug, fix_note), run_time=0.6)

        # ---- loop 5: run the tests again
        term.n += 1
        cmd2 = term.next_line("$ python -m pytest")
        with self.say("s07_10") as v:
            self.play(*self.phase("decide", 5), run_time=0.4)
            self.play(agent.animate.move_to(pos["term"]), *self.phase("act"), run_time=0.6)
            self.play(AddTextLetterByLetter(cmd2, run_time=0.8))

        p1 = term.next_line("test_stats.py ...", MUTED)
        p2 = term.next_line("✓ 3 passed", TEAL)
        with self.say("s07_11") as v:
            self.play(*self.phase("observe"), FadeIn(p1), run_time=0.5)
            self.play(FadeIn(p2, shift=RIGHT * 0.08), run_time=0.4)
            self.wait_until(v.word("जाँच") - 0.3)
            self.play(*self.phase("evaluate", color=TEAL), glow(p2, TEAL, 4), run_time=0.6)
            check = I.check_icon(0.3).move_to(self.w_ring)
            self.play(FadeIn(check, scale=0.6), self.w_ring.animate.set_stroke(TEAL, 2), run_time=0.5)

        # ---- the report
        head = VGroup(I.spark_icon(0.28, TEAL), en("report", 26, TEAL)).arrange(RIGHT, buff=0.12)
        lines = VGroup(
            VGroup(bn("Problem:", 24, RED), bn("an empty list caused a division by zero", 24, FG)).arrange(RIGHT, buff=0.15),
            VGroup(bn("Fix:", 24, AMBER), bn("return 0 early when the list is empty", 24, FG)).arrange(RIGHT, buff=0.15),
            VGroup(bn("Result:", 24, TEAL), bn("all tests pass", 24, FG), I.check_icon(0.26)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        body = VGroup(head, lines).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([0, -0.2, 0])
        # card sized to its text (with even padding) instead of a fixed size
        card = RoundedRectangle(width=body.width + 0.9, height=body.height + 0.7, corner_radius=0.18)
        card.set_stroke(TEAL, 1.8).set_fill(PANEL, 1).move_to(body)
        report = VGroup(card, head, lines)
        veil = Rectangle(width=config.frame_width + 1, height=config.frame_height + 1)
        veil.set_stroke(width=0).set_fill(BG, 0.86)
        with self.say("s07_12") as v:
            self.play(FadeIn(veil), run_time=0.6)
            self.play(FadeIn(card, scale=0.96), FadeIn(head), run_time=0.6)
            for i, w in enumerate(("दिक्कत", "बदला", "सब")):
                self.wait_until(v.word(w) - 0.3)
                self.play(FadeIn(lines[i], shift=RIGHT * 0.1), run_time=0.5)

        # ---- all five components, named
        def tag(text, color):
            return Pill(en(text, 20, color), color, pad_y=0.07)

        t_goal = tag("goal", FG).next_to(req, RIGHT, buff=0.25)
        t_model = tag("model", BLUE).next_to(agent, DOWN, buff=0.1)
        t_tools = tag("tools", TEAL).move_to(editor.frame.get_corner(DR) + LEFT * 0.75)
        t_env = tag("environment", AMBER).move_to(env.shape.get_bottom() + UP * 0.38)
        t_fb = tag("feedback", VIOLET).move_to(term.frame.get_bottom() + UP * 0.38)
        with self.say("s07_13") as v:
            self.play(FadeOut(report), FadeOut(veil), run_time=0.7)
            self.wait_until(v.word("Goal") - 0.2)
            self.play(FadeIn(t_goal, scale=0.9), run_time=0.35)
            self.wait_until(v.word("Model") - 0.2)
            self.play(FadeIn(t_model, scale=0.9), glow(agent.frame, BLUE, 4), run_time=0.35)
            self.wait_until(v.word("Tools") - 0.2)
            self.play(FadeIn(t_tools, scale=0.9), glow(editor.frame, TEAL, 4), glow(term.frame, TEAL, 4), run_time=0.4)
            self.wait_until(v.word("Environment") - 0.2)
            self.play(FadeIn(t_env, scale=0.9), env.lit(0.1), run_time=0.4)
            self.wait_until(v.word("Feedback") - 0.2)
            self.play(FadeIn(t_fb, scale=0.9), glow(VGroup(*out_m, p1, p2), VIOLET, 3), run_time=0.4)
            self.wait_until(v.word("Loop") - 0.4)
            spin = VGroup(self.w_ring, *self.w_dots.values())
            self.play(Rotate(spin, -TAU, about_point=self.w_ring.get_center()), run_time=1.4)
            self.play(Rotate(spin, -TAU, about_point=self.w_ring.get_center()), run_time=1.4)
        self.clear_all(0.8)
