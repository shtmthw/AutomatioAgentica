"""MCP server: the AutomatioAgentica pipeline as tools for any MCP client.

    .venv/bin/python -m automatio.mcp_server          (inside the repository)
    .venv/bin/python scripts/mcp_server.py            (from anywhere; what client configs use)
    .venv/bin/python -m automatio mcp-config          (prints the config for your client)

Every tool runs the same CLI as a shell harness would (`python -m automatio ... --json`) in a
subprocess, so state, cache, run lock and checks are shared: a production started from the
CLI can be continued over MCP and back. Nothing here changes how a stage behaves.

Long work never blocks a tool call. `run` and `preview` start a background job and wait up to
`wait_seconds` (default 45, below the ~60 s limit some clients put on a tool call), then
return either the result or `{"state": "running", "job_id": ...}`; call `wait` to keep
waiting. A job runs in its own session, so closing the client does not kill a 20-minute
render; `stop_run` stops it (the run resumes later from where it stopped).

For clients without a shell or file tools, the server also gives scoped file access: read
anything in the repository except credentials and caches, write only a production's
`narration.json`, `production.toml` and `scenes/`. Contact sheets and video frames come
back as images.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field

from . import ROOT, __version__, build_root, cache_root, local_dir, output_root, productions_dir
from .secrets import env_file, redact

try:
    import anyio
    from mcp.server.mcpserver import Context, Elicit, ElicitationResult, Image, MCPServer, Resolve
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations
except ImportError as e:                                    # pragma: no cover - reported to the user
    raise SystemExit("The MCP server needs the `mcp` package: "
                     "uv pip install --python .venv/bin/python -r pyproject.toml --extra mcp") from e

CHANNEL = "https://www.youtube.com/@anon14none"
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")
DEFAULT_WAIT = 45.0
MAX_WAIT = 600.0
MAX_READ = 400_000                       # characters per read_file call
DOCS = {"AGENTS.md": "The harness contract: the loop, approval, agent tasks, production rules and guidelines.",
        "docs/SCENE_AUTHORING.md": "How to write a Manim VoiceScene in the house style.",
        "ANIMINFO.md": "Production playbook: what worked and failed in every episode so far.",
        "README.md": "Overview, setup, deliverables.",
        "local/GUIDELINES.md": "This operator's own standing directions (only if the file exists)."}

INSTRUCTIONS = f"""AutomatioAgentica turns a script and a production plan into finished long-form videos
(Hindi and English, Manim animation, fixed house voices, separate subtitle files). Every video on
{CHANNEL} was made with it. You are the harness: the pipeline does the deterministic work and hands
creative work (translation, scene authoring, visual review) to you as agent tasks.

Start: `doctor`, then read AGENTS.md (read_file or the automatio://docs resources) and, if it exists,
local/GUIDELINES.md. New video: the user supplies a script AND a production plan (ask for a missing
one; never write a plan yourself) -> `new_production`. Then loop `run` and act on `state`:
- running: call `wait` with the job_id (renders take 15-25 min for a full video; resuming is safe).
- needs_approval: show the user approval.config and approval.estimate and ASK. Call `approve` only
  after their explicit yes, with `by` = who approved. Never approve on your own.
- needs_agent: `get_task`, do the work (read_file / write_file / edit_file or your own file tools),
  run the task's check (`check`), then `run` again. Scenes: `preview` and LOOK at every contact sheet.
- blocked: tell the user error.message and error.remedy exactly. Never invent credentials.
- failed: read error (log tail), fix what is yours (scenes, narration), `run` again.
- locked: a run is already going: `wait` with the slug.
- done: report from `report`.

Outcomes and task files name CLI commands such as `python -m automatio check scenes <slug>`. Each has
a matching tool (check, complete_review, preview, approve, run, status, ...); fields ending in `_mcp`
give the exact tool call. If you cannot see images, say that the visual review was not done by eye.
Voices are fixed per production: never change voice profiles or pass other voices."""

server = MCPServer(name="automatio", title="AutomatioAgentica", instructions=INSTRUCTIONS, version=__version__,
                   website_url=CHANNEL, log_level="WARNING")

RO = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)


# ------------------------------------------------------------------ CLI subprocesses
def _check_slug(slug: str) -> str:
    if not SLUG.fullmatch(slug or ""):
        raise ToolError(f"invalid production slug {slug!r}: lowercase letters, digits and dashes")
    return slug


def _cli_argv(*args: str) -> list[str]:
    return [sys.executable, "-m", "automatio", *args, "--json"]


def _parse(stdout: str, stderr: str, code: int | None) -> dict:
    try:
        d = json.loads(stdout)
    except json.JSONDecodeError:
        d = {"ok": False, "state": "failed", "error": {
            "code": "no_json", "message": "the CLI did not return JSON",
            "details": {"stdout_tail": redact(stdout[-1500:]), "stderr_tail": redact(stderr[-3000:])}}}
    if code is not None:
        d["exit_code"] = code
    return annotate(d)


async def cli(*args: str) -> dict:
    """Run a short CLI command and return its JSON object."""
    def go():
        return subprocess.run(_cli_argv(*args), cwd=ROOT, capture_output=True, text=True)
    cp = await anyio.to_thread.run_sync(go)
    return _parse(cp.stdout, cp.stderr, cp.returncode)


_CMD = re.compile(r"python -m automatio [^`\n;#|]+")


def tool_for(command: str) -> dict | None:
    """The MCP tool call for a CLI command line (`python -m automatio check scenes ep05`)."""
    try:
        argv = shlex.split(command)
    except ValueError:
        return None
    if argv[:3] != ["python", "-m", "automatio"] or len(argv) < 4:
        return None
    sub, rest = argv[3], argv[4:]
    pos, opts, i = [], {}, 0
    while i < len(rest):
        if rest[i].startswith("--"):
            k = rest[i][2:]
            v = rest[i + 1] if i + 1 < len(rest) and not rest[i + 1].startswith("--") else True
            opts.setdefault(k, []).append(v)
            i += 2 if v is not True else 1
        else:
            pos.append(rest[i])
            i += 1
    one = {k: v[-1] for k, v in opts.items()}
    if sub in ("status", "next", "task", "report", "estimate") and pos:
        return {"tool": {"next": "next_step", "task": "get_task"}.get(sub, sub), "arguments": {"slug": pos[0]}}
    if sub == "run" and pos:
        args = {"slug": pos[0]}
        if isinstance(one.get("lang"), str):
            args["langs"] = one["lang"]
        for k in ("until", "only"):
            if isinstance(one.get(k), str):
                args[k] = one[k]
        if opts.get("force"):
            args["force"] = [v for v in opts["force"] if isinstance(v, str)]
        return {"tool": "run", "arguments": args}
    if sub == "approve" and pos:
        budget = {}
        for spec in opts.get("budget", []):
            if isinstance(spec, str) and "=" in spec:
                k, _, v = spec.partition("=")
                try:
                    budget[k] = float(v)
                except ValueError:
                    pass
        return {"tool": "approve", "arguments": {"slug": pos[0], "budget": budget, "by": "<who approved>",
                                                 "confirmed_by_user": "<true only after the user said yes>"}}
    if sub == "check" and len(pos) >= 2:
        return {"tool": "check", "arguments": {"slug": pos[1], "what": pos[0]}}
    if sub == "complete" and len(pos) >= 2:
        return {"tool": "complete_review", "arguments": {"slug": pos[1], "notes": "<what you checked and fixed>"}}
    if sub == "preview" and len(pos) >= 2:
        args = {"slug": pos[0], "sections": pos[1]}
        if isinstance(one.get("lang"), str):
            args["lang"] = one["lang"]
        for k in ("hq", "audio", "paid"):
            if one.get(k) is True:
                args[k] = True
        return {"tool": "preview", "arguments": args}
    return None


def annotate(obj: Any) -> Any:
    """Add `<key>_mcp` next to every string that names CLI commands: the matching tool call(s)."""
    if isinstance(obj, list):
        return [annotate(x) for x in obj]
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        out[k] = annotate(v)
        if isinstance(v, str) and "python -m automatio" in v:
            calls = [c for c in (tool_for(m.strip().rstrip(".,)")) for m in _CMD.findall(v)) if c]
            if calls:
                out[f"{k}_mcp"] = calls[0] if len(calls) == 1 else calls
    return out


def dumps(obj: Any) -> str:
    return redact(json.dumps(obj, ensure_ascii=False, indent=1, default=str))


# ------------------------------------------------------------------ background jobs
def _jobs_dir() -> Path:
    d = build_root() / ".mcp" / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


_PROCS: dict[str, subprocess.Popen] = {}


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _job_done(job: dict) -> bool:
    p = _PROCS.get(job["id"])
    if p is not None:
        return p.poll() is not None
    return not _alive(job["pid"])


def start_job(kind: str, slug: str, args: list[str]) -> dict:
    jid = f"{kind}-{slug}-{time.strftime('%Y%m%dT%H%M%S')}-{os.urandom(2).hex()}"
    d = _jobs_dir()
    out, err = d / f"{jid}.out", d / f"{jid}.err"
    with open(out, "wb") as fo, open(err, "wb") as fe:
        p = subprocess.Popen(_cli_argv(*args), cwd=ROOT, stdout=fo, stderr=fe, stdin=subprocess.DEVNULL,
                             start_new_session=True)      # survives the client closing the server
    job = {"id": jid, "kind": kind, "slug": slug, "args": args, "pid": p.pid, "started": time.time(),
           "out": str(out), "err": str(err)}
    (d / f"{jid}.json").write_text(json.dumps(job), encoding="utf-8")
    _PROCS[jid] = p
    return job


def load_job(jid: str) -> dict:
    if not re.fullmatch(r"[a-z]+-[a-z0-9-]+-\d{8}T\d{6}-[0-9a-f]{4}", jid or ""):
        raise ToolError(f"unknown job id {jid!r}")
    f = _jobs_dir() / f"{jid}.json"
    if not f.exists():
        raise ToolError(f"unknown job id {jid!r}")
    return json.loads(f.read_text(encoding="utf-8"))


def active_job(kind: str, slug: str, args: list[str] | None = None) -> dict | None:
    """A job of this kind for this production that is still running (started by any server);
    with `args`, only one running exactly that command."""
    for f in sorted(_jobs_dir().glob(f"{kind}-{slug}-*.json"), reverse=True):
        job = json.loads(f.read_text(encoding="utf-8"))
        if job.get("slug") == slug and not _job_done(job) and (args is None or job.get("args") == args):
            return job
    return None


def job_result(job: dict) -> dict:
    p = _PROCS.pop(job["id"], None)
    code = p.returncode if p is not None else None
    out = Path(job["out"]).read_text(encoding="utf-8", errors="replace")
    err = Path(job["err"]).read_text(encoding="utf-8", errors="replace")
    d = _parse(out, err, code)
    d["job_id"] = job["id"]
    return d


def progress(slug: str) -> dict | None:
    try:
        return json.loads((build_root() / slug / "progress.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def lock_holder(slug: str) -> dict | None:
    try:
        d = json.loads((build_root() / slug / "run.lock").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return d if _alive(int(d.get("pid", -1))) else None


async def _wait_until(done, slug: str, seconds: float, ctx: Context | None) -> bool:
    end = time.monotonic() + max(0.0, min(seconds, MAX_WAIT))
    while not done():
        if time.monotonic() >= end:
            return False
        pr = progress(slug)
        if ctx is not None and pr:
            try:
                await ctx.report_progress(float(pr.get("done") or 0), float(pr.get("total") or 0) or None,
                                          f"{pr.get('stage')} {pr.get('detail', '')}".strip())
            except Exception:
                pass
        await anyio.sleep(1.0)
    return True


def _running(job: dict) -> dict:
    return {"ok": False, "state": "running", "job_id": job["id"], "kind": job["kind"], "production": job["slug"],
            "elapsed_s": round(time.time() - job["started"]), "progress": progress(job["slug"]),
            "next": f"call wait(job_id={job['id']!r}) to keep waiting; resuming after an interruption is safe"}


async def finish_or_running(job: dict, wait_seconds: float, ctx: Context | None) -> dict:
    if await _wait_until(lambda: _job_done(job), job["slug"], wait_seconds, ctx):
        return job_result(job)
    return _running(job)


# ------------------------------------------------------------------ file access
_DENY_PARTS = {".git", ".venv", "__pycache__", ".ruff_cache", "node_modules"}


def _roots() -> list[Path]:
    return [ROOT, productions_dir(), build_root(), output_root(), local_dir()]


def _resolve(path: str) -> Path:
    p = Path(path).expanduser()
    p = (p if p.is_absolute() else ROOT / p).resolve()
    if not any(p == r.resolve() or r.resolve() in p.parents for r in _roots()):
        raise ToolError(f"{path}: outside the repository and the pipeline folders")
    return p


def readable(path: str) -> Path:
    p = _resolve(path)
    if p == env_file().resolve() or p.name.startswith(".env") and p.name != ".env.example":
        raise ToolError("credential files are never read through MCP")
    if any(part in _DENY_PARTS for part in p.parts) or cache_root().resolve() in [p, *p.parents]:
        raise ToolError(f"{path}: not readable through MCP (repository internals or caches)")
    return p


def writable(path: str) -> Path:
    """Only the agent-authored files of a production: narration.json, production.toml, scenes/**."""
    p = _resolve(path)
    prod = productions_dir().resolve()
    try:
        relp = p.relative_to(prod)
    except ValueError:
        raise ToolError(f"{path}: writes are limited to productions/<slug>/narration.json, production.toml "
                         "and scenes/") from None
    parts = relp.parts
    if len(parts) < 2 or not SLUG.fullmatch(parts[0]):
        raise ToolError(f"{path}: not inside a production folder")
    ok = (len(parts) == 2 and parts[1] in ("narration.json", "production.toml")) or \
         (len(parts) >= 3 and parts[1] == "scenes" and p.suffix in (".py", ".md", ".json"))
    if not ok:
        raise ToolError(f"{path}: writes are limited to narration.json, production.toml and scenes/*.py "
                         "(inputs are the user's; outputs are the pipeline's)")
    return p


def _rel(p: Path) -> str:
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


IMAGE_EXT = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}


def image_of(path: str) -> Image:
    p = readable(path)
    if p.suffix.lower() not in IMAGE_EXT or not p.is_file():
        raise ToolError(f"{path}: not an image file (png/jpg/webp)")
    return Image(data=p.read_bytes(), format=IMAGE_EXT[p.suffix.lower()])


# ------------------------------------------------------------------ tools: environment and productions
@server.tool(annotations=RO, structured_output=False)
async def doctor(online: bool = False) -> str:
    """Check what this machine can do: tools, fonts, packages, credentials (presence only), providers.
    online=True also contacts the voice providers (no credits are spent). Run it first in a new session
    and report every failing item with its remedy."""
    return dumps(await cli("doctor", *(["--online"] if online else [])))


@server.tool(annotations=RO, structured_output=False)
async def list_productions() -> str:
    """List the productions in this checkout (slug, title, versions, whether it has been delivered).
    Use status(slug) for the stage table of one."""
    rows = []
    d = productions_dir()
    for p in sorted(d.glob("*/production.toml")):
        try:
            cfg = tomllib.loads(p.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as e:
            rows.append({"slug": p.parent.name, "error": str(e)})
            continue
        slug = p.parent.name
        vers = {l: {"voice": v.get("voice"), "mode": v.get("mode", "full")} for l, v in cfg.get("versions", {}).items()}
        rows.append({"slug": slug, "title": cfg.get("production", {}).get("title"), "versions": vers,
                     "scenes": len(list((p.parent / "scenes").glob("*.py"))),
                     "delivered": (output_root() / slug / "manifest.json").exists(),
                     "running": bool(lock_holder(slug))})
    return dumps({"ok": True, "productions_dir": _rel(d), "productions": rows})


@server.tool(annotations=RO, structured_output=False)
async def status(slug: str) -> str:
    """Stage table, progress of a running run, approval and credits spent for one production, plus `next`."""
    return dumps(await cli("status", _check_slug(slug)))


@server.tool(annotations=RO, structured_output=False)
async def next_step(slug: str) -> str:
    """The single next action for the harness (read-only; `run` does the work)."""
    return dumps(await cli("next", _check_slug(slug)))


@server.tool(annotations=RO, structured_output=False)
async def get_task(slug: str) -> str:
    """The waiting agent task: its metadata (id, check, then) and the full Markdown instructions."""
    return dumps(await cli("task", _check_slug(slug)))


@server.tool(annotations=RO, structured_output=False)
async def voices() -> str:
    """The voice profiles (house voices from voices.toml plus any local/voices.toml profiles)."""
    return dumps(await cli("voices"))


@server.tool(annotations=RO, structured_output=False)
async def estimate(slug: str) -> str:
    """Paid voice credits the remaining work of a production needs (cached lines are free)."""
    return dumps(await cli("estimate", _check_slug(slug)))


@server.tool(annotations=RO, structured_output=False)
async def report(slug: str) -> str:
    """The production report (Markdown): deliverables, verification per version, chapters and topics,
    warnings and what was not verified. Base your final report to the user on it."""
    return dumps(await cli("report", _check_slug(slug)))


@server.tool(annotations=WRITE, structured_output=False)
async def new_production(slug: str, title: str,
                         script_path: str = "", plan_path: str = "",
                         script_text: str = "", plan_text: str = "",
                         notes_paths: list[str] | None = None, notes_texts: list[str] | None = None,
                         dub: list[str] | None = None, languages: str = "",
                         replace_inputs: bool = False) -> str:
    """Create a production from the user's script and production plan (both required, Markdown or text).
    Give each as a file path on this machine or as the full text. Never write the plan yourself.
    dub=["hi"] makes Hindi a voice-over on the English master's timeline (one video plus a dub).
    languages defaults to "hi,en". Voices are the defaults (house voices, or local/voices.toml) and are
    not chosen here."""
    _check_slug(slug)
    tmp = build_root() / ".mcp" / "inputs" / slug
    def source(path: str, text: str, name: str) -> str:
        if path and text:
            raise ToolError(f"give {name} as a path or as text, not both")
        if text:
            tmp.mkdir(parents=True, exist_ok=True)
            f = tmp / f"{name}.md"
            f.write_text(text, encoding="utf-8")
            return str(f)
        if not path:
            raise ToolError(f"the {name} is required (ask the user for it; never write it yourself)")
        return str(Path(path).expanduser())
    args = ["new", slug, "--script", source(script_path, script_text, "script"),
            "--plan", source(plan_path, plan_text, "plan"), "--title", title]
    for i, n in enumerate(notes_paths or []):
        args += ["--notes", str(Path(n).expanduser())]
    for i, t in enumerate(notes_texts or []):
        args += ["--notes", source("", t, f"notes-{i + 1}")]
    for d in dub or []:
        args += ["--dub", d]
    if languages:
        args += ["--languages", languages]
    if replace_inputs:
        args.append("--force")
    return dumps(await cli(*args))


# ------------------------------------------------------------------ tools: the loop
@server.tool(annotations=WRITE, structured_output=False)
async def run(slug: str, langs: str = "", until: str = "", only: str = "", force: list[str] | None = None,
              wait_seconds: float = DEFAULT_WAIT, ctx: Context | None = None) -> str:
    """Run the pipeline until it is done or needs something (resumable; finished work is kept).
    Starts a background job, or attaches to this production's job if one is running, and waits up to
    wait_seconds. Returns the outcome (state done / needs_approval / needs_agent / blocked / failed /
    locked) or state "running" with a job_id for `wait`. langs="en" produces only some versions while
    another is blocked. A full video takes 15-25 minutes."""
    _check_slug(slug)
    job = active_job("run", slug)
    if job is None:
        if (h := lock_holder(slug)) is not None:
            return dumps({"ok": False, "state": "locked", "production": slug, "holder": h,
                          "progress": progress(slug),
                          "next": f"a run started outside this server is in progress: call wait(slug={slug!r})"})
        args = ["run", slug]
        if langs:
            args += ["--lang", langs]
        if until:
            args += ["--until", until]
        if only:
            args += ["--only", only]
        for f in force or []:
            args += ["--force", f]
        job = start_job("run", slug, args)
    return dumps(await finish_or_running(job, wait_seconds, ctx))


@server.tool(annotations=RO, structured_output=False)
async def wait(job_id: str = "", slug: str = "", wait_seconds: float = DEFAULT_WAIT,
               ctx: Context | None = None) -> list:
    """Keep waiting for a job from `run` or `preview` (job_id), or for a run of a production started
    elsewhere (slug). Returns the result when it finishes (a preview with its contact sheets),
    otherwise state "running" again."""
    if job_id:
        job = load_job(job_id)
        res = await finish_or_running(job, wait_seconds, ctx)
        return _with_sheets(res, True) if job["kind"] == "preview" else [dumps(res)]
    _check_slug(slug)
    if (job := active_job("run", slug)) is not None:
        return [dumps(await finish_or_running(job, wait_seconds, ctx))]
    if await _wait_until(lambda: lock_holder(slug) is None, slug, wait_seconds, ctx):
        return [dumps({"ok": True, "state": "idle", "production": slug, "next_step": await cli("next", slug)})]
    return [dumps({"ok": False, "state": "running", "production": slug, "holder": lock_holder(slug),
                   "progress": progress(slug), "next": f"call wait(slug={slug!r}) to keep waiting"})]


@server.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=False),
             structured_output=False)
async def stop_run(slug: str) -> str:
    """Stop the run (or preview) of a production that is in progress. Finished work is kept and the next
    `run` resumes where it stopped. Only when the user asks to stop."""
    _check_slug(slug)
    h = lock_holder(slug)
    if not h:
        return dumps({"ok": True, "stopped": None, "message": "nothing is running for this production"})
    cmd = str(h.get("command", ""))
    if not (cmd.startswith("run") or cmd.startswith("preview")):
        raise ToolError(f"the lock holder is not a run or preview ({cmd!r}); not stopping it")
    os.kill(int(h["pid"]), signal.SIGTERM)
    return dumps({"ok": True, "stopped": h, "message": "SIGTERM sent; the run stops after cleaning up"})


class Approval(BaseModel):
    approve: bool = Field(description="Approve this configuration and paid-voice budget?")
    name: str = Field(default="", description="Your name, recorded as the approver")


def _can_ask(ctx: Context) -> bool:
    """Whether this client can show the user a question mid-call (MCP elicitation)."""
    caps = ctx.client_capabilities
    if caps is None or getattr(caps, "elicitation", None) is None:
        return False
    try:                                   # >= 2026-07-28: asked through an input-required round
        from mcp.server.mcpserver.resolve import _uses_input_required
        if _uses_input_required(ctx.protocol_version):
            return True
    except Exception:
        pass
    return bool(getattr(ctx.session, "can_send_request", False))


async def _approval_question(slug: str, confirmed_by_user: bool, ctx: Context) -> Elicit[Approval] | None:
    """Ask the user directly when the client can; None means the conversation's yes stands."""
    if not confirmed_by_user or not _can_ask(ctx):
        return None
    ap = (await cli("next", _check_slug(slug))).get("approval") or {}
    msg = (f"Approve production {slug!r}?\n\nConfiguration: "
           + json.dumps(ap.get("config", {}), ensure_ascii=False, default=str)[:1500]
           + "\n\nPaid voice estimate: " + (json.dumps(ap.get("estimate"), ensure_ascii=False)
                                            if ap.get("estimate") else "none (free voices or all cached)"))
    return Elicit(msg, Approval)


@server.tool(annotations=WRITE, structured_output=False)
async def approve(slug: str, by: str, confirmed_by_user: bool, budget: dict[str, float] | None = None,
                  note: str = "",
                  answer: Annotated[ElicitationResult[Approval], Resolve(_approval_question)] = None) -> str:
    """Record the user's approval of a production's configuration and paid-voice budget.
    ONLY after the user explicitly approved in the conversation: show them approval.config and
    approval.estimate first, then set confirmed_by_user=true and by=<who approved>.
    budget caps paid credits per provider, e.g. {"elevenlabs": 8000} (use the recommended budget the
    user agreed to). If the client supports it, the server also asks the user directly."""
    _check_slug(slug)
    if not confirmed_by_user:
        return dumps({"ok": False, "state": "not_approved",
                      "message": "Ask the user first: show approval.config and approval.estimate and wait for an "
                                 "explicit yes. Then call approve with confirmed_by_user=true."})
    asked = answer is not None and not (getattr(answer, "action", "") == "accept" and answer.data is None)
    if asked:
        if answer.action != "accept" or not answer.data.approve:
            return dumps({"ok": False, "state": "not_approved", "asked_user_directly": True,
                          "message": "the user did not approve"})
        by = answer.data.name.strip() or by
    args = ["approve", slug, "--by", by]
    for k, v in (budget or {}).items():
        args += ["--budget", f"{k}={v:g}"]
    if note:
        args += ["--note", note]
    out = await cli(*args)
    out["asked_user_directly"] = asked
    return dumps(out)


@server.tool(annotations=RO, structured_output=False)
async def check(slug: str, what: str) -> str:
    """Validate agent work without running the pipeline. what: translate | scenes | narration | dub.
    Run it until it shows no errors before calling `run` again. `dub` forecasts whether a dub fits
    its master's timeline before any credits are spent."""
    if what not in ("translate", "scenes", "narration", "dub"):
        raise ToolError("what must be translate, scenes, narration or dub")
    return dumps(await cli("check", what, _check_slug(slug)))


@server.tool(annotations=WRITE, structured_output=False)
async def complete_review(slug: str, notes: str) -> str:
    """Mark the visual review done, after you LOOKED at every contact sheet (preview / view_image) and
    fixed what was wrong. notes: what you checked and fixed (at least a sentence)."""
    return dumps(await cli("complete", "review", _check_slug(slug), "--notes", notes))


@server.tool(annotations=WRITE, structured_output=False)
async def preview(slug: str, sections: str, lang: str = "", hq: bool = False, audio: bool = False,
                  paid: bool = False, include_images: bool = True, wait_seconds: float = DEFAULT_WAIT,
                  ctx: Context | None = None) -> list:
    """Render sections (e.g. "s05" or "s01,s02") at 480p and return their contact sheets as images
    (one frame per narration line). lang: hi / en / all; a dub language builds the dub of those sections
    over the master's picture instead (cached paid clips + free draft voice). paid=True voices missing
    dub lines with the paid voice within the approved budget: only when the user asks. May return
    state "running" with a job_id for `wait`."""
    _check_slug(slug)
    if not re.fullmatch(r"[a-z0-9_]+(,[a-z0-9_]+)*", sections):
        raise ToolError("sections: section keys like s05 or s01,s02")
    args = ["preview", slug, sections]
    if lang:
        args += ["--lang", lang]
    for flag, on in (("--hq", hq), ("--audio", audio), ("--paid", paid)):
        if on:
            args.append(flag)
    job = active_job("preview", slug, args) or start_job("preview", slug, args)
    res = await finish_or_running(job, wait_seconds, ctx)
    return _with_sheets(res, include_images)


def _with_sheets(res: dict, include_images: bool) -> list:
    parts: list = [dumps(res)]
    if include_images:
        for pv in res.get("previews") or []:
            if pv.get("sheet"):
                try:
                    parts += [f"contact sheet {pv['section']} [{pv['lang']}]: {pv['sheet']}", image_of(pv["sheet"])]
                except (ToolError, OSError) as e:
                    parts.append(f"(could not attach {pv['sheet']}: {e})")
    return parts


@server.tool(annotations=RO, structured_output=False)
async def view_image(path: str) -> list:
    """Return an image file (contact sheet, thumbnail, extracted frame) so you can look at it.
    path is relative to the repository (e.g. build/<slug>/preview/en/s05_sheet.jpg) or absolute."""
    return [_rel(readable(path)), image_of(path)]


@server.tool(annotations=RO, structured_output=False)
async def video_frame(path: str, seconds: float) -> list:
    """Extract one full-resolution frame of a video (e.g. output/<slug>/english/final-video.mp4) at
    `seconds` and return it as an image. Check finished videos at full resolution, not only the 480p
    contact sheets: small text, overlaps and glitches show up here."""
    src = readable(path)
    if not src.is_file() or src.suffix.lower() not in (".mp4", ".mov", ".mkv", ".webm"):
        raise ToolError(f"{path}: not a video file")
    out_dir = build_root() / ".mcp" / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{src.stem}_{seconds:09.3f}.png"
    def go():
        return subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{seconds:.3f}", "-i", str(src),
                               "-frames:v", "1", str(out)], capture_output=True, text=True)
    cp = await anyio.to_thread.run_sync(go)
    if cp.returncode != 0 or not out.exists():
        raise ToolError(f"ffmpeg could not extract a frame at {seconds}s: {cp.stderr[-500:]}")
    return [f"{_rel(src)} at {seconds:.3f}s -> {_rel(out)}", image_of(str(out))]


@server.tool(annotations=WRITE, structured_output=False)
async def say(texts: list[str], voice: str, allow_paid: bool = False, ctx: Context | None = None) -> str:
    """Audition text in a voice profile (writes output/samples/*). Profiles on a paid provider
    (ElevenLabs) spend credits: set allow_paid=true only when the user asked to hear the paid voice."""
    from .config import load_voices
    prof = load_voices().get(voice)
    if prof is None:
        raise ToolError(f"unknown voice {voice!r}; see voices()")
    if prof.provider == "elevenlabs" and not allow_paid:
        chars = sum(len(t) for t in texts)
        return dumps({"ok": False, "state": "not_run",
                      "message": f"{voice} is a paid voice (~{chars} credits). Ask the user, then call again "
                                 "with allow_paid=true."})
    return dumps(await cli("say", *texts, "--voice", voice))


@server.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=False),
             structured_output=False)
async def clean(slug: str, reset_state: bool = False) -> str:
    """Remove a production's temporary files (tmp/, preview/). reset_state=True also deletes its build
    state (approval, stage results; the cache and output/ are kept): only when the user asks."""
    args = ["clean", _check_slug(slug)] + (["--build"] if reset_state else [])
    return dumps(await cli(*args))


# ------------------------------------------------------------------ tools: files (for clients without their own)
@server.tool(annotations=RO, structured_output=False)
async def list_files(path: str = ".", pattern: str = "*") -> str:
    """List files under a folder of the repository (e.g. productions/agentic-ai-intro/scenes), with a
    glob pattern ("*.py", "**/*.jpg"). Credentials, caches and .git are never listed."""
    base = readable(path)
    if not base.is_dir():
        raise ToolError(f"{path}: not a folder")
    rows = []
    for p in sorted(base.glob(pattern)):
        try:
            readable(str(p))
        except ToolError:
            continue
        rows.append(_rel(p) + ("/" if p.is_dir() else f"  ({p.stat().st_size} B)"))
        if len(rows) >= 500:
            rows.append("... (truncated at 500)")
            break
    return "\n".join(rows) or "(empty)"


@server.tool(annotations=RO, structured_output=False)
async def read_file(path: str, offset: int = 0, limit: int = 0) -> str:
    """Read a text file of the repository: AGENTS.md, docs/SCENE_AUTHORING.md, task files under
    build/<slug>/tasks/, a production's narration.json and scenes, agentic_video/*.py (the component
    library), reports. offset/limit select lines (0 = from the start / to the end)."""
    p = readable(path)
    if not p.is_file():
        raise ToolError(f"{path}: not a file")
    text = p.read_text(encoding="utf-8", errors="replace")
    if offset or limit:
        lines = text.splitlines(keepends=True)
        text = "".join(lines[offset: offset + limit if limit else None])
    if len(text) > MAX_READ:
        text = text[:MAX_READ] + f"\n... (truncated; use offset/limit, the file has {len(text)} characters)"
    return redact(text)


@server.tool(annotations=WRITE, structured_output=False)
async def write_file(path: str, content: str) -> str:
    """Write a production's agent-authored file: productions/<slug>/narration.json, production.toml or
    scenes/<file>.py. Inputs (the user's script and plan), outputs and the shared library are not
    writable. Run the matching check afterwards."""
    p = writable(path)
    try:                                                     # never leave a file the pipeline cannot read
        if p.name == "narration.json":
            json.loads(content)
        if p.name == "production.toml":
            tomllib.loads(content)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError) as e:
        raise ToolError(f"{_rel(p)}: not valid {p.suffix[1:].upper()}, nothing written: {e}") from None
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(p)
    return f"wrote {_rel(p)} ({len(content)} characters)"


@server.tool(annotations=WRITE, structured_output=False)
async def edit_file(path: str, old: str, new: str, replace_all: bool = False) -> str:
    """Replace exact text in a writable production file (see write_file). `old` must occur exactly once
    unless replace_all=true; nothing is written if it does not match."""
    p = writable(path)
    text = p.read_text(encoding="utf-8")
    n = text.count(old)
    if n == 0:
        raise ToolError(f"{_rel(p)}: `old` not found; nothing changed")
    if n > 1 and not replace_all:
        raise ToolError(f"{_rel(p)}: `old` occurs {n} times; make it unique or set replace_all=true")
    out = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    return await write_file(str(p), out)


# ------------------------------------------------------------------ resources and the prompt
def _doc_resource(relpath: str, desc: str):
    def read() -> str:
        p = ROOT / relpath if not relpath.startswith("local/") else local_dir() / relpath.split("/", 1)[1]
        return p.read_text(encoding="utf-8") if p.exists() else f"({relpath} does not exist in this checkout)"
    server.resource(f"automatio://docs/{relpath}", name=relpath, description=desc, mime_type="text/markdown")(read)


for _path, _desc in DOCS.items():
    _doc_resource(_path, _desc)


@server.prompt(title="Produce a video")
def produce_video(slug: str = "") -> str:
    """Start or continue a production with AutomatioAgentica."""
    target = f"Continue the production `{slug}`." if slug else (
        "Start a new production: ask me for the script and the production plan if I have not given them.")
    return f"""{target}

Work as the harness of AutomatioAgentica (the pipeline behind every video on {CHANNEL}):
1. Call `doctor` and report any failing item with its remedy.
2. Read AGENTS.md and, if it exists, local/GUIDELINES.md. Raise anything in the material that conflicts
   with the production guidelines (e.g. no recap, a coding part that needs a screen recording) before approval.
3. New material: `new_production` with my script and plan (never write the plan yourself).
4. Loop `run` (and `wait` while it is running) until state is done:
   needs_approval -> show me the configuration and estimate and ask; `approve` only after my explicit yes.
   needs_agent -> `get_task`, do the work, run its check until it passes, then `run`.
   Scene work: read docs/SCENE_AUTHORING.md and 2-3 reference scenes, `preview`, look at every sheet.
   blocked -> tell me error.message and error.remedy exactly; offer `run` with langs=<others> if hinted.
5. When done: report from `report` (videos, durations, subtitles, chapters and topics per version,
   verification table with every warn/fail, credits spent, what was not verified).
"""


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
