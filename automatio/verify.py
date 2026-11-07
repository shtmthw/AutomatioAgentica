"""Quality checks on a finished version. Each check is pass / warn / fail with numbers;
any fail stops delivery.

  container      1 H.264 video + 1 AAC stereo audio stream, configured size/fps, no subtitle streams
  duration       container, video, audio and timeline agree
  completeness   every narration line is in the video exactly once, in script order
  loudness       integrated loudness and true peak on target (EBU R128)
  subtitles      SRT and VTT parse, agree, and have no overlaps / order / bounds problems
  subtitle text  the cues contain the whole subtitle-language script, in order
  sync           narration energy is covered by subtitles and every cue has narration under it
  subtitles (xx) [subtitles] own_language: the version's own-language files parse, agree, cover its
                 whole script in order and sit over its own speech
  no burn-in     the encode used no subtitle filter, and the subtitle band of sampled frames is clear
  layout         layout warnings reported by the scenes while rendering
  timing         actual section lengths vs the production plan (informational; names sections >20% off)
"""
from __future__ import annotations

import subprocess

import numpy as np

from . import subtitles as subs
from .audio import loudness, speech_frames
from .narration import display
from .plan import parse_plan
from .secrets import scrubbed_env
from .util import ffprobe, read_json, resolve

BG_RGB = (11, 17, 20)     # style.BG #0b1114


def _c(name, status, detail, **data):
    return {"check": name, "status": status, "detail": detail, **({"data": data} if data else {})}


def _band_frames(path, times, w, h, y0, y1) -> list[float]:
    """Fraction of non-background pixels in the band y0..y1 at each time."""
    out = []
    for t in times:
        cp = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                             "-vf", f"crop={w}:{y1 - y0}:0:{y0}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            capture_output=True, env=scrubbed_env())
        if cp.returncode or not cp.stdout:
            continue
        px = np.frombuffer(cp.stdout, np.uint8).reshape(-1, 3).astype(np.int16)
        diff = np.abs(px - np.array(BG_RGB, np.int16)).max(axis=1)
        out.append(float((diff > 48).mean()))
    return out


def _own_subtitles(prod, narr, lang: str, files: dict, duration: float, act, fr) -> dict:
    parsed = {fmt: subs.parse(resolve(p)) for fmt, p in files.items()}
    base = next(iter(parsed.values()))
    agree = all(len(c) == len(base) and all(abs(x[0] - y[0]) < 0.002 and abs(x[1] - y[1]) < 0.002 and x[2] == y[2]
                                            for x, y in zip(c, base)) for c in parsed.values())
    issues = subs.check(base, duration, prod.subtitles)
    fails = [i for i in issues if i["level"] == "fail"]
    expect = " ".join(display(ln[lang]) for _, ln in narr.lines()).split()
    shown = " ".join(t for _, _, t in base).split()
    covered = np.zeros(len(act), bool)
    for a, b, _ in base:
        covered[int(a / fr): max(int(a / fr) + 1, int(b / fr))] = True
    cov = float((act & covered).sum() / max(1, int(act.sum())))
    problems = []
    if not agree:
        problems.append("formats differ")
    if fails:
        problems.append(f"{len(fails)} error(s): {fails[0]['issue']} (cue {fails[0]['cue']})")
    if expect != shown:
        problems.append(f"cue text differs from the {lang} script ({len(shown)} vs {len(expect)} words)")
    status = "fail" if problems else ("warn" if cov < 0.9 or len(issues) > len(fails) else "pass")
    detail = "; ".join(problems) or (f"{len(base)} {lang} cues in {', '.join(parsed)}; complete {lang} script in "
                                     f"order; {cov * 100:.1f}% of the {lang} speech under a cue"
                                     + (f"; {len(issues)} warning(s)" if issues else ""))
    return _c(f"subtitles ({lang})", status, detail, speech_coverage=round(cov, 4), issues=issues[:20])


def verify(prod, narr, lang: str, asm: dict, sub_files: dict, man: dict, own_files: dict | None = None) -> dict:
    checks = []
    v = prod.video
    final = resolve(asm["final"])
    tl = read_json(resolve(asm["timeline"]))
    total = tl["total"]

    # ---- container
    info = ffprobe(final)
    st = info.get("streams", [])
    vs = [s for s in st if s.get("codec_type") == "video"]
    as_ = [s for s in st if s.get("codec_type") == "audio"]
    ss = [s for s in st if s.get("codec_type") == "subtitle"]
    problems = []
    if len(vs) != 1:
        problems.append(f"{len(vs)} video streams")
    else:
        s = vs[0]
        num, den = (int(x) for x in s.get("avg_frame_rate", "0/1").split("/"))
        fps = num / den if den else 0
        if s.get("codec_name") != "h264":
            problems.append(f"video codec {s.get('codec_name')}")
        if (s.get("width"), s.get("height")) != (v.width, v.height):
            problems.append(f"size {s.get('width')}x{s.get('height')} (expected {v.width}x{v.height})")
        if abs(fps - v.fps) > 0.01:
            problems.append(f"{fps:.2f} fps (expected {v.fps})")
        if s.get("pix_fmt") != "yuv420p":
            problems.append(f"pix_fmt {s.get('pix_fmt')}")
    if len(as_) != 1:
        problems.append(f"{len(as_)} audio streams")
    else:
        a = as_[0]
        if a.get("codec_name") != "aac" or int(a.get("channels", 0)) != 2 or a.get("sample_rate") != "48000":
            problems.append(f"audio {a.get('codec_name')} {a.get('channels')}ch {a.get('sample_rate')}Hz")
        tag = (a.get("tags") or {}).get("language")
        if tag != prod.versions[lang].audio_language:
            problems.append(f"audio language tag {tag!r}")
    if ss:
        problems.append(f"{len(ss)} subtitle stream(s) embedded")
    checks.append(_c("container", "fail" if problems else "pass",
                     "; ".join(problems) or f"h264 {v.width}x{v.height}@{v.fps} + aac stereo 48 kHz "
                     f"[{prod.versions[lang].audio_language}], no subtitle streams"))

    # ---- duration
    fdur = float(info["format"]["duration"])
    vdur = float(vs[0].get("duration", fdur)) if vs else 0
    adur = float(as_[0].get("duration", fdur)) if as_ else 0
    bad = abs(fdur - total) > 0.1 or abs(vdur - adur) > 0.15
    checks.append(_c("duration", "fail" if bad else "pass",
                     f"container {fdur:.2f}s, video {vdur:.2f}s, audio {adur:.2f}s, timeline {total:.2f}s",
                     seconds=round(fdur, 2)))

    # ---- completeness
    want = [ln["key"] for _, ln in narr.lines()]
    got = [ln["key"] for ln in tl["lines"]]
    if got == want:
        checks.append(_c("completeness", "pass", f"all {len(want)} narration lines placed once, in order"))
    else:
        missing = [k for k in want if k not in got]
        checks.append(_c("completeness", "fail", f"missing {missing[:8]}, order/extra differs", missing=missing))

    # ---- loudness
    ld = loudness(final)
    li, tp = ld["integrated_lufs"], ld["true_peak_dbtp"]
    au = prod.audio
    ok = li is not None and abs(li - au.voice_lufs) <= au.loudness_tolerance and tp is not None and tp <= au.true_peak_max
    checks.append(_c("loudness", "pass" if ok else "fail",
                     f"{li} LUFS integrated (target {au.voice_lufs}±{au.loudness_tolerance}), true peak {tp} dBTP "
                     f"(max {au.true_peak_max})", **ld))

    # ---- subtitles
    parsed = {fmt: subs.parse(resolve(p)) for fmt, p in sub_files.items()}
    base = next(iter(parsed.values()))
    agree = all(len(c) == len(base) and all(abs(x[0] - y[0]) < 0.002 and abs(x[1] - y[1]) < 0.002 and x[2] == y[2]
                                            for x, y in zip(c, base)) for c in parsed.values())
    issues = subs.check(base, fdur, prod.subtitles)
    fails = [i for i in issues if i["level"] == "fail"]
    warns = [i for i in issues if i["level"] == "warn"]
    status = "fail" if fails or not agree else ("warn" if warns else "pass")
    checks.append(_c("subtitles", status,
                     f"{len(base)} cues in {', '.join(parsed)}; " + ("formats agree" if agree else "FORMATS DIFFER")
                     + (f"; {len(fails)} error(s)" if fails else "") + (f"; {len(warns)} warning(s)" if warns else ""),
                     issues=issues[:20]))

    # ---- subtitle text coverage
    expect = " ".join(display(ln[prod.subtitles.language]) for _, ln in narr.lines()).split()
    shown = " ".join(t for _, _, t in base).split()
    checks.append(_c("subtitle text", "pass" if expect == shown else "fail",
                     "cues contain the complete subtitle script in order" if expect == shown else
                     f"cue text differs from the script ({len(shown)} vs {len(expect)} words)"))

    # ---- sync (energy of the narration stem vs cue windows)
    act, fr = speech_frames(resolve(asm["voice_stem"]))
    covered = np.zeros(len(act), bool)
    empty_cues = 0
    for a, b, _ in base:
        i0, i1 = int(a / fr), max(int(a / fr) + 1, int(b / fr))
        covered[i0:i1] = True
        if not act[i0:i1].any():
            empty_cues += 1
    speech_n = int(act.sum())
    cov = float((act & covered).sum() / max(1, speech_n))
    ok = cov >= 0.97 and empty_cues == 0
    checks.append(_c("sync", "pass" if ok else ("warn" if cov >= 0.9 else "fail"),
                     f"{cov * 100:.1f}% of narration is under a subtitle; {empty_cues} cue(s) without narration",
                     speech_coverage=round(cov, 4), silent_cues=empty_cues))
    if own_files:
        checks.append(_own_subtitles(prod, narr, lang, own_files, fdur, act, fr))

    # ---- burned-in subtitles
    enc = asm.get("encode", {})
    times = [(a + b) / 2 for a, b, _ in base[:: max(1, len(base) // 12)]][:12]
    y0, y1 = int(v.height * 0.885), int(v.height * 0.975)
    fr_band = _band_frames(final, times, v.width, v.height, y0, y1)
    busy = [f for f in fr_band if f > 0.005]
    if enc.get("subtitle_filter") or enc.get("subtitle_streams"):
        checks.append(_c("no burn-in", "fail", f"encode used subtitles: {enc}"))
    else:
        checks.append(_c("no burn-in", "warn" if len(busy) >= 3 else "pass",
                         f"no subtitle filter in the encode; subtitle band (y {y0}-{y1}) clear in "
                         f"{len(fr_band) - len(busy)}/{len(fr_band)} sampled frames under subtitle cues",
                         band_fill=[round(x, 4) for x in fr_band]))

    # ---- layout lint from the renders
    lint = []
    for s in tl["scenes"]:
        cues = read_json(resolve(s["mp4"]).with_name("cues.json")) or {}
        lint += [dict(x, section=s["section"]) for x in cues.get("lint", [])]
    checks.append(_c("layout", "warn" if lint else "pass",
                     f"{len(lint)} layout warning(s) from the scenes" if lint else "no content outside the frame "
                     "or below the subtitle safe line", warnings=lint[:20]))

    # ---- planned timing (info)
    try:
        plan = {p.number: p for p in parse_plan(prod.plan)}
    except Exception:
        plan = {}
    rows = []
    for s, sec in zip(tl["scenes"], narr.sections):
        p = plan.get(sec.get("plan_section") or "")
        rows.append({"section": s["section"], "actual": round(s["duration"], 1),
                     "planned": p.target if p else None})
    planned = sum(r["planned"] for r in rows if r["planned"])
    off = [f"{r['section']} {r['actual']:.0f}s vs {r['planned']:.0f}s ({(r['actual'] / r['planned'] - 1) * 100:+.0f}%)"
           for r in rows if r["planned"] and abs(r["actual"] / r["planned"] - 1) > 0.2]
    checks.append(_c("timing", "info", f"total {fdur / 60:.1f} min" + (f" (plan: {planned / 60:.1f} min)" if planned else "")
                     + (f"; more than 20% off the plan: {', '.join(off)}" if off else ""), sections=rows))

    worst = "fail" if any(c["status"] == "fail" for c in checks) else (
        "warn" if any(c["status"] == "warn" for c in checks) else "pass")
    return {"lang": lang, "status": worst, "checks": checks, "duration": round(fdur, 3)}
