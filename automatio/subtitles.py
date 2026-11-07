"""Subtitles (SRT + WebVTT) timed against each version's own narration.

Cross-language (e.g. English subtitles on the Hindi version): the subtitle is paired
sentence by sentence with the spoken narration - subtitle sentence i is shown while
spoken sentence i is heard - and long sentences are split at commas with the
sentence's time shared in proportion to length. (Unchanged from the previous
production; reproduces its .srt exactly.)

Same language (English subtitles on the English version): every cue is timed by the
words it contains, from the word timings of the narration itself.

Subtitles are always separate files; nothing is ever burned into the picture.
"""
from __future__ import annotations

import re
from pathlib import Path

from .narration import char_times, sentences

DEFAULTS = {"max_chars": 56, "hard_max": 68, "min_chars": 18, "lead": 0.08, "tail": 0.35, "min_duration": 0.9}


def _is_latin(tok: str) -> bool:
    return bool(re.match(r"^[A-Za-z]", tok))


class Splitter:
    def __init__(self, max_chars=56, hard_max=68, min_chars=18):
        self.max_chars, self.hard_max, self.min_chars = max_chars, hard_max, min_chars

    def halve(self, s: str) -> list[str]:
        """Split an over-long chunk at the word gap nearest its middle, never between
        two English words (so terms like "Agentic AI" stay together)."""
        if len(s) <= self.hard_max or " " not in s:
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
        return self.halve(left) + self.halve(right)

    def chunk_cost(self, n: int) -> float:
        c = 1.0
        if n > self.max_chars:
            c += (n - self.max_chars) * 0.15
        if n > self.hard_max:
            c += 100
        if n < self.min_chars:
            c += (self.min_chars - n) * 0.3
        return c

    def split(self, text: str) -> list[str]:
        """Split into readable cues: at sentence ends, then commas, choosing the grouping
        with the lowest cost (no tiny flicker cues, no very long ones)."""
        if len(text) <= self.max_chars:
            return [text]
        pieces: list[str] = []
        for sent in (x.strip() for x in re.split(r"(?<=[।.?!])\s+", text) if x.strip()):
            if len(sent) <= self.max_chars:
                pieces.append(sent)
            else:
                pieces.extend(p.strip() for p in re.split(r"(?<=,)\s+", sent) if p.strip())
        n = len(pieces)
        best, best_cost = None, None
        for mask in range(1 << (n - 1)):
            groups, cur = [], [pieces[0]]
            for i in range(1, n):
                if mask >> (i - 1) & 1:
                    groups.append(" ".join(cur))
                    cur = []
                cur.append(pieces[i])
            groups.append(" ".join(cur))
            cost = sum(self.chunk_cost(len(g)) for g in groups)
            if best_cost is None or cost < best_cost:
                best, best_cost = groups, cost
        out: list[str] = []
        for g in best:
            out.extend(self.halve(g))
        return out


def _sentence_spans(spoken: str, sents: list[str], words: list):
    ct = char_times(spoken, words)
    spans, pos = [], 0
    for sent in sents:
        a = spoken.find(sent, pos)
        a = pos if a < 0 else a
        b = a + len(sent)
        pos = b
        inside = [c for c in ct if a <= c[0] < b]
        spans.append((inside[0][1], inside[-1][2]) if inside else None)
    return spans


def line_cues(start: float, subtitle: str, spoken: str, words: list, *, same_language: bool = False,
              splitter: Splitter | None = None) -> list[tuple[float, float, str]]:
    """Absolute (start, end, text) cues for one narration line."""
    sp = splitter or Splitter()
    whole = (words[0][0], words[-1][0] + words[-1][1])
    cues: list[list] = []
    if same_language and spoken == subtitle:
        ct = char_times(spoken, words)
        pos, ok = 0, True
        timed = []
        for sent in sentences(subtitle):
            for c in sp.split(sent):
                a = spoken.find(c, pos)
                if a < 0:
                    ok = False
                    break
                b = a + len(c)
                pos = b
                inside = [x for x in ct if a <= x[0] < b]
                if not inside:
                    ok = False
                    break
                timed.append([start + inside[0][1], start + inside[-1][2], c])
            if not ok:
                break
        if ok and timed:
            cues = timed
    if not cues:
        es = sentences(subtitle)
        hs = sentences(spoken)
        spans = _sentence_spans(spoken, hs, words) if len(es) == len(hs) else None
        if not spans or any(s is None for s in spans):
            es, spans = [subtitle], [whole]
        for (t0, t1), sent in zip(spans, es):
            chunks = sp.split(sent)
            total = sum(len(c) for c in chunks)
            t = t0
            for c in chunks:
                d = (t1 - t0) * len(c) / total
                cues.append([start + t, start + t + d, c])
                t += d
    for k in range(len(cues) - 1):          # contiguous within the line
        cues[k][1] = max(cues[k][1], cues[k + 1][0] - 0.05)
    return [tuple(c) for c in cues]


def finalize(cues, lead=0.08, tail=0.35, min_dur=0.9, min_gap=0.04):
    out = []
    for i, (a, b, t) in enumerate(cues):
        a = max(0.0, a - lead)
        b = max(b + tail, a + min_dur)
        if i + 1 < len(cues):
            b = min(b, cues[i + 1][0] - lead - min_gap)
        out.append((a, b, t))
    return out


def build(placed_lines: list[tuple[float, dict]], *, same_language: bool, settings) -> list[tuple]:
    """Cues for a whole version from (absolute start, voice-manifest entry) pairs."""
    sp = Splitter(settings.max_chars, settings.hard_max, settings.min_chars)
    raw = []
    for t, e in placed_lines:
        raw.extend(line_cues(t, e["subtitle"], e["spoken"], e["words"], same_language=same_language, splitter=sp))
    raw.sort(key=lambda c: c[0])
    return finalize(raw, settings.lead, settings.tail, settings.min_duration)


# ------------------------------------------------------------------ writers / readers
def _ts(t: float, sep: str) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def srt_text(cues) -> str:
    lines = []
    for i, (a, b, t) in enumerate(cues, 1):
        lines += [str(i), f"{_ts(a, ',')} --> {_ts(b, ',')}", t, ""]
    return "\n".join(lines)


def vtt_text(cues) -> str:
    out = ["WEBVTT", ""]
    for i, (a, b, t) in enumerate(cues, 1):
        esc = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        out += [str(i), f"{_ts(a, '.')} --> {_ts(b, '.')}", esc, ""]
    return "\n".join(out)


def _parse_ts(s: str) -> float:
    h, m, rest = s.strip().replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def parse(path: Path) -> list[tuple[float, float, str]]:
    """Read an .srt or .vtt back into (start, end, text) cues."""
    text = Path(path).read_text(encoding="utf-8")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        rows = block.strip().splitlines()
        for i, r in enumerate(rows):
            if "-->" in r:
                a, b = r.split("-->")
                body = "\n".join(rows[i + 1:]).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
                cues.append((_parse_ts(a), _parse_ts(b.split()[0]), body))
                break
    return cues


def check(cues, duration: float, settings) -> list[dict]:
    """Subtitle QA: order, overlaps, on-screen time, length, reading speed, bounds."""
    issues = []
    for i, (a, b, t) in enumerate(cues):
        n = i + 1
        if not t.strip():
            issues.append({"level": "fail", "cue": n, "issue": "empty cue"})
        if b <= a:
            issues.append({"level": "fail", "cue": n, "issue": f"ends before it starts ({a:.3f} -> {b:.3f})"})
        if i and a < cues[i - 1][1] - 1e-3:
            issues.append({"level": "fail", "cue": n, "issue": f"overlaps cue {n - 1}"})
        if i and a < cues[i - 1][0]:
            issues.append({"level": "fail", "cue": n, "issue": "out of order"})
        if b > duration + 0.05:
            issues.append({"level": "fail", "cue": n, "issue": f"ends after the video ({b:.2f}s > {duration:.2f}s)"})
        if len(t) > settings.hard_max:
            issues.append({"level": "warn", "cue": n, "issue": f"{len(t)} characters (> {settings.hard_max})"})
        if b - a < 0.5:
            issues.append({"level": "warn", "cue": n, "issue": f"on screen only {b - a:.2f}s"})
        cps = len(t) / max(1e-3, b - a)
        if cps > settings.max_cps:
            issues.append({"level": "warn", "cue": n, "issue": f"reading speed {cps:.0f} chars/s"})
    return issues
