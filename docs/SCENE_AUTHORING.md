# Writing scenes for AutomatioAgentica

How to turn a section of the production plan into a Manim scene that renders
correctly in **every language version** and matches the house style of the reference
production (`productions/agentic-ai-intro/scenes/` - read two or three of them first).

## 1. How a scene is used

- One `VoiceScene` subclass per section of `narration.json`, in the production's
  `scenes/` folder, with `SECTION = "<section key>"`.
- The pipeline renders each scene **once per language** (Hindi, English, ...). The
  scene code is the same; only the narration timings differ. Never branch on language.
- Voice first, animation follows: line start times are decided by the narration,
  animations are placed inside each line with cue markers. Never hard-code a
  timeline in seconds.
- Every line of the section must be said exactly once, in order. The render fails
  otherwise (`must say every line of sNN once, in order`).

```python
from agentic_video.prelude import *          # manim + style + components + icons (I) + VoiceScene


class S03Agent(VoiceScene):
    SECTION = "s03"

    def construct(self):
        self.show_chapter()                                  # chapter tag, top-left
        title = en("AI Agent", 88, TEAL)
        self.narrate("s03_01", FadeIn(title, shift=UP * 0.12), run_time=0.9)

        zone = Zone(3.2, 2.4, TEAL, "system", label_size=24).move_to([-3.6, 0.75, 0])
        chip = I.chip_labeled(1.3, "model", BLUE).move_to(zone.shape.get_center() + DOWN * 0.2)
        with self.say("s03_02") as v:
            self.play(title.animate.scale(0.45).move_to([0, 2.75, 0]), run_time=0.8)
            self.wait_until(v.cue("system") - 0.3)           # {system} marker in every language
            self.play(FadeIn(zone), run_time=0.6)
            self.wait_until(v.cue("model") - 0.3)
            self.play(FadeIn(chip, scale=0.9), run_time=0.6)
        self.clear_all(0.8)                                  # fade everything out at the end
```

## 2. Timing API (`agentic_video/voice.py`)

| call | meaning |
|---|---|
| `with self.say(key) as v:` | start line `key` now; on exit wait until it is spoken (+0.35 s gap) |
| `self.narrate(key, *anims, run_time=)` | play animations at the line start, then wait it out |
| `v.cue("name")` | absolute time of the word after marker `{name}` in this line |
| `v.cue("name", end=True)` | ... the end of that word |
| `v.at(0.5)` | a fraction of the spoken line |
| `v.duration`, `v.end`, `v.remaining` | spoken length, end time, time left |
| `self.wait_until(t)` | wait until absolute time `t` (no-op if already past) |
| `self.show_chapter()` | fade in the chapter tag of this section |
| `self.attach(parent, *children)` | after animating children in, make them move/fade with `parent` |
| `self.clear_all(run_time)` | fade out everything (call at the end of the scene) |

`v.word("Browser")` still exists but only works for a word spoken in **every**
language; prefer markers.

If animations inside a line take longer than the line, the next line simply starts
later (a short pause). Keep per-line animation time below the shorter language's
line length when possible (the task file lists estimated durations per language).

## 3. Cue markers

Markers live in `narration.json`, in **every language** of the line, directly before
the word that should trigger the animation:

```json
{"key": "s05_07",
 "en": "Step three: {act}act. The agent uses a tool to do that work. Here, it {browser}opens the website with a browser.",
 "hi": "तीसरा कदम, {act}Act, यानी काम। Agent एक Tool से वह काम करता है। यहाँ उसने {browser}Browser से Website खोली।"}
```

- Names: lowercase `[a-z][a-z0-9_]*`, unique within a line, the same set in every language.
- Put the marker before the word carrying the same meaning in each language. If word
  order differs (Hindi is SOV), choose anchors so the cue order is the same; when it
  cannot be, a cue that is already in the past plays immediately (no error, but check it).
- Markers are removed before speech and subtitles; they cost nothing.
- Lists of cues are fine: `for i, name in enumerate(("questions", "explanations", "answers")):`
- Typical lead: `self.wait_until(v.cue("x") - 0.3)` so the element is there as the word lands.

## 4. Visual language (`agentic_video/style.py`)

Dark, quiet canvas; thin outlines; dotted rounded zones; light italic Latin labels.

| token | value | use |
|---|---|---|
| `BG` `PANEL` `PANEL_2` | `#0b1114` `#0f171c` `#121c22` | background, card/window fill |
| `FG` `MUTED` `DIM` `FAINT` | `#e6ecef` `#8b98a1` `#56636c` `#25313a` | text, secondary, tertiary, hairlines |
| `BLUE` | `#6cb4ee` | AI model / chatbot / "decide" |
| `TEAL` (`GREEN`) | `#6fd6b0` | agent / action / success |
| `AMBER` | `#e3a857` | environment / observation / caution |
| `VIOLET` | `#b49cf0` | feedback / evaluation |
| `RED` | `#ef7a85` | errors |

One accent per concept for the whole video. Text helpers:

- `en(s, size, color)` light italic Inter - labels. `en(s, italic=False)` upright.
- `bn(s, size, color)` upright body text / sentences (Inter, or Noto Sans Devanagari if the text has Hindi).
- `txt(s, ...)` picks automatically. `mono(s, size, color)` JetBrains Mono for code/URLs/files.
- `spaced("AGENTIC AI", 84, FG, tracking=0.42)` letter-spaced title cards.
- Type scale: `H1 64`, `H2 44`, `BODY 32`, `SMALL 24`, `TINY 19`. Strokes `STROKE 1.8`, `ZONE_STROKE 1.6`.

**On-screen text is English** in every scene (both versions share the visuals).

Layout: frame is 14.2 x 8 units, centre origin. Keep content between
`y = SAFE_BOTTOM (-2.75)` and `SAFE_TOP (3.25)`; the chapter tag sits top-left; the
band below -2.75 is where players draw the subtitles. Keep boxes tight to content.

Motion: `FadeIn(m, shift=UP * 0.1)` / `scale=0.9`, 0.4-0.9 s; a glowing `Token` travels
along paths (`MoveAlongPath`); emphasis with `pulse(m)` and `glow(m, color)`; dim
context with `dim(m, 0.2)`. Smooth, calm, no flashy effects.

### Engagement (the user's standing guidelines, see AGENTS.md)

- **Dense or repetitive stretches get more visuals.** Lists, repeated ideas and
  information-heavy lines get keyword text pop-ups (`Pill`, `en(...)`) on their cue
  words, small diagrams, icons, highlights or a travelling `Token`. Aim for something new
  on screen every ~5–8 s, and at least two cue markers in any line longer than ~10 s.
  Dim or fade earlier pop-ups so the frame stays clean.
- **Pop-ups are keywords (2–4 words), never the spoken sentence.** Putting the narration
  on screen is a burned-in caption, and subtitles exist only as separate files.
- **Coding and complex parts:** recreate them step by step with `Terminal`, `CodeEditor`
  and `Browser` (reference: `s07_bugfix.py`). The pipeline cannot insert real screen
  recordings yet. If a section truly needs one, tell the user instead of faking it.
- **Finish with a recap of all topics** (reference: recap cards in `s09_outro.py`). If the
  script has no recap lines, show the topics visually during the closing lines. Don't add
  narration; ask the user to extend the script.
- **No timestamps on screen:** both versions share the scenes but have different timings.
  Timestamps go into the chapter and topic lists instead.

## 5. Components (`agentic_video/components.py`)

| component | signature (main args) | notes |
|---|---|---|
| `Zone` | `(width, height, color, label=None, label_size=30, radius=None, fill_opacity=0.045)` | dotted rounded region; `.shape` (geometry), `.fill`, `.outline`, `.label`; `zone.lit()` / `zone.unlit()` animations |
| `Card` | `(width, height, color, title=None, icon=None, subtitle=None, fill=PANEL, stroke_width)` | `.frame` |
| `Pill` | `(text_or_mobject, color, size=24, pad_x, pad_y, icon=None)` | rounded tag; `.frame`, `.label` |
| `Bubble` | `(text, color, size=26, side="left"/"right", max_w=None)` | chat bubble with tail |
| `Window` | `(width, height, title, color=FAINT)` | app window with 3 dots; `.body_top_left` |
| `Terminal` | `(width, height, title="terminal", font_size=18)` | `t.next_line("$ cmd", color)` returns a positioned line (add/animate it yourself) |
| `Browser` | `(width, height, url)` | `.body_center`, `.make_url("...")` for URL swaps |
| `CodeEditor` | `(width, height, title, font_size=19)` | `ed.make_line(i, code)` -> (number, text); `ed.row_highlight(i, RED)` |
| `AgentBadge` | `(text="agent")` | teal pill with spark icon |
| `Token` | `(color=TEAL, r=0.09)` | glowing dot for paths |
| `arrow(start, end, color, opacity, width, tip)` | | straight arrow; `labeled_arrow(...)` with a rotated label; `curved_arrow(...)` |
| `labeled_icon(icon, label, sub)` | | icon + label (+ small caption) |
| `dim(m, opacity)`, `pulse(m, scale)`, `glow(m, color, width)` | | animations that never recolour fills |

Icons (`I.<name>(height, color)`), all line-drawn: `gear chip chip_labeled file_icon
folder_icon terminal_icon globe_icon database_icon api_icon user_icon target_icon
spark_icon check_icon cross_icon warn_icon lock_icon loop_icon trash_icon fork_icon
wrench_icon`. No image files.

## 6. Manim pitfalls (each one cost a re-render before)

1. Never assign `self.color = ...` in a VGroup subclass (it recolours every child). Use `self.accent`.
2. Reference geometry (e.g. a zone's `shape`) must be in the group (invisible) to move with it.
3. Mono text drops leading spaces: use `mono_line()` / `Terminal.next_line()` / `CodeEditor.make_line()`.
4. `Indicate(color=...)` recolours fills and defaults to yellow: prefer `pulse()` + `glow()`.
5. Dimming outline-only shapes with `set_opacity()` reveals their hidden fill: use `dim()` / `fade()`.
6. Glyph `Transform` breaks Devanagari shaping: use `FadeTransform` for non-Latin text swaps.
7. Don't `FadeTransform` a submobject of a group you will move later; keep such texts top-level.
8. Position things relative to a card **after** `arrange()`.
9. Values computed at init go stale after `move_to`; make them `@property`.
10. Fonts are picked from installed candidates (`style._pick_font`); watch logs for `Font ... not in`.
11. Don't use Pango `letter_spacing` markup; use `spaced()`.
12. Full-screen veil (rectangle, BG colour, 0.86 opacity) is the safe way to overlay a card.
13. Long labels can exceed the frame: anchor right-hand lists with `shift(RIGHT * (6.7 - g.get_right()[0]))`.
14. Agent loop diagrams: nodes on one true circle, arrows as `Arc` segments clipped at the node boxes
    (`productions/agentic-ai-intro/scenes/s05_loop.py`).

## 7. Checklist

- [ ] `python -m automatio check scenes <slug>`: no errors (every line said, every `v.cue` has its marker in every language).
- [ ] `python -m automatio preview <slug> <section> --lang all` and **look at the contact sheets** (one frame per line at 92 %).
- [ ] No layout warnings (outside the frame / below the safe line) in the preview output.
- [ ] Nothing in the narration was shortened to fit an animation.
- [ ] Dense or repetitive lines have extra visuals or keyword pop-ups; nothing on screen is a caption of the narration.
- [ ] The video ends with a recap of all topics.
