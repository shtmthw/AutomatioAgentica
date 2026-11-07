"""Deliverables: output/<slug>/ with one folder per language version, a production
manifest (machine-readable) and a report (human-readable).

    output/<slug>/
      manifest.json            inputs, voices (exact provider ids/settings), files + sha256, checks
      report.md                what was produced, checks, chapters, warnings, what could not be verified
      narration-script.md      every line in every language with its timestamp in each version
      script/                  <lang>/NN_<title>.txt per section, side-by-side.md ([deliver] script_dir)
      thumbnail.png/.jpg       (when the production has scenes/thumbnail.py)
      <alias>                  [deliver] aliases: plan-required file names, linked to the files below
      <label>/                 e.g. hindi/, english/
        final-video.mp4        H.264 + AAC, no subtitles in the picture or the container
        voiceover.mp3          dub versions only: the voice alone, same duration as the video
        subtitles-en.srt / .vtt
        subtitles-<lang>.srt / .vtt   [subtitles] own_language: in the version's own language
        chapters.txt           YouTube chapters (section starts in this version)
        topics.txt             chapters + key topics (narration `topic` fields) with this version's times
        timings.json           sections and lines with start/speech/slot times (e.g. to fit a later dub)
        narration/             lines/<key>.mp3, narration.json (text + timings), voice-track.flac
        assets/                scenes/<section>.mp4, music-track.flac, timeline.json, contact-sheets/

Files are hard links into the cache/build folders where possible (no extra disk space).
Everything here is derived from the pipeline's own outputs, so it is regenerated on every
delivery and never goes stale.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from . import __version__, ROOT
from .narration import display
from .secrets import redact, scrubbed_env
from .util import (atomic_write_json, atomic_write_text, fmt_stamp, fmt_time, link_or_copy, now_iso, read_json, rel,
                   remove_stale_links, resolve, sha256_file)

CHAPTER_MIN = 10.0          # YouTube: every chapter at least 10 s, at least 3 chapters, the first at 0:00


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


def slug_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "section"


def _chapter(sec: dict) -> tuple[str, str]:
    ch = sec.get("chapter") or {}
    return str(ch.get("number") or ""), ch.get("title") or sec["key"]


# ------------------------------------------------------------------ chapters, topics, timings
def chapters(narr, tl: dict) -> tuple[list[tuple[float, str]], list[str]]:
    """(start, title) per section in this version, and any YouTube chapter-rule problems."""
    starts = {s["section"]: s["offset"] for s in tl["scenes"]}
    out = [(starts[s["key"]], _chapter(s)[1]) for s in narr.sections if s["key"] in starts]
    issues = []
    if len(out) < 3:
        issues.append(f"only {len(out)} chapter(s); YouTube needs at least 3")
    if out and out[0][0] > 0.5:
        issues.append(f"the first chapter starts at {fmt_stamp(out[0][0])}, not 0:00")
    for i, (t, title) in enumerate(out):
        end = out[i + 1][0] if i + 1 < len(out) else tl["total"]
        if end - t < CHAPTER_MIN:
            issues.append(f"chapter {title!r} is {end - t:.1f}s long; YouTube needs at least {CHAPTER_MIN:.0f}s")
    return out, issues


def chapters_txt(narr, tl: dict) -> str:
    rows, _ = chapters(narr, tl)
    return "".join(f"{fmt_stamp(0.0 if i == 0 else t)} {title}\n" for i, (t, title) in enumerate(rows))


def topics_txt(narr, tl: dict) -> str:
    """Chapters with the key topics of each section indented beneath them (line `topic` fields)."""
    starts = {s["section"]: s["offset"] for s in tl["scenes"]}
    line_start = {ln["key"]: ln["start"] for ln in tl["lines"]}
    out = []
    for i, sec in enumerate(narr.sections):
        if sec["key"] not in starts:
            continue
        num, title = _chapter(sec)
        out.append(f"{fmt_stamp(0.0 if i == 0 else starts[sec['key']])} {num + '. ' if num else ''}{title}")
        for ln in sec["lines"]:
            t = (ln.get("topic") or "").strip()
            if t and ln["key"] in line_start:
                out.append(f"  {fmt_stamp(max(starts[sec['key']], line_start[ln['key']]))} {t}")
    return "\n".join(out) + "\n"


def timings(prod, narr, lang: str, tl: dict) -> dict:
    """Public timing file of one version: sections, lines with their slots, and (when a dub follows
    this version) the anchored segments a dub must keep."""
    ver = prod.versions[lang]
    by_sec = {s["key"]: s for s in narr.sections}
    lines_in = {ln["key"]: ln for _, ln in narr.lines()}
    secs = []
    for s in tl["scenes"]:
        num, title = _chapter(by_sec[s["section"]])
        secs.append({"key": s["section"], "number": num, "title": title, "start": round(s["offset"], 4),
                     "end": round(s["offset"] + s["duration"], 4), "duration": round(s["duration"], 4)})
    sec_end = {s["key"]: s["end"] for s in secs}
    rows = []
    for i, ln in enumerate(tl["lines"]):
        nxt = tl["lines"][i + 1] if i + 1 < len(tl["lines"]) else None
        slot_end = nxt["start"] if nxt and nxt["section"] == ln["section"] else sec_end[ln["section"]]
        src = lines_in.get(ln["key"], {})
        row = {k: ln[k] for k in ("key", "section", "start", "speech_start", "speech_end") if k in ln}
        row.update({"slot_end": round(slot_end, 4), "slot": round(slot_end - ln["start"], 4)})
        for k in ("speed", "lag"):
            if k in ln:
                row[k] = ln[k]
        if src.get("topic"):
            row["topic"] = src["topic"]
        row["text"] = display(src.get(lang, "")) if src.get(lang) else None
        rows.append(row)
    out = {"schema": "automatio.timings/1", "production": prod.slug, "lang": lang, "mode": ver.mode,
           "video": f"{ver.label}/final-video.mp4", "total": tl["total"], "sections": secs, "lines": rows}
    if ver.mode == "dub":
        out["follow"] = ver.follow
    dubs = [l for l in prod.dub_langs if prod.versions[l].follow == lang]
    if dubs and prod.dub.anchors:
        from .dub import segments
        out["segments"] = [{"section": sg["section"], "lines": [x["key"] for x in sg["lines"]],
                            "start": sg["lines"][0]["speech_start"], "end": round(sg["end"], 4)}
                           for sg in segments(tl, prod.dub)]
        out["note"] = (f"{', '.join(dubs)} is fitted to this timeline: every section and segment starts with its "
                       "first line here and must end before `end`.")
    return out


# ------------------------------------------------------------------ script exports
def script_files(prod, narr, out_dir: Path) -> list[Path]:
    """<script_dir>/<lang>/NN_<title>.txt (one per section, every line as a paragraph) and
    <script_dir>/side-by-side.md (all languages line by line, for checking a translation)."""
    d = out_dir / prod.deliver.script_dir
    _reset_dir(d)
    present = narr.languages_present()
    langs = [l for l in dict.fromkeys([prod.source_language, *prod.langs, prod.subtitles.language]) if l in present]
    files = []
    for lang in langs:
        for i, sec in enumerate(narr.sections, 1):
            num, title = _chapter(sec)
            num = num or f"{i:02d}"
            body = "\n\n".join(display(ln[lang]) for ln in sec["lines"] if ln.get(lang))
            p = d / lang / f"{num}_{slug_title(title)}.txt"
            atomic_write_text(p, f"{num}. {title}\n\n{body}\n")
            files.append(p)
    if len(langs) > 1:
        def cell(s):
            return s.replace("|", "\\|")
        md = [f"# {prod.title}: narration side by side", "",
              "Every narration line in every language, in order (" + " | ".join(langs) + ").", ""]
        for sec in narr.sections:
            num, title = _chapter(sec)
            md += [f"## {num + '. ' if num else ''}{title}", "", "| line | " + " | ".join(langs) + " |",
                   "|---|" + "---|" * len(langs)]
            md += [f"| {ln['key']} | " + " | ".join(cell(display(ln.get(l) or "")) for l in langs) + " |"
                   for ln in sec["lines"]]
            md.append("")
        p = d / "side-by-side.md"
        atomic_write_text(p, "\n".join(md))
        files.append(p)
    return files


# ------------------------------------------------------------------ one version
def deliver_version(prod, narr, lang: str, r: dict) -> tuple[dict, list[str]]:
    asm, sub_files, man, ver_res = r["assemble"], r["subtitles"], r["manifest"], r["verify"]
    out = prod.output_dir / prod.versions[lang].label
    out.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    files = {}
    final = out / "final-video.mp4"
    link_or_copy(resolve(asm["final"]), final)
    files["video"] = final
    for fmt, src in sub_files.items():
        dst = out / f"subtitles-{prod.subtitles.language}.{fmt}"
        link_or_copy(resolve(src), dst)
        files[f"subtitles_{fmt}"] = dst
    for fmt, src in (r.get("own_subtitles") or {}).items():
        dst = out / f"subtitles-{lang}.{fmt}"
        link_or_copy(resolve(src), dst)
        files[f"subtitles_{lang}_{fmt}"] = dst

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

    if prod.deliver.chapters:
        rows, issues = chapters(narr, tl)
        warnings += [f"{lang} chapters: {i}" for i in issues]
        atomic_write_text(out / "chapters.txt", chapters_txt(narr, tl))
        files["chapters"] = out / "chapters.txt"
        if narr.topics():
            atomic_write_text(out / "topics.txt", topics_txt(narr, tl))
            files["topics"] = out / "topics.txt"
        else:
            (out / "topics.txt").unlink(missing_ok=True)
    atomic_write_json(out / "timings.json", timings(prod, narr, lang, tl))
    files["timings"] = out / "timings.json"

    assets = out / "assets"
    _reset_dir(assets / "scenes")
    for s in tl["scenes"]:
        link_or_copy(resolve(s["mp4"]), assets / "scenes" / f"{s['section']}.mp4")
    if asm.get("music_stem"):
        link_or_copy(resolve(asm["music_stem"]), assets / "music-track.flac")
    link_or_copy(resolve(asm["timeline"]), assets / "timeline.json")
    _reset_dir(assets / "contact-sheets")
    for p in r.get("sheets", []):
        link_or_copy(resolve(p), assets / "contact-sheets" / Path(p).name)
    entry = {"label": prod.versions[lang].label, "dir": rel(out),
             "files": {k: _file(v, prod.output_dir) for k, v in files.items()},
             "lines": len(lines_out), "duration": tl["total"], "verification": ver_res}
    return entry, warnings


def narration_script(prod, narr, timelines: dict) -> str:
    langs = prod.langs
    starts = {l: {ln["key"]: ln["start"] for ln in tl["lines"]} for l, tl in timelines.items()}
    sec_starts = {l: {s["section"]: s["offset"] for s in tl["scenes"]} for l, tl in timelines.items()}
    out = [f"# {prod.title}", "", "Narration script with the start time of every line in each version.", ""]
    for l, tl in timelines.items():
        out.append(f"- **{prod.versions[l].label.capitalize()}** version: {fmt_time(tl['total'])}")
    out.append("")
    for sec in narr.sections:
        num, title = _chapter(sec)
        stamps = " · ".join(f"{prod.versions[l].label} `{fmt_time(sec_starts[l][sec['key']])}`" for l in timelines
                            if sec["key"] in sec_starts[l])
        out += [f"## {num} {title}".strip() + (f"  ({stamps})" if stamps else ""), ""]
        for ln in sec["lines"]:
            ts = " · ".join(f"{l} `{fmt_time(starts[l][ln['key']])}`" for l in timelines if ln["key"] in starts[l])
            rows = [f"- **{ln['key']}** {ts}" + (f"  · topic: *{ln['topic']}*" if ln.get("topic") else "")]
            for l in dict.fromkeys([*langs, prod.subtitles.language]):
                if ln.get(l):
                    rows.append(f"  - {l}: {display(ln[l])}")
            out += rows
        out.append("")
    return "\n".join(out)


def write_manifest(prod, narr, versions: dict, state, thumb: dict | None, extra: dict | None = None) -> dict:
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
        "subtitles": {"language": prod.subtitles.language, "formats": prod.subtitles.formats, "burned_in": False,
                      **({"own_language": prod.own_subtitle_langs()} if prod.own_subtitle_langs() else {})},
        "versions": {},
        "costs": {"spent_credits": state.data.get("spent", {})},
        "approval": {k: v for k, v in (state.approval or {}).items() if k != "fingerprint"},
        **(extra or {}),
    }
    for lang in prod.langs:                       # production order
        if lang in versions:
            v = versions[lang]
            if "voice" not in v:                  # entries kept from an earlier delivery already carry it
                v = {**v, "audio_language": prod.versions[lang].audio_language, "voice": prod.profile(lang).public()}
            man["versions"][lang] = v
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
            for name in ("chapters", "topics"):
                p = prod.output_dir / v["label"] / f"{name}.txt"
                if p.exists():
                    out += [f"{name.capitalize()} ({v['label']}):", "", "```", p.read_text(encoding="utf-8").rstrip(),
                            "```", ""]
        if manifest.get("aliases"):
            out += ["Plan file names (links): " + ", ".join(f"`{a}` -> `{t}`" for a, t in manifest["aliases"].items()),
                    ""]
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


def _aliases(prod) -> tuple[dict, list[str]]:
    done, warnings = {}, []
    for name, target in prod.deliver.aliases.items():
        src, dst = prod.output_dir / target, prod.output_dir / name
        if not src.is_file():
            warnings.append(f"alias {name}: {target} is not delivered (yet)")
            continue
        link_or_copy(src, dst)
        done[name] = target
    return done, warnings


def deliver(prod, narr, per_lang: dict, state, thumb_png: Path | None, keep_others: bool = False) -> dict:
    """Write output/<slug>/ for the versions in `per_lang`. With `keep_others` (a `run --lang`
    delivery), versions delivered earlier and still on disk stay in the manifest."""
    prod.output_dir.mkdir(parents=True, exist_ok=True)
    remove_stale_links(prod.output_dir)
    versions, timelines, warnings = {}, {}, []
    for lang, r in per_lang.items():
        versions[lang], w = deliver_version(prod, narr, lang, r)
        warnings += w
        timelines[lang] = read_json(resolve(r["assemble"]["timeline"]))
    if keep_others:
        old = read_json(prod.output_dir / "manifest.json") or {}
        for lang, v in (old.get("versions") or {}).items():
            tl = read_json(prod.output_dir / prod.versions[lang].label / "assets" / "timeline.json") \
                if lang in prod.versions else None
            if lang not in versions and tl and all((prod.output_dir / f["path"]).exists() for f in v["files"].values()):
                versions[lang] = v
                timelines[lang] = tl
    if not narr.topics() and prod.deliver.chapters:
        warnings.append("no topics in narration.json: add a short English `topic` to the line where each key topic "
                        "starts (guideline 6), and topics.txt is written for every version")
    timelines = {l: timelines[l] for l in prod.langs if l in timelines}
    atomic_write_text(prod.output_dir / "narration-script.md", narration_script(prod, narr, timelines))
    if prod.deliver.script:
        script_files(prod, narr, prod.output_dir)
    thumb = None
    if thumb_png:
        png = prod.output_dir / "thumbnail.png"
        link_or_copy(thumb_png, png)
        jpg = prod.output_dir / "thumbnail.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-vf", "scale=1280:720", "-q:v", "2",
                        str(jpg)], check=True, env=scrubbed_env())
        thumb = {"png": _file(png, prod.output_dir), "jpg": _file(jpg, prod.output_dir)}
    aliases, w = _aliases(prod)
    warnings += w
    man = write_manifest(prod, narr, versions, state, thumb, {"aliases": aliases} if aliases else None)
    atomic_write_text(prod.output_dir / "report.md", report_md(prod, state, man))
    return {**man, "_warnings": warnings}
