# AutomatioAgentica

**An agent-driven, end-to-end video production pipeline.** Hand a connected agent
harness (Claude Code or any agent with file and process access) a **script** and a
**production plan**. AutomatioAgentica turns them into finished long-form lessons in
**Hindi and English**: programmatic animation, the house voices, a broadcast-level mix, and
**separate English subtitle files** (never burned in). It also writes chapters, topics and
timings for every version.

```
User ──> Harness ──> AutomatioAgentica ──> Manim · ElevenLabs · edge-tts · ffmpeg ──> output/<slug>/
                        │  validate → approve → ingest → translate* → scenes* → draft → review*
                        │  → voice → render → assemble → subtitles → verify → deliver
                        └─ * agent tasks: creative work handed to the harness, then validated
```

The pipeline does all deterministic work and keeps resumable state. The harness agent
does the creative steps (Hindi adaptation, scene authoring, visual review) from
self-contained task files. Everything is driven by one CLI with a JSON protocol, so any
compatible harness can run it. **Agents: read [AGENTS.md](AGENTS.md).** Claude Code:
`/produce-video`.

## Two production shapes

| shape | what you get | example |
|---|---|---|
| **Two full versions** | Hindi and English videos, the same scenes, each timed to its own narration | Episode 01 |
| **Master + dub** | one video (e.g. English), plus a second language voiced onto the *same* picture and timeline: a voice-over MP3 that replaces the voice without any editing, and a dubbed MP4 | Episode 02 |

A dub is fitted to the master and never re-times it. Sections and numbered steps start on
time, and lines are time-stretched by at most 5 % only where needed. Lines that can't fit
are named so they can be rewritten shorter. Before any paid voicing, a **speech-length
forecast** calibrated on the voice's cached clips flags lines that won't fit. Rewriting is
free; voicing a line twice is not.

## Productions

| slug | title | shape | state |
|---|---|---|---|
| `agentic-ai-intro` | Episode 01: What is Agentic AI? | Hindi + English, full | delivered (Hindi 10:44, English 8:23); the regression reference |
| `ep02-inside-the-agent` | Episode 02: Inside an AI Agent: Who Actually Runs the Loop? | English master + Hindi dub | English delivered (13:17); Hindi dub waits for ElevenLabs credits (32 of 140 lines voiced) |
| `ep03-context-and-memory` | Episode 03: Context and Memory: How an Agent Handles Long Tasks | English (Hindi dub planned) | English delivered (13:12) with thumbnail; the Hindi voice-over is deferred and can be added later as a dub on the same timeline |
| `demo-tool-call` | What is a tool call? | Hindi + English, full | a two-line live smoke test of the ElevenLabs path |

Episode 01 is also the regression test. The pipeline reproduces its Hindi version (same
timings, byte-identical subtitles, zero new credits) and renders its English version timed
to its own narration.

## Quick start

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r pyproject.toml
echo "ELEVENLABS_API_KEY=sk_..." > .env            # Hindi voice; gitignored, never printed
.venv/bin/python -m automatio doctor --online      # tools, fonts, credentials, providers

# a new production from your files (anywhere on disk)
.venv/bin/python -m automatio new my-video --script ~/script.md --plan ~/plan.md --title "My video"
#   ... or one English video plus a Hindi voice-over on the same timeline:
.venv/bin/python -m automatio new my-video --script ~/script.md --plan ~/plan.md --dub hi
.venv/bin/python -m automatio run my-video         # repeat; the harness handles each stop
```

Requires `ffmpeg` (libx264, aac, flac, ebur128, rubberband), `uv`, and the fonts Inter,
JetBrains Mono and Noto Sans Devanagari. `doctor` checks all of it.

## What you supply, what you get

**Supply:** a script (Markdown or text; `##` headings become sections), a production plan
(free-form Markdown; numbered sections with `TIME: m:ss–m:ss` are picked up), optional
notes, and the API key. The voices are fixed house voices (`voices.toml`).

**Get** (`output/<slug>/`):

```
manifest.json            inputs + sha256, exact voice IDs/settings, files, every check result
report.md                deliverables, verification table, chapters + topics, warnings, what wasn't verified
narration-script.md      every line in every language with its timestamp in each version
script/                  <lang>/NN_<section>.txt per section, side-by-side.md (all languages, line by line)
thumbnail.png / .jpg     if the production has scenes/thumbnail.py
<alias>                  optional plan-required file names ([deliver] aliases), linked to the files below
hindi/   final-video.mp4  subtitles-en.srt/.vtt  chapters.txt  topics.txt  timings.json  narration/  assets/
english/ final-video.mp4  subtitles-en.srt/.vtt  chapters.txt  topics.txt  timings.json  narration/  assets/
```

- A dub version also has `voiceover.mp3`: the voice only, same duration as the video, 48 kHz.
- `chapters.txt` lists YouTube chapters (section starts in that version; the rules are
  checked). `topics.txt` adds the key topics: a short English `topic` on a narration line
  becomes a timestamp in every version, with that version's own time.
- `timings.json` lists sections and lines with their start, speech and slot times, which
  is what a later dub is fitted to.
- With `[subtitles] own_language = true`, each version also gets subtitles in its own
  language (e.g. `subtitles-hi.srt` timed to the Hindi voice).
- `narration/`: one clip per line, `narration.json` (text, absolute times, word timings),
  and the voice stem. `assets/`: scene renders, music stem, timeline, contact sheets.

The MP4s contain exactly one H.264 video and one AAC stereo stream (1920x1080, 30 fps,
CRF 17, -16 LUFS). No subtitles in the picture or the container.

## The house voices (exact, identical in every video)

| version | provider | voice | settings |
|---|---|---|---|
| Hindi | ElevenLabs `eleven_v4` | **Adam** `pNInz6obpgDQGcFmaJgB`, `language_code=hi` | stability 0.5, similarity 0.75, neighbour-line context, "AI" spoken "एआई" |
| English | edge-tts | **Andrew** `en-US-AndrewMultilingualNeural` | rate -5 %, pitch +0 Hz |
| Hindi draft | edge-tts | Madhur `hi-IN-MadhurNeural` | free stand-in, used only for drafts and dub previews before paid lines |

Defined in `voices.toml`. Clips are cached by (voice settings | spoken text), so a line is
paid for once. Re-runs, resumed runs and edited scripts only voice what changed.

## How it works

1. **Ingest:** the script becomes `narration.json` (sections → lines). A completeness
   guard fails the run if the narration ever drops or summarises script text.
2. **Translate** (agent): natural Hindi, same sentence count per line, cue markers
   copied. For a dub: concise but complete, written to fit the master's slots.
3. **Scenes** (agent): one Manim `VoiceScene` per section, in the house visual language.
   Animations are cued by **markers** in the narration (`… a {input}input …` →
   `v.cue("input")`), present in every rendered language. One scene file therefore
   renders in sync with both narrations.
4. **Draft + review:** free low-res render with contact sheets. The agent inspects them;
   layout lint flags anything off-frame or in the subtitle band.
5. **Voice:** the user-approved budget caps paid credits. A dub is forecast against the
   master first, a canary line checks the API before a batch, and retries back off on
   429/5xx. Paid clips cut off by the provider are re-taken. Credentials are redacted
   everywhere.
6. **Render:** each scene × language, in parallel, content-addressed cache.
7. **Assemble:** timeline from the renders themselves, voice placed per cue, -16 LUFS +
   look-ahead limiter, synthesised ambient music ducked 6 dB, x264 encode. A dub is fitted
   and mixed onto the master's picture (stream copy).
8. **Subtitles:** English SRT + VTT per version. On Hindi they are sentence-aligned to the
   Hindi speech; on English they are word-timed. A dub shares the master's.
9. **Verify:** streams, durations, completeness, loudness/true peak, subtitle integrity,
   narration-vs-subtitle sync, subtitle band clear (no burn-in), layout lint, timing vs
   plan, and for a dub its fit, clip defects and the voice-over MP3.
10. **Deliver:** the folder above, the manifest and the report.

State lives in `build/<slug>/state.json`. Every stage is fingerprinted by its inputs, so
`run` after an interruption, a crash or an edit continues where it stopped. Topics are
metadata and never invalidate renders or a review. If one version is blocked (e.g. no
credits left for the Hindi dub), `run <slug> --lang en` still produces and delivers the
others.

## Layout

```
automatio/          pipeline: cli, pipeline (stages), state, voice, providers/, render, audio, music,
                    subtitles, assemble, dub (+ preview), forecast, verify, deliver, tasks, doctor, secrets
agentic_video/      visual library: style, components, icons, internals (Episode 02 building blocks),
                    VoiceScene (+ runtime)
productions/<slug>/ production.toml, inputs/ (script, plan, notes), narration.json, scenes/
                    (ep03 adds scenes/memory_kit.py: context & memory components + overlap checker)
tools/              voice_pauses.py: caps overlong pauses inside free-voice narration clips
voices.toml         voice registry
docs/               SCENE_AUTHORING.md (for agents writing scenes)
tests/              unit tests + offline end-to-end pipeline test (full versions and a dub)
AGENTS.md CLAUDE.md .claude/skills/produce-video/   harness integration
ANIMINFO.md         production playbook: what worked, what failed, why (Episodes 01 and 02)
                    (Episode 03 decisions: productions/ep03-context-and-memory/inputs/notes-1.md)
CHANGELOG.md        what changed between pipeline versions
```

Tracked: code, `voices.toml`, `productions/*/` (inputs, narration, scenes). Gitignored:
`.env`, `cache/`, `build/`, `output/`, all media.

## Common commands

```bash
.venv/bin/python -m automatio status my-video                 # progress, approval, credits spent
.venv/bin/python -m automatio preview my-video s05 --lang all  # 480p render + contact sheets
.venv/bin/python -m automatio check dub my-video               # will the dub fit? (before paying)
.venv/bin/python -m automatio preview my-video s01,s02 --lang hi   # hear the dub of a few sections
.venv/bin/python -m automatio run my-video --lang en           # produce only some versions
.venv/bin/python -m automatio say "आपने एक AI Agent से कहा" --voice hindi-adam   # audition
.venv/bin/python -m automatio report my-video
.venv/bin/python -m unittest discover -s tests -v              # tests (offline, ~30 s)
```

## Polishing tools (added with Episode 03)

- **Natural pauses (`tools/voice_pauses.py`).** The English house voice (edge-tts Andrew) is
  deterministic and sometimes holds ~0.5 s at commas and colons or hesitates mid-phrase, which
  sounds halting. The tool shortens only the silence inside each cached clip (comma pauses to
  0.30 s, mid-phrase hesitations to 0.10 s, sentence breaks to 0.60 s; cuts in true silence with
  5 ms crossfades) and shifts the clip's word timings, so cues and subtitles stay exact. Voice,
  speed and pitch are untouched; paid (ElevenLabs) clips are never rewritten.

  ```bash
  .venv/bin/python tools/voice_pauses.py my-video --dry-run    # what would be cut
  .venv/bin/python tools/voice_pauses.py my-video              # polish, then:
  .venv/bin/python -m automatio run my-video --force voice     # rebuild manifest, renders, mix
  ```

- **Context & memory components (`productions/ep03-context-and-memory/scenes/memory_kit.py`).**
  Reusable building blocks on top of `agentic_video/internals.py`: `SizedCard` (height follows
  the amount of text), `SummaryCard`, `PlaceholderCard`, `NoteCard`, `NotesBlock`, `Notebook`
  (memory store), `LiveContext` (a context window whose meter and % readout are always computed
  from the cards inside it), `CallCounter`, `TechniqueTag` and `session_wipe` (session divider).
  Kept next to the production's scenes so Episodes 01 and 02 are not re-rendered; a later episode
  can import or promote them.
- **Overlap checker (`memory_kit.CheckedScene`).** Scenes that import the kit get a
  `VoiceScene` that, after every animation, compares the visible text, cards and pills of
  different objects and prints an `OVERLAP` line to the render log for anything that stays
  overlapped for more than 0.6 s (labels on their own panel are ignored). It also fades the
  chapter tag in with the first narration line, so sections start without dead air.

Pronunciation: add respellings under `[pronunciation.hi]` / `[pronunciation.en]` in
`production.toml` (or the voice profile in `voices.toml`). Subtitles always keep the
written form.
