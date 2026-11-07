# AutomatioAgentica

**A harness-driven, end-to-end video production pipeline.** Hand a connected agent
harness (Claude Code or any agent with file and process access) a **script** and a
**production plan**. AutomatioAgentica turns them into **two complete long-form
videos**, Hindi and English, with the house voices, programmatic animation, a
broadcast-level mix, and **separate English subtitle files for both** (never burned in).

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

The reference production is **"What is Agentic AI?"** (`productions/agentic-ai-intro/`),
a 10:44 beginner lesson. It is also the regression test: the pipeline reproduces its Hindi
version (same timings, byte-identical subtitles, zero new credits) and renders a full
English version timed to its own narration.

## Quick start

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r pyproject.toml
echo "ELEVENLABS_API_KEY=sk_..." > .env            # Hindi voice; gitignored, never printed
.venv/bin/python -m automatio doctor --online      # tools, fonts, credentials, providers

# a new production from your files (anywhere on disk)
.venv/bin/python -m automatio new my-video --script ~/script.md --plan ~/plan.md --title "My video"
.venv/bin/python -m automatio run my-video         # repeat; the harness handles each stop
```

Requires `ffmpeg` (libx264, aac, flac, ebur128), `uv`, and the fonts Inter, JetBrains Mono and
Noto Sans Devanagari. `doctor` checks all of it.

## What you supply, what you get

**Supply:** a script (Markdown or text; `##` headings become sections), a production plan
(free-form Markdown; numbered sections with `TIME: m:ss–m:ss` are picked up), optional
notes, the voices (`voices.toml`; defaults are the house voices), and the API key.

**Get** (`output/<slug>/`):

```
manifest.json            inputs + sha256, exact voice IDs/settings, files, every check result
report.md                deliverables, verification table, warnings, what wasn't verified
narration-script.md      every line in both languages with its timestamp in each version
thumbnail.png / .jpg     if the production has scenes/thumbnail.py
hindi/   final-video.mp4  subtitles-en.srt  subtitles-en.vtt  narration/  assets/
english/ final-video.mp4  subtitles-en.srt  subtitles-en.vtt  narration/  assets/
```

`narration/`: one clip per line, `narration.json` (text, absolute times, word timings),
and the voice stem. `assets/`: scene renders, music stem, timeline, contact sheets. The
MP4s contain exactly one H.264 video and one AAC stereo stream (1920x1080, 30 fps,
CRF 17, -16 LUFS). No subtitles in the picture or the container.

## The house voices (exact, from the first production)

| version | provider | voice | settings |
|---|---|---|---|
| Hindi | ElevenLabs `eleven_v4` | **Adam** `pNInz6obpgDQGcFmaJgB`, `language_code=hi` | stability 0.5, similarity 0.75, neighbour-line context, "AI" spoken "एआई" |
| English | edge-tts | **Andrew** `en-US-AndrewMultilingualNeural` | rate -5 %, pitch +0 Hz |
| Hindi draft | edge-tts | Madhur `hi-IN-MadhurNeural` | free stand-in used only for the low-res draft before paid lines |

Defined in `voices.toml`. Clips are cached by (voice settings | spoken text), so a line is
paid for once. Re-runs, resumed runs and edited scripts only voice what changed.

## How it works

1. **Ingest:** the script becomes `narration.json` (sections → lines). A completeness
   guard fails the run if the narration ever drops or summarises script text.
2. **Translate** (agent): natural Hindi, same sentence count per line, cue markers copied.
3. **Scenes** (agent): one Manim `VoiceScene` per section, in the house visual language.
   Animations are cued by **markers** in the narration (`… a {input}input …` →
   `v.cue("input")`), present in every language. One scene file therefore renders in sync
   with both narrations.
4. **Draft + review:** free low-res render of both versions with contact sheets. The
   agent inspects them; layout lint flags anything off-frame or in the subtitle band.
5. **Voice:** the user-approved budget caps paid credits; a canary line checks the API
   before a batch; retries back off on 429/5xx. Credentials are redacted everywhere.
6. **Render:** each scene × language, in parallel, content-addressed cache.
7. **Assemble:** timeline from the renders themselves, voice placed per cue, -16 LUFS +
   look-ahead limiter, synthesised ambient music ducked 6 dB, x264 encode.
8. **Subtitles:** English SRT + VTT per version. On Hindi they are sentence-aligned to the
   Hindi speech; on English they are word-timed.
9. **Verify:** streams, durations, completeness, loudness/true peak, subtitle integrity,
   narration-vs-subtitle sync, subtitle band clear (no burn-in), layout lint, timing vs plan.
10. **Deliver:** the folder above, the manifest and the report.

State lives in `build/<slug>/state.json`. Every stage is fingerprinted by its inputs, so
`run` after an interruption, a crash or an edit continues where it stopped.

## Layout

```
automatio/          pipeline: cli, pipeline (stages), state, voice, providers/, render,
                    audio, music, subtitles, assemble, verify, deliver, tasks, doctor, secrets
agentic_video/      visual library: style, components, icons, VoiceScene (+ runtime)
productions/<slug>/ production.toml, inputs/ (script, plan, notes), narration.json, scenes/
voices.toml         voice registry
docs/               SCENE_AUTHORING.md (for agents writing scenes)
tests/              unit tests + offline end-to-end pipeline test
AGENTS.md CLAUDE.md .claude/skills/produce-video/   harness integration
ANIMINFO.md         production playbook: what worked, what failed, why
```

Tracked: code, `voices.toml`, `productions/*/` (inputs, narration, scenes). Gitignored:
`.env`, `cache/`, `build/`, `output/`, all media.

## Common commands

```bash
.venv/bin/python -m automatio status my-video            # progress, approval, credits spent
.venv/bin/python -m automatio preview my-video s05 --lang all   # 480p render + contact sheets
.venv/bin/python -m automatio say "आपने एक AI Agent से कहा" --voice hindi-adam   # audition
.venv/bin/python -m automatio report my-video
.venv/bin/python -m unittest discover -s tests -v        # tests (offline, ~1 min)
```

Pronunciation: add respellings under `[pronunciation.hi]` in `production.toml` (or the
voice profile in `voices.toml`). Subtitles always keep the written form.
