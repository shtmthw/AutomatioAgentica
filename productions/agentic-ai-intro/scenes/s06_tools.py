"""06 · Tools - how an agent touches the outside world."""
from agentic_video.prelude import *

ROW_Y = [2.3, 1.18, 0.06, -1.06, -2.18]
ICON_X, NAME_X, DEMO_X = -2.85, -2.3, 4.55


class S06Tools(VoiceScene):
    SECTION = "s06"

    def construct(self):
        self.show_chapter()
        model = I.chip_labeled(1.9, "model", BLUE).move_to([0, 0.55, 0])
        q = bn("Why do agents need tools?", 38, FG).move_to([0, -1.35, 0])
        with self.say("s06_01") as v:
            self.play(FadeIn(model, scale=0.92), run_time=0.7)
            self.wait_until(v.cue("why") - 0.5)
            self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)

        # ---- a model alone only emits text
        out_bars = VGroup(*[Line(ORIGIN, RIGHT * w).set_stroke(MUTED, 3, opacity=0.8) for w in (1.6, 1.2, 1.4)])
        out_bars.arrange(DOWN, aligned_edge=LEFT, buff=0.16).next_to(model, RIGHT, buff=0.6)
        only_text = bn("only text", 22, MUTED).next_to(out_bars, DOWN, buff=0.2)

        specs = [
            ("filesystem", "read, create and change files", I.file_icon),
            ("terminal", "run commands and programs", I.terminal_icon),
            ("browser", "fetch information from websites", I.globe_icon),
            ("API", "talk to other services", I.api_icon),
            ("database", "search and update structured data", I.database_icon),
        ]
        rows = []
        for (name, desc, fn), y in zip(specs, ROW_Y):
            ic = fn(0.5, MUTED).move_to([ICON_X, y, 0])
            nm = en(name, 30, FG).move_to([NAME_X, y + 0.15, 0], aligned_edge=LEFT)
            ds = bn(desc, 19, MUTED).move_to([NAME_X, y - 0.2, 0], aligned_edge=LEFT)
            rows.append(VGroup(ic, nm, ds))
        hub = np.array([-5.35 + model.width * 0.66 / 2 + 0.02, 0.15, 0])
        wires = [Line(hub, r[0].get_left() + LEFT * 0.12).set_stroke(DIM, 1.4) for r in rows]

        with self.say("s06_02") as v:
            self.wait_until(v.cue("text") - 0.5)
            self.play(FadeOut(q), LaggedStart(*[Create(b) for b in out_bars], lag_ratio=0.25), run_time=0.9)
            self.play(FadeIn(only_text), run_time=0.4)
            self.wait_until(v.cue("outside") - 0.3)
            self.play(FadeOut(out_bars), FadeOut(only_text),
                      model.animate.scale(0.66).move_to([-5.35, 0.15, 0]), run_time=0.9)
            self.play(LaggedStart(*[Create(w) for w in wires], lag_ratio=0.1),
                      LaggedStart(*[FadeIn(r[0], shift=RIGHT * 0.1) for r in rows], lag_ratio=0.1), run_time=1.0)

        def light(i):
            r = rows[i]
            return [r[0].animate.set_stroke(TEAL), FadeIn(r[1], shift=RIGHT * 0.1), FadeIn(r[2], shift=RIGHT * 0.1),
                    wires[i].animate.set_stroke(TEAL, 1.8)]

        # ---- 1. filesystem
        y = ROW_Y[0]
        f1, f2, f3 = (I.file_icon(0.5, MUTED).move_to([DEMO_X - 1.2 + i * 1.2, y + 0.1, 0]) for i in range(3))
        tags = [en(t, 18, c).next_to(f, DOWN, buff=0.07) for t, c, f in
                (("read", TEAL, f1), ("modify", AMBER, f2), ("create", TEAL, f3))]
        with self.say("s06_03") as v:
            self.play(*light(0), FadeIn(f1), FadeIn(f2), run_time=0.7)
            self.wait_until(v.cue("read") - 0.2)
            self.play(glow(f1[0], TEAL), f1.animate.set_stroke(TEAL), FadeIn(tags[0]), run_time=0.6)
            self.wait_until(v.cue("create") - 0.2)
            self.play(FadeIn(f3, scale=0.6), f3.animate.set_stroke(TEAL), FadeIn(tags[2]), run_time=0.6)
            self.wait_until(v.cue("change") - 0.2)
            self.play(f2[2].animate.set_stroke(AMBER, opacity=1), f2[0].animate.set_stroke(AMBER), FadeIn(tags[1]),
                      run_time=0.6)

        # ---- 2. terminal
        y = ROW_Y[1]
        term = Terminal(3.4, 0.94, "terminal", font_size=16, line_gap=1.4, bar=0.24).move_to([DEMO_X, y, 0])
        with self.say("s06_04") as v:
            self.play(*light(1), FadeIn(term), run_time=0.7)
            t1 = term.next_line("$ python app.py")
            self.play(AddTextLetterByLetter(t1, run_time=0.8))
            t2 = term.next_line("✓ done", TEAL)
            self.play(FadeIn(t2, shift=RIGHT * 0.08), run_time=0.4)
        self.attach(term, t1, t2)

        # ---- 3. browser
        y = ROW_Y[2]
        br = Browser(3.4, 0.9, "news.example", bar=0.26).move_to([DEMO_X, y, 0])
        content = VGroup(*[Line(ORIGIN, RIGHT * w).set_stroke(MUTED, 3, opacity=0.7) for w in (2.4, 1.8)])
        content.arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to(br.body_center + LEFT * 0.3)
        with self.say("s06_05") as v:
            self.play(*light(2), FadeIn(br), run_time=0.7)
            self.wait_until(v.cue("info") - 0.4)
            self.play(LaggedStart(*[Create(c) for c in content], lag_ratio=0.3), run_time=0.8)

        # ---- 4. API
        y = ROW_Y[3]
        me = Pill(en("agent", 18, TEAL), TEAL).move_to([DEMO_X - 1.45, y, 0])
        svc = Pill(en("weather API", 18, FG), MUTED).move_to([DEMO_X + 1.3, y, 0])
        link = Line(me.get_right(), svc.get_left()).set_stroke(DIM, 1.4)
        req = mono("{ city: Delhi }", 14, BLUE).move_to(link.get_center() + UP * 0.33)
        res = mono("{ rain: 80% }", 14, TEAL).move_to(link.get_center() + DOWN * 0.33)
        pkt = Dot(radius=0.06, color=BLUE).move_to(link.get_start())
        with self.say("s06_06") as v:
            self.play(*light(3), FadeIn(me), FadeIn(svc), Create(link), run_time=0.7)
            self.wait_until(v.cue("talk") - 0.4)
            self.play(FadeIn(req), FadeIn(pkt), run_time=0.3)
            self.play(pkt.animate.move_to(link.get_end()), run_time=0.7)
            self.play(pkt.animate.set_color(TEAL), FadeIn(res), run_time=0.3)
            self.play(pkt.animate.move_to(link.get_start()), run_time=0.7)
            self.play(FadeOut(pkt), run_time=0.2)

        # ---- 5. database
        y = ROW_Y[4]
        cells = VGroup()
        for r in range(3):
            for c in range(4):
                cell = Rectangle(width=0.72, height=0.24).set_stroke(FAINT, 1.2)
                cell.set_fill(FAINT if r == 0 else PANEL, 1)
                cell.move_to([DEMO_X - 1.08 + c * 0.72, y + 0.24 - r * 0.24, 0])
                cells.add(cell)
        row_hl = VGroup(*cells[4:8]).copy().set_fill(TEAL, 0.25).set_stroke(TEAL, 1.2)
        with self.say("s06_07") as v:
            self.play(*light(4), FadeIn(cells), run_time=0.7)
            self.wait_until(v.cue("search") - 0.3)
            self.play(FadeIn(row_hl), run_time=0.4)
            self.wait_until(v.cue("update") - 0.3)
            self.play(cells[10].animate.set_fill(AMBER, 0.45), run_time=0.4)

        # ---- the model decides, the tool does the work
        tool = Card(2.2, 1.7, TEAL, stroke_width=1.8)
        t_ic = I.terminal_icon(0.68, TEAL).move_to(tool.frame.get_center() + UP * 0.14)
        t_nm = en("tool", 26, TEAL).next_to(t_ic, DOWN, buff=0.18)
        gear = I.gear(0.3, TEAL).move_to(tool.frame.get_corner(UR) + LEFT * 0.26 + DOWN * 0.26)
        tool.add(t_ic, t_nm, gear)
        tool.move_to([4.4, 0.5, 0])
        with self.say("s06_08"):
            self.play(*[FadeOut(m) for m in self.mobjects if m not in (model, self.chapter)], run_time=0.7)
            self.play(model.animate.scale(1.25).move_to([-4.4, 0.5, 0]), FadeIn(tool, shift=LEFT * 0.1), run_time=0.9)

        y_req, y_res = 0.95, 0.05
        a_req = arrow([model.get_right()[0] + 0.25, y_req, 0], [tool.get_left()[0] - 0.15, y_req, 0], color=BLUE)
        a_res = arrow([tool.get_left()[0] - 0.15, y_res, 0], [model.get_right()[0] + 0.25, y_res, 0], color=TEAL)
        l_req = bn("request", 22, BLUE).next_to(a_req, UP, buff=0.12)
        l_res = bn("result", 22, TEAL).next_to(a_res, DOWN, buff=0.12)
        decides = bn("decides", 28, BLUE).next_to(model, DOWN, buff=0.4)
        does = bn("does the real work", 28, TEAL).next_to(tool, DOWN, buff=0.4)
        req_pkt = Pill(mono("terminal: python app.py", 16, BLUE), BLUE, pad_y=0.08)
        res_pkt = Pill(mono("✓ 3 passed", 16, TEAL), TEAL, pad_y=0.08)

        with self.say("s06_09") as v:
            self.play(GrowArrow(a_req), FadeIn(l_req), run_time=0.6)
            self.wait_until(v.cue("tool") - 0.3)
            self.play(pulse(model, 1.06), glow(model.body, BLUE), FadeIn(decides, shift=UP * 0.08), run_time=0.7)
            self.wait_until(v.cue("request") - 0.5)
            req_pkt.move_to(a_req.get_start() + RIGHT * req_pkt.width / 2 + DOWN * 0.0)
            self.play(FadeIn(req_pkt, scale=0.9), run_time=0.3)
            self.play(req_pkt.animate.move_to(a_req.get_end() + LEFT * req_pkt.width / 2), run_time=1.0)
            self.play(FadeOut(req_pkt, scale=0.6), run_time=0.3)

        with self.say("s06_10") as v:
            gear.add_updater(lambda m, dt: m.rotate(-dt * 2.4))
            self.play(glow(tool.frame, TEAL), FadeIn(does, shift=UP * 0.08), run_time=0.8)
            self.wait_until(v.cue("result") - 0.4)
            gear.clear_updaters()
            self.play(GrowArrow(a_res), FadeIn(l_res), run_time=0.5)
            res_pkt.move_to(a_res.get_start() + LEFT * res_pkt.width / 2)
            self.play(FadeIn(res_pkt, scale=0.9), run_time=0.3)
            self.play(res_pkt.animate.move_to(a_res.get_end() + RIGHT * res_pkt.width / 2), run_time=1.0)
            self.play(FadeOut(res_pkt, scale=0.6), glow(model.body, TEAL), run_time=0.4)

        head = bn("the brain", 50, BLUE).move_to(decides)
        hand = bn("the hands", 50, TEAL).move_to(does)
        with self.say("s06_11") as v:
            self.wait_until(v.cue("brain") - 0.3)
            self.play(FadeTransform(decides, head), run_time=0.6)
            self.wait_until(v.cue("hands") - 0.3)
            self.play(FadeTransform(does, hand), run_time=0.6)
        self.wait(1.0)   # let the finished "brain / hands" picture sit for a moment
        self.clear_all(0.8)
