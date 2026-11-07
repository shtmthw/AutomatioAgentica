"""Scene rendering (Manim, one process per scene and language), contact sheets, thumbnail.

A render is cached under cache/render/<key>/ where the key covers everything that can
change the picture or its timing: the scene file, the shared visual library
(agentic_video/), helper modules next to the scenes, this section's voice timings
(durations, words, markers), chapter title, line gap, quality, resolution, fps and the
Manim version. Unchanged scenes are never re-rendered; a crashed or interrupted render
leaves no cache entry and simply runs again.
"""
from __future__ import annotations

import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import ROOT, cache_root
from .errors import AAError, StageFailed, ValidationFailed
from .log import log
from .scenes import SceneRef, check as check_scenes, discover
from .util import (atomic_write_json, file_fp, fingerprint, probe_duration, read_json, rel, resolve, run,
                   tree_fp)

_LIB_FP: str | None = None


def lib_fp() -> str:
    global _LIB_FP
    if _LIB_FP is None:
        _LIB_FP = tree_fp(sorted((ROOT / "agentic_video").glob("*.py")))
    return _LIB_FP


def manim_version() -> str:
    try:
        from importlib.metadata import version
        return version("manim")
    except Exception:
        return "?"


def helper_fp(prod) -> str:
    found, _ = discover(prod.scenes_dir)
    scene_files = {r.file for refs in found.values() for r in refs}
    helpers = [p for p in prod.scenes_dir.glob("*.py") if p not in scene_files and p.name != "thumbnail.py"]
    return tree_fp(helpers) if helpers else "-"


def resolution(prod, kind: str) -> tuple[int, int, int, str]:
    v = prod.video
    if kind == "draft":
        h = 480
        w = int(round(v.width * h / v.height / 2)) * 2
        return w, h, prod.review.draft_fps, prod.review.draft_quality
    return v.width, v.height, v.fps, v.quality


def render_key(prod, lang: str, sec: dict, ref: SceneRef, man: dict, kind: str, preview_audio: bool) -> str:
    w, h, fps, q = resolution(prod, kind)
    lines = [man["lines"][ln["key"]] for ln in sec["lines"]]
    timing = [(e["key"], e["hash"], e["duration"], e["speech_end"], e["words"], sorted(e["markers"].items()))
              for e in lines]
    ch = sec.get("chapter")
    return fingerprint("render-2", file_fp(ref.file), ref.cls, lib_fp(), helper_fp(prod), timing,
                       [ch.get("number"), ch.get("title")] if ch else None, prod.audio.line_gap,
                       w, h, fps, q, manim_version(), preview_audio, n=24)


def render_one(prod, lang: str, sec: dict, ref: SceneRef, man_path: Path, kind: str = "final",
               preview_audio: bool = False, use_cache: bool = True) -> dict:
    man = read_json(man_path)
    key = render_key(prod, lang, sec, ref, man, kind, preview_audio)
    cdir = cache_root() / "render" / key
    if use_cache and (cdir / "scene.mp4").exists() and (cdir / "cues.json").exists():
        cues = read_json(cdir / "cues.json")
        return {"section": sec["key"], "lang": lang, "mp4": rel(cdir / "scene.mp4"), "cues": rel(cdir / "cues.json"),
                "duration": cues["duration"], "cache_key": key, "cached": True, "lint": cues.get("lint", [])}
    w, h, fps, q = resolution(prod, kind)
    work = prod.build_dir / "tmp" / f"{kind}-{lang}-{sec['key']}-{key[:10]}-{os.getpid()}"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    ch = sec.get("chapter")
    rt = {"lang": lang, "section": sec["key"], "manifest": str(man_path.resolve()),
          "cues_out": str(work / "cues.json"), "chapter": [ch["number"], ch["title"]] if ch else None,
          "line_gap": prod.audio.line_gap, "fps": fps, "expected_keys": [ln["key"] for ln in sec["lines"]],
          "preview_audio": preview_audio, "pronunciation": prod.pron_table(lang, prod.profile(lang)), "lint": True}
    atomic_write_json(work / "runtime.json", rt)
    cmd = [sys.executable, "-m", "manim", f"-q{q}", "--resolution", f"{w},{h}", "--frame_rate", str(fps),
           "--disable_caching", "--progress_bar", "none", "--media_dir", str(work / "media"),
           "-o", ref.cls, str(ref.file), ref.cls]
    t0 = time.time()
    run(cmd, log_file=work / "render.log", cwd=ROOT, timeout=prod.render.timeout,
        env={"PYTHONPATH": f"{ROOT}:{prod.scenes_dir}", "AA_RUNTIME": str(work / "runtime.json"),
             "PYTHONDONTWRITEBYTECODE": "1"},
        what=f"manim render of {sec['key']} ({lang}, {kind})")
    mp4s = sorted((work / "media").rglob(f"{ref.cls}.mp4"), key=lambda p: p.stat().st_mtime)
    if not mp4s or not (work / "cues.json").exists():
        raise StageFailed(f"render of {sec['key']} ({lang}) produced no video/cue log; see {rel(work / 'render.log')}")
    cues = read_json(work / "cues.json")
    dur = probe_duration(mp4s[-1])
    if abs(dur - cues["duration"]) > 2.0 / fps + 0.05:
        raise StageFailed(f"{sec['key']} ({lang}): video is {dur:.2f}s but the cue log says {cues['duration']:.2f}s")
    tmp = cdir.with_name(cdir.name + ".partial")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    shutil.move(str(mp4s[-1]), tmp / "scene.mp4")
    shutil.move(str(work / "cues.json"), tmp / "cues.json")
    shutil.copy(work / "render.log", tmp / "render.log")
    atomic_write_json(tmp / "meta.json", {"section": sec["key"], "lang": lang, "kind": kind, "scene": rel(ref.file),
                                          "class": ref.cls, "seconds": round(time.time() - t0, 1),
                                          "resolution": [w, h], "fps": fps})
    shutil.rmtree(cdir, ignore_errors=True)
    tmp.rename(cdir)
    shutil.rmtree(work, ignore_errors=True)
    return {"section": sec["key"], "lang": lang, "mp4": rel(cdir / "scene.mp4"), "cues": rel(cdir / "cues.json"),
            "duration": cues["duration"], "cache_key": key, "cached": False, "lint": cues.get("lint", []),
            "seconds": round(time.time() - t0, 1)}


def index_path(prod, lang: str, kind: str) -> Path:
    return prod.build_dir / ("render" if kind == "final" else "draft") / lang / "index.json"


def render_all(prod, narr, langs: list[str], man_paths: dict, *, kind: str, state, use_cache: bool = True) -> dict:
    """Render every section for every language in one worker pool. Returns {lang: index}."""
    chk = check_scenes(prod, narr)
    if chk["errors"]:
        raise ValidationFailed("scene check failed:\n  " + "\n  ".join(chk["errors"][:20]),
                               remedy="Fix the scenes (see `python -m automatio check scenes`).")
    refs = chk["scenes"]
    jobs = [(lang, sec) for lang in langs for sec in narr.sections]
    results: dict[tuple, dict] = {}
    errors: dict[tuple, AAError | Exception] = {}
    total = len(jobs)
    done = 0
    workers = max(1, min(prod.render.jobs, total))
    log.info(f"rendering {total} scene(s) ({kind}, {'/'.join(langs)}) with {workers} worker(s)")
    ex = ThreadPoolExecutor(workers)
    futs = {ex.submit(render_one, prod, lang, sec, refs[sec["key"]], man_paths[lang], kind, False, use_cache):
            (lang, sec["key"]) for lang, sec in jobs}
    try:
        for fut in as_completed(futs):
            k = futs[fut]
            done += 1
            try:
                r = fut.result()
                results[k] = r
                how = "cached" if r["cached"] else f"rendered in {r.get('seconds', 0):.0f}s"
                warn = f", {len(r['lint'])} layout warning(s)" if r["lint"] else ""
                log.info(f"  {k[1]} [{k[0]}] {how} ({r['duration']:.1f}s){warn}")
            except Exception as e:     # keep rendering the others; report all failures
                errors[k] = e
                log.error(f"  {k[1]} [{k[0]}] FAILED: {getattr(e, 'message', e)}")
            state.progress(f"{kind}-render", done, total, f"{k[1]}:{k[0]}")
    except BaseException:
        # interrupted: start nothing new, stop running renders; finished ones stay cached
        ex.shutdown(wait=False, cancel_futures=True)
        from .util import terminate_children
        terminate_children()
        raise
    ex.shutdown(wait=True)
    indexes = {}
    for lang in langs:
        scenes = [results[(lang, s["key"])] for s in narr.sections if (lang, s["key"]) in results]
        idx = {"lang": lang, "kind": kind, "scenes": scenes, "complete": len(scenes) == len(narr.sections),
               "fingerprint": fingerprint([s["cache_key"] for s in scenes])}
        atomic_write_json(index_path(prod, lang, kind), idx)
        indexes[lang] = idx
    if errors:
        first = next(iter(errors.values()))
        msg = "; ".join(f"{s} [{l}]: {getattr(e, 'message', str(e))[:200]}" for (l, s), e in errors.items())
        err = StageFailed(f"{len(errors)} of {total} renders failed: {msg}",
                          remedy="Fix the scene(s); finished renders are cached and will not run again.",
                          details={"failed": [f"{s}:{l}" for (l, s) in errors],
                                   "tail": getattr(first, "details", {}).get("tail", [])})
        raise err
    return indexes


# ------------------------------------------------------------------ contact sheets
def contact_sheet(mp4: Path, cues: dict, man: dict, out: Path, cols: int = 3, width: int = 640) -> Path:
    """One frame per narration line, taken at 92% of the line (once its animations settle)."""
    times = [c["start"] + man["lines"][c["key"]]["speech_end"] * 0.92 for c in cues["cues"]]
    tmp = out.with_suffix("")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for i, t in enumerate(times):
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1",
             "-vf", f"scale={width}:-2", tmp / f"{i:02d}.png"], what="ffmpeg frame grab")
    rows = (len(times) + cols - 1) // cols
    run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", tmp / "%02d.png",
         "-vf", f"tile={cols}x{rows}:padding=4:color=0x333333", "-frames:v", "1", out], what="ffmpeg tile")
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def sheets_for(prod, lang: str, kind: str, idx: dict, man: dict) -> list[str]:
    out = []
    d = prod.build_dir / ("draft" if kind == "draft" else "render") / lang / "sheets"
    d.mkdir(parents=True, exist_ok=True)
    for s in idx["scenes"]:
        cues = read_json(resolve(s["cues"]))
        p = d / f"{s['section']}.jpg"
        if not p.exists() or p.stat().st_mtime < resolve(s["mp4"]).stat().st_mtime:
            contact_sheet(resolve(s["mp4"]), cues, man, p)
        out.append(rel(p))
    return out


# ------------------------------------------------------------------ thumbnail
def render_thumbnail(prod, ref: SceneRef) -> Path:
    key = fingerprint("thumb-1", file_fp(ref.file), lib_fp(), manim_version(), prod.video.width, prod.video.height)
    cdir = cache_root() / "render" / f"thumb-{key}"
    png = cdir / "thumbnail.png"
    if png.exists():
        return png
    work = prod.build_dir / "tmp" / f"thumb-{key[:10]}"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    run([sys.executable, "-m", "manim", "-qh", "-s", "--resolution", f"{prod.video.width},{prod.video.height}",
         "--disable_caching", "--progress_bar", "none", "--media_dir", str(work / "media"), "-o", "thumbnail",
         str(ref.file), ref.cls], log_file=work / "render.log", cwd=ROOT,
        env={"PYTHONPATH": f"{ROOT}:{prod.scenes_dir}"}, what="thumbnail render")
    found = sorted((work / "media").rglob("thumbnail*.png"), key=lambda p: p.stat().st_mtime)
    if not found:
        raise StageFailed("thumbnail render produced no image")
    cdir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(found[-1]), png)
    shutil.rmtree(work, ignore_errors=True)
    return png
