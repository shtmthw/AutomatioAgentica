"""08 · When does the loop stop? Normal stop, step limit, human approval, the model asks."""
from agentic_video.prelude import *

LC = np.array([-2.75, -0.05, 0])


def way(i, icon, title, sub, color):
    num = en(str(i), 30, color, italic=False, weight=NORMAL)
    body = VGroup(en(title, 26, FG), caps(sub, 13, MUTED)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    row = VGroup(num, icon, body).arrange(RIGHT, buff=0.28)
    row.num, row.icon, row.body = num, icon, body
    return row


class S08Stopping(VoiceScene):
    SECTION = "s08"

    def construct(self):
        self.show_chapter()
        loop = LoopDiagram(center=LC, radius=1.4, node_w=1.18, node_h=0.54, name_size=20, meanings=False, goal=False,
                           done=True, done_gap=1.75)
        tok = Token(TEAL, 0.08)
        q = en("?", 54, AMBER).move_to(loop.center)
        with self.say("s08_01") as v:
            self.play(LaggedStart(*[FadeIn(p) for p in loop.parts_in_order() if p not in (loop.done, loop.done_arrow)],
                                  lag_ratio=0.1), run_time=0.9)
            self.add(*[m for m in loop if m not in (loop.done, loop.done_arrow)])
            tok.move_to(loop.ring.get_start())
            trail = loop.trail(tok)
            self.add(trail)
            self.play(FadeIn(tok, scale=0.5), run_time=0.2)
            self.play(MoveAlongPath(tok, loop.ring), run_time=1.1, rate_func=linear)
            self.play(MoveAlongPath(tok, loop.ring), run_time=1.0, rate_func=linear)
            self.wait_until(v.cue("stop") - 0.3)
            self.play(FadeIn(q, scale=0.8), run_time=0.4)

        rows = VGroup(way(1, I.check_icon(0.34, TEAL), "normal stop", "no tool request", TEAL),
                      way(2, VGroup(en("#", 30, AMBER)), "step limit", "max iterations", AMBER),
                      way(3, I.user_icon(0.4, AMBER), "human approval", "before risky tools", AMBER),
                      way(4, en("?", 32, BLUE), "the model asks", "the loop waits", BLUE))
        rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT).move_to([3.7, 0.15, 0], aligned_edge=ORIGIN)
        rows.move_to([1.15, 0.15, 0], aligned_edge=LEFT)
        head = caps("four ways the loop ends", 16, MUTED).next_to(rows, UP, buff=0.42, aligned_edge=LEFT)
        for r in rows:
            r.num.save_state()
            r.num.set_color(DIM)
        with self.say("s08_02") as v:
            self.wait_until(v.cue("ways") - 0.3)
            self.play(FadeIn(head), LaggedStart(*[FadeIn(r.num, shift=LEFT * 0.08) for r in rows], lag_ratio=0.15),
                      run_time=0.7)

        def soften(r, level=0.4):
            """Dim (or restore) a row's texts only; icons are outline shapes and keep their look."""
            return [r.num.animate.set_opacity(level), r.body.animate.set_opacity(level)]

        def reveal(r, with_sub=True):
            anims = [Restore(r.num), FadeIn(r.icon, scale=0.8), FadeIn(r.body[0], shift=LEFT * 0.08)]
            if with_sub:
                anims.append(FadeIn(r.body[1]))
            return anims

        with self.say("s08_03") as v:
            self.wait_until(v.cue("normal") - 0.3)
            self.play(*reveal(rows[0], False), FadeOut(q), run_time=0.5)
            self.wait_until(v.cue("tool") - 0.3)
            self.play(FadeIn(rows[0].body[1]), run_time=0.4)
            self.wait_until(v.cue("finished") - 1.2)
            for a, b in (("decide", "act"), ("act", "observe"), ("observe", "evaluate")):
                self.play(MoveAlongPath(tok, loop.leg(a, b), rate_func=linear), run_time=0.2)
            self.play(FadeIn(loop.done_arrow), FadeIn(loop.done, scale=0.9), run_time=0.35)
            self.play(MoveAlongPath(tok, loop.leg("evaluate", "done")), *loop.focus("done"), run_time=0.6)

        def counter(n, color=FG, limit=False):
            lab = caps("iteration", 13, MUTED)
            num = en(f"{n}" + (" / 20" if limit else ""), 30, color, italic=False, weight=NORMAL)
            return VGroup(lab, num).arrange(DOWN, buff=0.06).move_to(loop.center)

        cnt = counter(1)
        with self.say("s08_04") as v:
            self.wait_until(v.cue("step") - 0.3)
            loop.nodes.pop("done")              # the exit is not part of the remaining demos
            self.play(*reveal(rows[1], False), *loop.all_normal(), FadeOut(loop.done), FadeOut(loop.done_arrow),
                      FadeOut(tok), *soften(rows[0]), run_time=0.5)
            self.remove(trail)
            tok.move_to(loop.ring.get_start())
            trail = loop.trail(tok)
            self.add(trail)
            self.play(FadeIn(tok, scale=0.5), run_time=0.25)
            self.wait_until(v.cue("trip") - 0.2)
            self.play(MoveAlongPath(tok, loop.ring), run_time=1.3, rate_func=smooth)
            self.wait_until(v.cue("iteration") - 0.3)
            self.play(FadeIn(cnt, scale=0.9), run_time=0.4)

        cnt2 = counter(1, limit=True)
        with self.say("s08_05") as v:
            self.wait_until(v.cue("maximum") - 0.3)
            self.play(FadeIn(rows[1].body[1]), run_time=0.4)
            self.wait_until(v.cue("twenty") - 0.3)
            self.play(FadeTransform(cnt, cnt2), run_time=0.4)

        stop = stop_icon(0.5).next_to(loop.nodes["decide"], UP, buff=0.18)
        safe = Pill(VGroup(shield_icon(0.3, TEAL), en("no endless loops", 21, TEAL)).arrange(RIGHT, buff=0.12), TEAL,
                    pad_x=0.22).move_to([LC[0], -2.3, 0])
        with self.say("s08_06") as v:
            self.wait_until(v.cue("reaches") - 0.3)
            count = ValueTracker(1)
            live = counter(1, limit=True)
            self.remove(cnt2)
            self.add(live)
            live.add_updater(lambda m: m.become(counter(int(round(count.get_value())), limit=True)))
            # three quick laps while the iteration counter runs up to the limit
            self.play(count.animate(rate_func=linear).set_value(20),
                      MoveAlongPath(tok, loop.ring, rate_func=lambda a: (3 * a) % 1), run_time=1.6)
            live.clear_updaters()
            cur = counter(20, RED, limit=True)
            self.remove(live)
            self.add(cur)
            self.wait_until(v.cue("halts") - 0.3)
            self.play(FadeIn(stop, scale=0.7), *loop.all_dim(), FadeOut(tok), run_time=0.5)
            self.wait_until(v.cue("protects") - 0.3)
            self.play(FadeIn(safe, shift=UP * 0.08), run_time=0.45)

        risky = VGroup(Pill(VGroup(I.trash_icon(0.26, RED), mono("delete a file", 17, FG)).arrange(RIGHT, buff=0.12), RED,
                            pad_x=0.18),
                       Pill(VGroup(I.terminal_icon(0.24, RED), mono("dangerous command", 17, FG)).arrange(RIGHT, buff=0.12),
                            RED, pad_x=0.18)).arrange(RIGHT, buff=0.25).move_to([LC[0], -2.3, 0])
        dialog = VGroup(RoundedRectangle(width=3.6, height=1.55, corner_radius=0.16).set_stroke(AMBER, 2).set_fill(PANEL, 1))
        d_t = bn("Allow this action?", 26, FG)
        yes = Pill(en("Yes", 22, TEAL, italic=False, weight=NORMAL), TEAL, pad_x=0.32)
        no = Pill(en("No", 22, RED, italic=False, weight=NORMAL), RED, pad_x=0.36)
        btns = VGroup(yes, no).arrange(RIGHT, buff=0.35)
        VGroup(d_t, btns).arrange(DOWN, buff=0.28).move_to(dialog[0])
        dialog.add(d_t, btns)
        dialog.move_to(loop.center).set_z_index(6)          # above the loop nodes
        with self.say("s08_07") as v:
            self.wait_until(v.cue("approval") - 0.3)
            self.remove(trail)
            tok.move_to(loop.leg("decide", "act").get_start())
            trail = loop.trail(tok)
            self.add(trail)
            self.play(*reveal(rows[2]), *soften(rows[1]), FadeOut(stop), FadeOut(cur), FadeOut(safe),
                      *loop.all_normal(), FadeIn(tok, scale=0.5), run_time=0.6)
            self.wait_until(v.cue("deleting") - 0.3)
            self.play(FadeIn(risky[0], shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("dangerous") - 0.3)
            self.play(FadeIn(risky[1], shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("pauses") - 0.6)
            self.play(MoveAlongPath(tok, loop.leg("decide", "act")), run_time=0.5)
            self.play(*loop.focus("act"), run_time=0.4)
            self.wait_until(v.cue("allow") - 0.3)
            self.play(FadeIn(dialog, scale=0.92), run_time=0.5)
            self.play(glow(yes.frame, TEAL, 5), glow(no.frame, RED, 5), run_time=0.6)

        ask = Bubble("Which file should I fix?", BLUE, 22, side="left").next_to(loop.nodes["decide"], UP, buff=0.32)
        gap_ = VGroup(DashedLine(LEFT * 0.7, RIGHT * 0.7, dash_length=0.08).set_stroke(AMBER, 2), en("?", 30, AMBER))
        gap_[1].next_to(gap_[0], UP, buff=0.04)
        gap_.move_to([LC[0], -2.25, 0])
        gap_lab = caps("missing info", 13, AMBER).next_to(gap_, RIGHT, buff=0.2)
        wait = VGroup(I.user_icon(0.36, FG), en("waiting for you", 22, FG),
                      VGroup(*[Dot(radius=0.04, color=FG) for _ in range(3)]).arrange(RIGHT, buff=0.08)).arrange(RIGHT, buff=0.16)
        wait.move_to([LC[0], -2.3, 0])
        with self.say("s08_08") as v:
            self.wait_until(v.cue("question") - 0.3)
            self.play(*reveal(rows[3], False), *soften(rows[2]), FadeOut(dialog), FadeOut(risky),
                      *loop.focus("decide"), FadeOut(tok), run_time=0.6)
            self.remove(trail)
            tok.move_to(loop.nodes["decide"].get_center())
            trail = loop.trail(tok)
            self.add(trail)
            self.wait_until(v.cue("missing") - 0.3)
            self.play(FadeIn(gap_), FadeIn(gap_lab), run_time=0.45)
            self.wait_until(v.cue("instead") - 0.3)
            self.play(FadeIn(ask, shift=UP * 0.1), run_time=0.5)
            self.wait_until(v.cue("waits") - 0.3)
            self.play(FadeOut(gap_), FadeOut(gap_lab), FadeIn(wait, shift=UP * 0.08), FadeIn(rows[3].body[1]),
                      *loop.all_dim(), run_time=0.6)

        harness = HarnessFrame(6.4, 5.1, label_size=17).move_to([LC[0] - 0.2, 0.0, 0])
        dev = Pill(VGroup(I.wrench_icon(0.26, AMBER), en("written by the developer", 21, FG)).arrange(RIGHT, buff=0.12),
                   AMBER, pad_x=0.22).move_to([LC[0], -2.3, 0])
        not_magic = VGroup(en("magic", 26, MUTED))
        not_magic.add(Line(not_magic.get_left() + LEFT * 0.08, not_magic.get_right() + RIGHT * 0.08).set_stroke(RED, 2.5))
        not_magic.next_to(head, UP, buff=0.25, aligned_edge=LEFT)
        with self.say("s08_09") as v:
            self.play(FadeOut(ask), FadeOut(wait), *loop.all_normal(), FadeOut(tok), run_time=0.5)
            self.wait_until(v.cue("magic") - 0.3)
            self.play(FadeIn(not_magic), run_time=0.4)
            self.wait_until(v.cue("safeguards") - 0.3)
            self.play(*[a for r in rows[1:] for a in soften(r, 1.0)], *[glow(r.icon, AMBER, 4) for r in rows[1:]],
                      run_time=0.6)
            self.wait_until(v.cue("harness") - 0.3)
            self.play(FadeIn(harness), run_time=0.6)
            self.wait_until(v.cue("developer") - 0.3)
            self.play(FadeIn(dev, shift=UP * 0.08), run_time=0.45)

        human = Pill(VGroup(I.user_icon(0.3, AMBER), en("human oversight", 22, AMBER)).arrange(RIGHT, buff=0.12), AMBER,
                     pad_x=0.24).move_to(dev)
        with self.say("s08_10") as v:
            self.wait_until(v.cue("oversight") - 0.3)
            self.play(FadeTransform(dev, human), glow(rows[2].icon, AMBER, 6), pulse(rows[2], 1.04), run_time=0.6)
        self.clear_all(0.8)
