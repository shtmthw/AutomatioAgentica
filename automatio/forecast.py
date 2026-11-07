"""Speech-length forecast: how long a voice will take to speak a text, before it is voiced.

Paid voices are expensive to get wrong. A dub line that is too long for its slot has to be
rewritten and voiced again, so it is paid for twice. This module predicts the speech length
of a line from its text, and `dub_forecast` runs the dub fitting (automatio/dub.py) on those
predictions. Lines that will not fit are named before a single credit is spent.

The model is a least-squares fit of speech length on simple text features: letters, sentence
ends, pauses (commas, colons, dashes), words, plus a constant. It is calibrated on every
cached clip of the same voice settings (cache/voice/<provider>/*.json, any production).
Speech length is measured exactly as the dub fitting measures it: the audible extent of the
clip (dub.audio_extent), not the provider's word timings. ElevenLabs alignments run ~0.45 s
past the audible end of a line, which would make every section look too long. With the house
Hindi voice (Adam, eleven_v4) the model is ~6.5 % (0.3 s) off per line; per segment the errors
partly cancel. Below MIN_SAMPLES cached clips it falls back to rates measured on the house
voices. Measured extents are memoised in cache/voice/<provider>/extents.cache.json.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import providers
from .util import atomic_write_json, read_json

MIN_SAMPLES = 24
_PAUSE = re.compile(r"[,;:—–]")
_END = re.compile(r"[।.?!](?=\s|$)")
_STRIP = re.compile(r"[\s।.?!,;:—–\-\"'()“”‘’]")
# fallback coefficients [letters, sentence ends, pauses, words, constant] in seconds of audible
# speech, fitted on the house voices (Nov 2026): Hindi Adam on eleven_v4 (135 clips),
# English Andrew on edge-tts (160 clips)
DEFAULT = {"hi": [0.0556, 0.56, 0.41, 0.109, -0.31], "en": [0.0534, 0.41, 0.35, 0.08, -0.54]}
GENERIC = [0.06, 0.5, 0.38, 0.09, -0.4]
_LOCK = threading.Lock()


def features(text: str) -> list[float]:
    t = text.strip()
    return [float(len(_STRIP.sub("", t))), float(len(_END.findall(t))), float(len(_PAUSE.findall(t))),
            float(len(t.split())), 1.0]


def audible(clip: Path) -> float:
    """Audible length of a clip (first to last moment with sound), memoised per clip file."""
    from .audio import decode
    from .dub import audio_extent
    memo = clip.parent / "extents.cache.json"
    with _LOCK:
        known = read_json(memo) or {}
        if clip.name in known:
            return float(known[clip.name])
    a0, a1 = audio_extent(decode(clip))
    with _LOCK:
        known = read_json(memo) or {}
        known[clip.name] = round(a1 - a0, 3)
        atomic_write_json(memo, known, indent=None)
    return a1 - a0


@dataclass
class DurationModel:
    coef: list
    samples: int = 0
    mae: float | None = None          # mean absolute error on the calibration clips (s)
    source: str = "default"
    measured: dict = field(default_factory=dict)    # exact spoken text -> measured audible length

    def predict(self, text: str) -> float:
        if text in self.measured:
            return self.measured[text]
        return max(0.4, float(np.dot(self.coef, features(text))))

    def describe(self) -> str:
        if self.source == "calibrated":
            return f"calibrated on {self.samples} cached clips (mean error {self.mae:.2f}s per line)"
        return "default speaking rates (too few cached clips of this voice to calibrate)"


_MODELS: dict = {}


def model_for(profile) -> DurationModel:
    """Duration model for a voice profile, calibrated on its cached clips."""
    prov = providers.get(profile.provider)
    fp = prov.fingerprint(profile)
    if fp in _MODELS:
        return _MODELS[fp]
    from .voice import cache_dir
    rows, measured = [], {}
    for meta in sorted(cache_dir(prov.name).glob("*.json")):
        d = read_json(meta) or {}
        clip = meta.with_suffix(f".{prov.ext}")
        if d.get("fingerprint") != fp or not d.get("text") or not clip.exists():
            continue
        span = audible(clip)
        if span > 0.2:
            rows.append((features(d["text"]), span))
            measured[d["text"]] = span
    base = DEFAULT.get(profile.language, GENERIC)
    if len(rows) >= MIN_SAMPLES:
        x = np.array([r[0] for r in rows])
        y = np.array([r[1] for r in rows])
        coef, *_ = np.linalg.lstsq(x, y, rcond=None)
        mae = float(np.abs(x @ coef - y).mean())
        m = DurationModel([float(c) for c in coef], len(rows), mae, "calibrated", measured)
    else:
        m = DurationModel(list(base), len(rows), None, "default", measured)
    _MODELS[fp] = m
    return m


def dub_forecast(prod, narr, lang: str, master_tl: dict, margin: float = 0.04) -> dict:
    """Fit the dub on predicted line lengths (measured where a clip of the exact text is cached).

    Returns the fit summary plus, per segment, the predicted need against its window:
      fits     - fits at the predicted lengths, even with `margin` (4 %) added to unvoiced lines
      tight    - fits at the predicted lengths, but not with the margin
      overflow - does not fit even at max_speedup: shorten these lines before voicing them
    A negative `margin` asks the optimistic question the voice stage's guard uses: does the
    segment overflow even if every unvoiced line comes out that much shorter?
    """
    from . import dub
    from . import voice as V
    prof = prod.profile(lang)
    model = model_for(prof)
    jobs = {j.key: j for j in V.plan(prod, narr, lang, prof)}
    lens, known = {}, {}
    for key, j in jobs.items():
        known[key] = j.cached
        lens[key] = audible(j.path) if j.cached else model.predict(j.send)

    def run(extra: float) -> dict:
        lines = {k: {"speech_start": 0.0, "speech_end": d * (1.0 if known[k] else 1.0 + extra)}
                 for k, d in lens.items()}
        return dub.fit(master_tl, lines, prod.dub)

    base, padded = (run(margin), run(0.0)) if margin < 0 else (run(0.0), run(margin))
    over = {tuple(o["lines"]): o for o in base["summary"]["overflow"]}
    over_m = {tuple(o["lines"]): o for o in padded["summary"]["overflow"]}
    placed = {p["key"]: p for p in base["placements"]}
    slots = line_slots(master_tl, prod.dub)
    segs = []
    for sg in dub.segments(master_tl, prod.dub):
        keys = tuple(ln["key"] for ln in sg["lines"])
        window = sg["end"] - sg["lines"][0]["speech_start"]
        need = sum(lens[k] for k in keys) + prod.dub.min_gap * (len(keys) - 1)
        last = placed[keys[-1]]
        status = "overflow" if keys in over else ("tight" if keys in over_m else "fits")
        segs.append({"section": sg["section"], "lines": list(keys), "window": round(window, 2),
                     "need": round(need, 2), "status": status, "speed": last["speed"],
                     "slack": round(last["segment_end"] - last["end"], 2),
                     "over_by": over[keys]["over_by"] if keys in over else None,
                     "unvoiced": [k for k in keys if not known[k]]})
    return {"lang": lang, "model": model.describe(), "summary": base["summary"], "segments": segs,
            "lines": {k: {"seconds": round(lens[k], 2), "measured": known[k], "slot": slots.get(k)} for k in lens},
            "at_risk": [s for s in segs if s["status"] != "fits"]}


def line_slots(master_tl: dict, settings) -> dict:
    """Seconds each line has on its own: from its master line's speech onset (the earliest a dub
    line may start) to the next master line's onset in its segment, or to the segment's end. A
    dub line longer than its slot (x max_speedup) pushes its neighbours; the last line of a
    segment longer than its slot cannot fit at all."""
    from . import dub
    out = {}
    for sg in dub.segments(master_tl, settings):
        lines = sg["lines"]
        for i, ln in enumerate(lines):
            end = lines[i + 1]["speech_start"] - settings.min_gap if i + 1 < len(lines) else sg["end"]
            out[ln["key"]] = round(end - ln["speech_start"], 2)
    return out
