# AutomatioAgentica

> **Every video on the [@anon14none](https://www.youtube.com/@anon14none) YouTube channel was
> made with this pipeline.** Each episode went from a script and a production plan to the
> finished MP4s, subtitle files, chapters and thumbnail through AutomatioAgentica, driven by an
> AI agent. The pipeline is open source (MIT); the episodes themselves are copyrighted
> (see [License](#license)).

**An agent-driven, end-to-end video production pipeline.** Give a connected agent harness
(Claude Code, Codex, Cursor, Gemini CLI, Claude Desktop, or any MCP client) a **script** and a
**production plan**. AutomatioAgentica turns them into finished long-form lessons in **Hindi
and English**: programmatic animation, fixed narrator voices, a broadcast-level mix, and
**separate subtitle files** (never burned in). It also writes chapters, topics and timings for
every version.

```
You ──> Agent harness ──> AutomatioAgentica ──> Manim · ElevenLabs · edge-tts · ffmpeg ──> output/<slug>/
         (CLI or MCP)        │  validate → approve → ingest → translate* → scenes* → draft → review*
                             │  → voice → render → assemble → subtitles → verify → deliver
                             └─ * agent tasks: creative work handed to the agent, then validated
```

The pipeline does all the deterministic work and keeps resumable state. The agent does the
creative steps (Hindi adaptation, scene authoring, visual review) from self-contained task
files. You approve the configuration and any paid voice budget before a credit is spent.

## Made with it: the @anon14none episodes

| episode | slug | shape | state |
|---|---|---|---|
| 01: What is Agentic AI? | `agentic-ai-intro` | Hindi + English, full | delivered (Hindi 10:44, English 8:23); the regression reference |
| 02: Inside an AI Agent: Who Actually Runs the Loop? | `ep02-inside-the-agent` | English master + Hindi dub | English delivered (13:17); Hindi dub waits for ElevenLabs credits |
| 03: Context and Memory: How an Agent Handles Long Tasks | `ep03-context-and-memory` | English (Hindi dub planned) | English delivered (13:12) |
| 04: Planning: How an Agent Handles Big Goals | `ep04-planning` | English (Hindi dub planned) | English delivered (13:25) after a polish pass |
| (smoke test) What is a tool call? | `demo-tool-call` | Hindi + English, full | two lines; a live test of the ElevenLabs path |

Their scripts, plans, narration and scene code are in `productions/`, so you can read exactly
how each video was made. They are © anon14none, all rights reserved
([`productions/LICENSE`](productions/LICENSE)): read them to learn the pipeline, then write
your own. The rendered media is not tracked; the videos are on the channel.

## Use it yourself

### 1. Install (one command)

Linux or macOS (on Windows, use WSL2 with Ubuntu). About 5 GB of free disk space.

```bash
git clone https://github.com/shtmthw/AutomatioAgentica.git
cd AutomatioAgentica
scripts/setup.sh
```

The script asks before it installs system packages, then:

1. installs ffmpeg (with libx264 and rubberband), cairo/pango, the fonts Inter, JetBrains Mono
   and Noto Sans Devanagari, and `uv`. It supports pacman, apt, dnf (with RPM Fusion for ffmpeg)
   and Homebrew;
2. creates a Python 3.12 venv in `.venv` (uv downloads Python 3.12 if you don't have it);
3. installs the Python packages, including the MCP SDK;
4. creates `.env` from `.env.example`;
5. runs `doctor` and the offline test suite (~30 s; it renders a tiny video with test tones).

Run it again at any time: it skips what is already there. Options: `--yes` (no questions),
`--skip-system` (Python side only), `--no-tests`. If something is missing, `doctor` names the
exact install command for your machine:

```bash
.venv/bin/python -m automatio doctor            # add --online to also test the voice providers
```

**Credentials:** English needs none. For the Hindi voice, put your ElevenLabs key in `.env`
(`ELEVENLABS_API_KEY=...`). The file is gitignored, and the pipeline never prints or logs the
key.

### 2. Connect your agent harness

**Harnesses with a shell** read the repository's instructions themselves. Open the folder and
talk to the agent:

| harness | how it finds the contract |
|---|---|
| Claude Code | `CLAUDE.md` + the `/produce-video` skill (`.claude/skills/`); `.claude/settings.json` pre-allows the pipeline commands (approval still asks) |
| Codex CLI, Cursor, GitHub Copilot agent mode | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` (imports `AGENTS.md`) |
| anything else with file and process access | point it at `AGENTS.md` |

**MCP clients** (Claude Desktop, or any harness used outside this folder) connect to the
bundled MCP server. Print the config for your client, with this checkout's paths filled in:

```bash
.venv/bin/python -m automatio mcp-config                   # all clients
.venv/bin/python -m automatio mcp-config --client codex    # claude-code | claude-desktop | codex | cursor | vscode | gemini | generic
```

| client | where the config goes |
|---|---|
| Claude Code | `claude mcp add automatio --scope user -- …` (printed), or the repo's `.mcp.json` when you run Claude Code in this folder |
| Claude Desktop | Settings → Developer → Edit Config (`claude_desktop_config.json`) |
| Codex | `~/.codex/config.toml`, `[mcp_servers.automatio]` |
| Cursor | `~/.cursor/mcp.json` or `.cursor/mcp.json` |
| VS Code (Copilot) | `.vscode/mcp.json` or `MCP: Add Server` |
| Gemini CLI | `~/.gemini/settings.json`, `mcpServers` |

Every config has the same shape, a local stdio server:

```json
{ "command": "/path/to/AutomatioAgentica/.venv/bin/python",
  "args": ["/path/to/AutomatioAgentica/scripts/mcp_server.py"] }
```

Restart the client and ask it to run the `doctor` tool. See [The MCP server](#the-mcp-server)
for what it offers.

### 3. Make a video

Write a script (Markdown; `##` headings become sections) and a production plan (what each
section shows, with `TIME: m:ss–m:ss` if you have targets). The episodes in `productions/*/inputs/`
are full examples. Then tell your agent:

> Make a video from `~/videos/ep01/script.md` and `~/videos/ep01/plan.md`, title "My first
> episode". English and Hindi.

The agent creates the production, shows you the configuration and the credit estimate, and
**waits for your yes**. Then it translates, writes the scenes, reviews the contact sheets and
runs until the videos are delivered to `output/<slug>/`, with a `report.md`. A 10-minute video
takes ~15–25 minutes of rendering; everything is resumable, so a closed laptop or a timeout
costs nothing. Other requests that work:

- "English only for now" (or "one English video plus a Hindi voice-over on the same timeline", a dub)
- "Show me section 5 before you continue" (a 480p preview with contact sheets)
- "Let me hear the Hindi dub of sections 1 and 2 first" (dub preview, nothing paid)
- "What's the status of ep05?"

### What it costs

- **English:** free (Microsoft edge-tts voice, no account).
- **Hindi:** ElevenLabs, ≈ 1 credit per character. A 10-minute script is ~7,000–10,000 credits;
  the free plan gave 10,000 a month when these episodes were made. Every paid line is cached and never paid for twice, and the
  approved budget caps spending. A dub's fit is forecast before anything is paid.
  ElevenLabs' free plan has no commercial licence: check their terms before monetising.
- Rendering is local (CPU). No other service is involved.

### Your own voices and guidelines

The house setup is what made the @anon14none videos: Hindi **ElevenLabs Adam** and English
**edge-tts Andrew**, plus the standing guidelines in `AGENTS.md`. To use your own, put them in
the gitignored `local/` folder (see [`local/README.md`](local/README.md)):

```bash
cp local/voices.example.toml local/voices.toml        # your profiles + [defaults] for `new`
cp local/GUIDELINES.example.md local/GUIDELINES.md    # your standing directions
.venv/bin/python -m automatio doctor                  # "local overrides" shows what is active
```

Your profiles get new names (the house profiles can't be redefined), so `git pull` never
conflicts with them and every production records exactly which voice it used.

## The MCP server

`automatio/mcp_server.py` exposes the pipeline as 24 tools. Every tool runs the same CLI a
shell harness would, so a production started from the CLI can be continued over MCP and back.

| group | tools |
|---|---|
| environment | `doctor`, `voices`, `list_productions` |
| the loop | `new_production` (script and plan as paths or text), `run`, `wait`, `stop_run`, `status`, `next_step`, `get_task`, `check`, `approve`, `complete_review`, `estimate`, `report` |
| looking | `preview` (contact sheets as images), `view_image`, `video_frame` (full-resolution frame of a video) |
| files | `list_files`, `read_file`, `write_file`, `edit_file` (for clients without their own) |
| other | `say` (audition a voice; paid voices need `allow_paid`), `clean` |

- **Long work never blocks a call.** `run` and `preview` start a background job and return
  `state: "running"` with a `job_id` after `wait_seconds` (default 45, below the ~60 s limit
  some clients set). `wait` continues. Jobs keep running if the client closes.
- **Approval stays yours.** `approve` requires `confirmed_by_user`, and when the client
  supports MCP elicitation the server asks you directly. A decline there can't be overridden.
- **Scoped file access.** Reads cover the repository except `.env`, caches and `.git`.
  Writes are limited to a production's `narration.json`, `production.toml` and `scenes/`. The
  script and plan stay yours, and outputs stay the pipeline's.
- Resources `automatio://docs/...` serve `AGENTS.md`, the scene guide and the playbook. The
  prompt `produce_video` starts the loop.

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

## What you supply, what you get

**Supply:** a script (Markdown or text; `##` headings become sections), a production plan
(free-form Markdown; numbered sections with `TIME: m:ss–m:ss` are picked up), optional
notes, and (for Hindi) the API key.

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

## The house voices (exact, identical in every @anon14none video)

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
                    subtitles, assemble, dub (+ preview), forecast, verify, deliver, tasks, doctor,
                    secrets, mcp_server
agentic_video/      visual library: style, components, icons, internals (Episode 02 building blocks),
                    VoiceScene (+ runtime)
productions/<slug>/ production.toml, inputs/ (script, plan, notes), narration.json, scenes/
                    (ep03: scenes/memory_kit.py; ep04: scenes/plan_kit.py)
                    the @anon14none episodes are all rights reserved (productions/LICENSE)
scripts/            setup.sh (one-command install), mcp_server.py (MCP launcher for client configs)
tools/              voice_pauses.py: caps overlong pauses inside free-voice narration clips
local/              your own voices and guidelines (gitignored except README and examples)
voices.toml         voice registry (the house voices)
docs/               SCENE_AUTHORING.md (for agents writing scenes)
tests/              unit tests, offline end-to-end pipeline test, MCP server test
AGENTS.md           the harness contract (CLAUDE.md, GEMINI.md and .claude/skills/ point to it)
.mcp.json           the MCP server for Claude Code in this folder
ANIMINFO.md         production playbook: what worked, what failed, why (Episodes 01 to 04)
CHANGELOG.md        what changed between pipeline versions
```

Tracked: code, `voices.toml`, `productions/*/` (inputs, narration, scenes). Gitignored:
`.env`, `local/*`, `cache/`, `build/`, `output/`, all media.

## Common commands

```bash
.venv/bin/python -m automatio new my-video --script ~/script.md --plan ~/plan.md --title "My video"
.venv/bin/python -m automatio new my-video --script ~/script.md --plan ~/plan.md --dub hi   # English + Hindi dub
.venv/bin/python -m automatio run my-video                    # repeat; the agent handles each stop
.venv/bin/python -m automatio status my-video                 # progress, approval, credits spent
.venv/bin/python -m automatio preview my-video s05 --lang all  # 480p render + contact sheets
.venv/bin/python -m automatio check dub my-video               # will the dub fit? (before paying)
.venv/bin/python -m automatio preview my-video s01,s02 --lang hi   # hear the dub of a few sections
.venv/bin/python -m automatio run my-video --lang en           # produce only some versions
.venv/bin/python -m automatio say "आपने एक AI Agent से कहा" --voice hindi-adam   # audition (paid voice)
.venv/bin/python -m automatio report my-video
.venv/bin/python -m automatio mcp-config                       # MCP client configs for this checkout
.venv/bin/python -m unittest discover -s tests -v              # tests (offline, ~30 s)
```

Every command takes `--json` (one JSON object on stdout) and returns a meaningful exit code:
0 done, 1 failed, 2 usage, 10 needs an agent task, 11 needs approval, 12 blocked, 13 locked.

## Polishing tools

- **Natural pauses (`tools/voice_pauses.py`).** The English house voice (edge-tts Andrew) is
  deterministic and sometimes holds ~0.5 s at commas and colons or hesitates mid-phrase, which
  sounds halting. The tool shortens only the silence inside each cached clip (comma pauses to
  0.30 s, mid-phrase hesitations to 0.10 s, sentence breaks to 0.60 s; cuts in true silence with
  5 ms crossfades) and shifts the clip's word timings, so cues and subtitles stay exact. Voice,
  speed and pitch are untouched; paid (ElevenLabs) clips are never rewritten. Run it on every
  edge-tts production before calling it final:

  ```bash
  .venv/bin/python tools/voice_pauses.py my-video --dry-run    # what would be cut
  .venv/bin/python tools/voice_pauses.py my-video              # polish, then:
  .venv/bin/python -m automatio run my-video                   # rebuilds what was timed to the old clips
  ```

- **Production kits.** Reusable components live next to the scenes that introduced them, so
  earlier episodes are never re-rendered: `productions/ep03-context-and-memory/scenes/memory_kit.py`
  (`SizedCard`, `SummaryCard`, `Notebook`, `LiveContext`, `CallCounter`, `session_wipe`, and
  `CheckedScene`, which logs any text or cards that stay overlapped for more than 0.6 s) and
  `productions/ep04-planning/scenes/plan_kit.py` (`PlanPanel`, `GoalCard`, `StepRow`,
  `StepCounter`). They belong to the copyrighted productions: later @anon14none episodes
  import them, and your productions get kits of their own.

Pronunciation: add respellings under `[pronunciation.hi]` / `[pronunciation.en]` in
`production.toml` (or the voice profile in `voices.toml`). Subtitles always keep the
written form.

## Contributing and tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The suite is offline: unit tests, an end-to-end run of a tiny production through the harness
protocol (full versions and a dub, real renders with test-tone voices), and the MCP server
driven by an in-memory client. On a fresh clone one test is skipped: it compares against
Episode 01's original media, which is not in the repository. GitHub Actions runs
`scripts/setup.sh` and the suite on a fresh Ubuntu checkout. Read [AGENTS.md](AGENTS.md) and [ANIMINFO.md](ANIMINFO.md) before changing the
pipeline. Changes to `agentic_video/` re-render every production.

## License

Two licenses, one repository (summary in [`NOTICE`](NOTICE)):

| what | license |
|---|---|
| **The pipeline**: `automatio/`, `agentic_video/`, `scripts/`, `tools/`, `tests/`, `docs/`, `local/` examples, `voices.toml`, the harness files and docs | [MIT](LICENSE) © 2026 anon14none: free to use, change and share, including commercially |
| **The @anon14none productions**: `productions/agentic-ai-intro`, `ep02-inside-the-agent`, `ep03-context-and-memory`, `ep04-planning`, `demo-tool-call`, and every video, voice-over, subtitle file and thumbnail rendered from them | © 2026 anon14none, **all rights reserved** ([`productions/LICENSE`](productions/LICENSE)) |

You may read the productions here to learn how the pipeline is used. Copying, adapting or
re-publishing their scripts, narration, scene code or videos needs written permission.
Productions you make yourself are entirely yours. If you publish videos made with the
pipeline, a mention of AutomatioAgentica is appreciated but not required.
