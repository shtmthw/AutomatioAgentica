# GEMINI.md

This repository is **AutomatioAgentica**, the video production pipeline behind every video
on [@anon14none](https://www.youtube.com/@anon14none). Its harness contract is shared by
every agent harness and lives in **AGENTS.md** (imported below). The production playbook is
[ANIMINFO.md](ANIMINFO.md); scene writing is in [docs/SCENE_AUTHORING.md](docs/SCENE_AUTHORING.md).

Call the pipeline as `.venv/bin/python -m automatio ...` from the repository root. A full
`run` takes 15–25 minutes; it is resumable, so a timeout is harmless: run it again.

@./AGENTS.md
