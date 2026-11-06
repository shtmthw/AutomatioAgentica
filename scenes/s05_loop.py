"""05 · The agent loop: goal -> decide -> act -> observe -> evaluate -> (repeat)."""
from agentic_video.prelude import *

C_ = np.array([-0.85, -0.38, 0])  # ring centre
R = 1.85                          # ring radius (to node centres)
NODE_W, NODE_H = 1.5, 0.72
ANG = {"decide": PI / 2, "act": 0.0, "observe": -PI / 2, "evaluate": PI}


def ring_point(a: float) -> np.ndarray:
    return C_ + R * np.array([np.cos(a), np.sin(a), 0.0])


class Node(VGroup):
    def __init__(self, name, meaning, color, pos):
        super().__init__()
        self.zone = Zone(NODE_W, NODE_H, color, None, radius=0.24, fill_opacity=0.045)
        lab = VGroup(en(name, 24, color), bn(meaning, 16, MUTED)).arrange(DOWN, buff=0.03)
        self.add(self.zone, lab)
        self.move_to(pos)
        self.accent = color


def leave_angle(a_node: float, direction: int, pad: float = 0.1) -> float:
    """Walk along the ring from a node's centre until clear of its box (+pad)."""
    c = ring_point(a_node)
    hw, hh = NODE_W / 2 + pad, NODE_H / 2 + pad
    a = a_node
    while True:
        a += 0.002 * direction
        p = ring_point(a)
        if abs(p[0] - c[0]) > hw or abs(p[1] - c[1]) > hh:
            return a


def ring_arc(a_from: float, a_to: float, color=MUTED, opacity=0.75):
    """Clockwise segment of the ring between two nodes, with an arrow tip.
    Returns (drawn arc, plain path for the travelling token)."""
    a0 = leave_angle(a_from, -1)          # leave the source node clockwise
    a1 = leave_angle(a_to, +1)            # arrive at the target from its counter-clockwise side
    path = Arc(radius=R, start_angle=a0, angle=a1 - a0, arc_center=C_)
    shown = path.copy().set_stroke(color, 1.9, opacity=opacity)
    shown.add_tip(tip_length=0.13, tip_width=0.13)
    shown.get_tip().set_fill(color, opacity).set_stroke(width=0)
    return shown, path


class S05Loop(VoiceScene):
    SECTION = "s05"

    def construct(self):
        self.show_chapter()
        q = bn("How does an agent actually work?", 46, FG)
        self.narrate("s05_01", FadeIn(q, shift=UP * 0.12), run_time=0.9)

        # ---- the ring
        N = {k: Node(n, m, c, ring_point(ANG[k])) for k, n, m, c in (
            ("decide", "decide", "next step", BLUE), ("act", "act", "use a tool", TEAL),
            ("observe", "observe", "the result", AMBER), ("evaluate", "evaluate", "goal met?", VIOLET))}
        N["goal"] = Node("goal", "instruction", FG, ring_point(PI / 2) + UP * 1.3)
        N["done"] = Node("done", "answer", TEAL, ring_point(PI) + LEFT * 2.3)
        d = N["decide"].zone.shape
        e = N["evaluate"].zone.shape
        A = {
            "da": ring_arc(PI / 2, 0.0),
            "ao": ring_arc(0.0, -PI / 2),
            "oe": ring_arc(-PI / 2, -PI),
            "ed": ring_arc(PI, PI / 2, color=VIOLET, opacity=0.9),
        }
        rep_lab = en("repeat", 20, VIOLET).rotate(PI / 4).move_to(C_ + (R + 0.42) * np.array([-0.7071, 0.7071, 0]))
        g_line = Line(N["goal"].zone.shape.get_bottom() + DOWN * 0.06, d.get_top() + UP * 0.08)
        g_arrow = arrow(g_line.get_start(), g_line.get_end())
        done_line = Line(e.get_left() + LEFT * 0.1, N["done"].zone.shape.get_right() + RIGHT * 0.1)
        done_arrow = arrow(done_line.get_start(), done_line.get_end(), color=TEAL)
        yes_lab = en("yes", 18, TEAL).next_to(done_line, UP, buff=0.08)

        title = en("agent loop", 28, MUTED).move_to(C_)
        with self.say("s05_02") as v:
            self.wait_until(v.word("चक्र") - 0.4)
            self.play(FadeOut(q, shift=UP * 0.1), run_time=0.4)
            ring = [N[k] for k in ("decide", "act", "observe", "evaluate")]
            self.play(LaggedStart(*[FadeIn(n, scale=0.92) for n in ring], lag_ratio=0.2), run_time=1.0)
            self.play(LaggedStart(*[Create(A[k][0]) for k in ("da", "ao", "oe", "ed")], lag_ratio=0.2),
                      FadeIn(rep_lab), run_time=1.2)
            self.wait_until(v.word("Loop") - 0.4)
            self.play(FadeIn(title, scale=0.95), run_time=0.6)

        # loop counter replaces the title
        def counter(n):
            return VGroup(en("loop", 20, DIM), bn("1234"[n - 1], 46, FG)).arrange(DOWN, buff=0.02).move_to(C_)

        cnt = counter(1)
        self.active = None

        def activate(key):
            anims = []
            if self.active is not None:
                anims.append(N[self.active].zone.unlit())
            anims += [N[key].zone.lit(0.16), pulse(N[key], 1.06)]
            self.active = key
            return anims

        tok = Token(TEAL, 0.085)

        def travel(path, rt=0.9):
            return MoveAlongPath(tok, path, run_time=rt, rate_func=smooth)

        with self.say("s05_03") as v:
            self.wait_until(v.word("Goal") - 0.3)
            self.play(FadeIn(N["goal"], shift=DOWN * 0.1), GrowArrow(g_arrow), FadeTransform(title, cnt), run_time=0.8)
            self.play(*activate("goal"), run_time=0.6)

        # right-hand panel
        px = 5.05
        goal_tag = en("goal", 18, MUTED).move_to([3.35, 3.0, 0], aligned_edge=LEFT)
        goal_card = Card(3.3, 0.88, FG, stroke_width=1.3)
        goal_card.add(bn("Will it rain in Delhi\ntomorrow? Tell me.", 22).move_to(goal_card.frame))
        goal_card.move_to([px, 2.38, 0])
        with self.say("s05_04"):
            self.play(FadeIn(goal_tag), FadeIn(goal_card, shift=LEFT * 0.12), run_time=0.7)
            tok.move_to(g_line.get_start())
            self.play(FadeIn(tok, scale=0.5), run_time=0.4)

        thought1 = Bubble("Let me check a\nweather website", size=22, side="left", color=BLUE, pad=0.2).move_to([px, 1.15, 0])
        with self.say("s05_05") as v:
            self.wait_until(v.word("Decide") - 0.3)
            self.play(travel(g_line), *activate("decide"), run_time=0.9)
            self.wait_until(v.word("Model") - 0.2)
            self.play(glow(N["decide"].zone.shape, BLUE), run_time=0.6)

        self.narrate("s05_06", FadeIn(thought1, shift=UP * 0.1), run_time=0.6)

        br = Browser(3.3, 1.35, "weather-a.com").move_to([px, -0.48, 0])
        bar_y = br.body_center[1] - 0.3
        bar_bg = Line([px - 1.3, bar_y, 0], [px + 1.3, bar_y, 0]).set_stroke(FAINT, 4)

        def load_bar(color, frac):
            return Line([px - 1.3, bar_y, 0], [px - 1.3 + 2.6 * frac, bar_y, 0]).set_stroke(color, 4)

        with self.say("s05_07") as v:
            self.wait_until(v.word("Act") - 0.3)
            self.play(travel(A["da"][1]), *activate("act"), run_time=0.9)
            self.wait_until(v.word("Browser") - 0.3)
            self.play(FadeIn(br, shift=UP * 0.1), run_time=0.6)
            bar = load_bar(TEAL, 0.62)
            self.play(Create(bar_bg), run_time=0.2)
            self.play(Create(bar), run_time=1.2, rate_func=linear)

        err = VGroup(I.cross_icon(0.26), bn("Page did not load", 24, RED)).arrange(RIGHT, buff=0.15)
        err.move_to(br.body_center + UP * 0.12)
        with self.say("s05_08") as v:
            self.wait_until(v.word("Observe") - 0.3)
            self.play(travel(A["ao"][1]), *activate("observe"), run_time=0.9)
            self.wait_until(v.word("लोड") - 0.4)
            self.play(bar.animate.set_stroke(RED), FadeIn(err, shift=UP * 0.08), run_time=0.5)

        verdict_no = Pill(bn("✗  goal not reached yet", 22, RED), RED).move_to([px, -1.98, 0])
        with self.say("s05_09") as v:
            self.wait_until(v.word("Evaluate") - 0.3)
            self.play(travel(A["oe"][1]), *activate("evaluate"), run_time=0.9)
            self.wait_until(v.word("नहीं") - 0.3)
            self.play(FadeIn(verdict_no, shift=UP * 0.08), run_time=0.5)

        cnt2 = counter(2)
        with self.say("s05_10"):
            self.play(travel(A["ed"][1], 1.1), *activate("decide"), glow(A["ed"][0], VIOLET, 5, 1.1),
                      FadeTransform(cnt, cnt2), run_time=1.1)

        thought2 = Bubble("Let me try a\ndifferent website", size=22, side="left", color=BLUE, pad=0.2).move_to(thought1)
        with self.say("s05_11"):
            self.play(FadeTransform(thought1, thought2), FadeOut(verdict_no), FadeOut(err), FadeOut(bar),
                      run_time=0.8)

        url2 = br.make_url("weather-b.com")
        ok = bn("Chance of rain: 80%", 23, TEAL).move_to(br.body_center + UP * 0.12)
        with self.say("s05_12") as v:
            self.wait_until(v.word("Browser") - 0.3)
            self.play(travel(A["da"][1]), *activate("act"), Transform(br.url, url2), run_time=0.9)
            bar2 = load_bar(TEAL, 1.0)
            self.play(Create(bar2), run_time=0.8, rate_func=linear)
            self.wait_until(v.word("नतीजा") - 0.4)
            self.play(travel(A["ao"][1]), *activate("observe"), run_time=0.9)
            self.play(FadeIn(ok, shift=UP * 0.08), run_time=0.5)

        verdict_ok = Pill(bn("✓  goal reached", 22, TEAL), TEAL).move_to([px, -1.98, 0])
        with self.say("s05_13") as v:
            self.wait_until(v.word("जाँच") - 0.3)
            self.play(travel(A["oe"][1]), *activate("evaluate"), run_time=0.9)
            self.play(FadeIn(verdict_ok, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.word("जवाब") - 0.5)
            self.play(GrowArrow(done_arrow), FadeIn(yes_lab), FadeIn(N["done"], scale=0.95), run_time=0.7)
            self.play(travel(done_line, 0.7), *activate("done"), run_time=0.7)
            self.play(glow(N["done"].zone.shape, TEAL), pulse(goal_card, 1.04), run_time=0.7)

        # ---- the plan changed along the way
        hist_title = bn("adapted after each result", 22, MUTED).move_to([px, 0.95, 0])
        rows = VGroup(
            VGroup(en("1", 24, DIM, italic=False), mono("weather-a.com", 18, MUTED), I.cross_icon(0.24)).arrange(RIGHT, buff=0.3),
            VGroup(en("2", 24, DIM, italic=False), mono("weather-b.com", 18, FG), I.check_icon(0.26)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([px, -0.25, 0])
        with self.say("s05_14") as v:
            self.play(FadeOut(thought2), FadeOut(br), FadeOut(bar_bg), FadeOut(bar2), FadeOut(ok), FadeOut(verdict_ok),
                      run_time=0.6)
            self.wait_until(v.word("नतीजे") - 0.3)
            self.play(FadeIn(hist_title, shift=UP * 0.08), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rows], lag_ratio=0.4), run_time=1.0)

        with self.say("s05_15") as v:
            self.play(tok.animate.move_to(A["da"][1].get_start()), N["done"].zone.unlit(), run_time=0.5)
            self.active = None
            for k in ("decide", "act", "observe", "evaluate"):
                word = k.capitalize()
                self.wait_until(v.word(word) - 0.15)
                self.play(*activate(k), glow(N[k].zone.shape, N[k].accent, 5), run_time=0.45)
            self.wait_until(v.word("फिर") - 0.3)
            self.play(glow(A["ed"][0], VIOLET, 5, 0.8), N["evaluate"].zone.unlit(), run_time=0.6)
            self.active = None
            for k in ("da", "ao", "oe", "ed"):
                self.play(travel(A[k][1], 0.42), run_time=0.42)
        self.clear_all(0.8)
