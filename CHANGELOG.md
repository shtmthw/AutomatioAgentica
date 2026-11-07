# Changelog

## 2.1.0 (2026-11-08)

Lessons of Episode 02 ("Inside an AI Agent", English master + Hindi dub) built into the pipeline.

- **Deliverables written by the pipeline**:
  - `<label>/chapters.txt` (YouTube chapters per version; the rules are checked).
  - `<label>/topics.txt`, from short English `topic` fields on narration lines. Topics are
    metadata and never invalidate renders or a visual review.
  - `<label>/timings.json` (sections, lines and slots, plus the dub segments of a master).
  - `script/<lang>/NN_<section>.txt` and `script/side-by-side.md` (folder set by
    `[deliver] script_dir`).
  - `[deliver.aliases]`: plan-required file names, linked inside `output/<slug>/`.
  - `report.md` now includes each version's chapters and topics.
- **Own-language subtitles:** `[subtitles] own_language = true` also writes
  `subtitles-<lang>.srt/.vtt` in each version's own language. A dub's are timed to its voice
  as placed and time-stretched. Verified by a new `subtitles (<lang>)` check.
- **Dub forecast** (`automatio/forecast.py`, `check dub`): predicts every dub segment's fit from
  the text before any credits are spent. It is calibrated on the voice's cached clips and
  measured on the audible audio (ElevenLabs alignments run ~0.45 s long). It is shown in the
  translate task and the approval request. The voice stage stops with a `dub-fit` agent task
  instead of paying for a segment that clearly cannot fit.
- **Dub preview:** `preview <slug> s01,s02 --lang hi` builds the dub of a few sections over the
  master's final picture, from cached paid clips and the free draft voice (`--paid` voices the
  missing ones within the budget).
- **Partial runs:** `run <slug> --lang en` produces and delivers only some versions (voice ->
  deliver), so one blocked version no longer holds back the others. Stages show `partial`, a
  blocked outcome carries a `hint` with the command, and the manifest keeps versions delivered
  earlier.
- `new --dub hi` creates a master + dub production (master first, `[dub]` block).
- `preview` takes several sections (`s01,s02`); `--lang <dub>` previews the dub (it used to try
  to render the dub language as if it were a full version).
- `doctor` checks the `rubberband` and `deesser` filters the dub needs.
- `verify`'s timing check names sections more than 20 % off the plan.
- Fixes and cleanup:
  - Re-delivering no longer leaves `.X.link` temp files when the target is already linked
    (POSIX rename between two links of one file is a no-op); old leftovers are removed.
  - Removed dead helpers (`need_tool`, `wait_for_lock_release`, `voice.clip_path`) and unused
    imports.
  - Removed the duplicate root `VIDEO-PLAN-2.txt` (identical to
    `productions/ep02-inside-the-agent/inputs/plan.txt`) and the empty `.temp` placeholder.
- Productions:
  - Episode 01 and Episode 02 narrations carry topics (Episode 02's are taken over from its
    hand-made `topics.txt`, whose regeneration is byte-identical).
  - Episode 02's `production.toml` produces the plan's file names.
  - One Episode 02 dub line was tightened to fit its slot.

## 2.0.0 (2026-11-07)

Harness-driven pipeline (`python -m automatio`): resumable stages, approval gate, agent tasks,
Hindi + English versions from one set of scenes, separate subtitles, verification, deliverables.
Dub versions (`mode = "dub"`): a language voiced over a master's picture and timeline.
