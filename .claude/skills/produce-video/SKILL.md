---
name: produce-video
description: Produce or continue an AutomatioAgentica video production. A script and a production plan become two complete long-form videos (Hindi and English) using the exact house voices, with separate English SRT/VTT subtitles for both and nothing burned in. Use when the user supplies a script/plan, asks to make, render or continue a video, asks for production status, or wants the deliverables.
---

# Produce a video with AutomatioAgentica

You are the harness. The pipeline does the deterministic work and keeps resumable state.
You handle approvals (with the user), creative agent tasks, and reporting. The full
contract is in `AGENTS.md`; this is the working loop.

## 0. Environment

```bash
.venv/bin/python -m automatio doctor            # add --online before the first paid run
```

Report any ✗ item with its remedy and stop if a critical one fails.

## 1. Start (new material) or continue (existing slug)

- Read "Production guidelines" in `AGENTS.md` first. Before approval, raise anything the
  material conflicts with: no recap of all topics, a coding part that needs a real screen
  recording, dense stretches that need more visuals.
- New: the user names a script file and a production plan (Markdown or text; convert
  .docx/.pdf to .md yourself, keeping every word). Pick a short slug and run:
  `.venv/bin/python -m automatio new <slug> --script <path> --plan <path> [--notes <path>] --title "<title>"`
  Voices are **fixed for every video**: `hindi-adam` (Hindi) and `english-andrew` (English),
  which are the defaults. Never pass `--voice`, never pick, add or swap a voice, and never edit
  the voice profiles in `voices.toml`. If something seems to call for another voice, ask the user.
  The user always supplies the production plan. If it's missing, ask for it; don't draft one.
- Continue: `.venv/bin/python -m automatio status <slug>`.

## 2. Loop

Run `.venv/bin/python -m automatio run <slug> --json` (in the background when stages
will render or encode), then act on `state`:

- **needs_approval**: summarise `approval.config` (languages, voices with provider IDs,
  subtitles, video) and `approval.estimate` (paid credits; *exact* once the translation
  exists). Ask the user with AskUserQuestion, recommending the suggested budget. On an
  explicit yes, run `approval.command` with `--by "<user's name or 'user'>"`. If the user
  declines or changes settings, edit `production.toml` accordingly, not the state.
- **needs_agent**: read `task.file` and do the task.
  - *translate*: edit `narration.json`. Natural conversational Hindi, English technical
    terms in Latin script, same sentence count as the English, every `{marker}` copied,
    numbers spelled out. Never summarise. Run `task.check` until it shows 0 errors.
    For a **dub** language (`mode = "dub"`), write each line to fit its master slot (concise, never
    cut; see "Dub versions" in AGENTS.md). After voicing, the `dub fit` check names any lines to shorten.
  - *scenes*: read `docs/SCENE_AUTHORING.md` and 2-3 reference scenes in
    `productions/agentic-ai-intro/scenes/`. Write one scene per section, add markers to
    every language, `check scenes`, then `preview <slug> <section> --lang all` and **Read
    the sheet image**. Fix and repeat.
  - *review*: Read **every** contact sheet image listed. Fix real problems (re-`preview`),
    then `complete review <slug> --notes "<what you checked/fixed>"`.
  - *narration*: restore missing script text, or list true non-narration under `excluded`.
- **blocked**: tell the user `error.message` and `error.remedy` verbatim (missing key,
  missing permission, out of credits, missing tool). Don't work around it.
- **failed**: read `error.details.tail` and the log it names. Fix what is yours (scene
  code, narration) and run again. Otherwise report it.
- **done**: go to 3.

Repeat until `done`. Each `run` skips everything already done; paid lines are never
paid for twice.

## 3. Report

Read `output/<slug>/report.md` and `output/<slug>/manifest.json`, then tell the user:

- the two videos (`output/<slug>/hindi/final-video.mp4`, `.../english/final-video.mp4`)
  with their durations, and the four subtitle files;
- the chapter and topic timestamps **per version**: write `output/<slug>/<label>/chapters.txt`
  and `topics.txt` from `narration-script.md`, as in guidelines 4 and 6 of AGENTS.md;
- the verification table per version, with every warn/fail honestly;
- credits spent, the voices used (provider + voice ID), and anything listed under "Not
  verified automatically". Listening quality needs the user's ears.

Do not claim success for anything the report does not show as verified.
