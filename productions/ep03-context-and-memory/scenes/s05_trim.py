"""05 · Technique 2: trim old messages. The oldest messages slide out (the system message stays
pinned; a tool call and its result leave together), the gentler placeholder version, and the danger:
a trimmed instruction the model can no longer see."""
from agentic_video.prelude import *
from memory_kit import *

CW_C = np.array([-3.75, -0.05, 0])
W = 3.48
RX = 2.95


def thin(role, text=None, content=None, h=0.28, size=12):
    return SizedCard(role, text, height=h, width=W, size=size, content=content)


def call(tool, arg):
    return ToolCallMsg(tool, arg, width=W, size=12, height=0.28)


def result(head, n, h, seed):
    body = VGroup(mono(head, 11, MUTED), code_block(1.7, n, size=0.033, color=DIM, seed=seed, gap=0.13)).arrange(
        DOWN, buff=0.08, aligned_edge=LEFT) if n else mono(head, 11, FG)
    return SizedCard("tool", content=body, height=h, width=W)


def bracket(cards, color=AMBER):
    g = VGroup(*cards)
    x = g.get_left()[0] - 0.24                     # just outside the window's left edge
    top, bot = g.get_top()[1] - 0.04, g.get_bottom()[1] + 0.04
    b = VGroup(Line([x, top, 0], [x - 0.14, top, 0]), Line([x - 0.14, top, 0], [x - 0.14, bot, 0]),
               Line([x - 0.14, bot, 0], [x, bot, 0])).set_stroke(color, 2.2)
    lab = caps("pair", 12, color).rotate(PI / 2).next_to(b, LEFT, buff=0.06)
    return VGroup(b, lab)


class S05Trim(VoiceScene):
    SECTION = "s05"

    def construct(self):
        self.show_chapter()
        tech = technique_tag(2)
        head = en("Trim old messages", 34, FG).move_to([RX, 2.6, 0])
        ctx = LiveContext(CW_C, 3.8, 5.3)
        sysc = thin("system", "You are a coding agent.")
        a1, t1 = call("read_file", '"config.txt"'), result("port = 8080, host = localhost", 0, 0.34, 1)
        a2, t2 = call("run_command", '"run tests"'), result("test log · 900 lines", 5, 0.95, 2)
        a3 = thin("assistant", "Found the bug in total().")
        u2 = thin("user", "Also check the login.")
        a4, t4 = call("read_file", '"login.py"'), result("login.py · whole file", 3, 0.70, 3)
        a5, t5 = call("edit_file", '"math_utils.py"'), result("File updated successfully", 0, 0.28, 4)
        for c in (sysc, a1, t1, a2, t2, a3, u2, a4, t4, a5, t5):
            ctx.place(c)
        fit = 0.95 * ctx.capacity - sum(ctx.units(c) for c in ctx.cards if c is not t2)
        t2.tokens = fit                                   # the window reads exactly 95 %

        with self.say("s05_01") as v:
            self.wait_until(v.cue("tech") - 0.3)
            self.play(FadeIn(tech, shift=DOWN * 0.08), run_time=0.5)
            self.wait_until(v.cue("trim") - 0.3)
            self.play(FadeIn(head, shift=UP * 0.08), run_time=0.5)

        with self.say("s05_02") as v:
            self.wait_until(v.cue("full") - 0.5)
            self.play(*ctx.appear(), LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in ctx.cards], lag_ratio=0.08),
                      run_time=1.2)
            self.wait_until(v.cue("removes") - 0.3)
            self.play(glow(VGroup(a1, t1), AMBER, 5), run_time=0.6)

        new = thin("user", "Now fix the login test.")
        new.move_to([RX - 1.0, 1.5, 0])
        new_lab = caps("new message", 13, MUTED).next_to(new, UP, buff=0.1, aligned_edge=LEFT)
        with self.say("s05_03") as v:
            self.wait_until(v.cue("pct") - 0.3)
            self.play(glow(ctx.readout, RED, 4), pulse(ctx.readout, 1.25), run_time=0.6)
            self.wait_until(v.cue("new") - 0.3)
            self.play(FadeIn(new, shift=LEFT * 0.15), FadeIn(new_lab), run_time=0.5)
            self.play(new.animate.shift(LEFT * 0.35), rate_func=there_and_back, run_time=0.5)

        with self.say("s05_04") as v:
            self.wait_until(v.cue("oldest") - 0.3)
            self.play(*ctx.remove([a1, t1], shift=LEFT * 1.2), run_time=0.7)
            self.wait_until(v.cue("drops") - 0.3)
            self.play(*ctx.relayout(), run_time=0.6)
            self.wait_until(v.cue("fits") - 0.4)
            self.play(FadeOut(new_lab), *ctx.add_from(new), run_time=0.7)

        pin = pin_icon(0.3, FG).next_to(sysc, LEFT, buff=0.1).shift(RIGHT * 0.32 + UP * 0.12)
        pin_lab = Pill(VGroup(pin_icon(0.2, MUTED), en("pinned: never trimmed", 19, FG)).arrange(RIGHT, buff=0.1), MUTED,
                       pad_x=0.18).move_to([RX, 1.6, 0])
        with self.say("s05_05") as v:
            self.wait_until(v.cue("system") - 0.3)
            self.play(glow(sysc.frame, FG, 5), run_time=0.5)
            self.wait_until(v.cue("pinned") - 0.3)
            self.play(FadeIn(pin, shift=DOWN * 0.15), FadeIn(pin_lab, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("together") - 0.4)
            br = bracket([a2, t2])
            pair_lab = Pill(en("tool call + result = a pair", 19, FG), AMBER, pad_x=0.18).move_to([RX, 0.9, 0])
            self.play(Create(br[0]), FadeIn(br[1]), FadeIn(pair_lab, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("pair") - 0.2)
            self.play(*ctx.remove([a2, t2], shift=LEFT * 1.2), FadeOut(br, shift=LEFT * 1.2), run_time=0.7)
            self.play(*ctx.relayout(), run_time=0.5)

        ph = PlaceholderCard("[old tool result removed]", width=W, size=12, height=0.3)
        gentle = Pill(en("gentler: keep the message, empty the result", 19, FG), TEAL, pad_x=0.18).move_to([RX, 0.2, 0])
        with self.say("s05_06") as v:
            self.wait_until(v.cue("gentler") - 0.3)
            self.play(FadeIn(gentle, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("tool") - 0.3)
            self.play(glow(t4.frame, TEAL, 5), run_time=0.5)
            self.wait_until(v.cue("note") - 0.3)
            self.play(*ctx.swap(t4, ph), run_time=0.6)
            self.play(*ctx.relayout(), run_time=0.5)

        # ---- the danger: a trimmed instruction
        rule = SizedCard("user", "Fix the crash. Do not change the\npublic function names.", height=0.5, width=W, size=12)
        rule_tag = Pill(en("the user's rule", 19, AMBER), AMBER, pad_x=0.18)
        work = [call("read_file", '"math_utils.py"'), result("math_utils.py · lines 1–200", 4, 0.8, 7),
                thin("assistant", "The crash is in total()."), call("run_command", '"run tests"'),
                result("test log · 600 lines", 6, 1.05, 8), thin("user", "Please clean up the code too."),
                call("read_file", '"report.py"'), result("report.py · whole file", 3, 0.7, 9),
                thin("assistant", "report.py looks fine."), call("run_command", '"run tests"'),
                result("test log · 600 lines", 4, 0.8, 10), thin("user", "And the login page?"),
                call("read_file", '"login.py"'), result("login.py · whole file", 3, 0.7, 11)]
        with self.say("s05_07") as v:
            self.wait_until(v.cue("danger") - 0.4)
            gone = ctx.clear()
            self.play(*[FadeOut(c) for c in gone if c is not sysc], FadeOut(pin_lab), FadeOut(pair_lab), FadeOut(gentle),
                      run_time=0.6)
            ctx.cards = [sysc]
            warn = Pill(VGroup(I.warn_icon(0.26, RED), en("the danger", 22, FG)).arrange(RIGHT, buff=0.12), RED,
                        pad_x=0.22).move_to([RX, 1.6, 0])
            self.play(FadeIn(warn, shift=UP * 0.08), *ctx.meter(), run_time=0.45)
            self.wait_until(v.cue("first") - 0.3)
            self.play(*ctx.add(rule, shift=DOWN * 0.2), run_time=0.6)
            self.play(glow(rule.frame, AMBER, 6), run_time=0.5)
            self.wait_until(v.cue("public") - 0.3)
            rule_tag.next_to(rule, RIGHT, buff=0.95)
            self.play(FadeIn(rule_tag, shift=LEFT * 0.1), pulse(rule, 1.04), run_time=0.5)
            # the task goes on: the window fills up behind the rule
            added = []
            for c in work:
                if c.height + ctx.gap > ctx.free() + 0.01:
                    break
                ctx.place(c)
                added.append(c)
            self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.12) for c in added], lag_ratio=0.35), *ctx.meter(),
                      run_time=1.1)

        rename = ToolCallMsg("edit_file", "rename total() → sum_all()", width=W, size=13, height=0.32)
        with self.say("s05_08") as v:
            self.play(FadeOut(rule_tag), run_time=0.3)
            self.wait_until(v.cue("trimmed") - 0.4)
            ghost = rule.copy()
            self.play(*ctx.remove([rule], shift=LEFT * 0.01), run_time=0.01)
            self.add(ghost)
            self.play(ghost.animate.move_to([RX - 0.3, 0.55, 0]).fade(0.55), *ctx.relayout(), run_time=0.9)
            self.wait_until(v.cue("later") - 0.3)
            rest = [c for c in work if c not in ctx.cards]
            for c in rest[:1]:
                if c.height + ctx.gap <= ctx.free() + 0.01:
                    self.play(*ctx.add(c, shift=DOWN * 0.15), run_time=0.25)
            self.wait_until(v.cue("renames") - 0.4)
            while rename.height + ctx.gap > ctx.free() + 0.01:            # make room the same blind way
                old = ctx.cards[1]
                pair = [old] + ([ctx.cards[2]] if old.role == "assistant" and ctx.cards[2].role == "tool" else [])
                self.play(*ctx.remove(pair, shift=LEFT * 1.0), run_time=0.3)
                self.play(*ctx.relayout(), run_time=0.3)
            self.play(*ctx.add(rename, shift=DOWN * 0.15), run_time=0.5)
            bad = I.warn_icon(0.36, RED).next_to(rename, RIGHT, buff=0.85)
            self.play(FadeIn(bad, scale=1.3), rename.outline.animate.set_stroke(RED), run_time=0.5)
            blind = VGroup(I.cross_icon(0.22), caps("outside the window", 13, RED)).arrange(RIGHT, buff=0.1)
            blind.next_to(ghost, UP, buff=0.14, aligned_edge=LEFT)
            self.wait_until(v.cue("no") - 0.3)
            self.play(FadeIn(blind, shift=UP * 0.06), glow(ghost.frame, RED, 5), run_time=0.6)

        simple = Pill(VGroup(I.check_icon(0.22, TEAL), en("simple · fast", 21, FG)).arrange(RIGHT, buff=0.12), TEAL,
                      pad_x=0.22)
        blind_p = Pill(en("blind", 21, FG), RED, pad_x=0.22)
        VGroup(simple, blind_p).arrange(RIGHT, buff=0.3).move_to([RX, -0.75, 0])
        imp = en("important or not", 20, MUTED).next_to(VGroup(simple, blind_p), DOWN, buff=0.22)
        with self.say("s05_09") as v:
            self.wait_until(v.cue("simple") - 0.3)
            self.play(FadeIn(simple, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("blind") - 0.3)
            self.play(FadeIn(blind_p, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("important") - 0.3)
            self.play(FadeIn(imp), run_time=0.4)

        line = DashedLine(ctx.cw.frame.get_corner(UR) + RIGHT * 0.05, ctx.cw.frame.get_corner(DR) + RIGHT * 0.05,
                          dash_length=0.08).set_stroke(RED, 2)
        unseen = Pill(VGroup(I.cross_icon(0.2), en("out of the window = unseen", 20, FG)).arrange(RIGHT, buff=0.12), RED,
                      pad_x=0.22).move_to([RX, -2.15, 0])
        with self.say("s05_10") as v:
            self.wait_until(v.cue("out") - 0.3)
            self.play(glow(ctx.cw.frame, FG, 6), run_time=0.5)
            self.wait_until(v.cue("cannot") - 0.3)
            self.play(FadeIn(unseen, shift=UP * 0.08), glow(ghost.frame, RED, 5), run_time=0.5)
        self.clear_all(0.6)
