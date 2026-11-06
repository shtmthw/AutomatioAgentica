"""09 · Conclusion - recap, the road ahead, title card."""
from agentic_video.prelude import *


def website_mock() -> VGroup:
    """Mini browser with a page that builds up: nav bar, hero, three cards."""
    br = Browser(3.9, 2.35, "my-website.com")
    bc = br.body_center
    nav = VGroup(Dot(radius=0.06, color=TEAL),
                 *[Line(ORIGIN, RIGHT * w).set_stroke(MUTED, 3, opacity=0.8) for w in (0.35, 0.35, 0.35)])
    nav.arrange(RIGHT, buff=0.18).move_to(bc + UP * 0.74 + LEFT * 0.95)
    hero = RoundedRectangle(width=3.4, height=0.62, corner_radius=0.1).set_stroke(TEAL, 1.3).set_fill(TEAL, 0.12)
    hero.move_to(bc + UP * 0.2)
    h_title = Line(ORIGIN, RIGHT * 1.6).set_stroke(FG, 4).move_to(hero.get_left() + RIGHT * 1.05 + UP * 0.1)
    h_sub = Line(ORIGIN, RIGHT * 1.1).set_stroke(MUTED, 3).move_to(hero.get_left() + RIGHT * 0.8 + DOWN * 0.1)
    h_btn = RoundedRectangle(width=0.62, height=0.2, corner_radius=0.1).set_stroke(width=0).set_fill(TEAL, 0.9)
    h_btn.move_to(hero.get_right() + LEFT * 0.55)
    cards = VGroup()
    for i in range(3):
        c = RoundedRectangle(width=1.0, height=0.55, corner_radius=0.08).set_stroke(FAINT, 1.4).set_fill(PANEL_2, 1)
        c.add(Line(ORIGIN, RIGHT * 0.6).set_stroke(MUTED, 3, opacity=0.7).move_to(c.get_center() + UP * 0.08),
              Line(ORIGIN, RIGHT * 0.4).set_stroke(DIM, 3).move_to(c.get_center() + DOWN * 0.1 + LEFT * 0.1))
        cards.add(c)
    cards.arrange(RIGHT, buff=0.2).move_to(bc + DOWN * 0.6)
    g = VGroup(br, nav, VGroup(hero, h_title, h_sub, h_btn), *cards)
    g.frame, g.parts = br, [nav, g[2], *cards]
    return g


def app_mock() -> VGroup:
    """Phone frame with an app screen that builds up: header, list, button."""
    body = RoundedRectangle(width=1.45, height=2.6, corner_radius=0.24).set_stroke(FG, 2).set_fill(PANEL, 1)
    notch = RoundedRectangle(width=0.42, height=0.08, corner_radius=0.04).set_stroke(width=0).set_fill(FAINT, 1)
    notch.move_to(body.get_top() + DOWN * 0.13)
    top = body.get_top()
    header = VGroup(Line(ORIGIN, RIGHT * 0.7).set_stroke(TEAL, 4),
                    Dot(radius=0.06, color=MUTED)).arrange(RIGHT, buff=0.32).move_to(top + DOWN * 0.42)
    rows = VGroup()
    for i in range(3):
        av = Circle(radius=0.1).set_stroke(MUTED, 1.4).set_fill(FAINT, 1)
        bars = VGroup(Line(ORIGIN, RIGHT * 0.62).set_stroke(FG, 3, opacity=0.8),
                      Line(ORIGIN, RIGHT * 0.42).set_stroke(DIM, 3)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        rows.add(VGroup(av, bars).arrange(RIGHT, buff=0.14))
    rows.arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to(body.get_center() + UP * 0.02)
    btn = RoundedRectangle(width=1.0, height=0.24, corner_radius=0.12).set_stroke(width=0).set_fill(TEAL, 0.9)
    btn.move_to(body.get_bottom() + UP * 0.36)
    g = VGroup(body, notch, header, *rows, btn)
    g.frame, g.parts = VGroup(body, notch), [header, *rows, btn]
    return g


class S09Outro(VoiceScene):
    SECTION = "s09"

    def construct(self):
        self.show_chapter()

        # ---- recap
        def recap_card(icon, text, color):
            card = Card(3.7, 2.05, color, stroke_width=1.5)
            icon.move_to(card.frame.get_center() + UP * 0.35)
            t = bn(text, 26, FG).next_to(icon, DOWN, buff=0.26)
            check = I.check_icon(0.3, TEAL).move_to(card.frame.get_corner(UR) + LEFT * 0.32 + DOWN * 0.32)
            card.add(icon, t)
            card.check = check
            return card

        chat_neq = VGroup(en("chat", 26, BLUE), en("≠", 30, FG), en("agent", 26, TEAL)).arrange(RIGHT, buff=0.15)
        cards = VGroup(
            recap_card(I.spark_icon(0.6, TEAL), "what an AI agent is", TEAL),
            recap_card(I.loop_icon(0.6, BLUE), "how it works", BLUE),
            recap_card(chat_neq, "chatbot vs agent", VIOLET),
        ).arrange(RIGHT, buff=0.4).move_to([0, 0.3, 0])
        for c in cards:  # position checks after layout (they are not part of the card group)
            c.check.move_to(c.frame.get_corner(UR) + LEFT * 0.32 + DOWN * 0.32)
        with self.say("s09_01") as v:
            for i, w in enumerate(("क्या", "कैसे", "फ़र्क")):
                self.wait_until(v.word(w) - 0.3)
                self.play(FadeIn(cards[i], shift=UP * 0.12), run_time=0.5)
                self.play(FadeIn(cards[i].check, scale=0.6), run_time=0.3)

        # ---- the road ahead
        y = 0.0
        start = np.array([-6.0, y, 0])
        end = np.array([6.05, y, 0])
        road = DashedLine(start, end, dash_length=0.09).set_stroke(DIM, 2)
        s_node = VGroup(Circle(radius=0.2).set_stroke(TEAL, 2).set_fill(TEAL, 0.9)).move_to(start)
        s_lab = bn("the basics", 22, TEAL).next_to(s_node, DOWN, buff=0.28)
        with self.say("s09_02") as v:
            self.wait_until(v.word("बुनियादी") - 0.6)
            checks = VGroup(*[c.check for c in cards])
            self.play(*[m.animate.scale(0.08).move_to(start).set_opacity(0) for m in (*cards, *checks)], run_time=0.9)
            self.remove(*cards, *checks)
            self.play(FadeIn(s_node, scale=0.5), FadeIn(s_lab), run_time=0.6)

        with self.say("s09_03") as v:
            self.play(Create(road), run_time=1.4)

        topics = ["Architecture", "Tool Integration", "Context Management", "Memory", "Planning", "Agentic Systems"]
        cues = ["Architecture", "Tool", "Context", "Memory", "Planning", "Agentic"]
        xs = np.linspace(-4.05, 4.2, len(topics))
        nodes, labels = VGroup(), VGroup()
        for i, (t, x) in enumerate(zip(topics, xs)):
            n = Circle(radius=0.13).set_stroke(BLUE, 2).set_fill(BG, 1).move_to([x, y, 0])
            lab = en(t, 24, FG)
            lab.next_to(n, UP if i % 2 == 0 else DOWN, buff=0.32)
            tick = Line(n.get_center(), lab.get_edge_center(DOWN if i % 2 == 0 else UP)).set_stroke(FAINT, 1.4)
            nodes.add(n)
            labels.add(VGroup(tick, lab))
        with self.say("s09_04") as v:
            for i, w in enumerate(cues):
                self.wait_until(v.word(w) - 0.25)
                self.play(FadeIn(nodes[i], scale=0.5), FadeIn(labels[i], shift=(DOWN if i % 2 == 0 else UP) * -0.08),
                          run_time=0.4)

        # ---- we'll also learn to build websites and apps
        end_dot = Circle(radius=0.16).set_stroke(TEAL, 2).set_fill(BG, 1).move_to(end)
        roadmap = VGroup(road, s_node, s_lab, nodes, labels, end_dot)
        site = website_mock().move_to([-2.0, -1.0, 0])
        app = app_mock().move_to([2.3, -1.0, 0])
        lab_y = max(site.get_top()[1], app.get_top()[1]) + 0.32   # shared baseline for both labels
        site_lab = en("Website", 28, TEAL).move_to([site.get_x(), lab_y, 0])
        app_lab = en("App", 28, TEAL).move_to([app.get_x(), lab_y, 0])
        plus = en("+", 44, MUTED).move_to([0.75, -1.0, 0])
        with self.say("s09_05") as v:
            self.play(FadeIn(end_dot, scale=0.5), run_time=0.3)
            self.play(roadmap.animate.scale(0.78).move_to([0, 2.05, 0]), run_time=0.9)
            self.wait_until(v.word("Website") - 0.35)
            self.play(FadeIn(site.frame, shift=UP * 0.1), FadeIn(site_lab, shift=UP * 0.08), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.06) for p in site.parts], lag_ratio=0.25), run_time=1.0)
            self.wait_until(v.word("App") - 0.35)
            self.play(FadeIn(plus), FadeIn(app.frame, shift=UP * 0.1), FadeIn(app_lab, shift=UP * 0.08), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.06) for p in app.parts], lag_ratio=0.2), run_time=1.0)
        self.play(glow(site.frame.frame, TEAL, 4), glow(app.frame[0], TEAL, 4), run_time=0.8)

        with self.say("s09_06") as v:
            self.wait_until(v.word("शुरुआत") - 0.4)
            self.play(glow(s_node[0], TEAL, 6, 1.0), pulse(s_node, 1.3), run_time=1.0)

        # ---- title card
        self.wait(0.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        t1 = spaced("AGENTIC AI", 84, FG, tracking=0.42, weight=LIGHT)
        rule = Line(LEFT * 1.6, RIGHT * 1.6).set_stroke(FAINT, 1.6)
        t2 = spaced("THE BEGINNING", 26, MUTED, tracking=0.75, weight=NORMAL)
        card = VGroup(t1, rule, t2).arrange(DOWN, buff=0.42).move_to(UP * 0.15)
        self.play(FadeIn(t1, shift=UP * 0.12), run_time=1.4)
        self.play(Create(rule), FadeIn(t2, shift=UP * 0.08), run_time=1.0)
        self.wait(4.0)
        self.play(FadeOut(card), run_time=1.5)
        self.wait(0.8)
