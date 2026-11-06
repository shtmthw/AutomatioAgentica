"""
Subtitle generation (SRT + styled ASS) from the voice manifest and the
per-scene cue timings, so subtitles follow the narration word timings.

Long narration lines are split into shorter cues at punctuation; each cue is
timed with the TTS word boundaries.
"""
from __future__ import annotations

import re

MAX_CHARS = 56      # preferred maximum per cue
HARD_MAX = 68       # above this a chunk is split at the word gap nearest its middle
MIN_CHARS = 18      # fragments shorter than this are glued to a neighbour (avoids flicker)


def _is_latin(tok: str) -> bool:
    return bool(re.match(r"^[A-Za-z]", tok))


def _halve(s: str) -> list[str]:
    """Split an over-long chunk at the word gap nearest its middle, never between
    two English words (so terms like "Agentic AI" stay together)."""
    if len(s) <= HARD_MAX or " " not in s:
        return [s]
    toks = s.split(" ")
    mid = len(s) / 2
    best, best_cost, pos = None, None, 0
    for i in range(1, len(toks)):
        pos += len(toks[i - 1]) + 1
        cost = abs(pos - mid) + (1000 if _is_latin(toks[i - 1]) and _is_latin(toks[i]) else 0)
        if best_cost is None or cost < best_cost:
            best, best_cost = i, cost
    left, right = " ".join(toks[:best]), " ".join(toks[best:])
    return _halve(left) + _halve(right)


def _chunk_cost(n: int) -> float:
    c = 1.0                                  # every extra cue costs a little
    if n > MAX_CHARS:
        c += (n - MAX_CHARS) * 0.15
    if n > HARD_MAX:
        c += 100
    if n < MIN_CHARS:
        c += (MIN_CHARS - n) * 0.3
    return c


def _split(text: str) -> list[str]:
    """Split a line into readable cues: at sentence ends, then commas, choosing the
    grouping of pieces with the lowest cost (no tiny flicker cues, no very long ones)."""
    if len(text) <= MAX_CHARS:
        return [text]
    pieces: list[str] = []
    for sent in (x.strip() for x in re.split(r"(?<=[।.?!])\s+", text) if x.strip()):
        if len(sent) <= MAX_CHARS:
            pieces.append(sent)
        else:
            pieces.extend(p.strip() for p in re.split(r"(?<=,)\s+", sent) if p.strip())
    n = len(pieces)
    best, best_cost = None, None
    for mask in range(1 << (n - 1)):          # bit i set -> cut after piece i
        groups, cur = [], [pieces[0]]
        for i in range(1, n):
            if mask >> (i - 1) & 1:
                groups.append(" ".join(cur))
                cur = []
            cur.append(pieces[i])
        groups.append(" ".join(cur))
        cost = sum(_chunk_cost(len(g)) for g in groups)
        if best_cost is None or cost < best_cost:
            best, best_cost = groups, cost
    out: list[str] = []
    for g in best:
        out.extend(_halve(g))
    return out


def _char_times(tts: str, words: list) -> list[tuple[int, float, float]]:
    """(char_index_in_tts, start, end) for every word boundary."""
    out, pos = [], 0
    for off, dur, w in words:
        i = tts.find(w, pos)
        if i < 0:
            i = pos
        out.append((i, off, off + dur))
        pos = i + len(w)
    return out


def _sentences(text: str, enders: str) -> list[str]:
    return [x.strip() for x in re.split(rf"(?<=[{enders}])\s+", text.strip()) if x.strip()]


def _sentence_spans(spoken: str, sentences: list[str], words: list):
    """(start, end) of each spoken sentence, from the word timings."""
    ct = _char_times(spoken, words)
    spans, pos = [], 0
    for sent in sentences:
        a = spoken.find(sent, pos)
        a = pos if a < 0 else a
        b = a + len(sent)
        pos = b
        inside = [c for c in ct if a <= c[0] < b]
        spans.append((inside[0][1], inside[-1][2]) if inside else None)
    return spans


def line_cues(start: float, entry: dict) -> list[tuple[float, float, str]]:
    """Absolute (start, end, text) cues for one narration line.

    The subtitle (entry["text"], English) is paired sentence-by-sentence with the
    spoken narration (entry["tts"], Hindi): subtitle sentence i is shown while
    spoken sentence i is heard. Long sentences are split at commas, with the
    sentence's time shared in proportion to length."""
    shown, spoken, words = entry["text"], entry["tts"], entry["words"]
    whole = (words[0][0], words[-1][0] + words[-1][1])
    es = _sentences(shown, ".?!।")
    hs = _sentences(spoken, "।?!.")
    spans = _sentence_spans(spoken, hs, words) if len(es) == len(hs) else None
    if not spans or any(sp is None for sp in spans):
        es, spans = [shown], [whole]
    cues = []
    for (t0, t1), sent in zip(spans, es):
        chunks = _split(sent)
        total = sum(len(c) for c in chunks)
        t = t0
        for c in chunks:
            d = (t1 - t0) * len(c) / total
            cues.append([start + t, start + t + d, c])
            t += d
    for k in range(len(cues) - 1):          # contiguous within the line
        cues[k][1] = max(cues[k][1], cues[k + 1][0] - 0.05)
    return [tuple(c) for c in cues]


def finalize(cues: list[tuple[float, float, str]], lead=0.08, tail=0.35, min_gap=0.04):
    out = []
    for i, (a, b, t) in enumerate(cues):
        a = max(0.0, a - lead)
        b = max(b + tail, a + 0.9)                       # minimum on-screen time
        if i + 1 < len(cues):
            b = min(b, cues[i + 1][0] - lead - min_gap)  # never overlap the next cue
        out.append((a, b, t))
    return out


def _ts_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ts_ass(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_srt(cues, path):
    lines = []
    for i, (a, b, t) in enumerate(cues, 1):
        lines += [str(i), f"{_ts_srt(a)} --> {_ts_srt(b)}", t, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Subs,{font},46,&H00EFECE6,&H00EFECE6,&H00141109,&H96141109,0,0,0,0,100,100,0,0,1,2.6,0,2,160,160,44,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def write_ass(cues, path):
    from agentic_video import config as C
    rows = [ASS_HEADER.replace("{font}", C.SUB_FONT)]
    for a, b, t in cues:
        t = t.replace("\n", "\\N")
        rows.append(f"Dialogue: 0,{_ts_ass(a)},{_ts_ass(b)},Subs,,0,0,0,,{{\\fad(120,120)}}{t}\n")
    path.write_text("".join(rows), encoding="utf-8")
