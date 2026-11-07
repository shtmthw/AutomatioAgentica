"""03 · Meet the harness: definition, the closed-room analogy, its responsibilities."""
from agentic_video.prelude import *


def duty(i, text, color=AMBER, size=22):
    g = VGroup(en(str(i), size, color, italic=False, weight=NORMAL), en(text, size, FG)).arrange(RIGHT, buff=0.16)
    return Pill(g, color, pad_x=0.26, pad_y=0.12)


class S03Harness(VoiceScene):
    SECTION = "s03"

    def construct(self):
        self.show_chapter()
        model = ModelBox(2.8, 1.7).move_to([0, 0.45, 0])
        harness = HarnessFrame(11.8, 4.7).move_to([0, 0.3, 0])
        with self.say("s03_01") as v:
            self.play(FadeIn(model, scale=0.92), run_time=0.5)
            self.wait_until(v.cue("harness") - 0.3)
            self.play(harness.grow_from(model, 1.0))

        ordinary = en("an ordinary program", 22, MUTED).next_to(harness.head, RIGHT, buff=0.3)
        jobs = VGroup(*[Pill(VGroup(ic, en(t, 21, FG)).arrange(RIGHT, buff=0.14), AMBER, pad_x=0.24, pad_y=0.11)
                        for ic, t in ((I.loop_icon(0.26, AMBER), "runs the loop"),
                                      (VGroup(en("⇄", 24, AMBER)), "talks to the model"),
                                      (I.wrench_icon(0.26, AMBER), "performs actions"))]).arrange(RIGHT, buff=0.28)
        jobs.move_to([0, -1.32, 0])
        with self.say("s03_02") as v:
            self.wait_until(v.cue("ordinary") - 0.3)
            self.play(FadeIn(ordinary, shift=LEFT * 0.1), run_time=0.5)
            for i, w in enumerate(("runs", "talks", "performs")):
                self.wait_until(v.cue(w) - 0.3)
                anims = [FadeIn(jobs[i], shift=UP * 0.1)]
                if w == "talks":
                    anims.append(model.think(0.6))
                self.play(*anims, run_time=0.5)

        # ---- the analogy: a closed room with a slot
        pic = en("a simple picture", 34, MUTED)
        with self.say("s03_03") as v:
            self.wait_until(v.cue("picture") - 0.4)
            self.play(*[FadeOut(m) for m in (model, harness, ordinary, jobs)], run_time=0.6)
            self.play(FadeIn(pic, scale=0.95), run_time=0.4)

        c = np.array([-3.0, 0.35, 0])
        RW, RH = 3.9, 3.1
        x0, x1, y0, y1 = c[0] - RW / 2, c[0] + RW / 2, c[1] - RH / 2, c[1] + RH / 2
        sy, sh = c[1], 0.36                                   # slot centre and height
        floor = Rectangle(width=RW, height=RH).move_to(c).set_stroke(width=0).set_fill(PANEL, 1)
        walls = VGroup(Line([x0, y1, 0], [x1, y1, 0]), Line([x0, y0, 0], [x1, y0, 0]), Line([x0, y0, 0], [x0, y1, 0]),
                       Line([x1, y1, 0], [x1, sy + sh / 2, 0]), Line([x1, sy - sh / 2, 0], [x1, y0, 0]))
        walls.set_stroke(FG, 3.2)
        slot = VGroup(Line([x1 - 0.14, sy + sh / 2, 0], [x1 + 0.14, sy + sh / 2, 0]),
                      Line([x1 - 0.14, sy - sh / 2, 0], [x1 + 0.14, sy - sh / 2, 0])).set_stroke(AMBER, 3)
        slot_lab = en("slot", 20, AMBER).move_to([x1 + 0.45, sy + 0.42, 0])
        no_doors = en("no doors", 20, DIM).move_to([c[0], y1 - 0.3, 0])
        dm = I.user_icon(0.95, BLUE).move_to([c[0] - 0.4, c[1] + 0.05, 0])
        dm_lab = en("decision-maker", 22, BLUE).next_to(dm, DOWN, buff=0.18)
        with self.say("s03_04") as v:
            self.play(FadeOut(pic), run_time=0.3)
            self.wait_until(v.cue("decision") - 0.3)
            self.play(FadeIn(floor), FadeIn(dm, shift=UP * 0.1), FadeIn(dm_lab), run_time=0.6)
            self.wait_until(v.cue("closed") - 0.3)
            self.play(Create(walls), FadeIn(no_doors), run_time=0.8)
            self.wait_until(v.cue("slot") - 0.3)
            self.play(FadeIn(slot), FadeIn(slot_lab, shift=DOWN * 0.06), glow(slot, AMBER, 6), run_time=0.6)

        asst = I.user_icon(0.95, AMBER).move_to([2.35, c[1] + 0.05, 0])
        asst_lab = en("assistant", 22, AMBER).next_to(asst, DOWN, buff=0.18)
        note_out = paper(0.72, 0.3, lines=2).move_to([1.25, sy, 0])
        note_in = note_out.copy().move_to([x1 - 0.75, sy, 0])
        with self.say("s03_05") as v:
            self.wait_until(v.cue("assistant") - 0.3)
            self.play(FadeIn(asst, shift=LEFT * 0.1), FadeIn(asst_lab), run_time=0.5)
            self.wait_until(v.cue("note") - 0.3)
            self.play(FadeIn(note_out, shift=LEFT * 0.1), run_time=0.4)
            self.play(note_out.animate.move_to(note_in), run_time=0.9)

        reply = VGroup(mono("open config.txt", 18, FG), bn("what does it say?", 18, MUTED)).arrange(DOWN, buff=0.08)
        reply_card = VGroup(RoundedRectangle(width=reply.width + 0.36, height=reply.height + 0.26, corner_radius=0.08)
                            .set_stroke(BLUE, 1.5).set_fill(PANEL, 1), reply)
        reply.move_to(reply_card[0])
        reply_card.move_to([2.35, 2.05, 0])
        slip = paper(0.72, 0.3, lines=2, color=BLUE).move_to([x1 - 0.75, sy, 0])
        with self.say("s03_06") as v:
            self.wait_until(v.cue("reads") - 0.3)
            self.play(glow(note_out.sheet, BLUE, 5), pulse(dm, 1.06), run_time=0.6)
            self.play(FadeOut(note_out), run_time=0.3)
            self.wait_until(v.cue("open") - 0.45)
            self.play(FadeIn(slip), run_time=0.25)
            self.play(slip.animate.move_to([1.25, sy, 0]), run_time=0.7)
            self.play(FadeIn(reply_card, shift=UP * 0.1), run_time=0.5)

        cfg = I.file_icon(0.85, TEAL).move_to([4.75, c[1] + 0.1, 0])
        cfg_lab = mono("config.txt", 17, TEAL).next_to(cfg, DOWN, buff=0.16)
        found = mono("port = 8080", 18, TEAL).next_to(cfg_lab, DOWN, buff=0.22)
        updated = paper(0.86, 0.36, lines=3).move_to([1.25, sy, 0])
        with self.say("s03_07") as v:
            self.wait_until(v.cue("opens") - 0.4)
            self.play(FadeIn(cfg, shift=LEFT * 0.1), FadeIn(cfg_lab), FadeOut(slip), run_time=0.5)
            self.play(glow(cfg, TEAL, 5), FadeIn(found, shift=DOWN * 0.08), run_time=0.6)
            self.play(found.copy().animate.scale(0.3).move_to(updated).set_opacity(0), FadeIn(updated), run_time=0.6)
            self.wait_until(v.cue("updated") - 0.35)
            self.play(updated.animate.move_to([x1 - 0.82, sy, 0]), run_time=0.9)

        def tag(text, color):
            return Pill(en(text, 22, color, italic=False, weight=NORMAL), color, pad_x=0.24, pad_y=0.09)

        t_model = tag("= MODEL", BLUE).move_to([dm.get_x(), y0 - 0.38, 0])
        t_harness = tag("= HARNESS", AMBER).move_to([asst.get_x(), y0 - 0.38, 0])
        t_tool = tag("= TOOL", TEAL).move_to([cfg.get_x(), y0 - 0.38, 0])
        with self.say("s03_08") as v:
            for w, t, who in (("model", t_model, dm), ("harness", t_harness, asst), ("tool", t_tool, cfg)):
                self.wait_until(v.cue(w) - 0.3)
                self.play(FadeIn(t, shift=UP * 0.08), pulse(who, 1.08), run_time=0.5)

        # ---- what the harness does
        big = HarnessFrame(12.7, 5.35).move_to([0, 0.18, 0])
        model2 = ModelBox(2.8, 1.6).move_to([0, 0.42, 0])
        duties = [duty(1, "stores the conversation"), duty(2, "sends it to the model"), duty(3, "reads the reply"),
                  duty(4, "runs the tools it asks for"), duty(5, "sends results back"), duty(6, "decides when to stop"),
                  duty(7, "enforces permissions & limits")]
        for i, d in enumerate(duties[:6]):
            col, row = divmod(i, 3)
            x = -4.05 if col == 0 else 4.05
            d.move_to([x, 1.55 - row * 1.12, 0])
        duties[6].move_to([0, -1.72, 0])
        links = VGroup(*[DashedLine(d.get_right() if d.get_x() < 0 else d.get_left(),
                                    [model2.frame.get_left()[0] if d.get_x() < 0 else model2.frame.get_right()[0],
                                     np.clip(d.get_y(), model2.frame.get_bottom()[1] + 0.2, model2.frame.get_top()[1] - 0.2), 0],
                                    dash_length=0.06).set_stroke(AMBER, 1.2, opacity=0.45) for d in duties[:6]])
        with self.say("s03_09") as v:
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.6)
            self.play(FadeIn(big), FadeIn(model2, scale=0.95), run_time=0.6)
            self.wait_until(v.cue("stores") - 0.3)
            self.play(FadeIn(duties[0], shift=RIGHT * 0.1), Create(links[0]), run_time=0.5)
            self.wait_until(v.cue("sends") - 0.3)
            self.play(FadeIn(duties[1], shift=RIGHT * 0.1), Create(links[1]), model2.think(0.6), run_time=0.6)

        with self.say("s03_10") as v:
            for i, w in ((2, "reads"), (3, "executes"), (4, "results")):
                self.wait_until(v.cue(w) - 0.3)
                self.play(FadeIn(duties[i], shift=RIGHT * 0.1 if i < 3 else LEFT * 0.1), Create(links[i]), run_time=0.5)

        with self.say("s03_11") as v:
            self.wait_until(v.cue("decides") - 0.3)
            self.play(FadeIn(duties[5], shift=LEFT * 0.1), Create(links[5]), run_time=0.5)
            self.wait_until(v.cue("enforces") - 0.3)
            self.play(FadeIn(duties[6], shift=UP * 0.1), run_time=0.5)
            self.play(glow(big.frame, AMBER, 6), run_time=0.7)

        # ---- the key line
        veil = Rectangle(width=16, height=9).set_stroke(width=0).set_fill(BG, 0.88)
        k1 = bn("The model decides.", 50, BLUE)
        k2 = bn("The harness does.", 50, AMBER)
        VGroup(k1, k2).arrange(DOWN, buff=0.35).move_to([0, 0.35, 0])
        with self.say("s03_12") as v:
            self.play(FadeIn(veil), run_time=0.5)
            self.wait_until(v.cue("decides") - 0.5)
            self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.5)
            self.wait_until(v.cue("does") - 0.4)
            self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.5)
        self.wait(0.5)

        # ---- an agent = model + harness + tools
        badge = AgentBadge("AI agent", size=30).move_to([-5.0, 0.35, 0])
        m = I.chip_labeled(1.2, "model", BLUE)
        hf = VGroup(RoundedRectangle(width=1.7, height=1.2, corner_radius=0.18).set_stroke(AMBER, 2.2).set_fill(AMBER, 0.05),
                    I.gear(0.42, AMBER))
        hf[1].move_to(hf[0])
        h_lab = en("harness", 24, AMBER).next_to(hf, DOWN, buff=0.16)
        tl = VGroup(I.file_icon(0.42, TEAL), I.terminal_icon(0.38, TEAL), I.globe_icon(0.42, TEAL)).arrange(RIGHT, buff=0.18)
        t_lab = en("tools", 24, TEAL).next_to(tl, DOWN, buff=0.22)
        m_lab = VGroup()   # chip_labeled carries its label
        eq = en("=", 44, MUTED)
        p1, p2 = en("+", 44, MUTED), en("+", 44, MUTED)
        row = VGroup(eq, m, p1, VGroup(hf, h_lab), p2, VGroup(tl, t_lab)).arrange(RIGHT, buff=0.42)
        row.next_to(badge, RIGHT, buff=0.42)
        full = VGroup(badge, row).move_to([0, 0.45, 0])
        with self.say("s03_13") as v:
            self.play(*[FadeOut(x) for x in self.mobjects if x is not self.chapter], run_time=0.6)
            self.wait_until(v.cue("agent") - 0.4)
            self.play(FadeIn(badge, scale=0.9), FadeIn(eq), run_time=0.5)
            self.wait_until(v.cue("model") - 0.3)
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.4)
            self.wait_until(v.cue("harness") - 0.3)
            self.play(FadeIn(p1), FadeIn(hf, shift=UP * 0.1), FadeIn(h_lab), run_time=0.4)
            self.wait_until(v.cue("tools") - 0.3)
            self.play(FadeIn(p2), FadeIn(tl, shift=UP * 0.1), FadeIn(t_lab), run_time=0.4)
            self.play(glow(m.body, BLUE, 5), glow(hf[0], AMBER, 5), *[glow(x, TEAL, 4) for x in tl], run_time=0.8)

        neq = VGroup(en("model", 34, BLUE), en("≠", 38, FG), en("agent", 34, TEAL)).arrange(RIGHT, buff=0.28)
        neq.move_to([0, -1.55, 0])
        ep1 = caps("as in episode 01", 15, DIM).next_to(neq, DOWN, buff=0.2)
        with self.say("s03_14") as v:
            self.wait_until(v.cue("last") - 0.3)
            self.play(FadeIn(ep1), run_time=0.4)
            self.wait_until(v.cue("not") - 0.4)
            self.play(FadeIn(neq, shift=UP * 0.1), run_time=0.6)
        self.clear_all(0.8)
