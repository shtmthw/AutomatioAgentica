"""Deliverables: output/<slug>/ with one folder per language version, a production
manifest (machine-readable) and a report (human-readable).

    output/<slug>/
      manifest.json            inputs, voices (exact provider ids/settings), files + sha256, checks
      report.md                what was produced, checks, warnings, what could not be verified
      narration-script.md      every line in every language with its timestamp in each version
      thumbnail.png/.jpg       (when the production has scenes/thumbnail.py)
      <label>/                 e.g. hindi/, english/
        final-video.mp4        H.264 + AAC, no subtitles in the picture or the container
        voiceover.mp3          dub versions only: the voice alone, same duration as the video
        subtitles-en.srt / .vtt
        narration/             lines/<key>.mp3, narration.json (text + timings), voice-track.flac
        assets/                scenes/<section>.mp4, music-track.flac, timeline.json, contact-sheets/

Files are hard links into the cache/build folders where possible (no extra disk space).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import __version__, ROOT
from .narration import display
from .secrets import redact, scrubbed_env
from .util import (atomic_write_json, atomic_write_text, fmt_time, link_or_copy, now_iso, read_json, rel, resolve,
                   sha256_file)


def _git_commit() -> str | None:
    try:
        cp = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            env=scrubbed_env())
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True,
                               env=scrubbed_env()).stdout.strip()
        return (cp.stdout.strip() + ("-dirty" if dirty else "")) if cp.returncode == 0 else None
    except OSError:
        return None


def _file(path: Path, base: Path) -> dict:
    return {"path": path.relative_to(base).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def _reset_dir(d: Path) -> None:
    """Pipeline-owned subfolders are rebuilt on every delivery (stale clips must not linger)."""
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)


def deliver_version(prod, narr, lang: str, asm: dict, sub_files: dict, man: dict, idx: dict, ver: dict,
                    sheets: list) -> dict:
    out = prod.output_dir / prod.versions[lang].label
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    final = out / "final-video.mp4"
    link_or_copy(resolve(asm["final"]), final)
    files["video"] = final
    for fmt, src in sub_files.items():
        dst = out / f"subtitles-{prod.subtitles.language}.{fmt}"
        link_or_copy(resolve(src), dst)
        files[f"subtitles_{fmt}"] = dst

    nar = out / "narration"
    _reset_dir(nar / "lines")
    tl = read_json(resolve(asm["timeline"]))
    starts = {ln["key"]: ln for ln in tl["lines"]}
    lines_out = []
    for key, e in man["lines"].items():
        src = resolve(e["file"])
        dst = nar / "lines" / f"{key}{src.suffix}"
        link_or_copy(src, dst)
        t = starts.get(key, {})
        lines_out.append({"key": key, "section": e["section"], "file": f"lines/{dst.name}",
                          "start": t.get("start"), "speech_start": t.get("speech_start"),
                          "speech_end": t.get("speech_end"), "clip_duration": e["duration"],
                          "text": e["display"], "spoken": e["spoken"], "subtitle": e["subtitle"],
                          "markers": e["markers"], "words": e["words"]})
    atomic_write_json(nar / "narration.json", {"lang": lang, "voice": man["voice"], "lines": lines_out})
    link_or_copy(resolve(asm["voice_stem"]), nar / "voice-track.flac")
    files["voice_track"] = nar / "voice-track.flac"
    if asm.get("voiceover_mp3"):                     # dub versions: voice only, same duration as the video
        vo = out / "voiceover.mp3"
        link_or_copy(resolve(asm["voiceover_mp3"]), vo)
        files["voiceover_mp3"] = vo

    assets = out / "assets"
    _reset_dir(assets / "scenes")
    for s in tl["scenes"]:
        link_or_copy(resolve(s["mp4"]), assets / "scenes" / f"{s['section']}.mp4")
    if asm.get("music_stem"):
        link_or_copy(resolve(asm["music_stem"]), assets / "music-track.flac")
    link_or_copy(resolve(asm["timeline"]), assets / "timeline.json")
    _reset_dir(assets / "contact-sheets")
    for p in sheets:
        link_or_copy(resolve(p), assets / "contact-sheets" / Path(p).name)
    return {"label": prod.versions[lang].label, "dir": rel(out), "files": {k: _file(v, prod.output_dir)
                                                                           for k, v in files.items()},
            "lines": len(lines_out), "duration": tl["total"], "verification": ver}


def narration_script(prod, narr, timelines: dict) -> str:
    langs = prod.langs
    starts = {l: {ln["key"]: ln["start"] for ln in tl["lines"]} for l, tl in timelines.items()}
    sec_starts = {l: {s["section"]: s["offset"] for s in tl["scenes"]} for l, tl in timelines.items()}
    out = [f"# {prod.title}", "", "Narration script with the start time of every line in each version.", ""]
    for l, tl in timelines.items():
        out.append(f"- **{prod.versions[l].label.capitalize()}** version: {fmt_time(tl['total'])}")
    out.append("")
    for sec in narr.sections:
        ch = sec.get("chapter") or {}
        stamps = " · ".join(f"{prod.versions[l].label} `{fmt_time(sec_starts[l][sec['key']])}`" for l in timelines
                            if sec["key"] in sec_starts[l])
        out += [f"## {ch.get('number', '')} {ch.get('title', sec['key'])}".strip() + (f"  ({stamps})" if stamps else ""), ""]
        for ln in sec["lines"]:
            ts = " · ".join(f"{l} `{fmt_time(starts[l][ln['key']])}`" for l in timelines if ln["key"] in starts[l])
            rows = [f"- **{ln['key']}** {ts}"]
            for l in dict.fromkeys([*langs, prod.subtitles.language]):
                if ln.get(l):
                    rows.append(f"  - {l}: {display(ln[l])}")
            out += rows
        out.append("")
    return "\n".join(out)


def write_manifest(prod, narr, versions: dict, state, thumb: dict | None) -> dict:
    inputs = {}
    for name, p in (("script", prod.script), ("plan", prod.plan), ("narration", prod.narration_path)):
        if p.exists():
            inputs[name] = {"path": rel(p), "sha256": sha256_file(p)}
    for n in prod.notes:
        if n.exists():
            inputs.setdefault("notes", []).append({"path": rel(n), "sha256": sha256_file(n)})
    man = {
        "schema": "automatio.manifest/1",
        "production": {"slug": prod.slug, "title": prod.title, "delivered_at": now_iso(),
                       "pipeline": f"AutomatioAgentica {__version__}", "git": _git_commit()},
        "inputs": inputs,
        "subtitles": {"language": prod.subtitles.language, "formats": prod.subtitles.formats, "burned_in": False},
        "versions": {},
        "costs": {"spent_credits": state.data.get("spent", {})},
        "approval": {k: v for k, v in (state.approval or {}).items() if k != "fingerprint"},
    }
    for lang, v in versions.items():
        prof = prod.profile(lang)
        man["versions"][lang] = {**v, "audio_language": prod.versions[lang].audio_language, "voice": prof.public()}
    if thumb:
        man["thumbnail"] = thumb
    atomic_write_json(prod.output_dir / "manifest.json", man)
    return man


def report_md(prod, state, manifest: dict | None = None) -> str:
    """Human-readable report from the state (works for partial runs too)."""
    st = state.data.get("stages", {})
    out = [f"# Production report: {prod.title}", "",
           f"- production: `{prod.slug}` ({rel(prod.dir)})", f"- updated: {state.data.get('updated_at')}",
           f"- pipeline: AutomatioAgentica {__version__}", ""]
    if manifest:
        out += ["## Deliverables", ""]
        for lang, v in manifest["versions"].items():
            vv = v["voice"]
            vid = vv.get("voice_id") or vv.get("voice")
            out.append(f"### {v['label'].capitalize()} ({lang}) - {fmt_time(v['duration'])}, "
                       f"verification **{v['verification']['status'].upper()}**")
            out.append(f"- voice: `{vv['profile']}` - {vv['provider']} `{vid}`"
                       + (f", model `{vv['model_id']}`" if vv.get("model_id") else "")
                       + (f", rate {vv['rate']}" if vv.get("rate") else ""))
            for k, f in v["files"].items():
                b = f["bytes"]
                size = f"{b / 1e6:.1f} MB" if b >= 1e6 else (f"{b / 1e3:.0f} kB" if b >= 1e4 else f"{b:,} bytes")
                out.append(f"- `{f['path']}` ({size})")
            out.append("")
            out.append("| check | result | detail |")
            out.append("|---|---|---|")
            for c in v["verification"]["checks"]:
                out.append(f"| {c['check']} | {c['status']} | {redact(c['detail'])} |")
            out.append("")
    out += ["## Stages", "", "| stage | status | finished | notes |", "|---|---|---|---|"]
    for sid, s in st.items():
        note = s.get("summary") or (s.get("error") or {}).get("message", "")
        out.append(f"| {sid} | {s.get('status')} | {s.get('finished_at', '')} | {redact(str(note))[:160]} |")
    out.append("")
    spent = state.data.get("spent", {})
    out += ["## Costs", "", "- paid credits spent by this production so far: "
            + (", ".join(f"{k}: {v:.0f}" for k, v in spent.items()) if spent else "none"), ""]
    warns = []
    for sid, s in st.items():
        warns += [f"{sid}: {w}" for w in s.get("warnings", [])]
    if warns:
        out += ["## Warnings", ""] + [f"- {redact(w)}" for w in warns[:60]] + [""]
    unver = []
    for sid, s in st.items():
        unver += s.get("unverified", [])
    unver += ["Listening quality (pronunciation, intonation) needs human ears: automated checks cover timing, "
              "loudness and sync, not how the voice sounds.",
              "Speech-to-text comparison of the narration was not run (no ASR engine installed); sync is verified "
              "from word timings and narration energy under the subtitles."]
    out += ["## Not verified automatically", ""] + [f"- {u}" for u in dict.fromkeys(unver)] + [""]
    return "\n".join(out)


def deliver(prod, narr, per_lang: dict, state, thumb_png: Path | None) -> dict:
    prod.output_dir.mkdir(parents=True, exist_ok=True)
    versions = {}
    timelines = {}
    for lang, r in per_lang.items():
        versions[lang] = deliver_version(prod, narr, lang, r["assemble"], r["subtitles"], r["manifest"], r["index"],
                                         r["verify"], r.get("sheets", []))
        timelines[lang] = read_json(resolve(r["assemble"]["timeline"]))
    atomic_write_text(prod.output_dir / "narration-script.md", narration_script(prod, narr, timelines))
    thumb = None
    if thumb_png:
        png = prod.output_dir / "thumbnail.png"
        link_or_copy(thumb_png, png)
        jpg = prod.output_dir / "thumbnail.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-vf", "scale=1280:720", "-q:v", "2",
                        str(jpg)], check=True, env=scrubbed_env())
        thumb = {"png": _file(png, prod.output_dir), "jpg": _file(jpg, prod.output_dir)}
    man = write_manifest(prod, narr, versions, state, thumb)
    atomic_write_text(prod.output_dir / "report.md", report_md(prod, state, man))
    return man
