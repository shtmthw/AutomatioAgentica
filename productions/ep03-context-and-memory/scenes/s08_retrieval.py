"""08 · Retrieval: 300 notes would overflow the context, so a few core rules are always loaded and
everything else is fetched on demand with a search_notes tool call (the same tool-calling pattern)."""
from agentic_video.prelude import *
from memory_kit import *

W = 3.08
CW_C = np.array([-4.3, -0.32, 0])
MODEL_C = np.array([0.35, 0.8, 0])
NB_C = np.array([4.7, 1.15, 0])
GRID_C = np.array([4.75, -1.15, 0])


def thin(role, text=None, content=None, h=0.28, size=12):
    return SizedCard(role, text, height=h, width=W, size=size, content=content)


class S08Retrieval(VoiceScene):
    SECTION = "s08"

    def construct(self):
        self.show_chapter()
        hf = HarnessFrame(13.5, 5.2).move_to([0, -0.08, 0])
        hf.head.move_to(hf.frame.get_corner(UR) + LEFT * (hf.head.width / 2 + 0.32) + DOWN * (hf.head.height / 2 + 0.24))
        ctx = LiveContext(CW_C, 3.4, 4.3, label_size=13)
        model = ModelBox(2.3, 1.3).move_to(MODEL_C)
        nb = Notebook(0.85).move_to(NB_C)
        pile = VGroup(*[NoteCard("Note", width=3.0, size=12).shift(UP * 0.07 * k + RIGHT * 0.05 * k) for k in range(6)])
        for k, n in enumerate(pile):
            n.set_z_index(-k)
        pile.move_to([NOTE_X := 4.75, -0.35, 0])
        count = Pill(en("300 notes", 22, MEMORY), MEMORY, pad_x=0.24).move_to([NOTE_X, -1.25, 0])
        weeks = VGroup(*[RoundedRectangle(width=0.32, height=0.34, corner_radius=0.05).set_stroke(MUTED, 1.4)
                         for _ in range(4)]).arrange(RIGHT, buff=0.1)
        weeks_lab = VGroup(weeks, caps("weeks later", 13, MUTED)).arrange(RIGHT, buff=0.16).move_to([NOTE_X, -2.0, 0])

        sysc = ctx.size(thin("system", "You are a coding agent."), 0.05)
        with self.say("s08_01") as v:
            self.play(FadeIn(hf), FadeIn(model, scale=0.95), FadeIn(nb), *ctx.appear(), run_time=0.7)
            self.wait_until(v.cue("pass") - 0.3)
            self.play(LaggedStart(*[FadeIn(w, scale=0.8) for w in weeks], lag_ratio=0.2), FadeIn(weeks_lab[1]),
                      run_time=0.8)
            self.wait_until(v.cue("count") - 0.5)
            self.play(LaggedStart(*[FadeIn(n, shift=DOWN * 0.1) for n in pile], lag_ratio=0.1), run_time=0.7)
            self.play(FadeIn(count, scale=0.9), run_time=0.4)

        lines = ["Tests run with: run tests", "Do not rename public functions", "Login bug: cause found",
                 "Server port is 8080", "Rahul prefers short answers", "Deploy with: run deploy-test",
                 "Ask before deleting files", "… and 293 more"]
        all_notes = NotesBlock(lines, width=W, size=11, min_h=0.0)
        ctx.size(all_notes, 0.65)
        target_h = 0.65 * ctx.capacity - ctx.gap
        if all_notes.height < target_h:
            all_notes = NotesBlock(lines, width=W, size=11, min_h=target_h)
            ctx.size(all_notes, 0.65)
        with self.say("s08_02") as v:
            self.play(*ctx.add(sysc, shift=DOWN * 0.1), run_time=0.4)
            self.wait_until(v.cue("all") - 0.4)
            src = pile.copy()
            self.play(src.animate.move_to(ctx.next_point(all_notes)).scale(0.6).set_opacity(0.4), run_time=0.7)
            self.remove(src)
            self.play(*ctx.add(all_notes, shift=LEFT * 0.2), run_time=0.6)
            self.wait_until(v.cue("pct") - 0.3)
            self.play(glow(ctx.readout, AMBER, 4), pulse(ctx.readout, 1.25), run_time=0.6)

        over = Pill(VGroup(I.warn_icon(0.26, AMBER), en("memory can overflow the context too", 18, FG)).arrange(RIGHT, buff=0.12),
                    AMBER, pad_x=0.22).move_to([MODEL_C[0] + 0.2, -0.85, 0])
        with self.say("s08_03") as v:
            self.wait_until(v.cue("overflow") - 0.3)
            self.play(FadeIn(over, shift=UP * 0.08), glow(ctx.cw.frame, AMBER, 6), run_time=0.6)

        term = VGroup(spaced("RETRIEVAL", 34, FG, tracking=0.3, weight=LIGHT),
                      en("bring back only the relevant notes", 19, MUTED)).arrange(DOWN, buff=0.14)
        term.move_to([MODEL_C[0] + 0.2, -1.35, 0])
        with self.say("s08_04") as v:
            self.wait_until(v.cue("retrieval") - 0.4)
            self.play(*ctx.remove([all_notes], shift=RIGHT * 0.4), FadeOut(over), run_time=0.5)
            self.play(*ctx.relayout(), FadeIn(term[0], shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("relevant") - 0.3)
            self.play(FadeIn(term[1]), run_time=0.4)

        core = NotesBlock(["Run tests before finishing a task", "Do not rename public functions",
                           "Ask before deleting files"], width=W, size=11, title="ALWAYS LOADED")
        ctx.size(core, 0.06)
        demand = caps("loaded on demand", 13, MEMORY).next_to(count, LEFT, buff=0.18)
        with self.say("s08_05") as v:
            self.wait_until(v.cue("always") - 0.4)
            self.play(FadeOut(term), *ctx.add(core, shift=LEFT * 0.2), run_time=0.6)
            pin = pin_icon(0.28, MEMORY).move_to(core.get_corner(UR) + LEFT * 0.12 + DOWN * 0.12)
            self.play(FadeIn(pin, shift=DOWN * 0.1), run_time=0.3)
            self.wait_until(v.cue("else") - 0.3)
            self.play(FadeIn(demand, shift=UP * 0.06), glow(nb.cover, MEMORY, 5), run_time=0.5)
            self.wait_until(v.cue("needed") - 0.3)
            self.play(pulse(pile, 1.05), run_time=0.5)

        with self.say("s08_06") as v:
            self.wait_until(v.cue("deploy") - 0.3)
            self.play(*ctx.add(ctx.size(thin("user", "Deploy the app to the test server."), 0.02)), run_time=0.45)

        req = ToolCallCard("search_notes", 'query = "deploy"', width=3.6, size=17).move_to([MODEL_C[0], -1.0, 0])
        ex = caps("example tool name", 11, MUTED).next_to(req, DOWN, buff=0.08, aligned_edge=RIGHT)
        msg = ctx.size(ToolCallMsg("search_notes", '"deploy"', width=W, size=12, height=0.28), 0.01)
        with self.say("s08_07") as v:
            self.wait_until(v.cue("call") - 0.4)
            self.play(model.think(0.5), FadeIn(req, shift=DOWN * 0.15), FadeOut(demand), run_time=0.6)
            self.play(FadeIn(ex), run_time=0.3)
            self.wait_until(v.cue("query") - 0.4)
            slot = ctx.next_point(msg)
            ctx.cards.append(msg)
            self.play(TransformFromCopy(req, msg.move_to(slot)), *ctx.meter(), run_time=0.6)

        grid = VGroup(*[Square(0.1).set_stroke(MEMORY, 0.8, opacity=0.6).set_fill(MEMORY, 0.12) for _ in range(300)])
        grid.arrange_in_grid(15, 20, buff=0.05).move_to(GRID_C)
        hits = [grid[127], grid[214]]
        hit_lab = caps("2 of 300", 14, MEMORY).next_to(grid, UP, buff=0.12)
        with self.say("s08_08") as v:
            self.wait_until(v.cue("searches") - 0.4)
            self.play(glow(hf.frame, AMBER, 5), pulse(hf.head, 1.1), FadeOut(weeks_lab), run_time=0.5)
            self.play(FadeOut(pile), FadeOut(count), FadeIn(grid, lag_ratio=0.002), run_time=0.8)
            self.wait_until(v.cue("two") - 0.4)
            self.play(*[h.animate.set_fill(MEMORY, 1).set_stroke(FG, 1.2, opacity=1).scale(1.6) for h in hits],
                      grid.animate.set_fill(opacity=0.06), FadeIn(hit_lab), run_time=0.6)
            for h in hits:
                h.set_fill(MEMORY, 1)

        found = SizedCard("tool", content=VGroup(bn("Deploy with: run deploy-test", 11, FG),
                                                 bn("Test server needs the VPN on", 11, FG)).arrange(DOWN, buff=0.05,
                                                                                                    aligned_edge=LEFT),
                          height=0.46, width=W)
        ctx.size(found, 0.04)
        with self.say("s08_09") as v:
            self.wait_until(v.cue("tool") - 0.5)
            flying = VGroup(*[h.copy() for h in hits])
            self.play(flying.animate.move_to(ctx.next_point(found)).scale(1.5), FadeOut(req), FadeOut(ex), run_time=0.7)
            self.remove(flying)
            self.play(*ctx.add(found, shift=LEFT * 0.1), run_time=0.5)
            self.wait_until(v.cue("barely") - 0.3)
            self.play(glow(ctx.cw.fill, TEAL, 5), pulse(ctx.readout, 1.2), run_time=0.6)

        p_req = Pill(VGroup(caps("model", 13, BLUE), en("requests", 21, FG)).arrange(RIGHT, buff=0.12), BLUE, pad_x=0.2)
        p_do = Pill(VGroup(caps("harness", 13, AMBER), en("does", 21, FG)).arrange(RIGHT, buff=0.12), AMBER, pad_x=0.2)
        pat = VGroup(p_req, p_do).arrange(RIGHT, buff=0.55).move_to([MODEL_C[0] + 0.45, -0.72, 0])
        pat_ar = arrow(p_req.get_right() + RIGHT * 0.06, p_do.get_left() + LEFT * 0.06, color=MUTED, tip=0.1)
        same = caps("same tool-calling pattern", 13, MUTED).next_to(pat, UP, buff=0.14)
        with self.say("s08_10") as v:
            self.wait_until(v.cue("same") - 0.3)
            self.play(FadeIn(same), run_time=0.4)
            self.wait_until(v.cue("requests") - 0.3)
            self.play(FadeIn(p_req, shift=UP * 0.08), run_time=0.4)
            self.wait_until(v.cue("does") - 0.3)
            self.play(GrowArrow(pat_ar), FadeIn(p_do, shift=UP * 0.08), run_time=0.45)
            tool_p = Pill(VGroup(I.wrench_icon(0.26, TEAL), en("just another tool", 21, FG)).arrange(RIGHT, buff=0.12),
                          TEAL, pad_x=0.22)
            place_p = Pill(VGroup(Notebook(0.3, label=None, sub=None).icon, en("a place to store text", 21, FG)).arrange(
                RIGHT, buff=0.12), MEMORY, pad_x=0.22)
            mem = VGroup(tool_p, en("+", 24, MUTED), place_p).arrange(RIGHT, buff=0.16)
            if mem.width > 4.4:
                mem.scale_to_fit_width(4.4)
            mem.move_to([MODEL_C[0] + 0.45, -1.5, 0])
            self.wait_until(v.cue("another") - 0.3)
            self.play(FadeIn(tool_p, shift=UP * 0.08), run_time=0.45)
            self.wait_until(v.cue("place") - 0.3)
            self.play(FadeIn(mem[1]), FadeIn(place_p, shift=UP * 0.08), run_time=0.45)

        later = Pill(VGroup(I.spark_icon(0.24, MUTED), en("smarter search: a later lesson", 20, MUTED)).arrange(RIGHT, buff=0.12),
                     DIM, pad_x=0.22).move_to([MODEL_C[0] + 0.45, -2.22, 0])
        with self.say("s08_11") as v:
            self.wait_until(v.cue("smarter") - 0.3)
            self.play(FadeIn(later, shift=UP * 0.08), run_time=0.5)
            self.wait_until(v.cue("later") - 0.3)
            self.play(glow(later.frame, MUTED, 4), run_time=0.5)
        self.clear_all(0.6)
