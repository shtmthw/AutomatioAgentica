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
  * what still does not fit is reported (the text has to be rewritten shorter), never cut.

Audio treatment (the voice-over is a deliverable of its own):

  * placement uses each clip's real audio extent (energy), not the provider's word timings;
  * every clip is trimmed to its audio, gets a 10 ms fade-in and a 50 ms fade-out (no clicks,
    no hard cuts), and - with `level_match` - is levelled to the same loudness (±6 dB at most);
  * the voice track goes through `voice_chain` (high-pass, de-esser, gentle compression), then the
    house mix (-16 LUFS, look-ahead limiter, ducked music);
  * clips whose ending is cut off by the provider are found by `clip_issues`; the voice stage
    re-takes them (`retakes`), and verification fails while any remain.

The dub shares the master's subtitle files (same picture, same lines in the same slots).
Outputs: <work>/final.mp4 (master picture, untouched + dub mix) and voiceover.mp3 (voice only,
same duration as the video, 48 kHz, `mp3_bitrate`).
"""
from __future__ import annotations

import hashlib
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
    h = hashlib.sha1(f"prep-2|{src.name}|{src.stat().st_size}|{speed:.3f}".encode()).hexdigest()[:16]
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
    info = {"lead": b0, "end": b1, "duration": len(y) / SR, "lufs": loud, "speed": speed}
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


def assemble(prod, narr, lang: str, master_asm: dict, man: dict, state) -> dict:
    """Dub version: fit, place, polish, mix (same music and treatment as the master), mux onto the
    master's picture (stream copy), and export the voice-only MP3."""
    ver = prod.versions[lang]
    st = prod.dub
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

    state.progress(f"assemble:{lang}", 1, 5, "prepare clips")
    base = {k: prepare_clip(resolve(man["lines"][k]["file"]), 1.0, work) for k in want}
    dub_lines = {k: {"speech_start": c["lead"], "speech_end": c["end"]} for k, c in base.items()}
    state.progress(f"assemble:{lang}", 2, 5, "fit")
    res = fit(mtl, dub_lines, st)
    sm = res["summary"]
    log.info(f"assemble {lang} (dub over {ver.follow}): {sm['lines']} lines; sped up {sm['sped_up']} "
             f"(max x{sm['max_speed']:.3f}); max lag {sm['max_lag']:.2f}s, max spill {sm['max_spill']:.2f}s; "
             f"{len(sm['overflow'])} overflowing segment(s)")
    loud = [c["lufs"] for c in base.values() if c.get("lufs") is not None]
    target = float(np.median(loud)) if loud else None
    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n, dtype=np.float32)
    speech = np.zeros(n, dtype=bool)
    for p in res["placements"]:
        c = base[p["key"]] if p["speed"] <= 1.0 else prepare_clip(resolve(man["lines"][p["key"]]["file"]), p["speed"], work)
        y, _ = sf.read(c["path"], dtype="float32")
        if st.level_match and target is not None and c.get("lufs") is not None:
            y = y * 10 ** (float(np.clip(target - c["lufs"], -6, 6)) / 20)
        t = p["onset"] - c["lead"]
        a = int(round(t * SR))
        b = min(n, a + len(y))
        if b > a:
            voice[a:b] += y[: b - a]
        speech[int(p["onset"] * SR): int(p["end"] * SR)] = True
    state.progress(f"assemble:{lang}", 3, 5, "polish + mix")
    voice = _voice_chain(voice, st.voice_chain, work)
    stems = mix(voice, speech, total, prod.audio, work)

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
    mp3 = work / "voiceover.mp3"
    part = tmp_path(mp3)
    # mono stem -> stereo at full level in both channels ("-ac 2" would pan it 3 dB down: the mix
    # levels the voice as heard in stereo, so the MP3 must duplicate the channel, not pan it)
    run(["ffmpeg", "-v", "error", "-y", "-i", stems["voice_stem"], "-af", "pan=stereo|c0=c0|c1=c0", "-ar", "48000",
         "-c:a", "libmp3lame", "-b:a", st.mp3_bitrate, "-t", f"{total:.3f}", "-metadata", f"title={title} - voice-over",
         "-metadata", f"language={ver.audio_language}", "-f", "mp3", part], what="ffmpeg mp3 (voice-over)")
    part.replace(mp3)
    Path(stems["mix"]).unlink(missing_ok=True)

    issues = {k: clip_issues(resolve(man["lines"][k]["file"]), man["lines"][k].get("words")) for k in want}
    issues = {k: v for k, v in issues.items() if v}
    lines = [{"key": p["key"], "section": p["section"], "start": round(p["onset"] - (base[p["key"]]["lead"] / p["speed"]), 4),
              "speech_start": round(p["onset"], 4), "speech_end": round(p["end"], 4), "speed": p["speed"],
              "lag": round(p["lag"], 3), "spill": round(p["spill"], 3)} for p in res["placements"]]
    sm["clip_issues"] = issues
    tl = {"lang": lang, "mode": "dub", "follow": ver.follow, "total": total, "scenes": mtl["scenes"],
          "lines": lines, "fit": sm}
    atomic_write_json(work / "timeline.json", tl)
    state.progress(f"assemble:{lang}", 5, 5, "done")
    return {"lang": lang, "final": rel(final), "total": total, "timeline": rel(work / "timeline.json"),
            "voice_stem": rel(stems["voice_stem"]), "voiceover_mp3": rel(mp3),
            "music_stem": rel(stems["music_stem"]) if stems["music_stem"] else None, "fit": sm,
            "encode": {"video": f"stream copy of {ver.follow} ({rel(master_mp4)})", "audio": f"aac {v.audio_bitrate}",
                       "subtitle_filter": None, "subtitle_streams": 0}}


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
