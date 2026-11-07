"""Dub versions: a language voiced over the master version's picture and timeline.

production.toml:

    [versions.en]                       # the master: rendered from the scenes, timed to its narration
    voice = "english-andrew"
    [versions.hi]                       # the dub: not rendered; voiced onto the English video
    voice = "hindi-adam"
    mode = "dub"
    follow = "en"
    [dub]                               # optional (defaults in config.DubSettings)
    max_speedup = 1.05
    anchors = ["s06_03", "s06_04", ...] # lines that must start together with their master line (steps)

The video's timing is final; the dub is fitted to it, never the other way round:

  * every dub line starts speaking when the master line starts speaking (speech onset to onset),
    or as soon as the previous dub line has finished (+ min_gap of real silence) - a lag is allowed;
  * a *segment* (a section, split at anchor lines) must end before the next segment's master
    line starts (or before the section ends): sections and steps start on time;
  * only where a segment would otherwise overflow, its lines are time-stretched (rubberband with
    speech settings, pitch and formants preserved) by the smallest factor that fits, at most
    `max_speedup` - never to reduce lag;
  * what still does not fit is reported (the text has to be rewritten shorter), never cut;
  * before paying for a dub, the voice stage forecasts the fit from the text (automatio/forecast.py)
    and stops with a `dub-fit` agent task if a segment clearly cannot fit.

Audio treatment (the voice-over is a deliverable of its own):

  * placement uses each clip's real audio extent (energy), not the provider's word timings;
  * every clip is trimmed to its audio, gets a 10 ms fade-in and a 50 ms fade-out (no clicks,
    no hard cuts), and - with `level_match` - is levelled to the same loudness (±6 dB at most);
  * the voice track goes through `voice_chain` (high-pass, de-esser, gentle compression), then the
    house mix (-16 LUFS, look-ahead limiter, ducked music);
  * clips whose ending is cut off by the provider are found by `clip_issues`; the voice stage
    re-takes them (`retakes`), and verification fails while any remain.

The dub shares the master's subtitle files (same picture, same lines in the same slots); with
[subtitles] own_language it also gets subtitles in its own language, timed to the dub voice as
placed (timeline lines carry `clip_t0` and `speed` for that).
Outputs: <work>/final.mp4 (master picture, untouched + dub mix) and voiceover.mp3 (voice only,
same duration as the video, 48 kHz, `mp3_bitrate`). `preview` builds the same for a few sections
(cached paid clips, the free draft voice for the rest) so a dub can be heard before it is paid for.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

from .audio import SR, decode, lufs, mix
from .errors import StageFailed
from .log import log
from .util import atomic_write_json, read_json, rel, resolve, run, tmp_path

FRAME = 0.01            # analysis frame (s)
EDGE_DB = -45.0         # audio counts as sound above this level relative to the clip peak
LEAD, TAIL = 0.03, 0.06 # kept around the audio when a clip is trimmed (s)
FADE_IN, FADE_OUT = 0.010, 0.050


# ------------------------------------------------------------------ clip analysis
def _frames(x: np.ndarray) -> np.ndarray:
    hop = int(FRAME * SR)
    n = len(x) // hop
    return np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12) if n else np.zeros(0)


def audio_extent(x: np.ndarray) -> tuple[float, float]:
    """(first, last) moment with sound, in seconds, from the waveform itself."""
    rms = _frames(x)
    if not len(rms):
        return 0.0, 0.0
    on = np.where(rms > rms.max() * 10 ** (EDGE_DB / 20))[0]
    if not len(on):
        return 0.0, len(x) / SR
    return on[0] * FRAME, (on[-1] + 1) * FRAME


def clip_issues(path: Path, words: list | None = None) -> list[str]:
    """Defects a listener hears: an ending cut off mid-sound (the provider stopped the audio
    before the last word finished), or digital clipping."""
    x = decode(path)
    out = []
    if not len(x):
        return ["empty clip"]
    peak = float(np.abs(x).max())
    dur = len(x) / SR
    tail = float(np.sqrt((x[-int(0.03 * SR):] ** 2).mean())) / max(peak, 1e-9)
    tail_db = 20 * np.log10(max(tail, 1e-9))
    over = ((words[-1][0] + words[-1][1]) - dur) if words else 0.0
    if tail_db > -42 or (over > 0.04 and tail_db > -60):
        out.append(f"ending cut off (last 30 ms at {tail_db:.0f} dB re peak"
                   + (f", last word runs {over * 1000:.0f} ms past the audio" if over > 0.04 else "") + ")")
    if peak >= 0.999:
        out.append("clipping")
    return out


def prepare_clip(src: Path, speed: float, work: Path) -> dict:
    """Trimmed, faded (and if needed time-stretched) mono clip; cached by content."""
    h = hashlib.sha1(f"prep-3|{src.name}|{src.stat().st_size}|{speed:.3f}".encode()).hexdigest()[:16]
    out = work / "clips" / f"{h}.wav"
    meta = out.with_suffix(".json")
    if out.exists() and meta.exists():
        return {"path": out, **read_json(meta)}
    out.parent.mkdir(parents=True, exist_ok=True)
    x = decode(src)
    a0, a1 = audio_extent(x)
    s0, s1 = max(0.0, a0 - LEAD), min(len(x) / SR, a1 + TAIL)
    flt = [f"atrim=start={s0:.3f}:end={s1:.3f}", "asetpts=PTS-STARTPTS"]
    if speed > 1.0 + 1e-9:
        flt.append(f"rubberband=tempo={speed:.4f}:transients=smooth:detector=soft:formant=preserved:pitchq=quality")
    part = tmp_path(out)
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", ",".join(flt), "-ar", str(SR), "-ac", "1", "-f", "wav", part],
        what="ffmpeg clip prep")
    y, _ = sf.read(part, dtype="float32")
    part.unlink(missing_ok=True)
    fi, fo = int(FADE_IN * SR), int(FADE_OUT * SR)
    if len(y) > fi + fo:
        y[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)
        y[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
    b0, b1 = audio_extent(y)
    sf.write(out, y, SR, subtype="FLOAT")
    try:
        loud = lufs(out)
    except Exception:
        loud = None
    info = {"lead": b0, "end": b1, "duration": len(y) / SR, "lufs": loud, "speed": speed, "trim_start": s0}
    atomic_write_json(meta, info)
    return {"path": out, **info}


# ------------------------------------------------------------------ fitting
def segments(master_tl: dict, settings) -> list[dict]:
    """Master lines grouped into segments: per section, split at anchor lines. Each segment gets
    `end`: the latest time its last dub line may finish."""
    anchors = set(settings.anchors or [])
    sec_end = {s["section"]: s["offset"] + s["duration"] for s in master_tl["scenes"]}
    segs: list[dict] = []
    for ln in master_tl["lines"]:
        new = (not segs or segs[-1]["section"] != ln["section"] or ln["key"] in anchors)
        if new:
            segs.append({"section": ln["section"], "lines": []})
        segs[-1]["lines"].append(ln)
    for i, sg in enumerate(segs):
        nxt = segs[i + 1] if i + 1 < len(segs) else None
        if nxt is not None and nxt["section"] == sg["section"]:
            sg["end"] = nxt["lines"][0]["speech_start"] - settings.min_gap
        else:
            sg["end"] = sec_end[sg["section"]] - settings.section_tail
    return segs


def _place(seg_lines, dub_lines, speed, prev_end, min_gap):
    out = []
    for m in seg_lines:
        d = dub_lines[m["key"]]
        lead = d["speech_start"] / speed
        dur = (d["speech_end"] - d["speech_start"]) / speed
        onset = max(m["speech_start"], prev_end + min_gap)
        out.append({"key": m["key"], "section": m["section"], "speed": speed, "onset": onset, "end": onset + dur,
                    "t": onset - lead, "lead": lead, "lag": onset - m["speech_start"]})
        prev_end = onset + dur
    return out, prev_end


def fit(master_tl: dict, dub_lines: dict, settings) -> dict:
    """Place every dub line on the master timeline. `dub_lines`: key -> {speech_start, speech_end}
    relative to the clip. A segment is sped up only if it would otherwise overflow, by the
    smallest step that fits. Returns placements and a summary."""
    placed, overflow, prev_end = [], [], -1e9
    steps = [round(1.0 + 0.005 * i, 3) for i in range(int(round((settings.max_speedup - 1.0) / 0.005)) + 1)]
    for sg in segments(master_tl, settings):
        # sections and steps start on time, whatever happened before (an overflow is reported, not propagated)
        prev_end = min(prev_end, sg["lines"][0]["speech_start"] - settings.min_gap)
        best = None
        for s in steps:
            cand, end = _place(sg["lines"], dub_lines, s, prev_end, settings.min_gap)
            if end <= sg["end"] + 1e-6:
                best = (cand, end)
                break
        if best is None:          # does not fit even at max speed: place at max, report
            cand, end = _place(sg["lines"], dub_lines, steps[-1], prev_end, settings.min_gap)
            best = (cand, end)
            overflow.append({"section": sg["section"], "lines": [c["key"] for c in cand],
                             "over_by": round(end - sg["end"], 3)})
        for c in best[0]:
            c["segment_end"] = sg["end"]
        placed += best[0]
        prev_end = best[1]
    # spill: how far a dub line runs into the next master line's speech
    master = {ln["key"]: ln for ln in master_tl["lines"]}
    keys = [ln["key"] for ln in master_tl["lines"]]
    for i, p in enumerate(placed):
        nxt = master[keys[i + 1]] if i + 1 < len(keys) and master[keys[i + 1]]["section"] == p["section"] else None
        limit = nxt["speech_start"] if nxt else p["segment_end"]
        p["spill"] = max(0.0, p["end"] - limit)
    sped = [p for p in placed if p["speed"] > 1.0]
    summary = {"lines": len(placed), "overflow": overflow,
               "sped_up": len(sped), "max_speed": max([p["speed"] for p in placed] or [1.0]),
               "max_lag": round(max([p["lag"] for p in placed] or [0.0]), 3),
               "mean_lag": round(sum(p["lag"] for p in placed) / max(1, len(placed)), 3),
               "max_spill": round(max([p["spill"] for p in placed] or [0.0]), 3),
               "lag_over": [p["key"] for p in placed if p["lag"] > settings.max_lag],
               "spill_over": [p["key"] for p in placed if p["spill"] > settings.max_spill]}
    return {"placements": placed, "summary": summary}


# ------------------------------------------------------------------ assembly
def _voice_chain(voice: np.ndarray, chain: str, work: Path) -> np.ndarray:
    if not chain:
        return voice
    src, dst = work / "voice_dry.wav", work / "voice_chain.wav"
    sf.write(src, voice, SR, subtype="FLOAT")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", chain, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_f32le", dst],
        what="ffmpeg voice chain")
    y, _ = sf.read(dst, dtype="float32")
    src.unlink(missing_ok=True)
    dst.unlink(missing_ok=True)
    out = np.zeros_like(voice)
    out[: min(len(y), len(voice))] = y[: len(voice)]
    return out


def voice_track(prod, mtl: dict, files: dict, work: Path, progress=None) -> dict:
    """Fit the clips `files` (line key -> clip path) onto the master timeline `mtl`, place them,
    polish and mix them. Used by the dub assembly (whole timeline) and the dub preview (a few
    sections). Returns the fit result, the mix stems and the dub's own timeline lines.

    Each line records `clip_t0` and `speed`: a moment τ of the original clip (e.g. a word time
    from the voice manifest) is heard at clip_t0 + τ / speed on the timeline."""
    st = prod.dub
    total = mtl["total"]
    keys = [ln["key"] for ln in mtl["lines"]]
    step = progress or (lambda i, what: None)
    step(1, "prepare clips")
    base = {k: prepare_clip(files[k], 1.0, work) for k in keys}
    dub_lines = {k: {"speech_start": c["lead"], "speech_end": c["end"]} for k, c in base.items()}
    step(2, "fit")
    res = fit(mtl, dub_lines, st)
    loud = [c["lufs"] for c in base.values() if c.get("lufs") is not None]
    target = float(np.median(loud)) if loud else None
    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n, dtype=np.float32)
    speech = np.zeros(n, dtype=bool)
    lines = []
    for p in res["placements"]:
        c = base[p["key"]] if p["speed"] <= 1.0 else prepare_clip(files[p["key"]], p["speed"], work)
        y, _ = sf.read(c["path"], dtype="float32")
        if st.level_match and target is not None and c.get("lufs") is not None:
            y = y * 10 ** (float(np.clip(target - c["lufs"], -6, 6)) / 20)
        t = p["onset"] - c["lead"]
        a = int(round(t * SR))
        b = min(n, a + len(y))
        if b > a:
            voice[a:b] += y[: b - a]
        speech[int(p["onset"] * SR): int(p["end"] * SR)] = True
        lines.append({"key": p["key"], "section": p["section"], "start": round(t, 4),
                      "speech_start": round(p["onset"], 4), "speech_end": round(p["end"], 4), "speed": p["speed"],
                      "clip_t0": round(t - c.get("trim_start", 0.0) / p["speed"], 4),
                      "lag": round(p["lag"], 3), "spill": round(p["spill"], 3)})
    step(3, "polish + mix")
    voice = _voice_chain(voice, st.voice_chain, work)
    stems = mix(voice, speech, total, prod.audio, work)
    return {"fit": res, "stems": stems, "lines": lines}


def _export_mp3(stem, dst: Path, total: float, bitrate: str, title: str, language: str) -> Path:
    """Voice-only MP3. The mono stem goes to both channels at full level ("-ac 2" would pan it
    3 dB down: the mix levels the voice as heard in stereo, so the MP3 duplicates the channel)."""
    part = tmp_path(dst)
    run(["ffmpeg", "-v", "error", "-y", "-i", stem, "-af", "pan=stereo|c0=c0|c1=c0", "-ar", "48000",
         "-c:a", "libmp3lame", "-b:a", bitrate, "-t", f"{total:.3f}", "-metadata", f"title={title} - voice-over",
         "-metadata", f"language={language}", "-f", "mp3", part], what="ffmpeg mp3 (voice-over)")
    part.replace(dst)
    return dst


def assemble(prod, narr, lang: str, master_asm: dict, man: dict, state) -> dict:
    """Dub version: fit, place, polish, mix (same music and treatment as the master), mux onto the
    master's picture (stream copy), and export the voice-only MP3."""
    ver = prod.versions[lang]
    work = prod.build_dir / "assemble" / lang
    work.mkdir(parents=True, exist_ok=True)
    mtl = read_json(resolve(master_asm["timeline"]))
    total = mtl["total"]
    want = [ln["key"] for _, ln in narr.lines()]
    if [ln["key"] for ln in mtl["lines"]] != want:
        raise StageFailed(f"{lang}: the master timeline does not hold every narration line in order; "
                          f"re-run the {ver.follow} version first")
    missing = [k for k in want if k not in man["lines"]]
    if missing:
        raise StageFailed(f"{lang}: no voice clip for {missing[:5]}")

    vt = voice_track(prod, mtl, {k: resolve(man["lines"][k]["file"]) for k in want}, work,
                     progress=lambda i, what: state.progress(f"assemble:{lang}", i, 5, what))
    sm, stems = vt["fit"]["summary"], vt["stems"]
    log.info(f"assemble {lang} (dub over {ver.follow}): {sm['lines']} lines; sped up {sm['sped_up']} "
             f"(max x{sm['max_speed']:.3f}); max lag {sm['max_lag']:.2f}s, max spill {sm['max_spill']:.2f}s; "
             f"{len(sm['overflow'])} overflowing segment(s)")

    state.progress(f"assemble:{lang}", 4, 5, "encode")
    master_mp4 = resolve(master_asm["final"])
    final = work / "final.mp4"
    part = tmp_path(final)
    v = prod.video
    title = f"{prod.title} ({ver.label.capitalize()})"
    run(["ffmpeg", "-v", "error", "-y", "-i", master_mp4, "-i", stems["mix"], "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", v.audio_bitrate, "-ar", "48000", "-ac", "2", "-sn", "-dn",
         "-t", f"{total:.3f}", "-movflags", "+faststart", "-metadata", f"title={title}",
         "-metadata:s:a:0", f"language={ver.audio_language}", part], log_file=work / "encode.log",
        what="ffmpeg mux (dub)")
    part.replace(final)
    mp3 = _export_mp3(stems["voice_stem"], work / "voiceover.mp3", total, prod.dub.mp3_bitrate, title,
                      ver.audio_language)
    Path(stems["mix"]).unlink(missing_ok=True)

    issues = {k: clip_issues(resolve(man["lines"][k]["file"]), man["lines"][k].get("words")) for k in want}
    sm["clip_issues"] = {k: v for k, v in issues.items() if v}
    tl = {"lang": lang, "mode": "dub", "follow": ver.follow, "total": total, "scenes": mtl["scenes"],
          "lines": vt["lines"], "fit": sm}
    atomic_write_json(work / "timeline.json", tl)
    state.progress(f"assemble:{lang}", 5, 5, "done")
    return {"lang": lang, "final": rel(final), "total": total, "timeline": rel(work / "timeline.json"),
            "voice_stem": rel(stems["voice_stem"]), "voiceover_mp3": rel(mp3),
            "music_stem": rel(stems["music_stem"]) if stems["music_stem"] else None, "fit": sm,
            "encode": {"video": f"stream copy of {ver.follow} ({rel(master_mp4)})", "audio": f"aac {v.audio_bitrate}",
                       "subtitle_filter": None, "subtitle_streams": 0}}


# ------------------------------------------------------------------ preview
def section_span(narr, sections: list[str]) -> list[str]:
    """The contiguous run of section keys from the first to the last one named."""
    order = [s["key"] for s in narr.sections]
    bad = [s for s in sections if s not in order]
    if bad or not sections:
        raise StageFailed(f"unknown section(s) {bad or sections}; sections: {order}")
    idx = sorted(order.index(s) for s in sections)
    return order[idx[0]: idx[-1] + 1]


def preview(prod, narr, lang: str, sections: list[str], state, *, paid: bool = False) -> dict:
    """Hear a dub before paying for all of it: the dub of a few sections over the master's final
    picture. Lines whose paid clip is cached use it. The others use the free draft voice, or with
    `paid=True` the paid voice (capped by the approved budget, cached for the real run)."""
    from . import voice as V
    ver = prod.versions[lang]
    if ver.mode != "dub":
        raise StageFailed(f"{lang} is not a dub version")
    master = state.stage(f"assemble:{ver.follow}")
    if master.get("status") != "done" or not resolve(master.get("final", "missing")).exists():
        raise StageFailed(f"the {ver.follow} master is not assembled yet",
                          remedy=f"python -m automatio run {prod.slug} --lang {ver.follow}")
    span = section_span(narr, sections)
    mtl = read_json(resolve(master["timeline"]))
    scenes = [s for s in mtl["scenes"] if s["section"] in span]
    t0, t1 = scenes[0]["offset"], scenes[-1]["offset"] + scenes[-1]["duration"]

    def shift(d, keys=("start", "speech_start", "speech_end", "offset")):
        return {k: (round(v - t0, 4) if k in keys else v) for k, v in d.items()}
    sub = {"total": round(t1 - t0, 4), "scenes": [shift(s) for s in scenes],
           "lines": [shift(ln) for ln in mtl["lines"] if ln["section"] in span]}

    prof = prod.profile(lang)
    jobs = [j for j in V.plan(prod, narr, lang, prof) if j.section in span]
    if paid and any(not j.cached for j in jobs):
        V.generate(prod, lang, prof, [j for j in jobs if not j.cached], state, approval=state.approval)
    files = {j.key: j.path for j in jobs if j.cached}
    stand_in = []
    if len(files) < len(jobs):
        draft = prod.profile(lang, draft=True)
        if draft.name == prof.name:
            raise StageFailed(f"{len(jobs) - len(files)} line(s) are not voiced and {prof.name} has no free draft "
                              "voice", remedy="Pass --paid to voice them (within the approved budget).")
        djobs = [j for j in V.plan(prod, narr, lang, draft) if j.section in span and j.key not in files]
        V.generate(prod, lang, draft, djobs, state, approval=None)
        files.update({j.key: j.path for j in djobs})
        stand_in = [j.key for j in djobs]

    name = span[0] if len(span) == 1 else f"{span[0]}-{span[-1]}"
    work = prod.build_dir / "preview" / lang / name
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    vt = voice_track(prod, sub, files, work)
    stems = vt["stems"]
    mp4 = work.parent / f"{name}.mp4"
    part = tmp_path(mp4)
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", resolve(master["final"]), "-i", stems["mix"],
         "-map", "0:v:0", "-map", "1:a:0", "-t", f"{sub['total']:.3f}", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", part], log_file=work / "encode.log", what="ffmpeg preview encode")
    part.replace(mp4)
    mp3 = _export_mp3(stems["voice_stem"], work.parent / f"{name}_voice.mp3", sub["total"], prod.dub.mp3_bitrate,
                      f"{prod.title} ({ver.label.capitalize()}) preview {name}", ver.audio_language)
    Path(stems["mix"]).unlink(missing_ok=True)
    sm = vt["fit"]["summary"]
    return {"lang": lang, "sections": span, "video": rel(mp4), "voice": rel(mp3),
            "from": round(t0, 2), "to": round(t1, 2), "lines": len(jobs),
            "paid_voice": len(jobs) - len(stand_in), "draft_voice": stand_in, "fit": sm}


# ------------------------------------------------------------------ checks
def checks(prod, lang: str, asm: dict, base_result: dict) -> list:
    """Dub-specific checks added to the generic verification of the finished version."""
    from .audio import loudness
    from .util import ffprobe
    out = []
    s = prod.dub
    fit_s = asm.get("fit") or read_json(resolve(asm["timeline"])).get("fit", {})
    over = fit_s.get("overflow", [])
    detail = (f"{fit_s['lines']} lines on the {prod.versions[lang].follow} timeline; sections and steps start on time"
              f"; {fit_s['sped_up']} line(s) sped up (max {(fit_s['max_speed'] - 1) * 100:.1f}%, limit "
              f"{(s.max_speedup - 1) * 100:.0f}%); lag max {fit_s['max_lag']:.2f}s / mean {fit_s['mean_lag']:.2f}s; "
              f"spill into the next line max {fit_s['max_spill']:.2f}s")
    if over:
        status = "fail"
        detail = (f"{len(over)} segment(s) do not fit even at {(s.max_speedup - 1) * 100:.0f}% faster - shorten the "
                  f"text of: " + "; ".join(f"{o['lines']} (+{o['over_by']:.2f}s)" for o in over[:6]))
    elif fit_s.get("lag_over") or fit_s.get("spill_over"):
        status = "warn"
        detail += (f"; over the limits: lag {fit_s.get('lag_over', [])[:6]}, spill {fit_s.get('spill_over', [])[:6]}")
    else:
        status = "pass"
    out.append({"check": "dub fit", "status": status, "detail": detail, "data": fit_s})

    ci = fit_s.get("clip_issues", {})
    out.append({"check": "voice clips", "status": "fail" if ci else "pass",
                "detail": ("re-voice: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in list(ci.items())[:8])) if ci else
                f"no clip ends cut off or clips; every line trimmed to its audio, faded, level-matched, "
                f"min {s.min_gap:.2f}s silence between lines", "data": ci})

    mp3 = resolve(asm["voiceover_mp3"])
    info = ffprobe(mp3)
    a = next((x for x in info.get("streams", []) if x.get("codec_type") == "audio"), {})
    dur = float(info.get("format", {}).get("duration", 0))
    br = int(info.get("format", {}).get("bit_rate", 0) or 0)
    ld = loudness(mp3)
    total = base_result.get("duration") or asm["total"]
    problems = []
    if a.get("codec_name") != "mp3":
        problems.append(f"codec {a.get('codec_name')}")
    if a.get("sample_rate") != "48000":
        problems.append(f"{a.get('sample_rate')} Hz")
    if br < 190_000:
        problems.append(f"{br // 1000} kbps")
    if abs(dur - total) > 0.06:
        problems.append(f"duration {dur:.3f}s vs video {total:.3f}s")
    li = ld["integrated_lufs"]
    if li is None or abs(li - prod.audio.voice_lufs) > 1.5:
        problems.append(f"loudness {li} LUFS")
    if ld["true_peak_dbtp"] is not None and ld["true_peak_dbtp"] > prod.audio.true_peak_max:
        problems.append(f"true peak {ld['true_peak_dbtp']} dBTP")
    out.append({"check": "voice-over mp3", "status": "fail" if problems else "pass",
                "detail": "; ".join(problems) or f"voice only, {dur:.2f}s (= video), 48 kHz, {br // 1000} kbps, "
                f"{li} LUFS, true peak {ld['true_peak_dbtp']} dBTP"})
    return out
