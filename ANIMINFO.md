# ANIMINFO: how this video was built (and how to rebuild it)

A playbook for producing this project's result again from scratch: a ~10–11 minute
beginner lesson, "What is Agentic AI?", with **Hindi narration** (ElevenLabs),
**English subtitles**, **English on-screen text**, and **100% programmatic animation**.
It covers what worked, what failed, and the path to follow.

---

## 1. Final stack (use exactly this)

| Need | Choice | Notes |
|---|---|---|
| Animation | **Manim Community 0.19+** (Cairo renderer) | Python 3.12 venv via `uv`. Pango handles complex scripts (Bangla/Devanagari) correctly |
| Voice | **ElevenLabs `eleven_v4`**, built-in voice **Adam** (`pNInz6obpgDQGcFmaJgB`), `language_code="hi"` | Endpoint `POST /v1/text-to-speech/{voice}/with-timestamps` returns `audio_base64` + **character alignment** |
| Fallback voice | `edge-tts` (`hi-IN-MadhurNeural`) | Free, has word boundaries; slower and more robotic |
| Music | Synthesised in numpy (pad chords + soft bells + FFT reverb) | No stock assets |
| Subtitles | Own SRT/ASS writer → burned in with ffmpeg `ass=` (libass) | Font Inter 46px; plus a soft-sub MP4 (`mov_text`) |
| Encode | ffmpeg libx264 `-preset slow -crf 17`, AAC 192k, 1080p30 | Scenes concat with `-c copy` first |
| Fonts | Inter (labels/body), JetBrains Mono (code), Noto Sans Devanagari / Bengali (if local script) | Resolve names via `manimpango.list_fonts()` |

Machine used: 12 cores, no GPU needed. Full scene render ≈ 3–4 min with 5 parallel
workers; final assembly ≈ 4–5 min.

---

## 2. Project layout

```
agentic_video/  narration.py (THE script)  pronunciation.py  config.py
                style.py (palette/fonts)    icons.py  components.py
                voice.py (VoiceScene: sync + cue logging)  prelude.py
scenes/         s01_intro.py … s09_outro.py  (one Scene class per chapter)
tools/          tts.py  eleven.py  subtitles.py  music.py  build.py
                preview.py (contact sheets)  say.py  export_script.py
assets/voice/   per-line mp3 + manifest.json (durations + word timings)
build/          intermediates (cues/, scenes/, logs/, preview/)
output/         final MP4s, .srt, script .md
.env            ELEVENLABS_API_KEY=... (gitignored)
```

Commands:
```bash
.venv/bin/python -m tools.build all -j 5        # voice → render → assemble
.venv/bin/python -m tools.build render s05      # one scene
.venv/bin/python -m tools.build assemble        # concat + mix + subs + encode
.venv/bin/python -m tools.preview s05           # 480p render + per-line contact sheet
AGENTIC_TTS_ENGINE=edge .venv/bin/python -m tools.tts   # free draft voice (no credits)
```

---

## 3. The core idea: voice-driven timing

**Voice first, animation follows.** Never time animations by hand.

1. `narration.py`: each line is `("s05_07", "<Hindi spoken>", "<English subtitle>")`.
   Same number of sentences in both (sentence i of the subtitle shows while sentence i is spoken).
2. `tools/tts.py`: one clip per line, cached by a hash of (engine, voice, settings, spoken
   text). The manifest stores `duration`, `speech_start/end` and `words: [[start, dur, text]]`.
   ElevenLabs character alignment → words by splitting on whitespace and dropping
   punctuation-only tokens and `[audio tags]`.
3. `VoiceScene.say(key)` context manager: records `renderer.time` as the line start, lets
   you `wait_until(v.word("Browser"))` to hit a spoken word, then waits out the line
   plus a 0.35 s gap. Writes `build/cues/<scene>.json`.
4. `build.py` places each clip at its exact cue time (scene offsets come from `ffprobe`
   on each rendered scene), then subtitles are generated from the same timings.
   Picture, voice and subtitles **cannot drift**.

Cue words (`v.word("...")`) must exist in the **spoken** line. After any script or
language change, run a static check: parse every `v.word("X")` under its
`self.say("key")` and confirm X (normalised) appears in that line's spoken text.
Also check dynamic cue lists. A missing cue raises `KeyError` at render time.

Keep **display text and cue words separate** (e.g. `labels = [...]` for pills vs
`cue_words = [...]` for timing): once languages differ they never match.

---

## 4. Visual language (matches the reference "CPU Scheduling Explained" style)

- Background `#0b1114`; FG `#e6ecef`; muted `#8b98a1`; dim `#56636c`; faint `#25313a`.
- One accent per concept for the whole video: **blue** model/decide, **teal**
  agent/act/success, **amber** environment/observe, **violet** feedback/evaluate, **red** errors.
- **Zones**: rounded rectangles with a dashed outline (`DashedVMobject`, ~0.085 unit dashes)
  and a 4–5% tinted fill; label inside at the top in light italic Inter.
- **Cards/windows**: thin 1.6 px strokes, panel fill `#0f171c`; terminal/editor windows
  with three dots and a mono title.
- Labels: light italic Inter. Sentences/body: **upright** Inter (italic sentences read worse).
- Layout safe area: content between y = −2.75 and 3.25 (subtitles live below). Chapter tag top-left.
- Keep boxes tight to content (the user asked for smaller boxes); trim empty space.
- Motion: FadeIn with a small shift, short (0.4–0.9 s); a glowing `Token` dot travels along
  paths; `pulse()` (scale there-and-back) and `glow()` (fading thick outline) for emphasis.

**Agent loop diagram (got wrong first, then fixed):** put four nodes on **one true
circle** and draw each arrow as an `Arc(radius=R, arc_center=C)` segment, clipped
where it leaves/enters each node box (walk the angle until the point exits the box +
padding). Goal enters straight down from above; "done" exits straight left. Never
let two arrows land on the same node edge, and keep the centre label small enough
to fit inside the ring.

---

## 5. Manim pitfalls (each one cost a re-render)

1. **Never assign `self.color = ...` in a VGroup subclass.** It is a property and
   recolours every child (cards became solid blue). Use `self.accent`.
2. Reference geometry (e.g. a zone's `shape`) must be **added to the group** (invisible) or it won't move with it.
3. **Mono text drops leading spaces.** Compute indentation as
   `n_spaces × char_width` and shift the text manually.
4. `Indicate(color=...)` recolours fills, and its default colour is yellow. Use a custom
   scale pulse plus an outline glow instead.
5. **Dimming:** `set_opacity()` on outline-only shapes reveals their hidden default fill
   (Circle = red). Use `mobject.fade(1 - opacity)` (multiplicative); for zones dim only outline + label.
6. **Glyph `Transform` breaks Bangla/Devanagari shaping.** Use `FadeTransform` for any
   non-Latin text swap.
7. Don't `FadeTransform` a submobject of a group you'll move later. Keep such texts top-level.
8. Objects positioned relative to a card **before** `arrange()` don't follow it. Position after layout.
9. Properties computed at init (e.g. a window's body centre) go stale after `move_to`. Make them `@property`.
10. **Font family names differ per system** (`JetBrains Mono` was installed as
    `JetBrainsMono Nerd Font Mono`; Manim silently fell back). Pick from candidates
    via `manimpango.list_fonts()` and watch logs for `Font ... not in`.
11. Pango `letter_spacing` markup explodes under Manim scaling. Build tracked titles glyph by glyph on a shared baseline.
12. A full-screen veil (rectangle, BG colour, 0.86 opacity) is the safe way to put an overlay card over a busy scene. Don't re-set opacities afterwards.
13. Width checks: long labels can exceed the frame. Anchor right-side lists with
    `shift(RIGHT * (6.7 - group.get_right()[0]))` and `arrange(..., aligned_edge=RIGHT)`.

---

## 6. Voice: what worked, what didn't

- **Worked:** ElevenLabs `eleven_v4` + built-in **Adam**, Hindi text with English tech
  terms in Latin script (Agent, Tool, Model…). Natural Hinglish delivery. Send
  `previous_text`/`next_text` (neighbouring lines of the same section) for continuity.
  Settings: stability 0.5, similarity 0.75 (v4 has no speed/style controls).
- **ElevenLabs free plan facts:** 10k credits/month (≈1 credit/char; full script ≈ 6.75k chars).
  **Free accounts cannot use Voice Library voices via the API** (HTTP 402), only built-in
  voices. Free plan has **no commercial licence**. Keys can be **permission-scoped**: a
  key with only Text-to-Speech fails `user_read` / `voices_read` / `models_read` (401).
  Make the code tolerate that.
- **Pronunciation dictionary** (`pronunciation.py`): word → spoken spelling, applied only
  to TTS (subtitles keep the original). E.g. `"AI": "एआई"` (user wanted "E-AYE";
  Bangla equivalent `এআই`). Prefer spelling fixes in the script itself for one-offs
  (the user corrected `এল` → `এলো`). `tools/say.py` makes quick audition MP3s.
- **Rejected / failed paths (don't repeat):**
  - edge-tts Bangla `bn-BD-PradeepNeural`: user found it "bad"/robotic.
  - Splicing an English voice (Prabhat) into Bangla sentences, even with pitch/EQ/
    loudness matching, carrier sentences and Rubber Band, was technically good but the user rejected it.
  - Azure Speech: user ruled it out (needs a paid key).
- Hindi narration runs longer than Bangla (≈11.5 chars/s with Adam); the video ended
  at 10:44 vs a 7–9 min target. If length matters, write a tighter script **before**
  spending credits, or time-stretch ~1.1–1.15× in post (formant-preserving).
- Always do a **free draft** (`AGENTIC_TTS_ENGINE=edge`) to validate cues and layout
  before spending ElevenLabs credits.

---

## 7. Subtitles

- English subtitles are aligned **sentence by sentence** to the Hindi audio:
  split the spoken text at `। ? ! .`, find each sentence's span from the word timings,
  and show the matching English sentence for that span.
- Long sentences are split at commas. Choose the grouping with the lowest cost
  (penalise >56 chars, hard cap 68, penalise <18-char fragments), and share time
  proportionally to length. Never split between two English words.
- Finalise: lead 0.08 s, tail 0.35 s, minimum 0.9 s on screen, never overlap the next cue.
- ASS style: Inter 46 px, light outline (2.6) in BG colour, bottom margin 44.
  Validate: no overlaps, max length, minimum duration.

---

## 8. Audio mix

- Measure narration loudness **in stereo**. A mono file measures 3 dB quieter than the
  same voice duplicated to L/R, which once made the mix 2.5 dB off target.
- Narration −16 LUFS, then a **look-ahead peak limiter** at −1.5 dBFS (1 ms blocks,
  5 ms look-ahead, 80 ms release). Don't scale the whole mix down for a few peaks.
- Music normalised to −33 LUFS, ducked 6 dB under speech with a smoothed (Hann 0.6 s)
  envelope built from known speech intervals (deterministic, no sidechain compressor).
- Final check: `ebur128` ⇒ I ≈ −16 LUFS, true peak ≤ −1 dB.
- Soft-sub MP4: **don't use `-shortest`** (the subtitle stream ends early and truncates the
  video). Use `-t <total>`.

---

## 9. Verification loop (do this every time)

1. Render all scenes (1080p30, 5 workers). Grep logs for `Traceback|KeyError|WARNING`.
2. Compare each scene's video duration with its cue log duration (must match).
3. `tools.preview` contact sheets: one frame per narration line at 92% of the line.
   **Look at every sheet** for overflow, overlaps, text off-frame or mid-animation glitches.
   Then grab full-res frames of the densest spots.
4. Assemble; `ffprobe` both MP4s (same duration, 1920×1080, 30 fps, AAC stereo,
   language tags), loudness check, SRT check, and one frame with burned subtitles.
5. Patch scene text with scripts that **assert each replacement matched**. Silent
   non-matches caused bugs (literal Unicode vs `\u` escapes).

---

## 10. Content structure that worked

9 chapters: Intro (AI that explains vs agent that acts on the same error) → AI model
(data → LLM, input/output, context, GPT/Claude/Gemini, "only produces text") →
Agent definition + 5 parts (goal, model, tools, environment, feedback) → Chatbot vs
agent (line vs loop; same chat UI, different abilities) → **Agent loop** with a weather
example that fails once, adapts and succeeds → Tools (filesystem, terminal, browser,
API, database; model decides, tool executes, "brain vs hands") → Real bug fix
(ZeroDivisionError in `average([])`, loop counter widget, report card, all five parts
tagged) → Reality check (risks, permissions, safeguards, human approval gate,
"more power = more responsibility") → Conclusion (recap cards, roadmap of next lessons,
website + app mockups building themselves, tracked "AGENTIC AI / THE BEGINNING" title card).

Reuse the same running example (the divide-by-zero crash) in the intro and the
bug-fix chapter. It gives the lesson a satisfying arc.
