"""07 · Memory: sessions, the rule that is lost when a session ends, the notebook (memory) inside the
harness but outside the model and the context window, save_note, notes loaded back in session 2,
the unchanged model, and what is worth saving."""
from agentic_video.prelude import *
from memory_kit import *

W = 3.08
CW_C = np.array([-4.3, -0.32, 0])
MODEL_C = np.array([0.35, 0.8, 0])
NB_C = np.array([4.7, 1.15, 0])
NOTE_X = 4.75


def thin(role, text=None, content=None, h=0.28, size=12, wrap=None):
    return SizedCard(role, text, height=h, width=W, size=size, content=content, wrap=wrap)


def call(tool, arg):
    return ToolCallMsg(tool, arg, width=W, size=12, height=0.28)


def note_slot(i):
    return np.array([NOTE_X, 0.15 - i * 0.5, 0])


class S07Memory(VoiceScene):
    SECTION = "s07"

    def construct(self):
        self.show_chapter()
        hf = HarnessFrame(13.5, 5.2).move_to([0, -0.08, 0])
        hf.head.move_to(hf.frame.get_corner(UR) + LEFT * (hf.head.width / 2 + 0.32) + DOWN * (hf.head.height / 2 + 0.24))
        ctx = LiveContext(CW_C, 3.4, 4.3, label_size=13)
        model = ModelBox(2.3, 1.3).move_to(MODEL_C)
        nb = Notebook(0.85).move_to(NB_C)
        session = {"pill": None}

        def set_session(n, extra=None):
            p = session_pill(n)
            if extra:
                p = Pill(VGroup(caps(f"session {n}", 15, MEMORY), caps(extra, 13, MUTED)).arrange(RIGHT, buff=0.14), MEMORY,
                         pad_x=0.2, pad_y=0.08)
            p.move_to([0, 2.95, 0])
            old = session["pill"]
            session["pill"] = p
            return [FadeIn(p, shift=DOWN * 0.08)] + ([FadeOut(old)] if old is not None else [])

        def wipe(text="SESSION 1 ENDS"):
            cards = ctx.clear()
            extra = [session["pill"]] if session["pill"] is not None else []
            session["pill"] = None
            session_wipe(self, cards + extra + list(wipe_also), text=text)
            wipe_also.clear()
            self.play(*ctx.meter(), run_time=0.3)

        wipe_also = []

        # ---- one conversation; what about tomorrow?
        convo = [thin("system", "You are a coding agent."), thin("user", "Why does total() crash?"),
                 call("read_file", '"math_utils.py"'), thin("tool", content=mono("def total(items): …", 11, FG))]
        for c in convo:
            ctx.place(c)
        tomorrow = Pill(en("tomorrow?", 26, FG), MEMORY, pad_x=0.28, pad_y=0.12).move_to([4.6, 0.6, 0])
        with self.say("s07_01") as v:
            self.wait_until(v.cue("one") - 0.5)
            self.play(FadeIn(hf), FadeIn(model, scale=0.95), *ctx.appear(), *[FadeIn(c) for c in convo], run_time=0.8)
            self.wait_until(v.cue("tomorrow") - 0.3)
            self.play(FadeIn(tomorrow, shift=LEFT * 0.1), run_time=0.5)

        bar = Line([2.45, -1.2, 0], [6.15, -1.2, 0]).set_stroke(MEMORY, 3)
        ticks = VGroup(*[Line(UP * 0.13, DOWN * 0.13).set_stroke(MEMORY, 3).move_to(p) for p in (bar.get_start(), bar.get_end())])
        s_lab = caps("session", 16, MEMORY).next_to(bar, UP, buff=0.18)
        st = caps("start", 12, MUTED).next_to(ticks[0], DOWN, buff=0.1)
        en_ = caps("end", 12, MUTED).next_to(ticks[1], DOWN, buff=0.1)
        sdef = en("one continuous conversation", 19, MUTED).next_to(st, DOWN, buff=0.14).align_to(bar, LEFT)
        timeline = VGroup(bar, ticks, s_lab, st, en_, sdef)
        with self.say("s07_02") as v:
            self.wait_until(v.cue("session") - 0.3)
            self.play(FadeIn(s_lab, shift=DOWN * 0.06), FadeIn(sdef), tomorrow.animate.fade(0.5), run_time=0.5)
            self.wait_until(v.cue("start") - 0.3)
            self.play(Create(ticks[0]), FadeIn(st), run_time=0.3)
            self.play(Create(bar), run_time=0.5)
            self.wait_until(v.cue("end") - 0.2)
            self.play(Create(ticks[1]), FadeIn(en_), run_time=0.3)

        # ---- session 1 without memory
        rule = thin("user", "In this project, always run the tests before you say a task is done.", h=0.46, wrap=40)
        s1 = [thin("system", "You are a coding agent."), rule]
        run1 = call("run_command", '"run tests"')
        with self.say("s07_03") as v:
            gone = ctx.clear()
            self.play(FadeOut(VGroup(*gone)), FadeOut(tomorrow), FadeOut(timeline), run_time=0.45)
            self.play(*set_session(1), *ctx.add(s1[0], shift=DOWN * 0.1), run_time=0.45)
            self.wait_until(v.cue("always") - 0.6)
            self.play(*ctx.add(rule), run_time=0.5)
            self.wait_until(v.cue("follows") - 0.4)
            self.play(*ctx.add(run1), model.think(0.5), run_time=0.5)
            ok = I.check_icon(0.26, TEAL).next_to(run1, RIGHT, buff=0.6)
            self.play(FadeIn(ok, scale=1.2), run_time=0.3)
            wipe_also.append(ok)

        with self.say("s07_04") as v:
            self.wait_until(v.cue("ends") - 0.4)
            wipe()

        fixed = thin("assistant", "Done! The login bug is fixed.")
        skip = VGroup(I.warn_icon(0.28, RED), caps("tests not run", 12, RED)).arrange(RIGHT, buff=0.1)
        ghost = thin("user", "In this project, always run the tests before you say a task is done.", h=0.46, wrap=40)
        ghost.move_to([NOTE_X - 0.2, -0.9, 0]).fade(0.7)
        cross = VGroup(I.cross_icon(0.22), caps("gone", 12, RED)).arrange(RIGHT, buff=0.1).next_to(ghost, UP, buff=0.12,
                                                                                                  aligned_edge=LEFT)
        with self.say("s07_05") as v:
            self.wait_until(v.cue("two") - 0.4)
            self.play(*set_session(2), *ctx.add(thin("system", "You are a coding agent."), shift=DOWN * 0.1), run_time=0.5)
            self.play(*ctx.add(thin("user", "Fix the login bug.")), run_time=0.4)
            self.wait_until(v.cue("skips") - 0.3)
            self.play(*ctx.add(fixed), run_time=0.45)
            skip.move_to(MODEL_C + DOWN * 1.15)
            self.play(FadeIn(skip, shift=LEFT * 0.08), run_time=0.4)
            self.wait_until(v.cue("gone") - 0.4)
            self.play(FadeIn(ghost), FadeIn(cross), run_time=0.5)

        # ---- memory: a notebook outside the window
        outside = VGroup(caps("outside the model", 12, MUTED), caps("outside the window", 12, MUTED)).arrange(DOWN, buff=0.05)
        outside.next_to(nb, LEFT, buff=0.3)
        with self.say("s07_06") as v:
            self.wait_until(v.cue("memory") - 0.4)
            self.play(FadeOut(ghost), FadeOut(cross), FadeIn(nb.icon, scale=0.9), FadeIn(nb.label), run_time=0.6)
            self.wait_until(v.cue("outside") - 0.3)
            self.play(FadeIn(outside, shift=RIGHT * 0.08), glow(nb.cover, MEMORY, 5), run_time=0.5)
            self.wait_until(v.cue("files") - 0.3)
            self.play(FadeIn(nb.sub, shift=UP * 0.05), run_time=0.4)
            self.wait_until(v.cue("back") - 0.3)
            self.play(pulse(nb.icon, 1.08), run_time=0.5)

        desk_p = Pill(en("the desk", 18, AMBER), AMBER, pad_x=0.16, pad_y=0.06)
        desk_p.move_to(ctx.cw.label)
        drawer = Pill(en("notebook in the drawer", 18, MEMORY), MEMORY, pad_x=0.16, pad_y=0.06).next_to(nb, DOWN, buff=0.14)
        with self.say("s07_07") as v:
            self.wait_until(v.cue("desk") - 0.3)
            self.play(FadeOut(outside), FadeOut(ctx.cw.label), FadeIn(desk_p, scale=0.9), run_time=0.45)
            self.wait_until(v.cue("notebook") - 0.3)
            self.play(FadeIn(drawer, scale=0.9), run_time=0.45)
            self.wait_until(v.cue("cleared") - 0.4)
            cards = ctx.clear()
            self.play(*[FadeOut(c, shift=LEFT * 0.3) for c in cards], FadeOut(skip), *ctx.meter(), run_time=0.6)
            self.wait_until(v.cue("stays") - 0.3)
            self.play(glow(nb.cover, MEMORY, 6), pulse(nb.icon, 1.1), run_time=0.6)

        # ---- session 1 again, with memory
        rule2 = thin("user", "In this project, always run the tests before you say a task is done. Remember this.",
                     h=0.62, wrap=40)
        with self.say("s07_08") as v:
            self.wait_until(v.cue("again") - 0.4)
            self.play(FadeOut(desk_p), FadeOut(drawer), FadeIn(ctx.cw.label), run_time=0.4)
            self.play(*set_session(1, "with memory"), *ctx.add(thin("system", "You are a coding agent."), shift=DOWN * 0.1),
                      run_time=0.5)
            self.wait_until(v.cue("remember") - 1.0)
            self.play(*ctx.add(rule2), run_time=0.5)
            self.play(glow(rule2.frame, MEMORY, 5), run_time=0.5)

        req = ToolCallCard("save_note", 'text = "Always run tests before finishing a task."', width=4.3, size=17)
        req.move_to([MODEL_C[0], -1.15, 0])
        ex = caps("example tool name", 11, MUTED).next_to(req, DOWN, buff=0.08, aligned_edge=RIGHT)
        msg = call("save_note", '"Always run tests…"')
        with self.say("s07_09") as v:
            self.wait_until(v.cue("call") - 0.4)
            self.play(model.think(0.5), FadeIn(req, shift=DOWN * 0.15), run_time=0.6)
            self.play(FadeIn(ex), run_time=0.3)
            self.wait_until(v.cue("save") - 0.2)
            slot = ctx.next_point(msg)
            ctx.cards.append(msg)
            self.play(TransformFromCopy(req, msg.move_to(slot)), *ctx.meter(), run_time=0.6)

        note1 = NoteCard("Always run tests before finishing a task.", width=3.2, size=13)
        note1.move_to([NOTE_X, -1.15, 0])                 # free space under the notebook, beside the tool call
        saved = thin("tool", "Note saved.")
        with self.say("s07_10") as v:
            self.wait_until(v.cue("executes") - 0.3)
            self.play(glow(hf.frame, AMBER, 6), pulse(hf.head, 1.1), run_time=0.6)
            self.wait_until(v.cue("saves") - 0.3)
            self.play(FadeIn(note1, scale=0.9), run_time=0.3)
            self.play(note1.animate.move_to(note_slot(0)), FadeOut(req), FadeOut(ex), run_time=0.7)
            self.play(glow(nb.cover, MEMORY, 5), run_time=0.4)
            self.wait_until(v.cue("tool") - 0.3)
            self.play(*ctx.add(saved), run_time=0.45)

        with self.say("s07_11") as v:
            self.wait_until(v.cue("ends") - 0.4)
            wipe()
            self.wait_until(v.cue("keeps") - 0.3)
            self.play(glow(note1.frame, MEMORY, 6), pulse(nb.icon, 1.08), run_time=0.6)

        # ---- session 2: the harness puts the notes back
        sys2 = thin("system", "You are a coding agent.")
        block = NotesBlock(["Always run tests before finishing a task."], width=W, size=12)
        ctx.size(block, 0.05)
        with self.say("s07_12") as v:
            self.wait_until(v.cue("two") - 0.4)
            self.play(*set_session(2), *ctx.add(sys2, shift=DOWN * 0.1), run_time=0.5)
            self.wait_until(v.cue("puts") - 0.5)
            tmp = note1.copy()
            self.play(tmp.animate.move_to(ctx.next_point(block)).scale(0.9), run_time=0.8)
            ctx.place(block)
            self.play(FadeTransform(tmp, block), *ctx.meter(), run_time=0.5)

        with self.say("s07_13") as v:
            self.wait_until(v.cue("fix") - 0.3)
            self.play(*ctx.add(thin("user", "Fix the login bug.")), run_time=0.45)

        run2 = call("run_command", '"run tests"')
        with self.say("s07_14") as v:
            self.wait_until(v.cue("fixes") - 0.3)
            self.play(*ctx.add(call("edit_file", '"login.py"')), model.think(0.4), run_time=0.4)
            self.play(*ctx.add(thin("tool", "File updated successfully")), run_time=0.4)
            self.wait_until(v.cue("run") - 0.5)
            self.play(*ctx.add(run2), model.think(0.4), run_time=0.45)
            link = CurvedArrow(block.frame.get_right() + RIGHT * 0.05, run2.frame.get_right() + RIGHT * 0.05, angle=-1.6,
                               color=MEMORY, stroke_width=2.2, tip_length=0.12)
            self.play(Create(link), run_time=0.6)

        same = unchanged_badge(model)
        both = caps("same model in session 1 and 2", 12, MUTED).next_to(same, DOWN, buff=0.1)
        with self.say("s07_15") as v:
            self.wait_until(v.cue("same") - 0.3)
            self.play(FadeIn(same, shift=UP * 0.06), FadeIn(both), glow(model.frame, BLUE, 5), run_time=0.6)
            self.wait_until(v.cue("learn") - 0.3)
            self.play(pulse(same, 1.1), run_time=0.5)

        with self.say("s07_16") as v:
            self.wait_until(v.cue("note") - 0.3)
            self.play(glow(block.frame, MEMORY, 6), pulse(block, 1.04), run_time=0.6)
            self.wait_until(v.cue("text") - 0.4)
            b = bundle_copy(ctx.cards, 0.3).move_to(ctx.group())
            self.play(b.animate.move_to(model.in_port + LEFT * 0.3).scale(0.6), run_time=0.8)
            self.play(FadeOut(b, scale=0.4), model.think(0.5), run_time=0.45)

        k1 = Pill(VGroup(caps("model", 13, BLUE), en("doesn't remember", 21, FG)).arrange(RIGHT, buff=0.14), BLUE, pad_x=0.22)
        k2 = Pill(VGroup(caps("harness", 13, AMBER), en("writes it down · brings it back", 21, FG)).arrange(RIGHT, buff=0.14),
                  AMBER, pad_x=0.22)
        keys = VGroup(k1, k2).arrange(DOWN, buff=0.18).move_to([MODEL_C[0] + 0.3, -1.55, 0])
        with self.say("s07_17") as v:
            self.wait_until(v.cue("remember") - 0.3)
            self.play(FadeOut(both), FadeIn(k1, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("writes") - 0.3)
            self.play(FadeIn(k2, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("brings") - 0.3)
            self.play(glow(k2.frame, AMBER, 5), run_time=0.5)

        # ---- what is worth saving
        kinds = [("fact", "Tests run with: run tests"), ("rule", "Do not rename public functions"),
                 ("progress", "Login bug: cause found, fix not written yet")]
        notes = []
        for i, (kind, text) in enumerate(kinds):
            n = NoteCard(text, width=3.2, size=13).move_to(note_slot(i + 1))
            lab = caps(kind, 11, MEMORY).next_to(n, LEFT, buff=0.12)
            notes.append(VGroup(n, lab))
        with self.say("s07_18") as v:
            self.wait_until(v.cue("facts") - 0.4)
            self.play(FadeOut(keys), FadeIn(notes[0], shift=DOWN * 0.15), run_time=0.5)
            self.wait_until(v.cue("rules") - 0.3)
            self.play(FadeIn(notes[1], shift=DOWN * 0.15), run_time=0.45)

        with self.say("s07_19") as v:
            self.wait_until(v.cue("progress") - 0.3)
            self.play(FadeIn(notes[2], shift=DOWN * 0.15), run_time=0.45)
            self.play(glow(nb.cover, MEMORY, 5), run_time=0.5)
        self.clear_all(0.6)
