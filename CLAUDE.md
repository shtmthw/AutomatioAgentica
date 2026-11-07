# CLAUDE.md

This repository is **AutomatioAgentica**, a harness-driven video production pipeline.
The harness contract is in **[AGENTS.md](AGENTS.md)**. Read it before acting on a production.
The production playbook (what worked, what failed) is [ANIMINFO.md](ANIMINFO.md). Scene
writing is covered in [docs/SCENE_AUTHORING.md](docs/SCENE_AUTHORING.md).

Claude Code specifics:

- Use the **`/produce-video`** skill (`.claude/skills/produce-video/SKILL.md`) to start or
  continue a production. It runs the `run --json` loop and handles each outcome.
- Always call the pipeline as `.venv/bin/python -m automatio ...` from the repo root.
- `run` can take 15–25 minutes for a full video. Start it with `run_in_background` and
  wait for the completion notification. Don't poll in a loop. Resuming after a timeout
  or interruption is safe.
- **Approval gate:** when `run` returns `needs_approval`, show the configuration and
  estimate and ask the user with AskUserQuestion. Run the `approve` command only after
  an explicit yes, with `--by` naming who approved.
- **Visual review:** open every contact sheet with the Read tool (images) before
  `complete review`. Don't mark a review complete without looking at the sheets.
- **Paid dubs:** run `check dub <slug>` before any paid dub voicing, and offer
  `preview <slug> s01,s02 --lang hi` so the user can hear the dub first. When one version is
  `blocked` (e.g. ElevenLabs credits), `run <slug> --lang <others>` still delivers the rest.
- **Chapters and topics** are written by the pipeline: maintain short English `"topic"` fields
  in `narration.json` instead of writing `chapters.txt`/`topics.txt` by hand.
- Don't edit `agentic_video/*.py` for one production: it re-renders every production (the
  library is part of every render's cache key) and forces new visual reviews.
- Never print or write `ELEVENLABS_API_KEY` (it lives in the gitignored `.env`).
- Code-only repo: `cache/`, `build/`, `output/`, media files and `.env` are gitignored.
  `productions/<slug>/` (production.toml, inputs, narration.json, scenes) is tracked.
- Tests: `.venv/bin/python -m unittest discover -s tests -v` (the offline pipeline test
  renders a tiny production with the tone test voices, ~30 s, including a dub).
