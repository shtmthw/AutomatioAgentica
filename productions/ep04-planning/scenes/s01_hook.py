"""01 · Busy, but lost: the recap builds Episodes 01-03 piece by piece (loop, model + harness, the
message list sent on every call, the limited context window with a summary, memory), held as one
diagram; then the hook (the agent works sixty calls and still misses half the job) and the title."""
from agentic_video.prelude import *
from memory_kit import *
from plan_kit import *

LOOP_C = np.array([-4.85, 0.3, 0])
HF_C = np.array([0.85, 0.1, 0])
CTX_C = np.array([-0.35, -0.35, 0])
MODEL_C = np.array([2.55, 1.15, 0])
NB_C = np.array([5.45, 0.35, 0])
W = 2.36


def thin(role, text=None, content=None, dashed=False):
    return SizedCard(role, text, height=0.3, width=W, size=11, content=content, dashed=dashed, tag_size=9)


class S01Hook(VoiceScene):
    SECTION = "s01"

    def construct(self):
        self.show_chapter()
        recap = Pill(en("so far · episodes 01–03", 18, MUTED), DIM, pad_x=0.22).move_to([5.0, 3.0, 0])
        with self.say("s01_01") as v:
            self.wait_until(v.cue("rebuild") - 0.3)
            self.play(FadeIn(recap, shift=DOWN * 0.08), run_time=0.5)

        # ---- 1. the loop
        loop = LoopDiagram(LOOP_C, radius=1.22, node_w=1.12, node_h=0.5, name_size=17, meanings=False, goal=False)
        tag1 = caps("episode 01", 12, DIM).move_to(LOOP_C + DOWN * 2.05)
        with self.say("s01_02") as v:
            self.wait_until(v.cue("loop") - 0.4)
            self.play(LaggedStart(*[FadeIn(m, scale=0.9) for m in loop.parts_in_order()], lag_ratio=0.08),
                      FadeIn(tag1), run_time=1.1)
            for k in ("decide", "act", "observe", "evaluate"):
                self.wait_until(v.cue(k) - 0.15)
                self.play(*loop.focus(k), run_time=0.35)
            self.wait_until(v.cue("repeat") - 0.2)
            self.play(*loop.all_normal(), glow(loop.arcs["ed"].line, VIOLET, 6), run_time=0.5)

        # ---- 2. model + harness
        model = ModelBox(1.75, 1.05, label_size=15).move_to(MODEL_C)
        hf = HarnessFrame(5.7, 5.0, label_size=17).move_to(HF_C)
        txt_out = Pill(mono("text", 15, BLUE), BLUE, pad_x=0.14).next_to(model, DOWN, buff=0.3)
        tools = VGroup(I.terminal_icon(0.36, TEAL), I.file_icon(0.38, TEAL), I.wrench_icon(0.34, TEAL)).arrange(RIGHT, buff=0.22)
        tools_lab = caps("runs the tools", 11, TEAL).next_to(tools, DOWN, buff=0.12)
        tools_g = VGroup(tools, tools_lab).move_to([2.55, -1.55, 0])
        tag2 = caps("episode 02", 12, DIM).move_to([HF_C[0] + 1.9, -2.6, 0])
        with self.say("s01_03") as v:
            self.wait_until(v.cue("model") - 0.3)
            self.play(FadeIn(model, scale=0.92), run_time=0.6)
            self.wait_until(v.cue("text") - 0.3)
            self.play(FadeIn(txt_out, shift=DOWN * 0.1), model.think(0.5), run_time=0.5)
            self.wait_until(v.cue("harness") - 0.4)
            self.play(hf.grow_from(model, 1.0), FadeIn(tag2), run_time=1.0)
            self.wait_until(v.cue("runs") - 0.3)
            self.play(FadeOut(txt_out), FadeIn(tools_g, shift=UP * 0.08), run_time=0.5)

        # ---- 3. the message list, sent whole on every call
        ctx = LiveContext(CTX_C, 2.65, 3.5, label="CONTEXT WINDOW", label_size=12, readout=False)
        cards = [thin("system", "You are a coding agent."), thin("user", "Fix the login bug."),
                 SizedCard("assistant", content=call_line("read_file", '"login.py"', 10), width=W, height=0.3, dashed=True,
                           tag_size=9),
                 thin("tool", content=mono("def login(user): …", 10, FG)),
                 SizedCard("assistant", content=call_line("edit_file", '"login.py"', 10), width=W, height=0.3, dashed=True,
                           tag_size=9),
                 thin("tool", "File updated.")]
        for c in cards:
            ctx.size(c, 0.135)
            ctx.place(c)
        list_lab = caps("message list", 12, MUTED).move_to(ctx.cw.label)
        with self.say("s01_04") as v:
            self.wait_until(v.cue("list") - 0.4)
            self.play(FadeIn(list_lab), LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in cards], lag_ratio=0.15),
                      run_time=1.2)
            self.wait_until(v.cue("every") - 0.3)
            badge = model.badge("call #7", size=13)
            self.play(FadeIn(badge, shift=DOWN * 0.06), run_time=0.4)
            self.wait_until(v.cue("whole") - 0.3)
            send_bundle(self, model, cards, run_time=0.7, scale=0.32)

        # ---- 4. the context window is limited: older cards become a summary
        summary = SummaryCard(["goal: fix the login bug", "login.py read and edited"], width=W, size=10)
        with self.say("s01_05") as v:
            self.wait_until(v.cue("cw") - 0.4)
            self.play(FadeOut(list_lab), *ctx.appear(), FadeOut(badge), run_time=0.6)
            self.wait_until(v.cue("limited") - 0.3)
            self.play(glow(ctx.cw.frame, AMBER, 6), run_time=0.5)
            self.wait_until(v.cue("summarizes") - 0.4)
            ctx.size(summary, 0.12)
            self.play(*ctx.replace(cards[1:5], summary), run_time=0.8)
            self.play(*ctx.relayout(), run_time=0.5)
        tag3 = caps("episode 03", 12, DIM).move_to([NB_C[0], -1.6, 0])

        # ---- 5. memory
        nb = Notebook(0.95).move_to(NB_C)
        note = NoteCard("Run tests before finishing", size=11, max_w=2.4)
        with self.say("s01_06") as v:
            self.wait_until(v.cue("memory") - 0.4)
            self.play(FadeIn(nb, shift=LEFT * 0.1), FadeIn(tag3), run_time=0.6)
            note.move_to(ctx.cards[-1])
            self.play(FadeIn(note, scale=0.9), run_time=0.3)
            self.play(note.animate.scale(0.8).next_to(nb, DOWN, buff=0.15), run_time=0.7)
            self.wait_until(v.cue("back") - 0.3)
            back = note.copy()
            self.play(back.animate.move_to(ctx.cw.frame.get_center() + DOWN * 0.9).set_opacity(0), glow(nb.cover, VIOLET, 5),
                      run_time=0.7)
            self.remove(back)

        # ---- the whole picture, held
        names = [("loop", loop, FG), ("model", model.frame, BLUE), ("harness", hf.frame, AMBER),
                 ("messages", VGroup(*ctx.cards), FG), ("context", ctx.cw.frame, FG), ("memory", nb.cover, VIOLET)]
        with self.say("s01_07") as v:
            for cue, m, col in names:
                self.wait_until(v.cue(cue) - 0.15)
                if cue == "loop":
                    self.play(*loop.all_lit(), run_time=0.35)
                    self.play(*loop.all_normal(), run_time=0.25)
                elif cue == "messages":
                    self.play(*[glow(c.frame if c.outline is None else c.outline, FG, 3, 0.5)
                                for c in ctx.cards if hasattr(c, "outline")], run_time=0.45)
                else:
                    self.play(glow(m, col, 7), run_time=0.45)
            self.wait_until(v.cue("so") - 0.3)
            self.play(FadeOut(recap), run_time=0.4)
        self.wait(1.0)

        # ---- the hook: a bigger job
        everything = [m for m in self.mobjects if m is not self.chapter]
        with self.say("s01_08") as v:
            self.play(*[FadeOut(m) for m in everything], run_time=0.7)

        rahul = VGroup(I.user_icon(0.42, FG), en("Rahul", 18, FG)).arrange(DOWN, buff=0.08).move_to([-5.95, 2.45, 0])
        ask = MessageCard("user", "Add a contact form to my website. It should save every message and show a thank-you note.",
                          width=10.6, size=18)
        ask.move_to([0.75, 2.45, 0])
        with self.say("s01_09") as v:
            self.wait_until(v.cue("asks") - 0.3)
            self.play(FadeIn(rahul, shift=RIGHT * 0.1), run_time=0.4)
            self.play(FadeIn(ask, shift=RIGHT * 0.15), run_time=0.6)
            self.wait_until(v.cue("save") - 0.2)
            self.play(Circumscribe(ask.body, color=DIM, stroke_width=1.5, buff=0.05, time_width=0.5), run_time=0.9)

        loop2 = LoopDiagram([-3.3, -0.3, 0], radius=1.3, node_w=1.2, node_h=0.52, name_size=18, meanings=False, goal=False)
        counter = CallCounter(1).move_to([-3.3, -2.35, 0])
        tok = Token(TEAL, 0.09).move_to(loop2.nodes["decide"])
        calls = [("read_file", '"index.html"'), ("edit_file", '"contact.html"'), ("run_command", '"list files"'),
                 ("read_file", '"style.css"'), ("edit_file", '"contact.html"'), ("edit_file", '"form.css"'),
                 ("read_file", '"contact.html"'), ("edit_file", '"index.html"')]
        call_cards = [ToolCallMsg(t, a, width=4.6, size=14, height=0.42) for t, a in calls]
        slots = [np.array([3.4, 1.1 - i * 0.55, 0]) for i in range(4)]

        def lap(rt=0.5):
            path = Circle(radius=1.3).move_to(loop2.center).rotate(PI / 2).flip(UP)
            self.play(MoveAlongPath(tok, path), rate_func=linear, run_time=rt)

        shown = []

        def flash(i):
            c = call_cards[i % len(call_cards)]
            c.move_to(slots[len(shown) % 4])
            anims = [FadeIn(c, shift=LEFT * 0.2)]
            if len(shown) >= 4:
                anims.append(FadeOut(shown[-4]))
            shown.append(c)
            return anims

        with self.say("s01_10") as v:
            self.wait_until(v.cue("work") - 0.3)
            self.play(LaggedStart(*[FadeIn(m, scale=0.92) for m in loop2.parts_in_order()], lag_ratio=0.05),
                      FadeIn(counter), FadeIn(tok), run_time=0.8)
            k = 0
            for cue, n in (("c10", 10), ("c30", 30), ("c60", 60)):
                self.wait_until(v.cue(cue) - 0.25)
                self.play(*counter.to(n), *flash(k), run_time=0.3)
                k += 1
                lap(0.45)
            self.wait_until(v.cue("after") - 0.3)
            for _ in range(3):
                self.play(*flash(k), run_time=0.22)
                k += 1
                lap(0.35)

        done = MessageCard("assistant", "Done! The contact form is ready.", width=4.6, size=18).move_to([3.4, 1.1, 0])
        with self.say("s01_11") as v:
            self.wait_until(v.cue("done") - 0.4)
            self.play(*[FadeOut(c) for c in shown[-4:]], FadeOut(tok), *loop2.all_dim(), run_time=0.4)
            self.play(FadeIn(done, shift=UP * 0.1), run_time=0.5)

        items = [("Form page", True, "form"), ("Saves every message", False, "saving"), ("Thank-you note", False, "thank")]
        rows = VGroup()
        for t, ok, _ in items:
            mark = I.check_icon(0.26, TEAL) if ok else I.cross_icon(0.26, RED)
            box = RoundedRectangle(width=0.42, height=0.42, corner_radius=0.08).set_stroke(TEAL if ok else RED, 1.5)
            mark.move_to(box)
            rows.add(VGroup(bn(t, 20, FG), VGroup(box, mark)))
        for r in rows:
            r[1].move_to(r[0].get_right() * 0 + RIGHT * 0)
        lab_w = max(r[0].width for r in rows)
        for i, r in enumerate(rows):
            r[0].move_to([1.7, -0.25 - i * 0.62, 0], aligned_edge=LEFT)
            r[1].move_to([1.7 + lab_w + 0.55, -0.25 - i * 0.62, 0])
        head = caps("what rahul asked for", 13, MUTED).move_to([1.7, 0.35, 0], aligned_edge=LEFT)
        with self.say("s01_12") as v:
            self.wait_until(v.cue("check") - 0.3)
            self.play(FadeIn(head, shift=DOWN * 0.06), run_time=0.4)
            for i, (_, ok, cue) in enumerate(items):
                self.wait_until(v.cue(cue) - 0.25)
                self.play(FadeIn(rows[i][0], shift=RIGHT * 0.1), FadeIn(rows[i][1][0]), run_time=0.3)
                self.wait_until(v.cue(cue + "_v") - 0.15)
                self.play(FadeIn(rows[i][1][1], scale=1.4), run_time=0.3)

        q = VGroup(en("60 steps of hard work.", 30, FG, italic=False), en("Why is half the job missing?", 30, RED,
                                                                            italic=False)).arrange(DOWN, buff=0.2)
        q.move_to([-3.3, -0.3, 0])
        with self.say("s01_13") as v:
            self.wait_until(v.cue("sixty") - 0.4)
            self.play(FadeOut(loop2), counter.animate.move_to([-3.3, 1.0, 0]), run_time=0.5)
            self.play(FadeIn(q[0], shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("why") - 0.3)
            self.play(FadeIn(q[1], shift=UP * 0.08), run_time=0.5)

        strip = VGroup(*[RoundedRectangle(width=0.3, height=0.3, corner_radius=0.06).set_stroke(TEAL, 1.4).set_fill(TEAL, 0.2)
                         for _ in range(12)]).arrange(RIGHT, buff=0.1).move_to([-3.3, -0.55, 0])
        busy = caps("busy at every step", 13, TEAL).next_to(strip, DOWN, buff=0.2)
        with self.say("s01_14") as v:
            self.wait_until(v.cue("lazy") - 0.3)
            self.play(q.animate.scale(0.62).move_to([-3.3, 0.35, 0]).fade(0.4), FadeOut(counter), run_time=0.5)
            self.wait_until(v.cue("hard") - 0.3)
            self.play(LaggedStart(*[FadeIn(b, scale=0.6) for b in strip], lag_ratio=0.12), FadeIn(busy), run_time=1.2)

        spot = Circle(radius=0.36).set_stroke(FG, 2.0).move_to(strip[-1])
        ahead = caps("one step ahead", 13, FG).next_to(spot, DOWN, buff=0.14)
        with self.say("s01_15") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(strip[:-1].animate.fade(0.7), FadeIn(spot, scale=1.3), FadeIn(ahead), FadeOut(busy), run_time=0.6)
            self.wait_until(v.cue("lost") - 0.3)
            self.play(ask.animate.fade(0.8), rahul.animate.fade(0.6), run_time=0.9)
            self.play(glow(rows[1][1][0], RED, 5), glow(rows[2][1][0], RED, 5), run_time=0.6)

        t1 = spaced("PLANNING", 72, FG, tracking=0.4, weight=LIGHT)
        rule = Line(LEFT * 1.4, RIGHT * 1.4).set_stroke(FAINT, 1.6)
        sub = spaced("AGENTIC AI · EPISODE 04", 20, MUTED, tracking=0.6, weight=NORMAL)
        card = VGroup(t1, rule, sub).arrange(DOWN, buff=0.4).move_to(UP * 0.35)
        with self.say("s01_16") as v:
            self.wait_until(v.cue("fix") - 0.3)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.6)
            self.wait_until(v.cue("title") - 0.5)
            self.play(FadeIn(t1, shift=UP * 0.12), run_time=0.9)
            self.play(Create(rule), FadeIn(sub, shift=UP * 0.06), run_time=0.7)
        self.wait(1.2)
        self.clear_all(0.6)
