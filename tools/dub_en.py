"""
English dub: the finished video, narrated in English by Microsoft Andrew
(edge-tts, config.EN_VOICE). Andrew speaks exactly the English subtitles, and
each subtitle cue while that cue is on screen.

Nothing is re-rendered: the picture and the burned-in subtitles are copied
untouched from output/<FINAL_NAME>.mp4, only the audio is new.

  1. The subtitle cues are rebuilt from the same timeline as tools/build.py and
     checked against output/<FINAL_NAME>.srt (they must be identical).
  2. Every English sentence is spoken as one utterance (natural intonation) with
     word timings. Cached in assets/voice_en/, so re-runs are offline and free.
  3. A sentence's words never start before their cue appears and are over
     before the next cue appears (the last one before its subtitle goes). If a
     sentence would outrun its cues it is re-spoken faster (5 % steps, up to
     EN_MAX_RATE). English is usually quicker than the Hindi, so a sentence split
     over two cues would have to wait at the cut: it may then be spoken slower
     (down to EN_MIN_RATE) and start a little late (up to EN_MAX_LATE), and the
     remaining wait goes to a comma (spoken-only commas: EN_PRONUNCIATION).
  4. The voice is levelled to VOICE_LUFS, the music is ducked under it, and the
     audio is muxed with the existing video.

    python -m tools.dub_en
      -> output/agentic_ai_intro_en_1080p.mp4   video + English voice
         output/agentic_ai_intro_en_audio.mp3   the audio alone (e.g. a YouTube audio track)
         build/dub_en_report.txt                every cue: on screen vs spoken
"""
from __future__ import annotations

import asyncio
import hashlib
import json

import numpy as np

from agentic_video import config as C
from agentic_video.pronunciation import EN_PRONUNCIATION, apply as pronounce
from tools import build, subtitles, tts

SR = build.SR
MARGIN = 0.05            # spoken words end at least this long before their cue disappears
LAT = 0.045              # edge-tts word times run this far ahead of the decoded audio (measured)
TOL = 0.04               # a cue may start this much before its speech time (still after it appears)
FADE = int(0.006 * SR)   # short fade where a sentence is cut to insert silence


# ------------------------------------------------------------------ cues
def sentences():
    """English sentences with their subtitle cues, on the final video's clock.

    Returns (sentences, total) where each sentence is
    {"text": str, "cues": [{"text", "at" (Hindi speech start), "show", "hide"}, ...]}."""
    _, lines, total = build.timeline()
    raw, groups = [], []
    for t, entry in lines:
        cues, grouped = subtitles.line_cues(t, entry, grouped=True)
        groups += [(s, [len(raw) + i for i in idx]) for s, idx in grouped]
        raw += cues
    order = sorted(range(len(raw)), key=lambda i: raw[i][0])     # same (stable) order as build.assemble
    final = subtitles.finalize([raw[i] for i in order])
    shown = {i: final[k] for k, i in enumerate(order)}

    check = C.BUILD / "dub_en_check.srt"
    subtitles.write_srt(final, check)
    srt = C.OUTPUT / f"{C.FINAL_NAME}.srt"
    if not srt.exists() or srt.read_text(encoding="utf-8") != check.read_text(encoding="utf-8"):
        raise SystemExit(f"{srt.name} is missing or out of date: run `python -m tools.build assemble` first")

    out = [{"text": s, "cues": [{"text": raw[i][2], "at": raw[i][0],
                                 "show": shown[i][0], "hide": shown[i][1]} for i in idx]}
           for s, idx in groups]
    return out, total


# ------------------------------------------------------------------ voice
class Voice:
    """edge-tts clips of whole sentences, cached by (voice, rate, pitch, text)."""

    def __init__(self):
        C.EN_VOICE_DIR.mkdir(parents=True, exist_ok=True)
        self.path = C.EN_VOICE_DIR / "manifest.json"
        self.cache = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.sem = asyncio.Semaphore(4)
        self.made = 0

    async def speak(self, text: str, rate: int) -> dict:
        key = hashlib.sha1(f"edge-en-1|{C.EN_VOICE}|{rate}|{C.EN_VOICE_PITCH}|{text}".encode()).hexdigest()[:16]
        mp3 = C.EN_VOICE_DIR / f"{key}.mp3"
        if key not in self.cache or not mp3.exists():
            async with self.sem:
                words = await tts.synth_edge(text, mp3, voice=C.EN_VOICE, rate=f"{rate:+d}%",
                                             pitch=C.EN_VOICE_PITCH)
            self.cache[key] = {"text": text, "rate": rate, "file": mp3.name,
                               "duration": build.probe_duration(mp3), "words": words}
            self.made += 1
        return self.cache[key]

    def save(self):
        self.path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1))


# ------------------------------------------------------------------ placement
def spoken_form(sent: dict) -> tuple[str, list[int]]:
    """The text sent to the voice, and where each cue ends in it."""
    parts = [pronounce(c["text"], EN_PRONUNCIATION) for c in sent["cues"]]
    ends, pos = [], -1
    for p in parts:
        pos += 1 + len(p)
        ends.append(pos)
    return " ".join(parts), ends


def owners(spoken: str, ends: list[int], words: list) -> tuple[list[int], list[bool]]:
    """For each spoken word: the index of the cue it belongs to (by character
    position), and whether a comma-like pause mark follows it in the text."""
    own, comma, pos = [], [], 0
    for _, _, w in words:
        i = spoken.find(w, pos)
        if i < 0 or i - pos > 3 + len(w):     # not found close by: assume it is the next word
            i = pos
        pos = i + len(w)
        own.append(next((k for k, e in enumerate(ends) if i < e), len(ends) - 1))
        comma.append(spoken[pos: pos + 1] in (",", ";", ":"))
    return own, comma


def place(sent: dict, clip: dict, late: float = 0.0) -> dict:
    """Where every cue's words land on the timeline when this clip is used and the
    sentence starts `late` seconds after its first cue's speech time.

    Rules: a cue's words start no earlier than the cue's speech time (its subtitle
    appears 0.08 s before that) and are over before the next cue of the sentence
    appears; the sentence's last cue is over MARGIN before its subtitle disappears.
    Where the English is quicker than the subtitles, silence is added before the
    cue's first word: at the cut itself when that is a comma, otherwise (or when
    the pause would be long) mostly at the previous cue's last comma."""
    spoken, ends = spoken_form(sent)
    words, cues = clip["words"], sent["cues"]
    own, comma = owners(spoken, ends, words)
    n, nw = len(cues), len(words)
    first = [own.index(j) if j in own else None for j in range(n)]
    last = [nw - 1 - own[::-1].index(j) if j in own else None for j in range(n)]
    if None in first:
        raise ValueError(f"could not map words to cues for: {sent['text']!r}")
    w_on = [o + LAT for o, _, _ in words]
    w_off = [o + d + LAT for o, d, _ in words]

    origin = cues[0]["at"] + late - w_on[0]    # timeline time of the clip's t=0
    add = [0.0] * nw                           # silence inserted before each word
    pauses, shift = [], 0.0                    # shift = total silence before cue j's first word
    for j in range(1, n):
        need = cues[j]["at"] - (origin + w_on[first[j]])
        if need <= shift + TOL:
            continue
        x = need - shift
        at_cut_comma = comma[last[j - 1]]
        # silence that must stay at the cut so the previous cue is over when cue j appears
        y = min(x, max(0.0, x - (cues[j]["show"] - (origin + w_off[last[j - 1]] + shift))))
        inner = [k for k in range(first[j - 1], last[j - 1]) if comma[k]]
        if inner and (not at_cut_comma or x > 0.6):
            y = max(y, x / 2) if at_cut_comma else y
            add[inner[-1] + 1] += x - y
            pauses.append((x - y, True))
        else:
            y = x
        add[first[j]] += y
        pauses.append((y, at_cut_comma))
        shift = need
    sh = np.cumsum(add)                        # total shift of every word

    pieces, cut_from = [], 0.0
    for k in range(1, nw):
        if add[k] > 1e-6:
            cut = (w_off[k - 1] + w_on[k]) / 2  # in the word gap
            pieces.append((cut_from, cut, origin + sh[k - 1]))
            cut_from = cut
    pieces.append((cut_from, clip["duration"], origin + sh[-1]))

    rows = [{"cue": cues[j],
             "start": origin + w_on[first[j]] + sh[first[j]],
             "end": origin + w_off[last[j]] + sh[last[j]],
             "limit": cues[j + 1]["show"] if j + 1 < n else cues[j]["hide"] - MARGIN}
            for j in range(n)]
    slack = min(r["limit"] - r["end"] for r in rows)
    pauses = [(x, c) for x, c in pauses if x > 1e-3]
    # how unnatural the result sounds: added pauses (a short one at a comma is fine,
    # any mid-phrase pause is bad), a pace away from the base, a late start
    cost = (sum(max(0.0, x - 0.2) if at_comma else 2.5 * x for x, at_comma in pauses)
            + 0.02 * abs(clip["rate"] - C.EN_VOICE_RATE) + 0.8 * late)
    return {"clip": clip, "rows": rows, "pieces": pieces, "slack": slack,
            "pauses": pauses, "late": late, "cost": cost}


async def fit(sent: dict, voice: Voice) -> dict:
    """Spoken at the base pace; faster only as much as needed to fit its cues. A
    sentence that would pause between its cues may be slowed a little and start a
    little late, whichever sounds most natural."""
    text = spoken_form(sent)[0]
    for rate in range(C.EN_VOICE_RATE, C.EN_MAX_RATE + 1, 5):
        plan = place(sent, await voice.speak(text, rate))
        if plan["slack"] >= 0:
            break
    if plan["slack"] < 0 or rate > C.EN_VOICE_RATE or not plan["pauses"]:
        return plan                            # (slack < 0: best effort, reported below)
    for rate in range(C.EN_VOICE_RATE, C.EN_MIN_RATE - 1, -5):
        clip = await voice.speak(text, rate)
        for late in np.arange(0.0, C.EN_MAX_LATE + 1e-6, 0.05):
            p = place(sent, clip, float(late))
            if p["slack"] >= 0 and p["cost"] < plan["cost"]:
                plan = p
    return plan


# ------------------------------------------------------------------ audio
def quietest(clip: np.ndarray, t: float, reach: float = 0.04) -> int:
    """The quietest 5 ms within `reach` of time t (a cut in a word gap): word
    timings are approximate, so this keeps cuts out of the words themselves."""
    hop = int(0.005 * SR)
    lo, hi = max(0, int((t - reach) * SR)), min(len(clip), int((t + reach) * SR))
    if hi - lo < 2 * hop:
        return int(round(t * SR))
    frames = np.lib.stride_tricks.sliding_window_view(clip[lo:hi] ** 2, hop)[::hop // 5]
    return lo + int(np.argmin(frames.mean(axis=1))) * (hop // 5) + hop // 2


def render(plans: list[dict], total: float):
    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n, dtype=np.float32)
    speech = np.zeros(n, dtype=bool)
    ramp = np.linspace(0, 1, FADE, dtype=np.float32)
    for p in plans:
        clip = build.decode(C.EN_VOICE_DIR / p["clip"]["file"])
        pieces = p["pieces"]
        cuts = [quietest(clip, b) for _, b, _ in pieces[:-1]]   # sample index of every cut
        bounds = [0] + cuts + [len(clip)]
        for k, (a, b, at) in enumerate(pieces):
            seg = clip[bounds[k]: bounds[k + 1]].copy()
            a = bounds[k] / SR
            if k > 0:
                seg[:FADE] *= ramp[: len(seg)]
            if k < len(p["pieces"]) - 1:
                seg[-FADE:] *= ramp[::-1][-len(seg):]
            i = int(round((at + a) * SR))
            seg = seg[: max(0, n - i)]
            voice[i: i + len(seg)] += seg
        for r in p["rows"]:
            speech[int(r["start"] * SR): int(r["end"] * SR)] = True
    return voice, speech


def report(plans: list[dict], total: float) -> str:
    def ts(t):
        return f"{int(t // 60)}:{t % 60:05.2f}"
    out = [f"English dub ({C.EN_VOICE}), {total:.1f}s",
           "subtitle on screen     | words spoken           | rate | text", ""]
    for p in plans:
        for r in p["rows"]:
            c = r["cue"]
            ok = "" if c["show"] <= r["start"] and r["end"] <= r["limit"] else "  <-- OUTSIDE"
            out.append(f"{ts(c['show'])}-{ts(c['hide'])} | {ts(r['start'])}-{ts(r['end'])} | "
                       f"{p['clip']['rate']:+3d}% | {c['text']}{ok}")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ main
async def plan_all():
    sents, total = sentences()
    voice = Voice()
    try:
        plans = await asyncio.gather(*(fit(s, voice) for s in sents))
    finally:
        voice.save()
    print(f"{len(sents)} sentences, {sum(len(s['cues']) for s in sents)} subtitle cues "
          f"({voice.made} new clip(s) from {C.EN_VOICE})")
    return plans, total


def main():
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    src = C.OUTPUT / f"{C.FINAL_NAME}.mp4"
    plans, total = asyncio.run(plan_all())
    if abs(build.probe_duration(src) - total) > 0.1:
        raise SystemExit(f"{src.name} does not match the timeline: run `python -m tools.build assemble` first")

    rows = [(p, r) for p in plans for r in p["rows"]]
    bad = [r for _, r in rows if not (r["cue"]["show"] <= r["start"] and r["end"] <= r["limit"])]
    faster = [p for p in plans if p["clip"]["rate"] > C.EN_VOICE_RATE]
    rep = C.BUILD / "dub_en_report.txt"
    rep.write_text(report(plans, total), encoding="utf-8")
    print(f"  {len(rows) - len(bad)}/{len(rows)} cues spoken inside their subtitle; "
          f"{len(faster)} sentence(s) sped up (max {max([p['clip']['rate'] for p in plans]):+d}%) -> {rep}")
    for r in bad:
        print(f"  outside: {r['cue']['text']!r}")

    print("mixing audio ...")
    voice, speech = render(plans, total)
    mix = build.mix_voice(voice, speech, total, tag="_en")

    out = C.OUTPUT / f"{C.EN_FINAL_NAME}.mp4"
    print("muxing (video copied, not re-encoded) ...")
    build.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", mix, "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart",
               "-metadata", "title=Agentic AI - The Beginning", "-metadata:s:a:0", "language=eng", str(out)])
    mp3 = C.OUTPUT / f"{C.EN_FINAL_NAME.replace('_1080p', '')}_audio.mp3"
    build.run(["ffmpeg", "-v", "error", "-y", "-i", mix, "-c:a", "libmp3lame", "-b:a", "256k",
               "-metadata", "title=Agentic AI - The Beginning (English)", str(mp3)])
    print(f"done -> {out}  ({build.probe_duration(out):.1f}s)\n        {mp3}")


if __name__ == "__main__":
    main()
