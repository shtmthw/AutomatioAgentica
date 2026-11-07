# ANIMINFO: how this video was built (and how to rebuild it)

A playbook for producing this project's result again from scratch: a ~10–11 minute
beginner lesson, "What is Agentic AI?", with **Hindi narration** (ElevenLabs),
**English subtitles**, **English on-screen text**, and **100% programmatic animation**.
It covers what worked, what failed, and the path to follow.

> **2.0:** this now runs as a harness-driven pipeline (`python -m automatio`, see
> [AGENTS.md](AGENTS.md)): two complete videos per production (Hindi + English, each timed
> to its own narration), English subtitles as separate SRT + VTT files, never burned in.

---

## 1. Final stack (use exactly this)

| Need | Choice | Notes |
|---|---|---|
| Animation | **Manim Community 0.19+** (Cairo renderer) | Python 3.12 venv via `uv`. Pango handles complex scripts (Bangla/Devanagari) correctly |
| Voice | **ElevenLabs `eleven_v4`**, built-in voice **Adam** (`pNInz6obpgDQGcFmaJgB`), `language_code="hi"` | Endpoint `POST /v1/text-to-speech/{voice}/with-timestamps` returns `audio_base64` + **character alignment** |
| Fallback voice | `edge-tts` (`hi-IN-MadhurNeural`) | Free, has word boundaries; slower and more robotic |
| Music | Synthesised in numpy (pad chords + soft bells + FFT reverb) | No stock assets |
| Subtitles | Own SRT + WebVTT writer, **separate files only** | 1.x burned them in with libass; 2.0 never does (no subtitle filter, no subtitle stream) |
| Encode | ffmpeg libx264 `-preset slow -crf 17`, AAC 192k, 1080p30 | Scenes concat with `-c copy` first |
| Fonts | Inter (labels/body), JetBrains Mono (code), Noto Sans Devanagari / Bengali (if local script) | Resolve names via `manimpango.list_fonts()` |

12 cores, no GPU: 1080p render of both versions ≈ 8 min (5 workers), assembly ≈ 4 min each.

---

## 2. Project layout

```
automatio/      the pipeline (stages, state, providers, render, audio, subtitles, verify, deliver, CLI)
agentic_video/  style.py (palette/fonts)  icons.py  components.py  prelude.py
                voice.py (VoiceScene: sync + cue logging + layout lint)  runtime.py
productions/agentic-ai-intro/
                production.toml  inputs/ (script, plan, notes)  narration.json (THE script, en + hi)
                scenes/ s01_intro.py … s09_outro.py, thumbnail.py
voices.toml     the house voices (exact provider IDs + settings + pronunciation)
cache/          voice clips, scene renders, music (content-addressed)
build/<slug>/   state.json, tasks/, logs/, drafts, intermediates
output/<slug>/  hindi/ english/ manifest.json report.md
.env            ELEVENLABS_API_KEY=... (gitignored)
```

Commands:
```bash
.venv/bin/python -m automatio run agentic-ai-intro              # everything, resumable
.venv/bin/python -m automatio preview agentic-ai-intro s05 --lang all   # 480p render + contact sheets
.venv/bin/python -m automatio status agentic-ai-intro
.venv/bin/python -m automatio say "आपने एक AI Agent से कहा" --voice hindi-adam
```

---

## 3. The core idea: voice-driven timing

**Voice first, animation follows.** Never time animations by hand.

1. `narration.json`: each line has every language, e.g. `{"key": "s05_07", "en": "...",
   "hi": "..."}`. Same number of sentences per language (subtitle sentence i shows while
   sentence i is spoken).
2. Voice stage: one clip per line and language, cached by hash(provider settings, spoken
   text). The manifest stores `duration`, `speech_start/end`, `words: [[start, dur, text]]`
   and every **cue marker** time. ElevenLabs character alignment → words (whitespace
   split; punctuation-only tokens and `[audio tags]` dropped).
3. `VoiceScene.say(key)` context manager: records `renderer.time` as the line start, lets
   you `wait_until(v.cue("browser"))` to hit the word after the `{browser}` marker, then
   waits out the line plus a 0.35 s gap. Writes the cue log for that render.
4. Assembly places each clip at its exact cue time (scene offsets from `ffprobe` on each
   rendered scene), then subtitles are generated from the same timings.
   Picture, voice and subtitles **cannot drift**.

**Cue markers, not cue words.** `v.word("पूछा")` (1.x) ties a scene to one language.
Markers go into every language (`"You {ask}ask an AI"` / `"आपने एक AI से {ask}पूछा"`), so
one scene stays in sync with either narration. `automatio check scenes` confirms every
`v.cue()` has its marker everywhere. Word order differs (Hindi is SOV): a cue already in
the past plays immediately. Keep display labels and cue names separate.

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
- **Pronunciation dictionary** (`voices.toml` / `[pronunciation.hi]`): word → spoken
  spelling, TTS only (subtitles keep the original). `"AI": "एआई"` (user wanted "E-AYE").
  Prefer script fixes for one-offs. `automatio say` makes audition clips.
- **Rejected / failed paths (don't repeat):**
  - edge-tts Bangla `bn-BD-PradeepNeural`: user found it "bad"/robotic.
  - Splicing an English voice (Prabhat) into Bangla sentences (pitch/EQ/loudness
    matched, Rubber Band): technically fine, rejected by the user.
  - Azure Speech: user ruled it out (needs a paid key).
- Hindi narration runs longer than Bangla (≈11.5 chars/s with Adam); the video ended
  at 10:44 vs a 7–9 min target. If length matters, write a tighter script **before**
  spending credits, or time-stretch ~1.1–1.15× in post (formant-preserving).
- Always do a **free draft** before spending credits (the `draft` stage does: Madhur
  stand-in for uncached Adam lines).

---

## 7. Subtitles

- English subtitles are aligned **sentence by sentence** to the Hindi audio:
  split the spoken text at `। ? ! .`, find each sentence's span from the word timings,
  and show the matching English sentence for that span.
- Long sentences are split at commas. Choose the grouping with the lowest cost
  (penalise >56 chars, hard cap 68, penalise <18-char fragments), and share time
  proportionally to length. Never split between two English words.
- Finalise: lead 0.08 s, tail 0.35 s, minimum 0.9 s on screen, never overlap the next cue.
- On the **English** version the subtitle is the narration itself, so each cue is timed by
  the words it contains (word-level), not by proportion.
- Delivered as `subtitles-en.srt` + `subtitles-en.vtt` per version; **never burned in**
  and never muxed into the MP4. Validate: SRT and VTT agree, no overlaps, order, bounds,
  max length, reading speed; the whole subtitle script appears in order.

---

## 8. Audio mix

- Measure narration loudness **in stereo**. A mono file measures 3 dB quieter than the
  same voice duplicated to L/R, which once made the mix 2.5 dB off target.
- Narration −16 LUFS, then a **look-ahead peak limiter** at −1.5 dBFS (1 ms blocks,
  5 ms look-ahead, 80 ms release). Don't scale the whole mix down for a few peaks.
- Music normalised to −33 LUFS, ducked 6 dB under speech with a smoothed (Hann 0.6 s)
  envelope built from known speech intervals (deterministic, no sidechain compressor).
- Check: `ebur128` ⇒ I ≈ −16 LUFS, true peak ≤ −1 dB. Cut with `-t <total>`, not `-shortest`.

---

## 9. Verification loop (do this every time)

Automated by the pipeline except 3 (the agent's `review` task).

1. Render every scene in every language; fail on tracebacks, missing markers, lines not said once in order.
2. Scene video duration = cue log duration.
3. Contact sheets (one frame per line at 92%, per language): **look at every sheet** for
   overflow, overlaps, off-frame text, mid-animation glitches. Layout lint helps.
4. Verify each MP4: streams (no subtitle stream), durations, every line in order,
   loudness/true peak, subtitles, narration energy under the cues, subtitle band clear.
5. Patch scene text with scripts that **assert each replacement matched** (silent
   non-matches caused bugs).

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

Reusing the divide-by-zero crash in the intro and the bug-fix chapter gives a satisfying arc.

---

## 11. English version

1.x dubbed the finished Hindi video (Andrew speaking the subtitles inside the Hindi
subtitle windows, burned-in picture): animation stayed cued to Hindi words and short
English sentences waited mid-phrase. **2.0 renders the English version on its own:** same
scenes and visuals, cues on the English narration, Andrew at a constant −5 %, subtitles
word-timed. It is shorter than the Hindi (8:23 vs 10:44) because nothing is padded.
edge-tts word times run ~45 ms ahead of the decoded MP3 (profile `latency = 0.045`).
Whisper puts sentence-initial words ~0.3 s early: check onsets against audio energy.
