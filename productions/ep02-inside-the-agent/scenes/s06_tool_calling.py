"""06 · Tool calling, step by step: the nine steps with the message list on the right,
the mapping onto the agent loop, the key line, and a failing tool (errors are feedback)."""
from agentic_video.prelude import *

LIST_X, LIST_TOP, CARD_W = 1.85, 2.25, 4.68
STAGE_X = -1.25                        # centre of the free stage between the model and the list


def call_content(tool, arg, size=17):
    return VGroup(mono(tool, size, BLUE), en("→", size + 2, MUTED), mono(arg, size, FG)).arrange(RIGHT, buff=0.14)


class S06ToolCalling(VoiceScene):
    SECTION = "s06"

    def send(self, mobs, model, rt=1.2):
        b = VGroup(*[m.copy() for m in mobs])
        self.add(b)
        self.play(b.animate.scale(0.3).move_to([LIST_X - 0.9, 1.6, 0]), run_time=rt * 0.35)
        self.play(b.animate(path_arc=PI * 0.4).scale(0.45).move_to(model.in_port + RIGHT * 0.25).set_opacity(0),
                  run_time=rt * 0.65)
        self.remove(b)

    def construct(self):
        self.show_chapter()
        title = spaced("TOOL CALLING", 60, FG, tracking=0.34, weight=LIGHT).move_to([0, 0.75, 0])
        sub = caps("step by step", 20, AMBER).next_to(title, DOWN, buff=0.35)
        steps = StepTracker(9).move_to([0, -0.55, 0])
        with self.say("s06_01") as v:
            self.wait_until(v.cue("toolcalling") - 0.4)
            self.play(FadeIn(title, shift=UP * 0.12), run_time=0.8)
            self.wait_until(v.cue("slowly") - 0.3)
            self.play(FadeIn(sub, shift=UP * 0.08), FadeIn(steps.dots, lag_ratio=0.1), run_time=0.8)

        # ---- the stage
        harness = HarnessFrame(13.4, 5.72).move_to([0, 0.15, 0])
        model = ModelBox(2.4, 1.4).move_to([-4.6, 0.95, 0])
        head = caps("messages", 16, MUTED).move_to([LIST_X, LIST_TOP + 0.42, 0], aligned_edge=LEFT)
        rule = Line([LIST_X, LIST_TOP + 0.24, 0], [LIST_X + CARD_W, LIST_TOP + 0.24, 0]).set_stroke(FAINT, 1.4)
        tools = VGroup(*[Pill(mono(n, 17, TEAL), TEAL, pad_x=0.18, pad_y=0.08)
                         for n in ("read_file", "run_command", "edit_file")]).arrange(RIGHT, buff=0.18)
        tools.move_to([-6.35, -2.15, 0], aligned_edge=LEFT)
        tools_lab = caps("tools", 14, TEAL).next_to(tools, UP, buff=0.14, aligned_edge=LEFT)
        lst = MessageList([LIST_X, LIST_TOP], gap=0.1)
        sysc = lst.push(MessageCard("system", "You are a helpful coding agent.", width=CARD_W, wrap=24))
        user = MessageCard("user", "What port does the server use in config.txt?", width=CARD_W, wrap=26)
        tracker_pos = np.array([-1.65, 2.7, 0])
        with self.say("s06_02") as v:
            self.wait_until(v.cue("task") - 0.4)
            self.play(FadeOut(title, shift=UP * 0.2), FadeOut(sub), FadeIn(harness), run_time=0.6)
            self.play(FadeIn(model, scale=0.95), FadeIn(tools), FadeIn(tools_lab), FadeIn(head), Create(rule),
                      FadeIn(sysc, shift=RIGHT * 0.1), steps.animate.move_to(tracker_pos), run_time=0.8)
            self.wait_until(v.cue("question") - 0.3)
            lst.push(user)
            self.play(FadeIn(user, shift=RIGHT * 0.12), run_time=0.5)

        badge = model.badge("call #1")
        with self.say("s06_03") as v:
            self.play(*steps.go(1), run_time=0.5)
            self.wait_until(v.cue("sends") - 0.3)
            self.play(glow(sysc.frame, AMBER, 4), glow(user.frame, AMBER, 4), run_time=0.5)
            self.wait_until(v.cue("descriptions") - 0.3)
            self.play(*[glow(t.frame, TEAL, 4) for t in tools], run_time=0.4)
            self.send([sysc, user, *tools], model, 1.2)
            self.play(FadeIn(badge, shift=DOWN * 0.06), model.think(0.6), run_time=0.6)

        with self.say("s06_04") as v:
            self.play(*steps.go(2), run_time=0.5)
            self.wait_until(v.cue("answer") - 0.3)
            self.play(model.think(0.8), run_time=0.8)

        call = ToolCallCard("read_file", 'path = "config.txt"', width=3.6, size=18).move_to([STAGE_X, 0.95, 0])
        c_arrow = arrow(model.out_port + RIGHT * 0.05, call.get_left() + LEFT * 0.06, color=BLUE, tip=0.1)
        with self.say("s06_05") as v:
            self.wait_until(v.cue("toolcall") - 0.35)
            self.play(GrowArrow(c_arrow), FadeIn(call, shift=RIGHT * 0.25), run_time=0.6)
            self.wait_until(v.cue("readfile") - 0.3)
            self.play(glow(call.rows[0], BLUE, 4), run_time=0.5)

        def note(icon, text, color, y):
            return Pill(VGroup(icon, en(text, 20, color)).arrange(RIGHT, buff=0.12), color, pad_x=0.2, pad_y=0.08
                        ).move_to([STAGE_X, y, 0])

        pause = pause_icon(0.32, AMBER).next_to(call, UP, buff=0.18)
        n1 = note(VGroup(), "only a request", BLUE, -0.12)
        n2 = note(VGroup(), "just text", BLUE, -0.64)
        n3 = note(I.lock_icon(0.24, MUTED), "nothing happened yet", MUTED, -1.16)
        with self.say("s06_06") as v:
            self.wait_until(v.cue("pause") - 0.3)
            self.play(FadeIn(pause, scale=0.7), run_time=0.4)
            self.wait_until(v.cue("request") - 0.3)
            self.play(FadeIn(n1, shift=UP * 0.08), call.outline.animate.set_stroke(width=2.6), run_time=0.45)
            self.wait_until(v.cue("text") - 0.3)
            self.play(FadeIn(n2, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("happened") - 0.3)
            self.play(FadeIn(n3, shift=UP * 0.08), run_time=0.45)
        self.wait(0.5)

        a_call = MessageCard("assistant", content=call_content("read_file", "config.txt"), width=CARD_W, dashed=True)
        lst.push(a_call)
        with self.say("s06_07") as v:
            self.wait_until(v.cue("adds") - 0.3)
            self.play(FadeOut(VGroup(pause, n1, n2, n3)), FadeOut(c_arrow), FadeTransform(call, a_call),
                      run_time=0.9)
            self.wait_until(v.cue("assistant") - 0.3)
            self.play(glow(a_call.tag[0], BLUE, 5), run_time=0.5)

        found = Pill(VGroup(I.wrench_icon(0.26, AMBER), en("tool request found", 21, AMBER)).arrange(RIGHT, buff=0.12),
                     AMBER, pad_x=0.22).move_to([STAGE_X, 1.0, 0])
        scan = Line(a_call.get_corner(UP + LEFT), a_call.get_corner(DOWN + LEFT)).set_stroke(AMBER, 4)
        with self.say("s06_08") as v:
            self.play(*steps.go(3), run_time=0.5)
            self.wait_until(v.cue("reads") - 0.3)
            self.play(FadeIn(scan), run_time=0.15)
            self.play(scan.animate.move_to(a_call.get_right()), run_time=0.8, rate_func=linear)
            self.play(FadeOut(scan), run_time=0.15)
            self.wait_until(v.cue("request") - 0.3)
            self.play(FadeIn(found, shift=LEFT * 0.12), glow(a_call.frame, AMBER, 5), run_time=0.5)

        shield = shield_icon(0.62, AMBER).move_to([STAGE_X - 0.95, -0.05, 0])
        perm = en("permission?", 22, AMBER).next_to(shield, RIGHT, buff=0.22)
        ok_perm = en("allowed", 22, TEAL).move_to(perm, aligned_edge=LEFT)
        tick = I.check_icon(0.3, TEAL).move_to(shield.get_center() + UP * 0.04)
        with self.say("s06_09") as v:
            self.play(*steps.go(4), run_time=0.5)
            self.wait_until(v.cue("permission") - 0.3)
            self.play(FadeIn(shield, scale=0.8), FadeIn(perm, shift=LEFT * 0.08), run_time=0.5)
            self.wait_until(v.cue("allowed") - 0.3)
            self.play(FadeIn(tick, scale=1.4), shield[0].animate.set_stroke(TEAL), FadeTransform(perm, ok_perm),
                      run_time=0.5)

        win = Window(2.75, 1.3, "config.txt").move_to([-0.3, -1.3, 0])
        l1 = mono("port = 8080", 17, FG)
        l2 = mono("host = localhost", 17, FG)
        VGroup(l1, l2).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to(win.frame.get_center() + DOWN * 0.15)
        fic = I.file_icon(0.55, MUTED).move_to(win)
        tok = Token(TEAL, 0.08)
        with self.say("s06_10") as v:
            self.play(*steps.go(5), run_time=0.5)
            self.wait_until(v.cue("executes") - 0.3)
            self.play(tools[0].frame.animate.set_fill(TEAL, 0.25), glow(tools[0].frame, TEAL, 6), run_time=0.5)
            tok.move_to(tools[0].get_top())
            path = Line(tools[0].get_top(), fic.get_left() + LEFT * 0.1)
            self.play(FadeIn(fic, scale=0.9), FadeIn(tok, scale=0.5), run_time=0.3)
            self.play(MoveAlongPath(tok, path), run_time=0.6)
            self.play(FadeOut(tok), run_time=0.15)
            self.wait_until(v.cue("opens") - 0.35)
            self.play(ReplacementTransform(fic, win), run_time=0.6)
            self.wait_until(v.cue("text") - 0.3)
            self.play(FadeIn(l1, shift=UP * 0.06), FadeIn(l2, shift=UP * 0.06), run_time=0.5)

        res = MessageCard("tool", content=VGroup(mono("port = 8080,", 16, FG), mono("host = localhost", 16, FG))
                          .arrange(RIGHT, buff=0.16), width=CARD_W)
        lst.push(res)
        with self.say("s06_11") as v:
            self.play(*steps.go(6), run_time=0.5)
            self.wait_until(v.cue("adds") - 0.3)
            self.play(FadeTransform(VGroup(l1.copy(), l2.copy()), res), tools[0].frame.animate.set_fill(PANEL, 1),
                      run_time=0.9)
            self.wait_until(v.cue("toolmsg") - 0.3)
            self.play(glow(res.tag[0], TEAL, 6), run_time=0.5)
            self.wait_until(v.cue("port") - 0.3)
            self.play(glow(res.frame, TEAL, 5), pulse(res, 1.03), run_time=0.6)

        badge2 = model.badge("call #2")
        with self.say("s06_12") as v:
            self.play(*steps.go(7), FadeOut(VGroup(found, shield, tick, ok_perm, win, l1, l2)), run_time=0.6)
            self.wait_until(v.cue("calls") - 0.3)
            self.play(FadeTransform(badge, badge2), run_time=0.4)
            self.wait_until(v.cue("updated") - 0.4)
            self.send([*lst.cards, *tools], model, 1.2)
            self.play(model.think(0.6), run_time=0.6)

        ans = MessageCard("assistant", "The server uses port 8080.", width=3.6, size=19, wrap=16).move_to([STAGE_X, 0.95, 0])
        a_arrow = arrow(model.out_port + RIGHT * 0.05, ans.get_left() + LEFT * 0.06, color=BLUE, tip=0.1)
        plain = caps("plain text · no tool call", 14, DIM).next_to(ans, DOWN, buff=0.16)
        with self.say("s06_13") as v:
            self.play(*steps.go(8), run_time=0.5)
            self.wait_until(v.cue("normal") - 0.3)
            self.play(model.think(0.6), run_time=0.6)
            self.wait_until(v.cue("answer") - 0.35)
            self.play(GrowArrow(a_arrow), FadeIn(ans, shift=RIGHT * 0.25), run_time=0.6)
            self.play(FadeIn(plain), run_time=0.4)

        final = MessageCard("assistant", "The server uses port 8080.", width=CARD_W)
        nocall = Pill(VGroup(I.cross_icon(0.2), en("no tool request", 20, FG)).arrange(RIGHT, buff=0.12), DIM,
                      pad_x=0.2).move_to([STAGE_X, -0.2, 0])
        userg = VGroup(I.user_icon(0.48, FG), Bubble("The server uses port 8080.", BLUE, 19, side="left"))
        userg.arrange(RIGHT, buff=0.2).move_to([STAGE_X + 0.1, -1.0, 0])
        stop = VGroup(stop_icon(0.42), en("loop stops", 22, RED)).arrange(RIGHT, buff=0.16).move_to([0.45, -1.78, 0])
        with self.say("s06_14") as v:
            self.play(*steps.go(9), run_time=0.5)
            self.wait_until(v.cue("no") - 0.3)
            self.play(FadeOut(plain), FadeIn(nocall, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("final") - 0.3)
            lst.push(final)
            self.play(FadeOut(a_arrow), FadeTransform(ans.copy(), final), FadeIn(userg, shift=UP * 0.08),
                      run_time=0.8)
            self.wait_until(v.cue("stops") - 0.3)
            self.play(FadeIn(stop, scale=0.9), run_time=0.5)
        self.wait(0.6)

        # ---- map the steps onto the agent loop
        rows_txt = ["send everything to the model", "model writes a tool call", "harness reads the reply",
                    "check permission", "run the tool", "add the tool result", "call the model again",
                    "model answers in text", "stop"]
        rows = VGroup(*[VGroup(en(str(i + 1), 19, AMBER, italic=False, weight=NORMAL), en(t, 19, MUTED)).arrange(RIGHT, buff=0.16)
                        for i, t in enumerate(rows_txt)]).arrange(DOWN, buff=0.21, aligned_edge=LEFT)
        rows.move_to([-6.35, 0.05, 0], aligned_edge=LEFT)
        loop = LoopDiagram(center=[-0.75, -0.2, 0], radius=1.2, node_w=1.12, node_h=0.5, name_size=19, meanings=False,
                           goal=False)

        def link(i, key):
            """Light curved connector from a step row to its loop stage, drawn under the nodes."""
            r = rows[i]
            a = r.get_right() + RIGHT * 0.12
            node = loop.nodes[key].zone.shape
            b = node.get_left() + LEFT * 0.05
            c = ArcBetweenPoints(a, b, angle=-PI / 7 if b[1] > a[1] else PI / 7)
            return c.set_stroke(LOOP_COLORS[key], 1.6, opacity=0.5).set_z_index(1)

        with self.say("s06_15") as v:
            self.wait_until(v.cue("map") - 0.4)
            self.play(FadeOut(VGroup(model, badge2, tools, tools_lab, ans, nocall, userg, stop, steps)), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.08) for r in rows], lag_ratio=0.06),
                      LaggedStart(*[FadeIn(p) for p in loop.parts_in_order()], lag_ratio=0.1), run_time=1.0)
            self.add(loop)

        lines = {}
        with self.say("s06_16") as v:
            self.wait_until(v.cue("decide") - 0.3)
            lines["d"] = link(1, "decide")
            self.play(*loop.focus("decide"), Create(lines["d"]), rows[1][1].animate.set_color(BLUE),
                      glow(a_call.frame, BLUE, 4), run_time=0.6)
            self.wait_until(v.cue("act") - 0.3)
            lines["a"] = VGroup(link(3, "act"), link(4, "act"))
            self.play(*loop.focus("act"), Create(lines["a"]), rows[3][1].animate.set_color(TEAL),
                      rows[4][1].animate.set_color(TEAL), run_time=0.6)

        with self.say("s06_17") as v:
            self.wait_until(v.cue("observe") - 0.3)
            lines["o"] = link(5, "observe")
            self.play(*loop.focus("observe"), Create(lines["o"]), rows[5][1].animate.set_color(AMBER),
                      glow(res.frame, AMBER, 4), run_time=0.6)
            self.wait_until(v.cue("evaluate") - 0.3)
            lines["e"] = VGroup(link(6, "evaluate"), link(7, "evaluate"))
            self.play(*loop.focus("evaluate"), Create(lines["e"]), rows[6][1].animate.set_color(VIOLET),
                      rows[7][1].animate.set_color(VIOLET), run_time=0.6)
            self.wait_until(v.cue("work") - 0.3)
            self.play(glow(loop.arcs["ed"].line, VIOLET, 6), loop.arcs["ed"].line.animate.set_stroke(opacity=1),
                      run_time=0.6)

        md = Pill(en("model decides", 21, BLUE), BLUE, pad_x=0.2).next_to(loop.nodes["decide"], UP, buff=0.2)
        hd = Pill(en("harness does", 21, AMBER), AMBER, pad_x=0.2).next_to(loop.nodes["observe"], DOWN, buff=0.18)
        with self.say("s06_18") as v:
            self.wait_until(v.cue("decides") - 0.3)
            self.play(*loop.focus("decide"), FadeIn(md, shift=DOWN * 0.08), run_time=0.5)
            self.wait_until(v.cue("does") - 0.3)
            self.play(*loop.focus(None), *[n.state("active")[0] for n in (loop.nodes["act"], loop.nodes["observe"])],
                      FadeIn(hd, shift=UP * 0.08), run_time=0.5)

        # ---- the key line
        veil = Rectangle(width=16, height=9).set_stroke(width=0).set_fill(BG, 0.9).set_z_index(8)
        magic = VGroup(en("magic", 34, MUTED))
        strike = Line(magic.get_left() + LEFT * 0.1, magic.get_right() + RIGHT * 0.1).set_stroke(RED, 3)
        magic.add(strike)
        magic.move_to([0, 2.0, 0])
        prog = caps("a simple program loop", 18, AMBER).move_to([0, 1.15, 0])
        parts = [bn("Ask the model", 30, BLUE), bn("→", 30, MUTED), bn("do what it requests", 30, AMBER),
                 bn("→", 30, MUTED), bn("add the result", 30, TEAL), bn("→", 30, MUTED), bn("ask again.", 30, BLUE)]
        sentence = VGroup(*parts).arrange(RIGHT, buff=0.22)
        if sentence.width > 12.8:
            sentence.scale_to_fit_width(12.8)
        sentence.move_to([0, 0.2, 0])
        back = CurvedArrow(parts[-1].get_bottom() + DOWN * 0.12, parts[0].get_bottom() + DOWN * 0.12, angle=-PI / 5)
        back.set_stroke(DIM, 1.8)
        back.get_tip().set_fill(DIM, 1).set_stroke(width=0)
        for m in (magic, prog, *parts, back):
            m.set_z_index(9)                     # above the veil, which sits above the loop nodes
        with self.say("s06_19") as v:
            self.play(FadeIn(veil), run_time=0.4)
            self.wait_until(v.cue("magic") - 0.3)
            self.play(FadeIn(magic[0]), run_time=0.3)
            self.play(Create(strike), run_time=0.3)
            self.wait_until(v.cue("program") - 0.3)
            self.play(FadeIn(prog, shift=UP * 0.06), run_time=0.4)
            for key, idx in (("ask", (0,)), ("do", (1, 2)), ("add", (3, 4)), ("again", (5, 6))):
                self.wait_until(v.cue(key) - 0.25)
                self.play(*[FadeIn(parts[i], shift=RIGHT * 0.08) for i in idx], run_time=0.35)
            self.play(Create(back), run_time=0.5)
        self.wait(0.6)

        # ---- when a tool fails
        lst.remove(res)
        lst.remove(final)
        model.move_to([-4.6, 0.95, 0])
        missing = VGroup(I.file_icon(0.7, MUTED), I.cross_icon(0.34)).arrange(RIGHT, buff=0.12)
        missing_lab = mono("config.txt", 17, MUTED).next_to(missing, DOWN, buff=0.14)
        miss = VGroup(missing, missing_lab).move_to([STAGE_X, -0.9, 0])
        what_if = caps("what if a tool fails?", 16, RED).move_to([STAGE_X, 1.95, 0])
        with self.say("s06_20") as v:
            self.play(*[FadeOut(m) for m in (veil, magic, prog, *parts, back, rows, loop, md, hd, *lines.values(), res, final)],
                      run_time=0.6)
            self.play(FadeIn(model), FadeIn(tools), FadeIn(tools_lab), run_time=0.5)
            self.wait_until(v.cue("wrong") - 0.3)
            self.play(FadeIn(what_if, shift=DOWN * 0.08), run_time=0.4)
            self.wait_until(v.cue("exist") - 0.35)
            self.play(FadeIn(miss, shift=UP * 0.08), run_time=0.5)

        err = MessageCard("tool", "Error: config.txt not found", width=CARD_W, accent=RED, text_color=RED, size=18)
        lst.push(err)
        no_crash = Pill(VGroup(I.check_icon(0.22, TEAL), en("no crash", 20, TEAL)).arrange(RIGHT, buff=0.12), TEAL,
                        pad_x=0.2).move_to([STAGE_X, 0.6, 0])
        with self.say("s06_21") as v:
            self.wait_until(v.cue("crash") - 0.3)
            self.play(glow(harness.frame, AMBER, 6), FadeIn(no_crash, scale=0.9), run_time=0.6)
            self.wait_until(v.cue("error") - 0.3)
            self.play(FadeIn(err, shift=RIGHT * 0.15), run_time=0.5)

        retry = ToolCallCard("run_command", "find config.txt", width=3.9, size=18).move_to([STAGE_X, 0.95, 0])
        r_card = MessageCard("assistant", content=VGroup(mono("run_command", 16, BLUE), mono("find config.txt", 16, FG))
                             .arrange(DOWN, buff=0.06, aligned_edge=LEFT), width=CARD_W, dashed=True)
        fb = Pill(en("errors are feedback", 22, VIOLET), VIOLET, pad_x=0.24).move_to([STAGE_X, -0.5, 0])
        with self.say("s06_22") as v:
            self.play(FadeOut(no_crash), FadeOut(miss), FadeOut(what_if), run_time=0.4)
            self.wait_until(v.cue("reads") - 0.4)
            self.send(lst.cards, model, 1.0)
            self.play(model.think(0.5), run_time=0.5)
            self.wait_until(v.cue("another") - 0.3)
            self.play(FadeIn(retry, shift=RIGHT * 0.25), run_time=0.5)
            lst.push(r_card)
            self.play(FadeTransform(retry.copy(), r_card), run_time=0.7)
            self.wait_until(v.cue("feedback") - 0.3)
            self.play(FadeIn(fb, shift=UP * 0.08), run_time=0.5)
        self.clear_all(0.8)
