"""04 · The conversation is a list of messages: four roles, the memory test done right,
the whole list is sent on every call."""
from agentic_video.prelude import *

LIST_X, LIST_TOP, CARD_W = -0.35, 2.2, 6.55


def legend_item(role, text):
    c = ROLE_COLORS[role]
    tag = VGroup(RoundedRectangle(width=1.36, height=0.3, corner_radius=0.08).set_stroke(c, 1.3).set_fill(c, 0.14),
                 caps(role, 14, c))
    tag[1].move_to(tag[0])
    return VGroup(tag, en(text, 20, MUTED)).arrange(RIGHT, buff=0.16)


def stack(n, w=1.5, h=0.17, gap=0.06):
    roles = ["system", "user", "assistant", "user", "assistant", "user", "assistant"]
    g = VGroup(*[RoundedRectangle(width=w, height=h, corner_radius=0.04).set_stroke(ROLE_COLORS[roles[i]], 1.2)
                 .set_fill(ROLE_COLORS[roles[i]], 0.18) for i in range(n)]).arrange(DOWN, buff=gap)
    return g


class S04Messages(VoiceScene):
    SECTION = "s04"

    def send(self, cards, model, rt=1.3, arc=PI * 0.45):
        """The whole list travels into the model (over the top, into its input side)."""
        b = VGroup(*[c.copy() for c in cards])
        self.add(b)
        self.play(b.animate.scale(0.3).next_to(cards[0], LEFT, buff=0.3).shift(DOWN * 0.4), run_time=rt * 0.35)
        self.play(b.animate(path_arc=arc).scale(0.5).move_to(model.in_port + RIGHT * 0.25).set_opacity(0),
                  run_time=rt * 0.65)
        self.remove(b)
        self.play(model.think(0.6), run_time=0.6)

    def construct(self):
        self.show_chapter()
        harness = HarnessFrame(13.4, 5.72).move_to([0, 0.15, 0])
        model = ModelBox(2.5, 1.5).move_to([-4.65, 0.25, 0])
        head = caps("messages", 16, MUTED).move_to([LIST_X, LIST_TOP + 0.38, 0], aligned_edge=LEFT)
        rule = Line([LIST_X, LIST_TOP + 0.2, 0], [LIST_X + CARD_W, LIST_TOP + 0.2, 0]).set_stroke(FAINT, 1.4)
        lst = MessageList([LIST_X, LIST_TOP], gap=0.12)

        with self.say("s04_01") as v:
            self.play(FadeIn(harness), FadeIn(model, scale=0.95), run_time=0.7)
            self.wait_until(v.cue("list") - 0.3)
            self.play(FadeIn(head, shift=DOWN * 0.06), Create(rule), run_time=0.5)

        ph = MessageCard("system", "a message", width=CARD_W, label="role", accent=DIM, text_color=MUTED)
        lst.place(ph)
        role_lab = en("role", 22, AMBER).next_to(ph.tag, DOWN, buff=0.22)
        with self.say("s04_02") as v:
            self.wait_until(v.cue("stores") - 0.3)
            self.play(glow(harness.frame, AMBER, 5), run_time=0.6)
            self.wait_until(v.cue("message") - 0.3)
            self.play(FadeIn(ph, shift=RIGHT * 0.15), run_time=0.5)
            self.wait_until(v.cue("role") - 0.3)
            self.play(glow(ph.tag[0], AMBER, 6), FadeIn(role_lab, shift=UP * 0.06), run_time=0.6)

        legend = VGroup(legend_item("system", "developer's rules"), legend_item("user", "the person"),
                        legend_item("assistant", "the model"), legend_item("tool", "tool results"))
        legend.arrange(RIGHT, buff=0.5).move_to([0, -2.2, 0])
        if legend.width > 12.6:
            legend.scale_to_fit_width(12.6)

        sysc = MessageCard("system", "You are a helpful coding agent. Ask before deleting any file.", width=CARD_W,
                           wrap=40)
        lst.push(sysc)
        with self.say("s04_03") as v:
            self.wait_until(v.cue("system") - 0.3)
            self.play(FadeOut(ph), FadeOut(role_lab), FadeIn(VGroup(sysc.frame, sysc.tag)), run_time=0.5)
            self.wait_until(v.cue("instructions") - 0.3)
            self.play(FadeIn(legend[0], shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("rules") - 0.3)
            self.play(glow(sysc.frame, MUTED, 5), run_time=0.6)

        with self.say("s04_04") as v:
            self.wait_until(v.cue("example") - 0.3)
            self.play(FadeIn(sysc.body, shift=RIGHT * 0.1), run_time=0.6)

        sp = Pill(en("system prompt", 22, FG), MUTED, pad_x=0.24).move_to([-1.95, sysc.get_y() + 0.05, 0])
        sp_arrow = arrow(sp.get_right() + RIGHT * 0.05, sysc.get_left() + LEFT * 0.06, color=MUTED, tip=0.1)
        with self.say("s04_05") as v:
            self.wait_until(v.cue("prompt") - 0.3)
            self.play(FadeIn(sp, shift=RIGHT * 0.1), GrowArrow(sp_arrow), run_time=0.5)

        u1 = lst.push(MessageCard("user", "My name is Rahul.", width=CARD_W))
        with self.say("s04_06") as v:
            self.wait_until(v.cue("user") - 0.3)
            self.play(FadeIn(VGroup(u1.frame, u1.tag), shift=RIGHT * 0.12), FadeIn(legend[1], shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("example") - 0.3)
            self.play(FadeIn(u1.body, shift=RIGHT * 0.1), run_time=0.5)

        a1 = lst.push(MessageCard("assistant", "Hello, Rahul!", width=CARD_W))
        with self.say("s04_07") as v:
            self.wait_until(v.cue("assistant") - 0.3)
            self.play(FadeIn(VGroup(a1.frame, a1.tag), shift=RIGHT * 0.12), FadeIn(legend[2], shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("example") - 0.3)
            self.play(FadeIn(a1.body, shift=RIGHT * 0.1), run_time=0.5)

        later = caps("later", 14, DIM).next_to(legend[3], UP, buff=0.12)
        with self.say("s04_08") as v:
            self.wait_until(v.cue("tool") - 0.3)
            self.play(FadeIn(legend[3], shift=UP * 0.08), glow(legend[3][0][0], TEAL, 5), run_time=0.5)
            self.wait_until(v.cue("soon") - 0.3)
            self.play(FadeIn(later, shift=DOWN * 0.05), run_time=0.4)

        # ---- the memory test, done right
        replay = Pill(en("memory test, again", 22, FG), FG, pad_x=0.26).move_to([-4.65, 1.75, 0])
        with self.say("s04_09") as v:
            self.wait_until(v.cue("replay") - 0.3)
            self.play(FadeOut(sp), FadeOut(sp_arrow), FadeOut(later), legend.animate.fade(0.55),
                      FadeIn(replay, shift=DOWN * 0.08), run_time=0.6)

        u2 = MessageCard("user", "What is my name?", width=CARD_W)
        with self.say("s04_10") as v:
            for w, c in (("system", sysc), ("name", u1), ("hello", a1)):
                self.wait_until(v.cue(w) - 0.2)
                self.play(glow(c.frame, c.accent, 5, 0.5), pulse(c, 1.03, 0.5), run_time=0.5)
            self.wait_until(v.cue("question") - 0.3)
            lst.push(u2)
            self.play(FadeIn(u2, shift=RIGHT * 0.15), run_time=0.5)

        def outline(cards, color=AMBER):
            g = VGroup(*cards)
            r = RoundedRectangle(width=g.width + 0.24, height=g.height + 0.22, corner_radius=0.14).move_to(g)
            return dashed_outline(r, color, 1.8)

        out1 = outline(lst.cards)
        with self.say("s04_11") as v:
            self.wait_until(v.cue("entire") - 0.3)
            self.play(Create(out1), run_time=0.6)
            self.wait_until(v.cue("bundle") - 0.5)
            self.send(lst.cards, model, 1.3)

        reply = MessageCard("assistant", "Your name is Rahul.", width=4.3).move_to([-2.65, -1.15, 0])
        r_arrow = arrow(model.frame.get_bottom() + DOWN * 0.05 + RIGHT * 0.75, reply.get_top() + UP * 0.05 + LEFT * 0.9,
                        color=BLUE, tip=0.1)
        with self.say("s04_12") as v:
            self.wait_until(v.cue("reply") - 0.35)
            self.play(FadeOut(out1), GrowArrow(r_arrow), FadeIn(reply, shift=RIGHT * 0.2), run_time=0.6)

        final = MessageCard("assistant", "Your name is Rahul.", width=CARD_W)
        lst.push(final)
        with self.say("s04_13") as v:
            self.wait_until(v.cue("adds") - 0.3)
            self.play(FadeOut(r_arrow), FadeTransform(reply, final), run_time=0.8)
            self.wait_until(v.cue("assistant") - 0.3)
            self.play(glow(final.tag[0], BLUE, 6), run_time=0.5)

        key = Pill(en("the whole conversation, every call", 22, AMBER), AMBER, pad_x=0.28).move_to([-3.35, -1.15, 0])
        with self.say("s04_14") as v:
            self.wait_until(v.cue("key") - 0.3)
            self.play(FadeIn(key, shift=UP * 0.08), FadeOut(replay), run_time=0.5)
            self.wait_until(v.cue("whole") - 0.4)
            out2 = outline(lst.cards)
            self.play(Create(out2), run_time=0.5)
            self.send(lst.cards, model, 1.2)
            self.play(FadeOut(out2), run_time=0.3)

        mem = Pill(VGroup(caps("memory", 15, AMBER), en("lives here", 20, FG)).arrange(RIGHT, buff=0.14), AMBER,
                   pad_x=0.22).move_to([LIST_X + CARD_W - 1.2, LIST_TOP + 0.4, 0])
        nomem = en("no memory", 20, DIM).next_to(model, UP, buff=0.22)
        with self.say("s04_15") as v:
            self.wait_until(v.cue("remember") - 0.3)
            self.play(model.think(0.6), run_time=0.6)
            self.wait_until(v.cue("memory") - 0.3)
            self.play(FadeIn(mem, shift=DOWN * 0.08), FadeIn(nomem), run_time=0.5)
            self.wait_until(v.cue("harness") - 0.3)
            self.play(glow(harness.frame, AMBER, 7), pulse(lst.group(), 1.02), run_time=0.8)

        # ---- the bundle grows with every call
        veil = Rectangle(width=16, height=9).set_stroke(width=0).set_fill(BG, 0.9)
        stacks = VGroup()
        for i, n in enumerate((2, 4, 6)):
            s = stack(n)
            lab = VGroup(caps("call", 16, MUTED), en(f"#{i + 1}", 26, FG, italic=False, weight=NORMAL)).arrange(RIGHT, buff=0.1)
            g = VGroup(lab, s).arrange(DOWN, buff=0.25)
            stacks.add(g)
        stacks.arrange(RIGHT, buff=1.6, aligned_edge=DOWN).move_to([0, 0.15, 0])
        grow = arrow(stacks[0].get_corner(DOWN + RIGHT) + DOWN * 0.3 + LEFT * 0.4,
                     stacks[2].get_corner(DOWN + RIGHT) + DOWN * 0.3, color=AMBER, tip=0.12)
        grow_lab = en("bigger every call", 22, AMBER).next_to(grow, DOWN, buff=0.14)
        with self.say("s04_16") as v:
            self.wait_until(v.cue("bigger") - 0.4)
            self.play(FadeIn(veil), run_time=0.5)
            for i, w in enumerate(("one", "two", "three")):
                self.wait_until(v.cue(w) - 0.3)
                self.play(FadeIn(stacks[i], shift=UP * 0.12), run_time=0.45)
            self.play(GrowArrow(grow), FadeIn(grow_lab), run_time=0.5)

        with self.say("s04_17") as v:
            self.play(glow(stacks[2][1], AMBER, 5), pulse(stacks[2], 1.05), run_time=0.7)
        self.wait(0.5)
        self.clear_all(0.8)
