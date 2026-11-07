"""09 · Full replay: the Episode 01 bug fix at the level of messages. Message list on the left,
loop on the right (active stage glowing), a call counter on the model, the context meter rising."""
from agentic_video.prelude import *

LX, LTOP, LW = -6.6, 2.95, 5.7
MX, MB, MT = -0.42, -2.42, 2.72          # context meter: x, bottom, top


def msg(role, text=None, content=None, dashed=False, accent=None, text_color=FG, wrap=None):
    return MessageCard(role, text, width=LW, size=16, content=content, dashed=dashed, accent=accent,
                       text_color=text_color, wrap=wrap, min_h=0.37, tag_size=12)


def call(tool, arg):
    return VGroup(mono(tool, 15, BLUE), en("→", 17, MUTED), mono(arg, 15, FG)).arrange(RIGHT, buff=0.12)


class S09Replay(VoiceScene):
    SECTION = "s09"

    def construct(self):
        self.show_chapter()
        lst = MessageList([LX, LTOP], gap=0.05)
        model = ModelBox(2.3, 1.25, label_size=19).move_to([1.75, 1.65, 0])
        loop = LoopDiagram(center=[4.75, -0.4, 0], radius=1.3, node_w=1.1, node_h=0.5, name_size=19, meanings=False,
                           goal=True, done=True, goal_gap=0.95, done_gap=1.55)
        m_box = RoundedRectangle(width=0.17, height=MT - MB, corner_radius=0.085).set_stroke(DIM, 1.3).set_fill(BG, 1)
        m_box.move_to([MX, (MT + MB) / 2, 0])
        m_lab = caps("context", 13, MUTED).next_to(m_box, DOWN, buff=0.1)
        state = {"fill": Rectangle(width=0.1, height=0.002).set_stroke(width=0).set_fill(TEAL, 0).move_to([MX, MB + 0.05, 0])}

        def meter(frac):
            h = max(0.002, (MT - MB - 0.1) * frac)
            new = Rectangle(width=0.1, height=h).set_stroke(width=0).set_fill(meter_color(frac), 0.95)
            new.move_to([MX, MB + 0.05 + h / 2, 0])
            return Transform(state["fill"], new)

        link = DashedLine([MX + 0.25, model.get_y(), 0], model.in_port + LEFT * 0.06, dash_length=0.07)
        link.set_stroke(AMBER, 1.6, opacity=0.7)
        link_path = Line(link.get_start(), link.get_end())     # DashedLine has no path of its own
        tok = Token(TEAL, 0.075)
        lt = Token(AMBER, 0.07)
        cur = {"badge": None, "at": None}

        def new_call(n):
            """Call #n: the whole list travels to the model again."""
            b = model.badge(f"call #{n}")
            anims = [FadeIn(b, shift=DOWN * 0.06)] if cur["badge"] is None else [FadeTransform(cur["badge"], b)]
            cur["badge"] = b
            lt.move_to(link.get_start())
            self.add(lt)
            self.play(*anims, MoveAlongPath(lt, link_path), run_time=0.5)
            self.remove(lt)
            self.play(model.think(0.45), run_time=0.45)

        def go(b, rt=0.5):
            a = cur["at"]
            anims = loop.focus(b)
            if a is not None:
                anims.append(MoveAlongPath(tok, loop.leg(a, b)))
            cur["at"] = b
            self.play(*anims, run_time=rt)

        def add(card, frac, rt=0.45):
            lst.push(card)
            self.play(FadeIn(card, shift=RIGHT * 0.2), meter(frac), run_time=rt)

        # ---- set up
        ep1 = Pill(VGroup(I.wrench_icon(0.28, AMBER), en("the bug fix from Episode 01", 22, FG)).arrange(RIGHT, buff=0.14),
                   AMBER, pad_x=0.26).move_to([-3.75, 0.3, 0])
        with self.say("s09_01") as v:
            self.wait_until(v.cue("together") - 0.3)
            self.play(FadeIn(model, scale=0.95), LaggedStart(*[FadeIn(p) for p in loop.parts_in_order()], lag_ratio=0.06),
                      run_time=1.0)
            self.add(loop)
            self.wait_until(v.cue("bugfix") - 0.3)
            self.play(FadeIn(ep1, shift=UP * 0.08), run_time=0.5)

        with self.say("s09_02") as v:
            self.wait_until(v.cue("replay") - 0.3)
            self.play(FadeOut(ep1, shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("messages") - 0.3)
            self.play(FadeIn(m_box), FadeIn(m_lab), FadeIn(state["fill"]), Create(link), *loop.all_normal(), run_time=0.5)

        with self.say("s09_03") as v:
            self.wait_until(v.cue("msg") - 0.3)
            tok.move_to(loop.goal.get_center())
            self.add(tok, loop.trail(tok))
            add(msg("user", "The program is crashing. Find the bug and fix it.", wrap=34), 0.1)
            go("goal")

        # ---- call 1: run the tests
        with self.say("s09_04") as v:
            self.wait_until(v.cue("call") - 0.3)
            new_call(1)
            self.wait_until(v.cue("decides") - 0.3)
            go("decide")
            self.wait_until(v.cue("requests") - 0.3)
            add(msg("assistant", content=call("run_command", "run tests"), dashed=True), 0.19)

        with self.say("s09_05") as v:
            self.wait_until(v.cue("runs") - 0.3)
            go("act")
            self.wait_until(v.cue("failed") - 0.35)
            go("observe", 0.4)
            add(msg("tool", content=VGroup(I.cross_icon(0.18), bn("Test failed: wrong result in total()", 16, RED))
                    .arrange(RIGHT, buff=0.1)), 0.28)

        # ---- call 2: read the file
        with self.say("s09_06") as v:
            self.wait_until(v.cue("call") - 0.6)
            go("evaluate", 0.4)
            new_call(2)
            go("decide", 0.4)
            self.wait_until(v.cue("read") - 0.3)
            add(msg("assistant", content=call("read_file", "math_utils.py"), dashed=True), 0.36)

        code = code_block(2.6, 3, color=MUTED, gap=0.085)
        with self.say("s09_07") as v:
            self.wait_until(v.cue("reads") - 0.3)
            go("act")
            self.wait_until(v.cue("code") - 0.35)
            go("observe", 0.4)
            add(msg("tool", content=VGroup(mono("math_utils.py", 13, MUTED), code).arrange(RIGHT, buff=0.25)), 0.5)

        # ---- call 3: fix it
        with self.say("s09_08") as v:
            self.wait_until(v.cue("call") - 0.6)
            go("evaluate", 0.4)
            new_call(3)
            go("decide", 0.4)
            self.wait_until(v.cue("spotted") - 0.3)
            self.play(code[1].animate.set_stroke(RED, opacity=1), glow(code[1], RED, 6), run_time=0.5)
            self.wait_until(v.cue("edit") - 0.3)
            add(msg("assistant", content=call("edit_file", "math_utils.py"), dashed=True), 0.58)

        with self.say("s09_09") as v:
            self.wait_until(v.cue("change") - 0.3)
            go("act")
            self.wait_until(v.cue("updated") - 0.35)
            go("observe", 0.4)
            add(msg("tool", "File updated successfully"), 0.66)

        # ---- call 4: check
        with self.say("s09_10") as v:
            self.wait_until(v.cue("call") - 0.6)
            go("evaluate", 0.4)
            new_call(4)
            go("decide", 0.4)
            self.wait_until(v.cue("run") - 0.3)
            add(msg("assistant", content=call("run_command", "run tests"), dashed=True), 0.74)

        with self.say("s09_11") as v:
            self.wait_until(v.cue("passed") - 0.6)
            go("act", 0.35)
            go("observe", 0.35)
            add(msg("tool", content=VGroup(bn("All tests passed", 16, TEAL), I.check_icon(0.2, TEAL)).arrange(RIGHT, buff=0.1)),
                0.82)

        # ---- call 5: the final answer
        nocall = caps("no tool request", 13, DIM).next_to(model, DOWN, buff=0.16)
        final = msg("assistant", "Bug fixed. total() was adding the numbers incorrectly.", wrap=34)
        with self.say("s09_12") as v:
            self.wait_until(v.cue("call") - 0.6)
            go("evaluate", 0.4)
            new_call(5)
            self.wait_until(v.cue("no") - 0.3)
            self.play(FadeIn(nocall), run_time=0.35)
            self.wait_until(v.cue("final") - 0.3)
            add(final, 0.9)

        with self.say("s09_13") as v:
            self.wait_until(v.cue("incorrectly") - 0.4)
            self.play(glow(final.frame, BLUE, 5), run_time=0.5)
            go("done", 0.6)

        user = VGroup(I.user_icon(0.42, FG), Bubble("Bug fixed.", BLUE, 20, side="left")).arrange(RIGHT, buff=0.16)
        user.next_to(loop.done, DOWN, buff=0.45)
        with self.say("s09_14") as v:
            self.wait_until(v.cue("shows") - 0.3)
            self.play(FadeIn(user, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("quiet") - 0.3)
            self.play(*loop.all_dim(), FadeOut(tok), FadeOut(nocall), run_time=0.8)
            self.remove(tok)

        whole = RoundedRectangle(width=LW + 0.2, height=LTOP - lst.bottom + 0.12, corner_radius=0.12)
        whole.move_to([LX + LW / 2, (LTOP + lst.bottom) / 2, 0])
        whole_o = dashed_outline(whole, AMBER, 1.8)
        five = Pill(en("5 calls · full history each time", 20, AMBER), AMBER, pad_x=0.22).move_to([4.45, -2.42, 0])
        if five.get_right()[0] > 6.75:
            five.shift(LEFT * (five.get_right()[0] - 6.75))
        with self.say("s09_15") as v:
            self.wait_until(v.cue("calls") - 0.3)
            self.play(glow(cur["badge"].frame, BLUE, 6), pulse(cur["badge"], 1.15), run_time=0.6)
            self.wait_until(v.cue("history") - 0.4)
            self.play(Create(whole_o), FadeIn(five, shift=UP * 0.06), run_time=0.6)
            lt.move_to(link.get_start())
            self.add(lt)
            self.play(MoveAlongPath(lt, link_path), run_time=0.5)
            self.remove(lt)

        with self.say("s09_16") as v:
            self.wait_until(v.cue("growing") - 0.3)
            self.play(meter(0.97), glow(m_box, AMBER, 6), run_time=0.7)
        self.clear_all(0.8)
