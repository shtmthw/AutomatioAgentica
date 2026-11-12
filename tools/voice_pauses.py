"""Cap overlong pauses inside narration clips (free voices only).

The house English voice (edge-tts, Andrew) holds about half a second at many commas and colons
("So, ... why not", "Without it, ... the model") and sometimes hesitates in the middle of a
phrase where the text has no punctuation at all ("Every step ... adds more messages"). Heard
line after line, that sounds halting. The engine is deterministic, so re-voicing gives the same
take; this tool shortens the silence itself instead:

  * a pause after a word with no punctuation      -> at most 0.10 s
  * a pause at a comma, colon, semicolon or dash  -> at most 0.30 s
  * a pause between two sentences of one line     -> at most 0.60 s

Only silence is removed (from the quiet middle of each pause, with 5 ms crossfades): the speech
itself, its speed, pitch and intonation are untouched. The clip's word timings are shifted to
match, so cue markers and subtitles stay exact. The polished clip replaces the cached clip under
the same cache key (same text, same voice settings) and is marked in its metadata, so running
the tool again does nothing. Paid providers are refused (their clips are never rewritten).

    .venv/bin/python tools/voice_pauses.py <slug> [--lang en] [--keys s01_01,s02_03] [--dry-run]

Afterwards run `python -m automatio run <slug> --force voice` so the voice manifest, the renders
and the timeline are rebuilt from the polished clips.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automatio import providers  # noqa: E402
from automatio import voice as V  # noqa: E402
from automatio.pipeline import Pipeline  # noqa: E402
from automatio.util import atomic_write_json, now_iso, probe_duration  # noqa: E402

SR = 24000
CAPS = {"none": 0.10, "comma": 0.30, "sentence": 0.60}
QUIET_DB = -48.0          # below this (20 ms RMS) a frame counts as silence
MARGIN = 0.04             # silence kept on each side of a cut
FADE = 0.005


def boundaries(spoken: str, words: list) -> list[str]:
    """For each word but the last: what follows it in the text (none / comma / sentence)."""
    low = spoken.lower()
    cur, kinds = 0, []
    for _, _, w in words:
        token = re.sub(r"[^\w'%]", "", w.lower().split()[0]) if w.strip() else ""
        i = low.find(token, cur) if token else -1
        if i < 0:
            kinds.append("none")
            continue
        j = i
        # the engine may report several spoken words as one boundary ("20% to 60%"): skip to its end
        for part in w.lower().split():
            part = re.sub(r"[^\w'%]", "", part)
            k = low.find(part, j) if part else -1
            if k >= 0:
                j = k + len(part)
        while j < len(low) and (low[j].isalnum() or low[j] in "'_%"):
            j += 1
        k = j
        while k < len(low) and not low[k].isalnum():
            k += 1
        gap = low[j:k]
        kinds.append("sentence" if re.search(r"[.?!]", gap) else "comma" if re.search(r"[,:;—–]|\s-\s", gap)
                     else "none")
        cur = j
    return kinds[:-1]


def decode(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def encode(x: np.ndarray, path: Path):
    tmp = path.with_name(path.stem + ".polish.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "libmp3lame", "-b:a", "128k", str(tmp)], input=x.astype(np.float32).tobytes(), check=True)
    tmp.replace(path)


def quiet_run(db: np.ndarray, t0: float, t1: float, hop: float) -> tuple[float, float] | None:
    """Longest run of quiet frames inside [t0, t1] (seconds)."""
    a, b = max(0, int(t0 / hop)), min(len(db), int(t1 / hop))
    best, i = None, a
    while i < b:
        if db[i] < QUIET_DB:
            j = i
            while j < b and db[j] < QUIET_DB:
                j += 1
            if best is None or (j - i) > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    return (best[0] * hop, best[1] * hop) if best else None


def plan_cuts(x: np.ndarray, words: list, kinds: list, latency: float) -> list[tuple[float, float, str, float]]:
    hop = 0.005
    win = int(0.02 * SR)
    n = max(1, (len(x) - win) // int(hop * SR))
    frames = np.lib.stride_tricks.sliding_window_view(x, win)[:: int(hop * SR)][:n]
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    cuts = []
    for i, kind in enumerate(kinds):
        end = words[i][0] + words[i][1] + latency
        nxt = words[i + 1][0] + latency
        gap = nxt - end
        cap = CAPS[kind]
        if gap <= cap + 0.03:
            continue
        q = quiet_run(db, end - 0.06, nxt + 0.06, hop)
        if not q:
            continue
        qs, qe = q[0] + MARGIN, q[1] - MARGIN
        room = qe - qs
        remove = min(gap - cap, room)
        if remove < 0.03:
            continue
        mid = (qs + qe) / 2
        cuts.append((mid - remove / 2, mid + remove / 2, kind, round(gap, 3)))
    return cuts


def apply_cuts(x: np.ndarray, cuts: list) -> np.ndarray:
    f = int(FADE * SR)
    out, pos = [], 0
    for a, b, *_ in cuts:
        ia, ib = int(a * SR), int(b * SR)
        head = x[pos:ia].copy()
        tail_start = x[ib:ib + f].copy()
        if len(head) >= f and len(tail_start) == f:          # 5 ms crossfade across the cut
            ramp = np.linspace(1, 0, f, dtype=np.float32)
            head[-f:] = head[-f:] * ramp + tail_start * (1 - ramp)
            pos = ib + f
        else:
            pos = ib
        out.append(head)
    out.append(x[pos:])
    return np.concatenate(out)


def shift_words(words: list, cuts: list, latency: float) -> list:
    out = []
    for s, d, w in words:
        t = s + latency
        removed = sum(b - a for a, b, *_ in cuts if b <= t + 1e-6)
        out.append([round(s - removed, 4), d, w])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("slug")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--keys", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default="")
    a = ap.parse_args()

    p = Pipeline(a.slug)
    profile = p.prod.profile(a.lang)
    prov = providers.get(profile.provider)
    if prov.paid:
        sys.exit(f"{profile.name} is a paid voice ({prov.name}); its clips are never rewritten. Refusing.")
    latency = prov.latency(profile)
    jobs = V.plan(p.prod, p.narr, a.lang, profile)
    if a.keys:
        want = set(a.keys.split(","))
        jobs = [j for j in jobs if j.key in want]
    report, total = {}, 0.0
    for job in jobs:
        if not job.cached:
            print(f"{job.key}: not voiced yet (run the voice stage first)")
            continue
        meta = json.loads(job.meta.read_text())
        if (meta.get("meta") or {}).get("pause_polish"):
            report[job.key] = {"skipped": "already polished"}
            continue
        words = meta["words"]
        kinds = boundaries(job.spoken, words)
        x = decode(job.path)
        cuts = plan_cuts(x, words, kinds, latency)
        saved = sum(b - c for c, b, *_ in cuts)
        total += saved
        report[job.key] = {"cuts": [[round(c, 3), round(b, 3), k, g] for c, b, k, g in cuts], "saved": round(saved, 3)}
        desc = ", ".join(f"{k} {g:.2f}->{g - (b - c):.2f}" for c, b, k, g in cuts)
        print(f"{job.key}: -{saved:.2f}s  {desc}")
        if a.dry_run:
            continue
        y = apply_cuts(x, cuts) if cuts else x
        if cuts:
            encode(y, job.path)
        new_words = shift_words(words, cuts, latency) if cuts else words
        meta.update({"words": new_words, "duration": probe_duration(job.path)})
        meta.setdefault("meta", {})["pause_polish"] = {"caps": CAPS, "cuts": report[job.key]["cuts"],
                                                       "saved": round(saved, 3), "at": now_iso()}
        atomic_write_json(job.meta, meta)
    print(f"{len(jobs)} lines; {total:.1f} s of dead air removed{' (dry run)' if a.dry_run else ''}")
    if a.report:
        Path(a.report).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
