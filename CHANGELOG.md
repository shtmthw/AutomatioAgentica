# Changelog

## 2.2.0 (2026-11-17)

Anyone can pull the repository and run it from their own harness. Every video on the
[@anon14none](https://www.youtube.com/@anon14none) channel was made with this pipeline.

- **MCP server** (`automatio/mcp_server.py`, launcher `scripts/mcp_server.py`, entry point
  `automatio-mcp`): 24 tools over the same CLI, so state, cache and the run lock are shared with
  shell harnesses. `run` and `preview` start background jobs and return a `job_id` instead of
  blocking (`wait` continues); jobs survive the client closing. `approve` needs
  `confirmed_by_user` and also asks the user through MCP elicitation when the client supports it
  (both the 2025-11-25 and 2026-07-28 protocols). Contact sheets and full-resolution video frames
  come back as images. Scoped file tools are provided for clients without their own: read
  anything but credentials and caches, write only `narration.json`, `production.toml` and
  `scenes/`. CLI commands named in outcomes get `<field>_mcp` twins with the exact tool call.
  Docs are MCP resources; `produce_video` is an MCP prompt.
- **`mcp-config`** prints ready-to-paste configs (absolute paths) for Claude Code, Claude
  Desktop, Codex, Cursor, VS Code and Gemini CLI. The repo ships `.mcp.json` (Claude Code
  project server) and `GEMINI.md` (points Gemini CLI at `AGENTS.md`).
- **One-command setup:** `scripts/setup.sh` installs the system packages (pacman, apt, dnf or
  brew), creates the Python 3.12 venv with uv, installs the packages, creates `.env` from the
  new `.env.example`, and runs `doctor` and the tests. `doctor` remedies now name the install
  command for the machine's package manager, and it reports the `mcp` package and local overrides.
- **Operator overrides (`local/`, gitignored):** `local/voices.toml` adds voice profiles under
  new names (house profiles can't be redefined) and `[defaults]` picks the voices `new` uses;
  `local/GUIDELINES.md` adds standing directions the agent reads. With an empty `local/` nothing
  changes. `AA_LOCAL_DIR` moves the folder.
- **Claude Code project settings** (`.claude/settings.json`): pipeline commands are allowed
  without a prompt; `approve`, `say` and `clean` still ask; `.env` can't be read or edited.
- **Episode 04 polish, built in:** render fingerprints include the voice clip timings
  (`voice.timing_fp`), so clips polished in place re-render exactly the scenes timed to them;
  `tools/voice_pauses.py` removes the stale voice manifests itself (a plain `run` then
  rebuilds); English subtitle cues are segmented over the word timings by dynamic programming.
- **Docs:** README rewritten for new users (setup, connecting a harness, costs, overrides);
  AGENTS.md gains "Connecting a harness" and "Before calling a video final"; ANIMINFO.md gains
  the lessons of Episodes 03 and 04.
- **Licenses:** the pipeline is MIT (`LICENSE`). The @anon14none productions in `productions/`
  and everything rendered from them stay all rights reserved (`productions/LICENSE`); `NOTICE`
  maps which is which. Productions other people make with the pipeline are theirs.
- Tests: `tests/test_mcp_server.py` (tool mapping, file sandbox, approval with and without
  elicitation, the loop to a preview image over MCP, local overrides). A GitHub Actions workflow
  runs setup and the whole suite on Ubuntu.

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
