"""05 · How the model learns about tools: tool descriptions travel with the messages."""
from agentic_video.prelude import *


def params(name, meaning, size=19):
    return VGroup(mono(name, size, FG), bn(meaning, size - 2, MUTED)).arrange(RIGHT, buff=0.18)


def mini_stack(n=3, w=1.7):
    roles = ["system", "user", "assistant"]
    return VGroup(*[RoundedRectangle(width=w, height=0.2, corner_radius=0.05).set_stroke(ROLE_COLORS[roles[i % 3]], 1.2)
                    .set_fill(ROLE_COLORS[roles[i % 3]], 0.18) for i in range(n)]).arrange(DOWN, buff=0.07)


class S05Tools(VoiceScene):
    SECTION = "s05"

    def construct(self):
        self.show_chapter()
        model = ModelBox(2.6, 1.6).move_to([-2.6, 0.35, 0])
        wall = DashedLine([0.9, 2.1, 0], [0.9, -1.6, 0], dash_length=0.12).set_stroke(DIM, 3)
        comp = VGroup(I.terminal_icon(1.0, MUTED), en("the computer", 24, MUTED)).arrange(DOWN, buff=0.22).move_to([3.7, 0.35, 0])
        unknown = VGroup(*[VGroup(RoundedRectangle(width=0.8, height=0.55, corner_radius=0.1).set_stroke(DIM, 1.5),
                                  en("?", 30, AMBER)) for _ in range(3)])
        for u in unknown:
            u[1].move_to(u[0])
        unknown.arrange(RIGHT, buff=0.22).move_to([-3.35, 2.05, 0])
        unk_lab = en("which tools?", 22, AMBER).next_to(unknown, RIGHT, buff=0.3)
        with self.say("s05_01") as v:
            self.play(FadeIn(model, scale=0.95), run_time=0.5)
            self.wait_until(v.cue("see") - 0.4)
            self.play(Create(wall), FadeIn(comp, shift=LEFT * 0.1), run_time=0.7)
            self.wait_until(v.cue("tools") - 0.4)
            self.play(LaggedStart(*[FadeIn(u, scale=0.8) for u in unknown], lag_ratio=0.2), FadeIn(unk_lab), run_time=0.8)

        # ---- the harness tells it
        harness = HarnessFrame(13.4, 5.72).move_to([0, 0.15, 0])
        main = ToolCard("read_file", "Reads the text inside a file", params("path", "which file to read"), width=6.9,
                        value_size=21, label_size=15, label_w=2.0)
        main.move_to([2.95, 1.4, 0])
        with self.say("s05_02") as v:
            self.wait_until(v.cue("tells") - 0.4)
            self.play(FadeOut(wall), FadeOut(comp), FadeOut(unknown), FadeOut(unk_lab),
                      model.animate.move_to([-4.65, 0.25, 0]), run_time=0.7)
            self.play(FadeIn(harness), run_time=0.5)
            self.wait_until(v.cue("description") - 0.3)
            self.play(FadeIn(VGroup(main.frame, main.tint), scale=0.96), run_time=0.5)

        with self.say("s05_03") as v:
            self.wait_until(v.cue("parts") - 0.3)
            self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.08) for l in main.labels], lag_ratio=0.25), run_time=0.8)
            self.wait_until(v.cue("name") - 0.2)
            self.play(glow(main.labels[0], TEAL, 4), run_time=0.4)
            self.wait_until(v.cue("value") - 0.3)
            self.play(FadeIn(main.values[0], shift=RIGHT * 0.1), run_time=0.5)

        with self.say("s05_04") as v:
            self.wait_until(v.cue("description") - 0.2)
            self.play(glow(main.labels[1], TEAL, 4), run_time=0.4)
            self.wait_until(v.cue("value") - 0.3)
            self.play(FadeIn(main.values[1], shift=RIGHT * 0.1), run_time=0.5)

        with self.say("s05_05") as v:
            self.wait_until(v.cue("parameters") - 0.2)
            self.play(glow(main.labels[2], TEAL, 4), run_time=0.4)
            self.wait_until(v.cue("path") - 0.3)
            self.play(FadeIn(main.values[2], shift=RIGHT * 0.1), run_time=0.5)

        small = dict(width=4.6, value_size=17, label_size=12, label_w=1.5, pad=0.18, row_gap=0.16)
        run_c = ToolCard("run_command", "Runs a command in the terminal", params("command", "", 16), **small)
        edit_c = ToolCard("edit_file", "Changes the text of a file", params("path, new_text", "", 16), **small)
        run_c.move_to([-0.55, -0.62, 0])
        edit_c.move_to([4.25, -0.62, 0])
        with self.say("s05_06") as v:
            self.wait_until(v.cue("more") - 0.3)
            self.play(main.animate.shift(UP * 0.35), run_time=0.4)
            self.wait_until(v.cue("run") - 0.3)
            self.play(FadeIn(run_c, shift=UP * 0.12), run_time=0.5)

        with self.say("s05_07") as v:
            self.play(FadeIn(edit_c, shift=UP * 0.12), run_time=0.5)

        msgs = mini_stack(3)
        msgs_lab = caps("messages", 14, MUTED).next_to(msgs, UP, buff=0.12)
        msg_g = VGroup(msgs_lab, msgs).move_to([-4.65, -1.75, 0])
        cards = [main, run_c, edit_c]
        with self.say("s05_08") as v:
            self.wait_until(v.cue("descriptions") - 0.3)
            self.play(*[glow(c.frame, TEAL, 5) for c in cards], run_time=0.6)
            self.wait_until(v.cue("list") - 0.3)
            self.play(FadeIn(msg_g, shift=UP * 0.1), run_time=0.4)
            b = VGroup(*[c.copy() for c in cards], msgs.copy())
            self.add(b)
            self.play(b.animate(path_arc=PI * 0.35).scale(0.16).move_to(model.in_port + RIGHT * 0.25).set_opacity(0),
                      run_time=1.2)
            self.remove(b)
            self.play(model.think(0.6), run_time=0.6)

        only = Pill(VGroup(caps("sees", 15, BLUE), en("descriptions only", 21, FG)).arrange(RIGHT, buff=0.14), BLUE,
                    pad_x=0.24).next_to(model, UP, buff=0.3)
        with self.say("s05_09") as v:
            self.wait_until(v.cue("important") - 0.3)
            self.play(FadeOut(msg_g), run_time=0.4)
            self.wait_until(v.cue("sees") - 0.3)
            self.play(FadeIn(only, shift=DOWN * 0.08), *[glow(c.frame, TEAL, 5) for c in cards], run_time=0.6)

        prog = Window(2.7, 1.45, "program").move_to([-4.65, -1.55, 0])
        code = code_block(1.9, 4, color=DIM).move_to(prog.frame.get_center() + DOWN * 0.15)
        lock = I.lock_icon(0.36, MUTED).move_to(prog.frame.get_corner(UP + RIGHT) + LEFT * 0.3 + DOWN * 0.18)
        link = DashedLine(model.frame.get_bottom() + DOWN * 0.04, prog.frame.get_top() + UP * 0.04, dash_length=0.06)
        link.set_stroke(DIM, 1.6)
        x = I.cross_icon(0.26).move_to(link.get_center() + RIGHT * 0.3)
        with self.say("s05_10") as v:
            self.wait_until(v.cue("program") - 0.4)
            self.play(FadeIn(prog, shift=UP * 0.08), FadeIn(code), FadeIn(lock), run_time=0.5)
            self.play(Create(link), FadeIn(x, scale=1.3), run_time=0.4)

        # ---- vague vs clear descriptions
        def column(x, head, color, name, desc, par):
            h = VGroup(caps(head, 18, color)).move_to([x, 2.42, 0])
            card = ToolCard(name, desc, par, width=5.6, value_size=18, label_size=13, label_w=1.7, pad=0.2, row_gap=0.18)
            card.move_to([x, 1.15, 0])
            m = ModelBox(2.0, 1.15, label_size=17).move_to([x - 0.4, -1.05, 0])
            a = arrow(card.get_bottom() + DOWN * 0.06 + LEFT * 0.4, m.frame.get_top() + UP * 0.06, color=MUTED, tip=0.1)
            return h, card, m, a

        vh, vcard, vm, va = column(-3.45, "vague", RED, "file_tool", "does file stuff", mono("?", 18, MUTED))
        ch, ccard, cm, ca = column(3.45, "clear", TEAL, "read_file", "Reads the text inside a file", params("path", "which file", 17))
        huh = en("?", 60, AMBER).next_to(vm, RIGHT, buff=0.35)
        pick = VGroup(I.check_icon(0.4, TEAL), en("picks it", 24, TEAL)).arrange(RIGHT, buff=0.14).next_to(cm, RIGHT, buff=0.3)
        with self.say("s05_11") as v:
            self.wait_until(v.cue("matters") - 0.4)
            self.play(*[FadeOut(o) for o in self.mobjects if o is not self.chapter], run_time=0.6)
            self.wait_until(v.cue("vague") - 0.3)
            self.play(FadeIn(vh), FadeIn(vcard, shift=DOWN * 0.1), run_time=0.5)
            self.play(glow(vcard.values[1], RED, 4), run_time=0.4)
            self.wait_until(v.cue("sure") - 0.6)
            self.play(GrowArrow(va), FadeIn(vm, scale=0.95), run_time=0.5)
            self.play(FadeIn(huh, scale=0.7), Wiggle(vm, scale_value=1.04, rotation_angle=0.03 * TAU), run_time=0.8)

        with self.say("s05_12") as v:
            self.wait_until(v.cue("clear") - 0.3)
            self.play(FadeIn(ch), FadeIn(ccard, shift=DOWN * 0.1), run_time=0.5)
            self.play(glow(ccard.values[1], TEAL, 4), run_time=0.4)
            self.wait_until(v.cue("confidence") - 0.8)
            self.play(GrowArrow(ca), FadeIn(cm, scale=0.95), run_time=0.5)
            self.play(FadeIn(pick, shift=LEFT * 0.1), glow(ccard.frame, TEAL, 6), cm.think(0.6), run_time=0.6)

        def warn(icon, text, color):
            return Pill(VGroup(icon, en(text, 22, color)).arrange(RIGHT, buff=0.14), color, pad_x=0.26, pad_y=0.1)

        risks = VGroup(warn(I.warn_icon(0.3, AMBER), "still makes mistakes", AMBER),
                       warn(I.cross_icon(0.22), "wrong tool", RED), warn(I.cross_icon(0.22), "wrong input", RED))
        risks.arrange(RIGHT, buff=0.4).move_to([0, -2.28, 0])
        with self.say("s05_13") as v:
            self.wait_until(v.cue("mistakes") - 0.3)
            self.play(FadeIn(risks[0], shift=UP * 0.1), run_time=0.5)
            self.wait_until(v.cue("wrong") - 0.3)
            self.play(FadeIn(risks[1], shift=UP * 0.1), run_time=0.45)
            self.wait_until(v.cue("input") - 0.3)
            self.play(FadeIn(risks[2], shift=UP * 0.1), run_time=0.45)
        self.clear_all(0.8)
