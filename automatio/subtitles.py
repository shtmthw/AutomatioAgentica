"""Subtitles (SRT + WebVTT) timed against each version's own narration.

Cross-language (e.g. English subtitles on the Hindi version): the subtitle is paired
sentence by sentence with the spoken narration - subtitle sentence i is shown while
spoken sentence i is heard - and long sentences are split at commas with the
sentence's time shared in proportion to length. (Unchanged from the previous
production; reproduces its .srt exactly.)

Same language (English subtitles on the English version): every cue is timed by the
words it contains, from the word timings of the narration itself. Subtitle words are
aligned with the spoken words, so lines with respelled terms ("run_command" spoken as
"run command") are word-timed too. Cue breaks are chosen per line by dynamic programming:
sentence ends first, then colons, commas and conjunctions, never after "the", "of",
"to"...; no flash cues, no cues over max_chars where a better break exists.

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


# ------------------------------------------------------------------ same language: word-timed cues
# Break preferences inside a line (lower = better place to end a cue).
_CONJ = {"and", "but", "or", "so", "because", "which", "who", "that", "while", "when", "then", "before", "after",
         "if", "until", "instead", "unless", "where"}
_FUNC = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "with", "by", "from", "as", "into", "is", "are", "was",
         "be", "its", "my", "your", "his", "her", "their", "our", "this", "these", "those", "than", "and", "or", "but",
         "it's", "we'll", "let's", "what", "how", "very", "not", "because", "which", "who", "while", "when", "if",
         "until", "unless", "where", "whether", "such", "like", "so"}
_VERB = {"is", "are", "was", "were"}


def _norm(tok: str) -> str:
    return re.sub(r"[^\w']", "", tok.lower().replace("’", "'"))


def token_times(subtitle: str, spoken: str, words: list) -> list[tuple[str, float, float]] | None:
    """(token, start, end) for every whitespace token of the subtitle, from the word timings of
    the spoken text. The spoken text may differ from the subtitle where words were respelled for
    the voice ("run_command" -> "run command", "index.html" -> "index dot H T M L"): subtitle and
    spoken tokens are aligned, and a respelled token takes the time of all its spoken words."""
    import difflib
    sub = subtitle.split()
    spk = spoken.split()
    if not sub or not spk or not words:
        return None
    ct = char_times(spoken, words)                       # (char index, start, end) per timed word
    pos, spans = 0, []
    for tok in spk:                                      # time span of every spoken token
        i = spoken.find(tok, pos)
        i = pos if i < 0 else i
        j = i + len(tok)
        pos = j
        inside = [(a, b) for k, a, b in ct if i <= k < j]
        spans.append((inside[0][0], inside[-1][1]) if inside else None)
    for k, s in enumerate(spans):                        # punctuation-only tokens: borrow a neighbour
        if s is None:
            prev = next((spans[m] for m in range(k - 1, -1, -1) if spans[m]), None)
            nxt = next((spans[m] for m in range(k + 1, len(spans)) if spans[m]), None)
            t = prev[1] if prev else (nxt[0] if nxt else 0.0)
            spans[k] = (t, t)
    sm = difflib.SequenceMatcher(a=[_norm(t) for t in sub], b=[_norm(t) for t in spk], autojunk=False)
    out: list = [None] * len(sub)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for d in range(i2 - i1):
                out[i1 + d] = spans[j1 + d]
        elif op == "replace":
            n, m = i2 - i1, j2 - j1
            for d in range(n):                           # share the spoken span in order
                a = j1 + (d * m) // n
                b = max(a + 1, j1 + ((d + 1) * m) // n)
                out[i1 + d] = (spans[a][0], spans[b - 1][1])
        elif op == "insert":                             # spoken words with no subtitle token: extend the previous
            if i1 > 0 and out[i1 - 1]:
                out[i1 - 1] = (out[i1 - 1][0], spans[j2 - 1][1])
    for k in range(len(out)):                            # subtitle tokens that are not spoken: zero length
        if out[k] is None:
            t = out[k - 1][1] if k and out[k - 1] else spans[0][0]
            out[k] = (t, t)
    return [(tok, a, b) for tok, (a, b) in zip(sub, out)]


def segment(toks: list[tuple[str, float, float]], max_chars=56, hard_max=68, min_chars=18) -> list[tuple[int, int]]:
    """Choose cue boundaries for one line by dynamic programming over its tokens.

    A cue should end where the speaker pauses in meaning: at a sentence end (best), then a
    colon or semicolon, a comma, before a conjunction; never right after "the", "of", "to"...
    Cues longer than max_chars, flashes shorter than a second and reading speeds above
    20 characters per second are penalised; two sentences share a cue only when that avoids
    a flash cue."""
    n = len(toks)
    text = [t for t, _, _ in toks]

    def brk(k: int) -> float:                            # cost of ending a cue after token k
        if k == n - 1:
            return 0.0
        t, nxt = text[k], _norm(text[k + 1])
        c = 0.0 if re.search(r"[.?!]['\"”)]?$", t) else 0.6 if re.search(r"[:;—–]$", t) else \
            1.2 if t.endswith(",") else 2.5 if nxt in _CONJ else 3.5 if nxt in _VERB else 5.0
        if _norm(t) in _FUNC and not re.search(r"[.,:;?!]$", t):
            c += 6.0
        return c

    def cost(i: int, j: int) -> float:                   # cue made of tokens i..j-1
        s = " ".join(text[i:j])
        L = len(s)
        d = toks[j - 1][2] - toks[i][1]
        c = 2.0
        if L > max_chars:
            c += (L - max_chars) * 1.0
        if L > hard_max:
            c += 200.0
        if L < min_chars - 4:
            c += (min_chars - 4 - L) * 0.25
        if d < 1.0:
            c += (1.0 - d) * 6.0
        cps = L / max(0.3, d + 0.35)
        if cps > 20:
            c += (cps - 20) * 0.8
        inner = sum(1 for k in range(i, j - 1) if re.search(r"[.?!]['\"”)]?$", text[k]))
        return c + 2.5 * inner

    best = [0.0] + [float("inf")] * n
    back = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - 40), j):
            v = best[i] + cost(i, j) + brk(j - 1)
            if v < best[j]:
                best[j], back[j] = v, i
    out, j = [], n
    while j > 0:
        out.append((back[j], j))
        j = back[j]
    return out[::-1]


def word_cues(start: float, subtitle: str, spoken: str, words: list,
              splitter: Splitter | None = None) -> list[tuple[float, float, str]] | None:
    """Same-language cues for one line, each timed from the first to the last word it contains."""
    toks = token_times(subtitle, spoken, words)
    if not toks:
        return None
    sp = splitter or Splitter()
    return [(start + toks[i][1], start + toks[j - 1][2], " ".join(t for t, _, _ in toks[i:j]))
            for i, j in segment(toks, sp.max_chars, sp.hard_max, sp.min_chars)]


def line_cues(start: float, subtitle: str, spoken: str, words: list, *, same_language: bool = False,
              splitter: Splitter | None = None) -> list[tuple[float, float, str]]:
    """Absolute (start, end, text) cues for one narration line."""
    sp = splitter or Splitter()
    whole = (words[0][0], words[-1][0] + words[-1][1])
    cues: list[list] = []
    if same_language:
        wc = word_cues(start, subtitle, spoken, words, sp)
        if wc:
            return wc
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


def finalize_words(cues, lead=0.08, tail=0.35, min_dur=0.9, min_gap=0.04):
    """Display times for word-timed cues (start = first word, end = last word): a cue is on screen
    `lead` before its first word and `tail` after its last, but never after its first word starts and
    never gone before its last word ends. When cues follow each other closely, the next cue gives up
    part of its lead instead of cutting the end of the previous one, and the previous one stays up
    until the next appears (no blink between them)."""
    n = len(cues)
    starts = []
    for i, (a, b, t) in enumerate(cues):
        s = a - lead
        if i:
            s = max(s, cues[i - 1][1] + min_gap)         # leave the previous cue up until its last word ends
        starts.append(max(0.0, min(s, a)))
    out = []
    for i, (a, b, t) in enumerate(cues):
        s = starts[i]
        e = max(b + tail, s + min_dur)
        if i + 1 < n:
            e = min(max(min(e, starts[i + 1] - min_gap), b),  # keep the last word covered ...
                    starts[i + 1] - min_gap / 2)            # ... but never touch the next cue (words < 40 ms apart)
        out.append((s, e, t))
    return out


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
    if same_language and all(len(c) == 3 for c in raw):
        return finalize_words(raw, settings.lead, settings.tail, settings.min_duration)
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
