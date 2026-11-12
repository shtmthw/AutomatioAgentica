"""03 · Why not just use a bigger window? The window stretches taller, then three reasons: it still
fills up, it gets slower and more expensive, details get lost in the clutter. The desk analogy,
the definition of context management, and the key line."""
from agentic_video.prelude import *
from memory_kit import *

CX, BOTTOM = -4.2, -2.62
W = 3.3
RX = 2.85                 # centre of the right-hand column


def thin(i):
    roles = ("assistant", "tool")
    r = roles[i % 2]
    col = BLUE if r == "assistant" else TEAL
    return SizedCard(r, content=code_block(1.4, 1, size=0.035, color=col, seed=i), height=0.27, width=W,
                     dashed=(r == "assistant"))


def reason(i, text, color):
    return Pill(VGroup(en(str(i), 22, color, italic=False, weight=NORMAL), en(text, 22, FG)).arrange(RIGHT, buff=0.16),
                color, pad_x=0.24, pad_y=0.1)


def desk(n_papers, messy, color):
    top = RoundedRectangle(width=3.1, height=1.75, corner_radius=0.12).set_stroke(color, 2).set_fill(color, 0.05)
    papers = VGroup()
    rnd = np.random.default_rng(3)
    if messy:
        for k in range(n_papers):
            p = paper(0.5, 0.36, 2, line_color=DIM).rotate(rnd.uniform(-0.5, 0.5))
            p.move_to(top.get_center() + np.array([rnd.uniform(-1.25, 1.25), rnd.uniform(-0.62, 0.62), 0]))
            papers.add(p)
    else:
        for k in range(n_papers):
            p = paper(0.42, 0.52, 3)
            papers.add(p)
        papers.arrange_in_grid(2, 5, buff=(0.12, 0.14)).move_to(top)
    return VGroup(top, papers)


class S03BiggerWindow(VoiceScene):
    SECTION = "s03"

    def construct(self):
        self.show_chapter()
        h0 = 2.6
        ctx = LiveContext([CX, BOTTOM + h0 / 2, 0], 3.6, h0)
        k = 0
        while ctx.free() > 0.5:
            ctx.place(thin(k))
            k += 1
        last = SizedCard("tool", content=code_block(1.4, 1, size=0.035, color=TEAL, seed=99), height=ctx.free(), width=W)
        ctx.size(last, 1.0 - ctx.level())
        ctx.place(last)
        ctx.cw.frame.set_stroke(RED)
        q = Pill(en("a bigger window?", 26, FG), FG, pad_x=0.28, pad_y=0.12).move_to([RX, 2.55, 0])

        with self.say("s03_01") as v:
            self.play(*ctx.appear(), LaggedStart(*[FadeIn(c) for c in ctx.cards], lag_ratio=0.05), run_time=0.9)
            self.wait_until(v.cue("bigger") - 0.4)
            self.play(FadeIn(q, shift=DOWN * 0.08), run_time=0.4)
            self.play(*ctx.resize(5.25, stroke=FG), run_time=0.95)

        r1 = reason(1, "it still has a limit", RED)
        r2 = reason(2, "slower and more expensive", AMBER)
        r3 = reason(3, "details get lost", VIOLET)
        rows = VGroup(r1, r2, r3).arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to([RX, 0.75, 0])
        helps = Pill(VGroup(I.check_icon(0.22, TEAL), en("helps", 22, FG)).arrange(RIGHT, buff=0.12), TEAL, pad_x=0.22)
        nots = Pill(VGroup(I.cross_icon(0.2), en("doesn't solve it", 22, FG)).arrange(RIGHT, buff=0.12), RED, pad_x=0.22)
        VGroup(helps, nots).arrange(RIGHT, buff=0.3).move_to([RX, 1.75, 0])
        with self.say("s03_02") as v:
            self.wait_until(v.cue("help") - 0.3)
            self.play(FadeIn(helps, shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("solve") - 0.3)
            self.play(FadeIn(nots, shift=UP * 0.08), run_time=0.4)

        with self.say("s03_03") as v:
            self.wait_until(v.cue("one") - 0.3)
            self.play(FadeOut(helps), FadeOut(nots), FadeIn(r1, shift=LEFT * 0.1), run_time=0.5)
            self.wait_until(v.cue("fills") - 0.4)
            while ctx.free() > 0.5:
                self.play(*ctx.add(thin(k), shift=DOWN * 0.15), run_time=0.15)
                k += 1
            fill = SizedCard("tool", content=code_block(1.4, 1, size=0.035, color=TEAL, seed=7), height=ctx.free(), width=W)
            ctx.size(fill, 1.0 - ctx.level())
            self.play(*ctx.add(fill, shift=DOWN * 0.15), run_time=0.25)
            self.play(ctx.cw.frame.animate.set_stroke(RED), glow(ctx.cw.frame, RED, 6), run_time=0.5)

        clock = clock_icon(0.36, FG)
        coins = coins_icon(0.36, AMBER)
        t_bar = Rectangle(width=0.3, height=0.16).set_stroke(width=0).set_fill(FG, 0.8)
        c_bar = Rectangle(width=0.3, height=0.16).set_stroke(width=0).set_fill(AMBER, 0.85)
        t_row = VGroup(clock, caps("time per call", 14, MUTED)).arrange(RIGHT, buff=0.16)
        c_row = VGroup(coins, caps("cost per call", 14, MUTED)).arrange(RIGHT, buff=0.16)
        meters = VGroup(t_row, c_row).arrange(DOWN, buff=0.38, aligned_edge=LEFT).move_to([RX - 1.4, -1.25, 0])
        t_bar.next_to(t_row, RIGHT, buff=0.3)
        c_bar.next_to(c_row, RIGHT, buff=0.3)
        x_l = max(t_bar.get_left()[0], c_bar.get_left()[0])
        t_bar.move_to([x_l, t_bar.get_y(), 0], aligned_edge=LEFT)
        c_bar.move_to([x_l, c_bar.get_y(), 0], aligned_edge=LEFT)
        with self.say("s03_04") as v:
            self.wait_until(v.cue("two") - 0.3)
            self.play(FadeIn(r2, shift=LEFT * 0.1), run_time=0.45)
            self.wait_until(v.cue("slower") - 0.3)
            self.play(FadeIn(t_row), FadeIn(t_bar), run_time=0.4)
            self.wait_until(v.cue("expensive") - 0.3)
            self.play(FadeIn(c_row), FadeIn(c_bar), run_time=0.4)
            self.wait_until(v.cue("costs") - 0.3)
            self.play(t_bar.animate.stretch_to_fit_width(2.6).align_to(t_bar, LEFT),
                      c_bar.animate.stretch_to_fit_width(2.6).align_to(c_bar, LEFT),
                      glow(ctx.cw.fill, RED, 5), run_time=1.4)

        # ---- details get lost: hundreds of dim messages, one important goal among them
        inner_top = ctx.top
        n = 46
        hay = VGroup()
        for j in range(n):
            col = (BLUE, TEAL, MUTED)[j % 3]
            b = RoundedRectangle(width=ctx.card_w * (0.55 + 0.4 * ((j * 37) % 11) / 11), height=0.07, corner_radius=0.03)
            b.set_stroke(width=0).set_fill(col, 0.28)
            hay.add(b)
        hay.arrange(DOWN, buff=0.03, aligned_edge=LEFT)
        hay.stretch_to_fit_height(ctx.inner).move_to([ctx.x0, inner_top, 0], aligned_edge=UL)
        goal = SizedCard("user", "Goal: fix the crash.", height=0.3, width=W, size=13)
        goal.move_to([ctx.x0 + W / 2, hay[n // 2].get_y(), 0])
        cover = BackgroundRectangle(goal, color=PANEL_2, fill_opacity=1, buff=0.04)
        with self.say("s03_05") as v:
            self.wait_until(v.cue("three") - 0.3)
            self.play(FadeIn(r3, shift=LEFT * 0.1), FadeOut(meters), FadeOut(t_bar), FadeOut(c_bar), run_time=0.5)
            self.wait_until(v.cue("cluttered") - 0.5)
            old = ctx.clear()
            self.play(FadeOut(VGroup(*old)), FadeIn(hay), run_time=0.8)
            hay.tokens = ctx.capacity
            ctx.cards = [hay]
            self.wait_until(v.cue("reliable") - 0.3)
            self.play(glow(ctx.cw.frame, VIOLET, 6), run_time=0.7)

        with self.say("s03_06") as v:
            self.wait_until(v.cue("goal") - 0.4)
            self.play(FadeIn(cover), FadeIn(goal, scale=1.15), glow(goal.frame, AMBER, 6), run_time=0.6)
            self.wait_until(v.cue("lost") - 0.3)
            self.play(goal.animate.fade(0.8), cover.animate.set_opacity(0), run_time=1.0)

        # ---- the desk
        messy = desk(26, True, MUTED).move_to([RX - 1.75, -1.35, 0])
        clean = desk(10, False, TEAL).move_to([RX + 1.75, -1.35, 0])
        m_lab = VGroup(I.cross_icon(0.2), en("1,000 papers", 19, MUTED)).arrange(RIGHT, buff=0.12).next_to(messy, UP, buff=0.12)
        c_lab = VGroup(I.check_icon(0.22, TEAL), en("the right 10", 19, TEAL)).arrange(RIGHT, buff=0.12).next_to(clean, UP,
                                                                                                                 buff=0.12)
        with self.say("s03_07") as v:
            self.wait_until(v.cue("desk") - 0.4)
            self.play(rows.animate.shift(UP * 0.55).fade(0.4), q.animate.fade(0.5), run_time=0.4)
            self.play(FadeIn(messy[0]), LaggedStart(*[FadeIn(p, scale=1.2) for p in messy[1]], lag_ratio=0.03),
                      FadeIn(m_lab), run_time=1.0)
            self.wait_until(v.cue("clean") - 0.3)
            self.play(FadeIn(clean[0]), run_time=0.4)
            self.wait_until(v.cue("right") - 0.4)
            self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in clean[1]], lag_ratio=0.08), FadeIn(c_lab),
                      run_time=0.9)

        # ---- context management
        t1 = spaced("CONTEXT MANAGEMENT", 46, FG, tracking=0.28, weight=LIGHT)
        if t1.width > 11.5:
            t1.scale_to_fit_width(11.5)
        eq = VGroup(en("=", 34, MUTED), en("deciding what the model sees on each call", 32, FG)).arrange(RIGHT, buff=0.2)
        if eq.width > 12.0:
            eq.scale_to_fit_width(12.0)
        dfn = VGroup(t1, eq).arrange(DOWN, buff=0.4).move_to([0, 1.0, 0])
        job = Pill(VGroup(I.gear(0.3, AMBER), en("the harness's job", 22, FG)).arrange(RIGHT, buff=0.14), AMBER, pad_x=0.26)
        dev = en("set up by the developers who build it", 20, MUTED)
        VGroup(job, dev).arrange(RIGHT, buff=0.3).move_to([0, -0.45, 0])
        with self.say("s03_08") as v:
            self.wait_until(v.cue("cm") - 0.5)
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chapter], run_time=0.5)
            self.play(FadeIn(t1, shift=UP * 0.1), run_time=0.6)
            self.wait_until(v.cue("sees") - 0.6)
            self.play(FadeIn(eq, shift=UP * 0.08), run_time=0.6)
            self.wait_until(v.cue("harness") - 0.3)
            self.play(FadeIn(job, shift=UP * 0.08), run_time=0.45)
            self.play(FadeIn(dev), run_time=0.4)

        more = VGroup(en("more context", 30, MUTED), I.cross_icon(0.26)).arrange(RIGHT, buff=0.2)
        right = VGroup(en("the right context", 34, TEAL), I.check_icon(0.3, TEAL)).arrange(RIGHT, buff=0.2)
        goal_row = VGroup(more, right).arrange(RIGHT, buff=1.2).move_to([0, -1.75, 0])
        strike = Line(more[0].get_left(), more[0].get_right()).set_stroke(RED, 2.4)
        with self.say("s03_09") as v:
            self.wait_until(v.cue("more") - 0.3)
            self.play(FadeIn(more, shift=UP * 0.08), run_time=0.45)
            self.play(Create(strike), run_time=0.35)
            self.wait_until(v.cue("right") - 0.3)
            self.play(FadeIn(right, shift=UP * 0.08), run_time=0.5)
            self.play(pulse(right, 1.08), run_time=0.6)
        self.wait(0.3)
        self.clear_all(0.6)
