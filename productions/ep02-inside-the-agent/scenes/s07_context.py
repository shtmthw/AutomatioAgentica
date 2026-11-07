"""07 · The context window: a fixed limit (measured in tokens), the desk analogy, a huge tool
result fills it, what happens when it is full, cost, and context management."""
from agentic_video.prelude import *

CW_C = np.array([-1.75, -0.05, 0])
CW_W, CW_H = 4.0, 5.0
CARD_W = CW_W - 0.36


def card(role, text=None, content=None, label=None, accent=None, min_h=0.36, text_color=FG):
    return MessageCard(role, text, width=CARD_W, size=15, content=content, label=label, accent=accent, min_h=min_h,
                       tag_size=12, text_color=text_color)


def call(tool, arg):
    return VGroup(mono(tool, 13, BLUE), en("→", 15, MUTED), mono(arg, 13, FG)).arrange(RIGHT, buff=0.1)


class S07Context(VoiceScene):
    SECTION = "s07"

    def construct(self):
        self.show_chapter()
        cw = ContextWindow(CW_W, CW_H).move_to(CW_C)
        top = cw.frame.get_top()[1] - 0.18
        inner = CW_H - 0.36
        lst = MessageList([cw.frame.get_left()[0] + 0.18, top], gap=0.05)

        def frac():
            return min(1.0, (top - lst.bottom) / inner)

        def drop(c, rt=0.45):
            lst.push(c)
            self.play(FadeIn(c, shift=DOWN * 0.25), cw.meter_to(frac()), run_time=rt)

        # ---- the list keeps growing
        bars = VGroup(*[RoundedRectangle(width=1.7, height=0.17, corner_radius=0.04)
                        .set_stroke(ROLE_COLORS[r], 1.2).set_fill(ROLE_COLORS[r], 0.18)
                        for r in ("system", "user", "assistant", "tool", "assistant", "tool", "assistant")])
        bars.arrange(UP, buff=0.07).move_to([0, -0.6, 0], aligned_edge=DOWN)
        ceiling = DashedLine([-2.0, 1.25, 0], [2.0, 1.25, 0], dash_length=0.1).set_stroke(RED, 2)
        ceil_lab = caps("limit", 15, RED).next_to(ceiling, RIGHT, buff=0.2)
        with self.say("s07_01") as v:
            self.wait_until(v.cue("grows") - 0.3)
            self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in bars], lag_ratio=0.3), run_time=1.6)
            self.wait_until(v.cue("forever") - 0.4)
            self.play(Create(ceiling), FadeIn(ceil_lab), run_time=0.5)
            self.play(bars.animate.shift(UP * 0.35), rate_func=there_and_back, run_time=0.6)

        # ---- everything sent in one call must fit
        sysc = card("system", "coding agent rules")
        u = card("user", "What port does…?")
        a = card("assistant", content=call("read_file", "config.txt"))
        tl = card("tool", "3 tool descriptions", label="tool list", accent=TEAL)
        res = card("tool", content=VGroup(mono("port = 8080, host = localhost,", 12, FG),
                                          mono("timeout = 30, debug = off", 12, FG)).arrange(DOWN, buff=0.06, aligned_edge=LEFT))
        with self.say("s07_02") as v:
            self.play(FadeOut(bars), FadeOut(ceiling), FadeOut(ceil_lab), run_time=0.4)
            self.wait_until(v.cue("limit") - 0.3)
            self.play(FadeIn(cw.frame), FadeIn(cw.meter_box), FadeIn(cw.fill), run_time=0.6)
            self.wait_until(v.cue("system") - 0.3)
            drop(sysc)
            self.wait_until(v.cue("messages") - 0.3)
            drop(u, 0.35)
            drop(a, 0.35)
            self.wait_until(v.cue("descriptions") - 0.3)
            drop(tl)
            self.wait_until(v.cue("results") - 0.3)
            drop(res)

        with self.say("s07_03") as v:
            self.wait_until(v.cue("cw") - 0.35)
            self.play(FadeIn(cw.label, shift=DOWN * 0.08), glow(cw.frame, FG, 6), run_time=0.7)

        # ---- tokens
        tok_lab = caps("tokens", 14, MUTED).next_to(cw.meter_box, UP, buff=0.14)
        word = bn("understanding", 40, FG).move_to([4.35, 1.2, 0])
        chips = VGroup(*[Pill(mono(p, 24, c), c, pad_x=0.16) for p, c in
                         (("under", BLUE), ("stand", TEAL), ("ing", AMBER))]).arrange(RIGHT, buff=0.12)
        chips.move_to([4.35, 0.05, 0])
        chip_lab = en("3 tokens", 22, MUTED).next_to(chips, DOWN, buff=0.28)
        with self.say("s07_04") as v:
            self.wait_until(v.cue("tokens") - 0.3)
            self.play(FadeIn(tok_lab, shift=DOWN * 0.06), glow(cw.meter_box, FG, 5), run_time=0.5)
            self.wait_until(v.cue("piece") - 0.4)
            self.play(FadeIn(word, shift=LEFT * 0.1), run_time=0.5)
            self.wait_until(v.cue("part") - 0.3)
            self.play(TransformFromCopy(word, chips), FadeIn(chip_lab), run_time=0.8)

        # ---- the desk
        desk = RoundedRectangle(width=3.7, height=2.35, corner_radius=0.16).set_stroke(AMBER, 2).set_fill(AMBER, 0.05)
        desk.move_to([4.4, 0.05, 0])
        desk_lab = VGroup(en("desk", 26, AMBER), caps("fixed size", 14, MUTED)).arrange(RIGHT, buff=0.2)
        desk_lab.next_to(desk, UP, buff=0.18)
        same = en("≈", 44, MUTED).move_to([1.65, 0.05, 0])
        spots = [desk.get_center() + np.array([x, y, 0]) for x, y in ((-1.05, 0.55), (0.0, 0.6), (1.05, 0.5),
                                                                       (-0.95, -0.45), (0.1, -0.5), (1.05, -0.45))]
        papers = [paper(0.82, 0.6, 3).rotate(r).move_to(p) for p, r in zip(spots, (0.08, -0.05, 0.06, -0.08, 0.04, -0.06))]
        with self.say("s07_05") as v:
            self.play(FadeOut(word), FadeOut(chips), FadeOut(chip_lab), run_time=0.4)
            self.wait_until(v.cue("desk") - 0.3)
            self.play(FadeIn(desk), FadeIn(desk_lab, shift=DOWN * 0.06), FadeIn(same), run_time=0.6)
            self.wait_until(v.cue("paper") - 0.3)
            self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.2) for p in papers[:3]], lag_ratio=0.3), run_time=0.9)
            self.wait_until(v.cue("same") - 0.3)
            self.play(*[glow(p.sheet, AMBER, 4) for p in papers[:3]], run_time=0.6)

        more = [card("assistant", content=call("run_command", "tests"))]
        with self.say("s07_06") as v:
            self.wait_until(v.cue("works") - 0.3)
            for c in more:
                drop(c, 0.4)
            self.wait_until(v.cue("fills") - 0.4)
            self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.2) for p in papers[3:]], lag_ratio=0.25), run_time=0.8)

        remaining = (lst.bottom - lst.gap) - (top - inner) - 0.06     # free space left in the window
        body = VGroup(mono("big_log.txt", 13, MUTED), code_block(1.7, 7, color=DIM, gap=0.15)).arrange(
            DOWN, buff=0.12, aligned_edge=LEFT)
        if body.height > remaining - 0.32:
            body.scale_to_fit_height(remaining - 0.32)
        huge = card("tool", content=body, min_h=remaining)
        huge.scale(0.84).move_to([-5.48, 0.2, 0])                      # waiting outside, left of the window
        big_file = VGroup(I.file_icon(0.62, MUTED), en("a very large file", 20, MUTED)).arrange(RIGHT, buff=0.16)
        big_file.next_to(huge, UP, buff=0.2)
        if big_file.get_left()[0] < -6.75:
            big_file.shift(RIGHT * (-6.75 - big_file.get_left()[0]))
        with self.say("s07_07") as v:
            self.wait_until(v.cue("huge") - 0.3)
            self.play(FadeIn(huge, shift=RIGHT * 0.15), run_time=0.6)
            self.wait_until(v.cue("large") - 0.3)
            self.play(FadeIn(big_file, shift=DOWN * 0.06), run_time=0.5)

        cover = RoundedRectangle(width=3.4, height=1.9, corner_radius=0.08).set_stroke(MUTED, 1.6).set_fill(PANEL_2, 1)
        cover.move_to(desk.get_center() + DOWN * 0.08)
        cover_lines = code_block(2.6, 6, color=DIM, gap=0.24).move_to(cover)
        with self.say("s07_08") as v:
            self.wait_until(v.cue("gone") - 0.8)
            slot = lst.next_point(huge.copy().scale(1 / 0.84))
            lst.cards.append(huge)
            self.play(FadeOut(big_file), huge.animate.scale(1 / 0.84).move_to(slot), cw.meter_to(0.93), FadeIn(cover),
                      FadeIn(cover_lines),
                      run_time=0.9)
            self.play(glow(cw.fill, AMBER, 5), run_time=0.4)

        full = Pill(en("full", 22, RED, italic=False, weight=NORMAL), RED, pad_x=0.24).move_to(cw.label)
        extra = card("user", "and one more…").scale(0.8).move_to([cw.frame.get_x() + 0.55, cw.frame.get_top()[1] + 0.78, 0])
        with self.say("s07_09") as v:
            self.wait_until(v.cue("full") - 0.5)
            self.play(cw.meter_to(1.0), cw.frame.animate.set_stroke(RED), FadeOut(cw.label), FadeIn(full, scale=0.9),
                      run_time=0.6)
            self.play(FadeIn(extra, shift=DOWN * 0.2), run_time=0.3)
            self.play(extra.animate.shift(DOWN * 0.25), rate_func=there_and_back, run_time=0.4)
            self.play(FadeOut(extra, shift=UP * 0.2), run_time=0.3)

        # ---- what happens when it is full
        def option(i, text, color, icon=None):
            parts = [en(str(i), 22, color, italic=False, weight=NORMAL)]
            if icon is not None:
                parts.append(icon)
            parts.append(en(text, 22, FG))
            return Pill(VGroup(*parts).arrange(RIGHT, buff=0.14), color, pad_x=0.24, pad_y=0.1)

        head = caps("when it is full", 16, MUTED).move_to([4.3, 2.45, 0])
        opts = VGroup(option(1, "the request fails", RED, I.cross_icon(0.2)),
                      option(2, "remove or shorten old messages", AMBER),
                      option(3, "replace old messages with a summary", VIOLET)).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        opts.move_to([4.25, 1.2, 0])
        if opts.get_right()[0] > 6.75:
            opts.shift(LEFT * (opts.get_right()[0] - 6.75))
        with self.say("s07_10") as v:
            self.play(*[FadeOut(m) for m in (desk, desk_lab, same, *papers, cover, cover_lines)], run_time=0.5)
            self.play(FadeIn(head), run_time=0.3)
            self.wait_until(v.cue("fail") - 0.3)
            self.play(FadeIn(opts[0], shift=LEFT * 0.1), glow(cw.frame, RED, 6), run_time=0.5)

        def relayout(rt=0.6, level=None):
            anims = [c.animate.move_to(p) for c, p in lst.layout_targets()]
            lv = frac() if level is None else level
            return self.play(*anims, cw.meter_to(lv), run_time=rt)

        with self.say("s07_11") as v:
            self.wait_until(v.cue("remove") - 0.3)
            self.play(FadeIn(opts[1], shift=LEFT * 0.1), run_time=0.45)
            gone = [lst.cards[1], lst.cards[2]]
            self.play(*[FadeOut(c, shift=LEFT * 0.4) for c in gone], run_time=0.5)
            for c in gone:
                lst.remove(c)
            relayout(0.5)
            self.play(cw.frame.animate.set_stroke(FG, opacity=0.8), FadeOut(full), FadeIn(cw.label), run_time=0.3)
            self.wait_until(v.cue("shorten") - 0.3)
            short = card("tool", content=mono("port = 8080", 13, FG))
            old = lst.cards[2]                       # the two-line tool result
            short.move_to(old.get_top() + DOWN * short.height / 2)
            self.play(FadeTransform(old, short), run_time=0.5)
            lst.cards[2] = short
            relayout(0.4)

        with self.say("s07_12") as v:
            self.wait_until(v.cue("summary") - 0.4)
            self.play(FadeIn(opts[2], shift=LEFT * 0.1), run_time=0.45)
            olds = lst.cards[2:4]                    # older results and messages
            summ = card("system", "port 8080, tests pass", label="summary", accent=VIOLET)
            summ.move_to(VGroup(*olds).get_top() + DOWN * summ.height / 2)
            self.play(*[c.animate.move_to(summ).scale(0.96).set_opacity(0) for c in olds], FadeIn(summ, scale=0.96),
                      run_time=0.7)
            self.remove(*olds)
            lst.cards[2:4] = [summ]
            relayout(0.5)

        cost_h = caps("longer context", 16, MUTED).move_to([4.3, -0.55, 0])
        slow = Pill(VGroup(clock_icon(0.3, FG), en("slower", 22, FG)).arrange(RIGHT, buff=0.14), FG, pad_x=0.24)
        pricey = Pill(VGroup(coins_icon(0.3, AMBER), en("more expensive", 22, FG)).arrange(RIGHT, buff=0.14), AMBER,
                      pad_x=0.24)
        VGroup(slow, pricey).arrange(RIGHT, buff=0.3).move_to([4.3, -1.2, 0])
        with self.say("s07_13") as v:
            self.wait_until(v.cue("cost") - 0.3)
            self.play(opts.animate.fade(0.6), FadeIn(cost_h), run_time=0.45)
            self.wait_until(v.cue("slower") - 0.3)
            self.play(FadeIn(slow, shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("expensive") - 0.3)
            self.play(FadeIn(pricey, shift=UP * 0.08), run_time=0.4)

        keep = lst.cards[:-1]
        drop_ = lst.cards[-1:]
        keep_marks = VGroup(*[I.check_icon(0.26, TEAL).next_to(c, RIGHT, buff=0.12) for c in keep])
        drop_marks = VGroup(*[I.cross_icon(0.22).next_to(c, RIGHT, buff=0.14) for c in drop_])
        hard = Pill(en("one of the hardest problems", 22, AMBER), AMBER, pad_x=0.26).move_to([4.3, -2.15, 0])
        with self.say("s07_14") as v:
            self.wait_until(v.cue("stays") - 0.3)
            self.play(FadeIn(keep_marks, scale=0.8), run_time=0.4)
            self.wait_until(v.cue("goes") - 0.3)
            self.play(FadeIn(drop_marks, scale=0.8), run_time=0.4)
            self.wait_until(v.cue("hardest") - 0.3)
            self.play(FadeIn(hard, shift=UP * 0.08), run_time=0.5)

        t1 = spaced("CONTEXT MANAGEMENT", 46, FG, tracking=0.3, weight=LIGHT)
        if t1.width > 12.0:
            t1.scale_to_fit_width(12.0)
        t1.move_to([0, 0.45, 0])
        nxt = caps("next lesson", 18, AMBER).next_to(t1, DOWN, buff=0.45)
        with self.say("s07_15") as v:
            self.wait_until(v.cue("cm") - 0.5)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.5)
            self.play(FadeIn(t1, shift=UP * 0.1), run_time=0.7)
            self.wait_until(v.cue("next") - 0.3)
            self.play(FadeIn(nxt, shift=UP * 0.06), run_time=0.5)
        self.wait(0.4)
        self.clear_all(0.8)
