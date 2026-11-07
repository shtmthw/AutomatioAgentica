# AGENTS.md - operating AutomatioAgentica from an agent harness

You are connected to **AutomatioAgentica**, a video production pipeline. The user gives
a script, a production plan and (optionally) voices and credentials; the pipeline and
you produce two complete long-form videos - Hindi and English - with separate English
subtitle files. This file is the contract between the pipeline and any harness
(Claude Code, Codex, a custom agent runner, ...). Claude Code users: see also `CLAUDE.md`
and the `/produce-video` skill.

```
User ──> Harness (you) ──> python -m automatio ──> Manim · ElevenLabs · edge-tts · ffmpeg ──> output/<slug>/
             ▲                       │
             └── agent tasks ────────┘   (translation, scene authoring, visual review)
```

The pipeline does everything deterministic (validation, cost estimate, narration with
the exact house voices, rendering every language, mixing, encoding, subtitles,
verification, packaging, reports) and keeps resumable state. It hands **creative work**
back to you as agent tasks with exact instructions and a validation command. You never
need to copy text between tools by hand.

## New session? Start here

1. **Check the environment:** `.venv/bin/python -m automatio doctor` (add `--online`
   before a run that will spend ElevenLabs credits). Report any ✗ with its remedy.
2. **See what exists:** `ls productions/`, then `.venv/bin/python -m automatio status <slug>`
   for anything in progress. `status` and `next` are read-only.
3. **Continue a production:** run `.venv/bin/python -m automatio run <slug> --json` and act on
   the outcome (see [The loop](#the-loop)). It resumes exactly where the last session stopped.
4. **New video:** the user gives a script and a production plan (any path). Read both,
   then read [Production guidelines](#production-guidelines-from-the-user) below. Raise
   any guideline the material conflicts with (no recap, a coding section that needs a
   screen recording, ...) *before* approval. Then:
   `.venv/bin/python -m automatio new <slug> --script <file> --plan <file> --title "<title>"`
   and loop `run --json` until `done`.
5. **Before writing scenes**, read `docs/SCENE_AUTHORING.md` and two or three scenes of
   the reference production `productions/agentic-ai-intro/scenes/`.
6. **When done**, report from `output/<slug>/report.md` and hand over the chapter and topic
   timestamps for both versions (guidelines 4 and 6).

Reference material: `ANIMINFO.md` (what worked and failed in the first production),
`README.md` (overview), `voices.toml` (the exact voices).

## Requirements of the harness

- File read/write inside this repository (or the folders set by `AA_PRODUCTIONS_DIR`,
  `AA_BUILD_DIR`, `AA_CACHE_DIR`, `AA_OUTPUT_DIR`).
- Running commands: `.venv/bin/python -m automatio ...`, which starts manim and ffmpeg.
- Network only for the voice stage (ElevenLabs API, edge-tts). Everything else is offline.
- Reading images, for the visual review task. Without it, tell the user the review was skipped.
- Long commands: a full run takes ~15–25 min for a 10-minute video. Run it in the
  background if your harness supports that, or step through with `--until <stage>`. An
  interrupted run resumes where it stopped; just run the same command again.

Check the environment first: `python -m automatio doctor` (add `--online` to contact the
providers; no credits are spent).

## The loop

```bash
python -m automatio new <slug> --script <file> --plan <file> [--notes <file>]   # once
python -m automatio run <slug> --json        # repeat until state == "done"
```

`run` (or `next`, which only looks) returns one JSON object. Act on `state`:

| state | exit | what you do |
|---|---|---|
| `done` | 0 | Report the deliverables to the user (read `output/<slug>/report.md`). |
| `needs_approval` | 11 | Show the user `approval.config` and `approval.estimate`, and **ask for approval**. Only after they say yes, run `approval.command` (adjust `--budget` / `--by` to what they agreed). Then `run` again. |
| `needs_agent` | 10 | Read `task.file`, do the work, run `task.check` until it passes, then `run` again. |
| `blocked` | 12 | A credential, permission, plan limit or tool is missing. Tell the user `error.message` and `error.remedy` **exactly**. Never invent or guess credentials. |
| `failed` | 1 | Read `error` (with log tail). Fix it if it is in your remit (scene code, narration), otherwise report it. Then `run` again. |
| `locked` | 13 | Another run is in progress: wait for it (`status` shows progress). |

Never edit `build/<slug>/state.json` by hand and never fake a check. If a stage cannot
be verified, say so in your report.

## Approval and credentials

- **Approval is the user's decision.** Run `approve` only after the user explicitly
  approves the configuration and the paid-voice budget in the conversation. Record who
  approved with `--by`. The budget caps paid credits for the whole production; if it
  runs out, the pipeline stops with `needs_approval` again.
- The approval covers the configuration. Changing voices, languages or video settings
  later requires a new approval.
- Credentials (e.g. `ELEVENLABS_API_KEY`) come from the harness environment or the
  gitignored `.env`. Never print them, write them to files, or put them in commands.
  The pipeline redacts secrets from all its output; `doctor` shows only presence.
- The ElevenLabs key in use may lack `User: Read`, so the credit balance can't be read.
  The pipeline then verifies access with one "canary" line before a paid batch. Paid
  lines are cached and are never paid for twice.

## Agent tasks

All tasks are self-contained Markdown files under `build/<slug>/tasks/`. Summary:

**translate**: fill the missing language(s) in `productions/<slug>/narration.json`.
Natural, conversational standard Hindi, English technical terms kept in Latin script
(explained once with "यानी ..."). Same number of sentences as the English line (subtitle
sentence *i* shows while sentence *i* is spoken). Copy every `{marker}` to the matching
word. Write numbers and symbols as they are spoken. **Never summarise, shorten or skip.**
Check: `python -m automatio check translate <slug>`.

**scenes**: write one Manim `VoiceScene` per section in `productions/<slug>/scenes/`,
following the plan and the house style. Read `docs/SCENE_AUTHORING.md`; the reference
implementation is `productions/agentic-ai-intro/scenes/`. Put cue markers in every
language of `narration.json` and use `v.cue()`. On-screen text is English. Check:
`python -m automatio check scenes <slug>`. Iterate with `python -m automatio preview
<slug> <section> --lang all` and **look at the contact sheet images**.

**review**: inspect every draft contact sheet (one frame per line, all languages). Fix
any layout problem in the scenes, then run
`python -m automatio complete review <slug> --notes "<what you checked/fixed>"`.

**narration**: the narration drifted from the supplied script. Restore the missing text,
or list genuine non-narration paragraphs under `excluded` with a reason.

## Production rules (do not break)

- Two complete versions per production (Hindi + English), the same scenes and visuals,
  each timed to its own narration. Do not shorten the video or the script to save time or
  credits.
- **The voices are fixed and identical across all videos:** Hindi **ElevenLabs `eleven_v4`,
  voice Adam `pNInz6obpgDQGcFmaJgB`** (profile `hindi-adam`: stability 0.5, similarity 0.75,
  "AI" -> "एआई"); English **edge-tts `en-US-AndrewMultilingualNeural`** (profile
  `english-andrew`, -5 %). These are the defaults of `new`. Never pass `--voice`, never select,
  add or swap a voice, never change these profiles' settings, and never substitute a
  similar-sounding voice. If the voice seems to need changing, ask the user. (The only other
  voice is the free `hindi-madhur-draft` stand-in, which the pipeline uses by itself in the
  low-res draft and which never reaches a final video.)
- The user supplies the script **and** the production plan. If either is missing, ask for
  it; don't write a plan yourself.
- Subtitles are separate files only (`subtitles-en.srt` + `.vtt` for both versions).
  Nothing is burned into the picture and no subtitle stream goes into the MP4.
- Keep the visual language and audio treatment of the reference production unless the
  new plan explicitly says otherwise.

## Production guidelines (from the user)

These are the user's standing directions for every video. Apply them unless a plan
explicitly says otherwise.

1. **No burned-in subtitles: subtitles only as separate files.** The final MP4s carry
   picture and sound only. Never add an `ass`/`subtitles` filter, never mux a subtitle
   stream, and never put the narration sentence on screen as a caption. The `verify` stage
   checks this ("no burn-in", "container"). Fix a warn/fail there; never ignore it.
2. **Make repetitive or information-heavy parts more engaging.** When a stretch repeats
   an idea, lists many items, or packs in a lot of information, add more visuals:
   - keyword **text pop-ups** (`Pill`, `en(...)`) that appear on the cue word;
   - small diagrams, icons, highlights or a travelling `Token`;
   - a progress or step marker, so viewers see where they are.

   Rule of thumb: something new on screen every ~5–8 s, and at least two cue markers in
   any line longer than ~10 s. Pop-ups are short keywords (2–4 words), never the spoken
   sentence (that would be a burned-in caption). Keep them inside the safe area, and fade
   or dim old ones so the frame doesn't clutter.
3. **Complex and coding parts may need screen recordings (later videos).** Today the
   pipeline is code-only (Manim) and **cannot insert external footage**. Until it can:
   - recreate the steps with `Terminal`, `CodeEditor` and `Browser`, line by line and
     command by command (see `scenes/s07_bugfix.py` in the reference production);
   - if a plan asks for, or the content clearly needs, a real screen recording, tell the
     user before scene authoring. Ask them for the recording, and say that using it needs
     a pipeline extension (a clip-scene type that places an MP4 in the timeline and times
     it to the narration lines). Don't fake it and don't skip the content.
4. **Add timestamps.** Every delivery includes chapter timestamps for **each** version.
   The Hindi and English timings differ, so never reuse one list for both. Take the
   section start times from `output/<slug>/narration-script.md` (or
   `<label>/assets/timeline.json`). Write them as YouTube chapters (`0:00 Introduction`:
   the first entry at 0:00, at least 3 entries, each chapter at least 10 s long) to
   `output/<slug>/<label>/chapters.txt`, and include them in your final report.
   Don't burn timestamps into the picture: the shared scenes would show wrong times in
   one of the versions.
5. **End with a quick recap of all topics.** Every video closes with a short recap that
   names each topic covered, in order. The reference production does this with recap
   cards in `s09_outro.py`. If the supplied script has no recap, **do not write narration
   for it yourself.** The completeness guard rejects narration that isn't in the script,
   and the script is the user's. At approval time, propose recap lines and ask the user to
   add them to the script. Until then, the closing scene may show the topics visually
   during the existing closing lines.
6. **Add topic timestamps.** Beyond one chapter per section, list the key topics inside
   each section with their start times, per version (e.g. `4:34 The agent loop`,
   `5:12 Weather example: first website fails`). Use the line start times in
   `narration-script.md` or `<label>/narration/narration.json`. Write them to
   `output/<slug>/<label>/topics.txt` and add them to the report. The recap (guideline 5)
   should cover the same topics.

   `chapters.txt` and `topics.txt` are written by you, not by the pipeline. Regenerate
   both after every delivery that changes the timeline.

## Commands

```
doctor [--online]          environment / tools / fonts / credentials / providers
new <slug> --script --plan create a production from files anywhere on disk (copied into inputs/)
status <slug>              stage table, live progress, approval, spent credits
next <slug>                the single next action (no side effects)
run <slug> [--until S] [--only S] [--force S]
approve <slug> --budget elevenlabs=N --by "<who>"
task <slug>                print the waiting agent task
check translate|scenes|narration <slug>
complete review <slug> --notes "..."
preview <slug> <section> [--lang hi|en|all] [--hq] [--audio]
say "text" --voice hindi-adam       audition pronunciation (cached; ElevenLabs spends credits)
estimate <slug> | report <slug> | voices | clean <slug> [--build]
```

Add `--json` to any command for machine-readable output.

## Where things are

```
voices.toml                     house voices (exact provider IDs and settings)
automatio/                      the pipeline (stages, providers, state, CLI)
agentic_video/                  visual library: style, components, icons, VoiceScene
docs/SCENE_AUTHORING.md         how to write scenes
productions/<slug>/             production.toml, inputs/, narration.json, scenes/   (tracked)
build/<slug>/                   state.json, tasks/, logs/, drafts, intermediates    (gitignored)
cache/                          voice clips, renders, music - content-addressed     (gitignored)
output/<slug>/                  deliverables, manifest.json, report.md              (gitignored)
ANIMINFO.md                     the production playbook: what worked, what failed, why
```
