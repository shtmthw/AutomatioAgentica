"""Command line interface - the surface a harness drives.

    python -m automatio doctor [--online]              what this environment can do
    python -m automatio new <slug> --script F --plan F  start a production from your files
    python -m automatio status <slug>                   stage table, progress, approval
    python -m automatio next <slug>                     the single next action for the harness
    python -m automatio run <slug> [--until S] [--only S] [--force S]
    python -m automatio approve <slug> --budget elevenlabs=N [--by NAME]   (after the user approves)
    python -m automatio task <slug>                     print the waiting agent task
    python -m automatio check translate|scenes|narration <slug>
    python -m automatio complete review <slug> --notes "..."
    python -m automatio preview <slug> <section> [--lang hi] [--hq] [--audio]
    python -m automatio say "text" [--voice hindi-adam]
    python -m automatio report <slug> | estimate <slug> | voices | clean <slug>

Every command accepts --json: one JSON object on stdout (logs go to stderr), exit code
0 done, 1 failed, 2 usage, 10 needs_agent, 11 needs_approval, 12 blocked, 13 locked.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from . import __version__, output_root, productions_dir
from .errors import EXIT, AAError, InputError, UsageError, ValidationFailed
from .log import add_file, log, remove, setup
from .secrets import redact
from .util import atomic_write_text, now_iso, rel

ICON = {"done": "✓", "skipped": "–", "failed": "✗", "running": "…", "waiting_agent": "◆", "waiting_approval": "?",
        "pending": "·", "stale": "↻"}


def emit(obj: dict, as_json: bool, text: str | None = None) -> None:
    if as_json:
        print(redact(json.dumps(obj, ensure_ascii=False, indent=1, default=str)))
    elif text is not None:
        print(redact(text))


# ------------------------------------------------------------------ commands
def cmd_doctor(a):
    from .doctor import run_doctor
    r = run_doctor(online=a.online)
    lines = [f"AutomatioAgentica {__version__} - environment check" + (" (online)" if a.online else " (offline; "
             "add --online to contact the providers)")]
    for c in r["checks"]:
        mark = "✓" if c["ok"] and not c.get("warn") else ("!" if c["ok"] else ("✗" if c["critical"] else "!"))
        lines.append(f"  {mark} {c['check']}: {c['detail']}" + (f"\n      -> {c['remedy']}" if c.get("remedy") else ""))
    lines.append("ready" if r["ok"] else "NOT READY: fix the ✗ items above")
    emit(r, a.json, "\n".join(lines))
    return 0 if r["ok"] else EXIT["blocked"]


TEMPLATE = '''# AutomatioAgentica production.
# Defaults reproduce the house style of "What is Agentic AI?" (Nov 2026): Manim
# animation, voice-first timing, -16 LUFS mix with ducked ambient music, 1080p30
# H.264 CRF 17, English subtitles as separate SRT + VTT files (never burned in).
# Change only what this production needs. Voices are profiles from voices.toml.

[production]
title = {title}
source_language = "{source}"
script = "{script}"
plan = "{plan}"
notes = [{notes}]

{versions}
[subtitles]
language = "en"
formats = ["srt", "vtt"]

# [video]   width, height, fps, quality, encoder ("libx264" | "copy"), crf, preset, audio_bitrate
# [audio]   voice_lufs, music_lufs, duck_db, line_gap, limiter_db, music ("ambient" | "none")
# [review]  draft (free low-res draft before paid voices), visual_review (agent checks contact sheets)
# [render]  jobs (parallel Manim processes), timeout
# [pronunciation.hi]  production-specific respellings, e.g. "LLM" = "एल एल एम"
'''
DEFAULT_VOICES = {"hi": "hindi-adam", "en": "english-andrew"}


def cmd_new(a):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.slug):
        raise UsageError("slug must be lowercase letters, digits and dashes (e.g. my-next-video)")
    d = productions_dir() / a.slug
    if (d / "production.toml").exists() and not a.force:
        raise InputError(f"production {a.slug!r} already exists at {rel(d)}",
                         remedy="Pick another slug, or pass --force to replace its inputs (narration and scenes "
                                "are kept).")
    from .config import load_voices
    voices = load_voices()
    langs = [l.strip() for l in a.languages.split(",") if l.strip()]
    chosen = {}
    for spec in a.voice or []:
        l, _, v = spec.partition("=")
        chosen[l] = v
    for l in langs:
        v = chosen.get(l) or DEFAULT_VOICES.get(l)
        if not v or v not in voices:
            raise UsageError(f"no voice for {l!r}: pass --voice {l}=<profile> (profiles: {', '.join(voices)})")
        chosen[l] = v
    inputs = d / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (d / "scenes").mkdir(exist_ok=True)

    def take(src: str, name: str) -> str:
        p = Path(src).expanduser()
        if not p.exists():
            raise InputError(f"file not found: {p}")
        if p.suffix.lower() in (".docx", ".pdf", ".doc", ".odt", ".rtf"):
            raise InputError(f"{p.name}: convert it to Markdown or plain text first (UTF-8)",
                             remedy="The harness agent can do this: read the document and save it as .md, "
                                    "keeping every word of the narration.")
        dst = inputs / (name + (p.suffix if p.suffix.lower() in (".md", ".txt") else ".md"))
        shutil.copy2(p, dst)
        return dst.relative_to(d).as_posix()

    script = take(a.script, "script")
    plan = take(a.plan, "plan")
    notes = [take(n, f"notes-{i + 1}") for i, n in enumerate(a.notes or [])]
    def _voice_note(v):
        pr = voices[v]
        ident = pr.get("voice_id") or pr.get("voice") or ""
        extra = ", ".join(str(x) for x in (pr.get("voice_name"), pr.get("model_id"), pr.get("rate")) if x)
        return f"{pr.provider} {ident}" + (f" ({extra})" if extra else "")

    versions = "".join(f'[versions.{l}]\nvoice = "{chosen[l]}"   # {_voice_note(chosen[l])}\n\n' for l in langs)
    toml = TEMPLATE.format(title=json.dumps(a.title or a.slug.replace("-", " ").title(), ensure_ascii=False),
                           source=a.source_language, script=script, plan=plan,
                           notes=", ".join(json.dumps(n) for n in notes), versions=versions)
    if not (d / "production.toml").exists():          # --force replaces inputs, never a customised config
        atomic_write_text(d / "production.toml", toml)
    out = {"ok": True, "production": a.slug, "dir": rel(d), "files": [script, plan, *notes],
           "next": f"python -m automatio run {a.slug}"}
    emit(out, a.json, f"created {rel(d)}/ (inputs copied; production.toml written)\n"
                      f"next: python -m automatio run {a.slug}")
    return 0


def _pipeline(a):
    from .pipeline import Pipeline
    return Pipeline(a.production)


def cmd_status(a):
    p = _pipeline(a)
    s = p.status()
    lines = [f"{s['title']}  [{s['production']}]  ({s['dir']})"]
    if s["running"]:
        pr = s.get("progress") or {}
        lines.append(f"  RUNNING (pid {s['running']['pid']}): {pr.get('stage')} {pr.get('done')}/{pr.get('total')} "
                     f"{pr.get('detail', '')}")
    for r in s["stages"]:
        parts = "  " + " ".join(f"{k.split(':', 1)[1]}={ICON.get(v, v)}" for k, v in r["parts"].items()) if r["parts"] else ""
        lines.append(f"  {ICON.get(r['status'], '?')} {r['stage']:<10} {r['status']:<16} {r['summary'][:110]}{parts}")
    if s["approval"]:
        lines.append(f"  approval: {s['approval'].get('approved_at')} by {s['approval'].get('by')}, "
                     f"budget {s['approval'].get('budget')}")
    if s["spent"]:
        lines.append(f"  spent: {s['spent']}")
    nxt = p.next_action()
    s["next"] = nxt
    lines.append(f"next: {nxt['action']}" + (f" - {nxt.get('why', '')}" if nxt.get("why") else ""))
    emit(s, a.json, "\n".join(lines))
    return 0


def cmd_next(a):
    p = _pipeline(a)
    n = p.next_action()
    emit(n, a.json, json.dumps(n, ensure_ascii=False, indent=1, default=str))
    return 0


def _print_outcome(o, a) -> int:
    d = o.to_dict()
    lines = [f"[{o.state}] {o.stage or ''}: {o.message}"]
    if o.task:
        lines += [f"  agent task: {o.task['title']}", f"  instructions: {o.task['file']}"]
        if o.task.get("check"):
            lines.append(f"  check: {o.task['check']}")
        lines.append(f"  then: {o.task['then']}")
    if o.approval:
        ap = o.approval
        lines.append(f"  {ap['reason']}")
        lines.append("  configuration: " + json.dumps(ap["config"], ensure_ascii=False, default=str))
        lines.append("  paid voice estimate: " + (json.dumps(ap["estimate"], ensure_ascii=False) if ap["estimate"]
                                                   else "none (all voices free or already cached)"))
        lines.append(f"  after the user approves: {ap['command']}")
    if o.error:
        if o.error.get("remedy"):
            lines.append(f"  remedy: {o.error['remedy']}")
        tail = o.error.get("details", {}).get("tail") or o.error.get("details", {}).get("traceback")
        if tail:
            lines += ["  | " + t for t in tail[-8:]]
    emit(d, a.json, "\n".join(lines))
    return o.exit_code


def cmd_run(a):
    p = _pipeline(a)
    stamp = now_iso().replace(":", "")[:15]
    h = add_file(p.prod.build_dir / "logs" / f"run-{stamp}.log")
    try:
        log.info(f"run {p.prod.slug} (AutomatioAgentica {__version__})")
        o = p.run(until=a.until, only=a.only, force=tuple(a.force or ()))
    finally:
        remove(h)
    return _print_outcome(o, a)


def _parse_budget(specs) -> dict:
    out = {}
    for s in specs or []:
        k, _, v = s.partition("=")
        try:
            out[k.strip()] = float(v)
        except ValueError:
            raise UsageError(f"--budget expects provider=credits, got {s!r}") from None
    return out


def cmd_approve(a):
    from .util import fingerprint
    p = _pipeline(a)
    est = p.estimate()
    budget = _parse_budget(a.budget)
    for prov, e in est.items():
        if prov not in budget:
            raise UsageError(f"this production uses the paid provider {prov!r} (estimate ~{e['credits']:.0f} credits): "
                             f"pass --budget {prov}=<max credits> (recommended {e['recommended_budget']})")
    rec = {"approved_at": now_iso(), "by": a.by, "note": a.note, "budget": budget, "estimate": est,
           "config": p.config_summary(), "fingerprint": p.approval_fp()}
    p.state.set_approval(rec)
    p.state.event("approved", by=a.by, budget=budget)
    out = {"ok": True, "approval": {k: v for k, v in rec.items() if k != "fingerprint"},
           "next": f"python -m automatio run {p.prod.slug}"}
    emit(out, a.json, f"approved by {a.by}; budget {budget or 'none needed'}\nnext: python -m automatio run {p.prod.slug}")
    return 0


def cmd_task(a):
    p = _pipeline(a)
    n = p.next_action()
    if n["action"] != "agent_task":
        emit({"ok": True, "task": None, "next": n}, a.json, f"no agent task is waiting (next: {n['action']})")
        return 0
    t = n["task"]
    body = Path(t["file"]) if Path(t["file"]).is_absolute() else Path(__file__).resolve().parent.parent / t["file"]
    emit({"ok": True, "task": t, "content": body.read_text(encoding="utf-8")}, a.json, body.read_text(encoding="utf-8"))
    return 0


def cmd_check(a):
    from . import narration as N
    from .scenes import check as check_scenes
    p = _pipeline(a)
    prod = p.prod
    if a.what in ("translate", "narration"):
        rep = N.validate(p.narr, langs=prod.langs, subtitle_lang=prod.subtitles.language, source_lang=prod.source_language,
                         marker_langs=prod.marker_langs, dub_langs=prod.dub_langs)
        if a.what == "narration":
            comp = N.completeness(prod, p.narr)
            rep["completeness"] = comp
            if comp["coverage"] < 0.985 or comp["ratio"] < 0.97:
                rep["errors"].append(f"narration covers {comp['coverage'] * 100:.1f}% of the script; missing: "
                                     f"{comp['missing'][:5]}")
    else:
        rep = check_scenes(prod, p.narr)
        rep["scenes"] = {k: f"{rel(r.file)}:{r.cls}" for k, r in rep["scenes"].items()}
    ok = not rep["errors"]
    n_err = len(rep["errors"])
    lines = [f"check {a.what}: " + ("OK" if ok else f"{n_err} error(s)")]
    lines += [f"  ✗ {e}" for e in rep["errors"][:80]] + [f"  ! {w}" for w in rep["warnings"][:60]]
    emit({"ok": ok, **rep}, a.json, "\n".join(lines))
    return 0 if ok else EXIT["failed"]


def cmd_complete(a):
    p = _pipeline(a)
    if a.what != "review":
        raise UsageError("only `complete review` exists; other agent tasks complete when their check passes")
    if not a.notes or len(a.notes.strip()) < 10:
        raise UsageError("--notes is required: say what you checked and fixed")
    s = p.complete_review(a.notes.strip())
    emit({"ok": True, "review": s, "next": f"python -m automatio run {p.prod.slug}"}, a.json,
         f"review recorded\nnext: python -m automatio run {p.prod.slug}")
    return 0


def cmd_preview(a):
    from . import render as R
    from . import voice as V
    from .scenes import check as check_scenes
    p = _pipeline(a)
    prod, narr = p.prod, p.narr
    sec = next((s for s in narr.sections if s["key"] == a.section), None)
    if sec is None:
        raise UsageError(f"no section {a.section!r}; sections: {[s['key'] for s in narr.sections]}")
    chk = check_scenes(prod, narr)
    if sec["key"] not in chk["scenes"]:
        raise ValidationFailed(f"no valid scene for {sec['key']}: " + "; ".join(e for e in chk["errors"] if sec["key"] in e))
    langs = prod.full_langs if a.lang in (None, "all") else [a.lang]   # dub versions are not rendered
    kind = "final" if a.hq else "draft"
    out = []
    for lang in langs:
        V.run_language(prod, narr, lang, p.state, draft=True)
        man_path = V.manifest_path(prod, lang, draft=True)
        r = R.render_one(prod, lang, sec, chk["scenes"][sec["key"]], man_path, kind=kind, preview_audio=a.audio)
        from .util import read_json, resolve
        d = prod.build_dir / "preview" / lang
        d.mkdir(parents=True, exist_ok=True)
        from .util import link_or_copy
        mp4 = d / f"{sec['key']}.mp4"
        link_or_copy(resolve(r["mp4"]), mp4)
        sheet = R.contact_sheet(mp4, read_json(resolve(r["cues"])), read_json(man_path), d / f"{sec['key']}_sheet.jpg")
        out.append({"lang": lang, "video": rel(mp4), "sheet": rel(sheet), "duration": r["duration"],
                    "cached": r["cached"], "lint": r["lint"]})
    lines = []
    for o in out:
        lines.append(f"{sec['key']} [{o['lang']}] {o['duration']:.1f}s  sheet: {o['sheet']}  video: {o['video']}"
                     + (" (cached)" if o["cached"] else ""))
        lines += [f"  ! {x['line']} t={x['t']}: {x['issue']} {x['mobject']} {x['texts']}" for x in o["lint"]]
    emit({"ok": True, "previews": out}, a.json, "\n".join(lines))
    return 0


def cmd_say(a):
    from . import voice as V
    from .config import load_voices
    voices = load_voices()
    if a.voice not in voices:
        raise UsageError(f"unknown voice {a.voice!r}; profiles: {', '.join(voices)}")
    prof = voices[a.voice]
    table = None if a.raw else prof.pronunciation
    outs = []
    for t in a.texts:
        path = V.audition(prof, t, output_root() / "samples", table)
        outs.append(rel(path))
    emit({"ok": True, "files": outs}, a.json, "\n".join(outs))
    return 0


def cmd_report(a):
    from .deliver import report_md
    from .util import read_json
    p = _pipeline(a)
    md = report_md(p.prod, p.state, read_json(p.prod.output_dir / "manifest.json"))
    path = p.prod.build_dir / "report.md"
    atomic_write_text(path, md)
    emit({"ok": True, "report": rel(path), "markdown": md}, a.json, md)
    return 0


def cmd_estimate(a):
    p = _pipeline(a)
    e = p.estimate()
    emit({"ok": True, "estimate": e}, a.json, json.dumps(e, ensure_ascii=False, indent=1) if e else
         "no paid voices to generate (free voices, or all clips cached)")
    return 0


def cmd_voices(a):
    from .config import load_voices
    v = load_voices()
    rows = {k: {"language": p.language, "provider": p.provider, **p.settings, "draft": p.draft,
                "description": p.description} for k, p in v.items()}
    emit({"ok": True, "voices": rows}, a.json,
         "\n".join(f"{k:<20} {p.language}  {p.provider:<10} {p.settings.get('voice_id') or p.settings.get('voice', '')}"
                   f"  {p.description[:60]}" for k, p in v.items()))
    return 0


def cmd_clean(a):
    p = _pipeline(a)
    removed = []
    for sub in ("tmp", "preview"):
        d = p.prod.build_dir / sub
        if d.exists():
            shutil.rmtree(d)
            removed.append(rel(d))
    if a.build:
        if p.status()["running"]:
            raise UsageError("a run is in progress")
        shutil.rmtree(p.prod.build_dir, ignore_errors=True)
        removed.append(rel(p.prod.build_dir) + " (state reset; cache and output kept)")
    emit({"ok": True, "removed": removed}, a.json, "removed: " + (", ".join(removed) or "nothing"))
    return 0


def cmd_import_legacy(a):
    from . import ROOT
    from .config import load_voices
    from . import providers
    from .voice import import_legacy
    prof = load_voices()[a.voice]
    fp = providers.get(prof.provider).fingerprint(prof)
    n = import_legacy(ROOT / "assets" / "voice" / "manifest.json", ROOT / "assets" / "voice", prof.provider, fp)
    emit({"ok": True, "imported": n}, a.json, f"adopted {n} clip(s) from assets/voice into the cache")
    return 0


# ------------------------------------------------------------------ parser
def build_parser():
    ap = argparse.ArgumentParser(prog="python -m automatio", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"AutomatioAgentica {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output on stdout")
    common.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("doctor", parents=[common], help="check tools, fonts, credentials, providers")
    s.add_argument("--online", action="store_true", help="also contact the providers (no credits spent)")
    s.set_defaults(fn=cmd_doctor)

    s = sub.add_parser("new", parents=[common], help="create a production from a script and a plan")
    s.add_argument("slug")
    s.add_argument("--script", required=True)
    s.add_argument("--plan", required=True)
    s.add_argument("--notes", action="append", help="extra direction files (repeatable)")
    s.add_argument("--title")
    s.add_argument("--source-language", default="en")
    s.add_argument("--languages", default="hi,en", help="versions to produce (default hi,en)")
    s.add_argument("--voice", action="append", help="lang=profile (default hi=hindi-adam, en=english-andrew)")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_new)

    for name, fn, hlp in (("status", cmd_status, "stage table and progress"),
                          ("next", cmd_next, "the next action for the harness"),
                          ("task", cmd_task, "print the waiting agent task"),
                          ("report", cmd_report, "write and print the production report"),
                          ("estimate", cmd_estimate, "paid voice cost of the remaining work")):
        s = sub.add_parser(name, parents=[common], help=hlp)
        s.add_argument("production", nargs="?")
        s.set_defaults(fn=fn)

    s = sub.add_parser("run", parents=[common], help="run stages until done or blocked (resumable)")
    s.add_argument("production", nargs="?")
    s.add_argument("--until", help="stop after this stage")
    s.add_argument("--only", help="run just this stage")
    s.add_argument("--force", action="append", help="redo a stage even if it is up to date (repeatable)")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("approve", parents=[common], help="record the user's approval (only after they approve)")
    s.add_argument("production", nargs="?")
    s.add_argument("--budget", action="append", help="provider=max_credits, e.g. elevenlabs=8000")
    s.add_argument("--by", default="user (via harness)", help="who approved")
    s.add_argument("--note", default="")
    s.set_defaults(fn=cmd_approve)

    s = sub.add_parser("check", parents=[common], help="validate agent work without running the pipeline")
    s.add_argument("what", choices=["translate", "scenes", "narration"])
    s.add_argument("production", nargs="?")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("complete", parents=[common], help="mark the visual review as done")
    s.add_argument("what", choices=["review"])
    s.add_argument("production", nargs="?")
    s.add_argument("--notes", required=True)
    s.set_defaults(fn=cmd_complete)

    s = sub.add_parser("preview", parents=[common], help="quick render + contact sheet of one section")
    s.add_argument("production")
    s.add_argument("section")
    s.add_argument("--lang", default=None, help="hi / en / all (default all)")
    s.add_argument("--hq", action="store_true", help="final resolution instead of 480p")
    s.add_argument("--audio", action="store_true", help="embed the narration in the preview video")
    s.set_defaults(fn=cmd_preview)

    s = sub.add_parser("say", parents=[common], help="hear text in a voice (writes output/samples/)")
    s.add_argument("texts", nargs="+")
    s.add_argument("--voice", default="hindi-adam")
    s.add_argument("--raw", action="store_true", help="skip the pronunciation dictionary")
    s.set_defaults(fn=cmd_say)

    s = sub.add_parser("voices", parents=[common], help="list voice profiles")
    s.set_defaults(fn=cmd_voices)

    s = sub.add_parser("clean", parents=[common], help="remove temporary files of a production")
    s.add_argument("production", nargs="?")
    s.add_argument("--build", action="store_true", help="also reset its build state (cache/output kept)")
    s.set_defaults(fn=cmd_clean)

    s = sub.add_parser("import-legacy", parents=[common], help="adopt pre-2.0 voice clips into the cache")
    s.add_argument("--voice", default="hindi-adam")
    s.set_defaults(fn=cmd_import_legacy)
    return ap


def _on_signal(signum, frame):
    from .util import terminate_children
    terminate_children()
    raise KeyboardInterrupt(f"signal {signum}")


def main(argv=None) -> int:
    import signal
    ap = build_parser()
    a = ap.parse_args(argv)
    setup(verbose=getattr(a, "verbose", False), quiet=False)
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)
    try:
        return a.fn(a)
    except AAError as e:
        emit({"ok": False, "state": e.outcome, "error": e.to_dict()}, getattr(a, "json", False),
             f"[{e.outcome}] {e.code}: {e.message}" + (f"\n  remedy: {e.remedy}" if e.remedy else ""))
        return e.exit_code
    except KeyboardInterrupt:
        from .util import terminate_children
        terminate_children()
        emit({"ok": False, "state": "failed", "error": {
                 "code": "interrupted", "message": "interrupted",
                 "remedy": "Run the same command again: finished work is kept and the run resumes."}},
             getattr(a, "json", False), "interrupted - run the same command again to resume")
        return EXIT["failed"]


if __name__ == "__main__":
    sys.exit(main())
