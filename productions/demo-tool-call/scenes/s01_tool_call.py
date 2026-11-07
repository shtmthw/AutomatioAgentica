"""01 · Tool calls - the model writes a request, the tool returns a result."""
from agentic_video.prelude import *


class S01ToolCall(VoiceScene):
    SECTION = "s01"

    def construct(self):
        self.show_chapter()
        model = I.chip_labeled(1.7, "model", BLUE).move_to([-4.3, 0.1, 0])
        tool = Card(2.2, 1.7, TEAL, stroke_width=1.8)
        t_ic = I.terminal_icon(0.68, TEAL).move_to(tool.frame.get_center() + UP * 0.14)
        t_nm = en("tool", 26, TEAL).next_to(t_ic, DOWN, buff=0.18)
        gear = I.gear(0.3, TEAL).move_to(tool.frame.get_corner(UR) + LEFT * 0.26 + DOWN * 0.26)
        tool.add(t_ic, t_nm, gear)
        tool.move_to([4.3, 0.1, 0])

        y_req, y_res = 0.55, -0.35
        a_req = arrow([model.get_right()[0] + 0.25, y_req, 0], [tool.get_left()[0] - 0.15, y_req, 0], color=BLUE)
        a_res = arrow([tool.get_left()[0] - 0.15, y_res, 0], [model.get_right()[0] + 0.25, y_res, 0], color=TEAL)
        l_req = bn("request", 22, BLUE).next_to(a_req, UP, buff=0.12)
        l_res = bn("result", 22, TEAL).next_to(a_res, DOWN, buff=0.12)
        title = en("tool call", 44, FG).move_to([0, 2.35, 0])
        req = Pill(mono('terminal: "python app.py"', 16, BLUE), BLUE, pad_y=0.08)
        res = Pill(mono("✓ 3 passed", 16, TEAL), TEAL, pad_y=0.08)

        with self.say("s01_01") as v:
            self.play(FadeIn(model, scale=0.92), FadeIn(tool, shift=LEFT * 0.1), run_time=0.8)
            self.wait_until(v.cue("call") - 0.3)
            self.play(FadeIn(title, shift=DOWN * 0.1), GrowArrow(a_req), FadeIn(l_req), run_time=0.7)

        with self.say("s01_02") as v:
            self.wait_until(v.cue("request") - 0.4)
            req.move_to(a_req.get_start() + RIGHT * req.width / 2)
            self.play(FadeIn(req, scale=0.9), pulse(model, 1.06), run_time=0.4)
            self.play(req.animate.move_to(a_req.get_end() + LEFT * req.width / 2), run_time=0.8)
            self.play(FadeOut(req, scale=0.6), glow(tool.frame, TEAL), run_time=0.4)
            self.wait_until(v.cue("result") - 0.5)
            self.play(GrowArrow(a_res), FadeIn(l_res), run_time=0.4)
            res.move_to(a_res.get_start() + LEFT * res.width / 2)
            self.play(FadeIn(res, scale=0.9), run_time=0.3)
            self.play(res.animate.move_to(a_res.get_end() + RIGHT * res.width / 2), run_time=0.8)
            self.play(FadeOut(res, scale=0.6), glow(model.body, TEAL), run_time=0.4)
        self.wait(0.8)
        self.clear_all(0.8)
