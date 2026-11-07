"""The narration script: markers, spoken text, sentences, narration.json, script ingest
and completeness checks.

narration.json (one per production, tracked in git) holds every narration line in
every language, grouped into sections (one section = one scene):

    {"schema": "automatio.narration/1", "title": "...", "source_language": "en",
     "sections": [{"key": "s01", "chapter": {"number": "01", "title": "Introduction"},
                   "plan_section": "01",
                   "lines": [{"key": "s01_01", "topic": "The error an agent can fix",
                              "en": "Imagine you're running a program, and suddenly an {error}error appears.",
                              "hi": "मान लीजिए, कोई प्रोग्राम चलाते समय अचानक एक {error}Error आ गया।"}]}],
     "excluded": [{"text": "...", "reason": "visual direction, not narration"}]}

Cue markers `{name}` (lowercase) sit directly before the word at which an animation
should happen. They are removed before speech and subtitles; the voice stage records
the time of the word that follows each marker, and scenes use `v.cue("name")`. The
same marker names must appear in every language, which is what keeps one scene file
in sync with every language's narration.

`topic` (optional, English, a few words) marks a line where a key topic starts. The
deliver stage turns topics into each version's topics.txt with that version's own
times. Topics are metadata: they never change what is spoken, rendered or reviewed.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path

from .errors import InputError
from .util import atomic_write_json, file_fp, read_json

SCHEMA = "automatio.narration/1"
MARKER = re.compile(r"\{([a-z][a-z0-9_]*)\}")
TAG = re.compile(r"\s*\[[^\]]+\]\s*")          # ElevenLabs audio tags, e.g. [warmly]
ENDERS = ".?!।"
KEY = re.compile(r"^[a-z0-9][a-z0-9_]*$")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
SCRIPTS = {"hi": DEVANAGARI, "mr": DEVANAGARI, "bn": re.compile(r"[ঀ-৿]")}
META_KEYS = ("topic",)          # line fields that are metadata only (never spoken, rendered or timed)
TOPIC_MAX = 60


# ------------------------------------------------------------------ text
def pronounce(text: str, table: dict | None) -> str:
    """Replace every dictionary word by its spoken form (case-sensitive, whole word,
    longest entry first). Subtitles never use this; only what is spoken changes."""
    if not table:
        return text
    for word in sorted(table, key=len, reverse=True):
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", table[word], text)
    return text


def compose(text: str, table: dict | None = None, strip_tags: bool = False) -> tuple[str, dict[str, int]]:
    """Text with markers removed (pronunciation applied, audio tags optionally
    stripped) and the character position of every marker in the result.

    The pronunciation table is applied segment by segment between markers, so
    marker positions stay exact even when respellings change the length."""
    parts = MARKER.split(text)
    out, pos = "", {}
    for i, part in enumerate(parts):
        if i % 2:
            pos[part] = len(out)
            continue
        seg = TAG.sub(" ", part) if strip_tags else part
        seg = pronounce(seg, table)
        if out.endswith(" ") and seg.startswith(" "):
            seg = seg.lstrip(" ")
        out += seg
    lead = len(out) - len(out.lstrip())
    out = out.strip()
    return out, {k: min(max(0, v - lead), len(out)) for k, v in pos.items()}


def display(text: str) -> str:
    """What is shown (subtitles): no markers, no audio tags, no respelling."""
    return compose(text, None, strip_tags=True)[0]


def markers_in(text: str) -> list[str]:
    return MARKER.findall(text or "")


def sentences(text: str) -> list[str]:
    return [x.strip() for x in re.split(rf"(?<=[{ENDERS}])\s+", text.strip()) if x.strip()]


def char_times(spoken: str, words: list) -> list[tuple[int, float, float]]:
    """(character index in `spoken`, start, end) for every timed word."""
    out, pos = [], 0
    for off, dur, w in words:
        i = spoken.find(w, pos)
        if i < 0:
            i = pos
        out.append((i, off, off + dur))
        pos = i + len(w)
    return out


def marker_times(spoken: str, words: list, positions: dict[str, int]) -> dict[str, float]:
    """Time (relative to the clip) of the first word at or after each marker."""
    ct = char_times(spoken, words)
    end = words[-1][0] + words[-1][1] if words else 0.0
    return {name: next((s for i, s, _ in ct if i >= p), end) for name, p in positions.items()}


# ------------------------------------------------------------------ narration.json
class Narration:
    def __init__(self, path: Path, data: dict):
        self.path, self.data = Path(path), data

    @property
    def sections(self) -> list[dict]:
        return self.data.get("sections", [])

    def section(self, key: str) -> dict:
        for s in self.sections:
            if s["key"] == key:
                return s
        raise KeyError(key)

    def lines(self):
        for s in self.sections:
            for ln in s.get("lines", []):
                yield s, ln

    def line(self, key: str) -> dict:
        for _, ln in self.lines():
            if ln["key"] == key:
                return ln
        raise KeyError(key)

    def text(self, line: dict, lang: str) -> str | None:
        return line.get(lang)

    def spoken_source(self, line: dict, lang: str) -> str:
        """The text the voice speaks before pronunciation: an explicit `spoken` override
        for this language if present, otherwise the line text."""
        return (line.get("spoken") or {}).get(lang) or line[lang]

    def languages_present(self) -> set:
        langs = set()
        for _, ln in self.lines():
            langs |= {k for k in ln if len(k) <= 3 and k != "key" and isinstance(ln[k], str)}
        return langs

    def topics(self) -> list[tuple[str, str]]:
        """(line key, topic) in narration order."""
        return [(ln["key"], ln["topic"].strip()) for _, ln in self.lines()
                if isinstance(ln.get("topic"), str) and ln["topic"].strip()]

    def save(self) -> None:
        atomic_write_json(self.path, self.data, indent=2)


def content_fingerprint(path: Path) -> str:
    """Fingerprint of narration.json without its metadata fields (topics).

    A file without metadata keeps its plain file fingerprint. With metadata, the file is
    fingerprinted as `Narration.save()` would write it without those fields, which is
    byte-identical to the file before they were added. So adding or editing topics never
    invalidates renders, drafts or a visual review that are otherwise up to date."""
    data = read_json(path)
    if not isinstance(data, dict):
        return file_fp(path)
    stripped, found = json.loads(json.dumps(data)), False
    for s in stripped.get("sections", []):
        for ln in s.get("lines", []):
            for k in META_KEYS:
                if k in ln:
                    ln.pop(k)
                    found = True
    if not found:
        return file_fp(path)
    canon = json.dumps(stripped, ensure_ascii=False, indent=2, default=str) + "\n"
    return hashlib.sha1(canon.encode("utf-8")).hexdigest()[:20]


def load_narration(path: Path) -> Narration | None:
    data = read_json(path)
    if data is None:
        return None
    if not isinstance(data, dict) or "sections" not in data:
        raise InputError(f"{path.name} is not a narration file (no `sections`)")
    return Narration(path, data)


def validate(narr: Narration, *, langs: list[str], subtitle_lang: str, source_lang: str,
             marker_langs: list[str] | None = None, dub_langs: list[str] | None = None) -> dict:
    """Structure + per-language checks. Returns {"errors": [...], "warnings": [...]}.

    `marker_langs`: languages that must carry the same cue markers as the source (default: all).
    `dub_langs`: dub versions. They are not rendered (no markers needed) and are not subtitled
    (they share the master's subtitles), so sentence parity is a warning, and a line that quotes
    on-screen English verbatim is allowed (warning)."""
    dub_langs = set(dub_langs or [])
    errors, warnings = [], []
    if narr.data.get("schema") != SCHEMA:
        warnings.append(f"schema should be {SCHEMA!r}")
    if not narr.sections:
        errors.append("no sections")
    seen_s, seen_l = set(), set()
    required = list(dict.fromkeys([source_lang, subtitle_lang, *langs]))
    for s in narr.sections:
        k = s.get("key", "")
        if not KEY.match(k) or k in seen_s:
            errors.append(f"section key {k!r} is invalid or duplicated")
        seen_s.add(k)
        ch = s.get("chapter")
        if ch is not None and not (isinstance(ch, dict) and "title" in ch):
            errors.append(f"[{k}] chapter must be {{'number': '01', 'title': '...'}} or null")
        if not s.get("lines"):
            errors.append(f"[{k}] has no lines")
        for ln in s.get("lines", []):
            lk = ln.get("key", "")
            where = f"[{lk}]"
            if not KEY.match(lk) or lk in seen_l:
                errors.append(f"line key {lk!r} is invalid or duplicated")
            seen_l.add(lk)
            if "topic" in ln:
                t = ln["topic"]
                if not isinstance(t, str) or not t.strip() or "\n" in t:
                    errors.append(f"{where} topic must be a short one-line string")
                elif len(t) > TOPIC_MAX:
                    warnings.append(f"{where} topic is {len(t)} characters; keep it under {TOPIC_MAX} (a few words)")
                elif DEVANAGARI.search(t):
                    warnings.append(f"{where} topic {t!r} should be English (it goes into the video description)")
            missing = [l for l in required if not (ln.get(l) or "").strip()]
            if missing:
                errors.append(f"{where} missing text for: {', '.join(missing)}")
                continue
            marks = {l: markers_in(ln[l]) for l in required}
            for l, m in marks.items():
                if len(m) != len(set(m)):
                    errors.append(f"{where} {l}: a marker is used twice in one line: {m}")
                for bad in re.findall(r"\{[^}]*\}", MARKER.sub("", ln[l])):
                    warnings.append(f"{where} {l}: {bad!r} is not a valid marker (use lowercase {{name}})")
            ref = marks[source_lang]
            for l, m in marks.items():
                if marker_langs is not None and l not in marker_langs:
                    continue
                if set(m) != set(ref):
                    errors.append(f"{where} markers differ: {source_lang}={ref} {l}={m}")
                elif m != ref:
                    warnings.append(f"{where} marker order differs ({source_lang}={ref} {l}={m}); "
                                    "animations cued later in one language play immediately in the other")
            ns = {l: len(sentences(display(ln[l]))) for l in required}
            for l in langs:
                if l != subtitle_lang and ns[l] != ns[subtitle_lang]:
                    (warnings if l in dub_langs else errors).append(
                        f"{where} {l} has {ns[l]} sentence(s) but the {subtitle_lang} subtitle text has "
                        f"{ns[subtitle_lang]}; subtitle sentence i is shown while sentence i is spoken")
            for l in required:
                pat = SCRIPTS.get(l)
                if pat and not pat.search(ln[l]):
                    (warnings if l in dub_langs else errors).append(
                        f"{where} {l} text contains no {l} script characters (untranslated?)")
                if l != source_lang and display(ln[l]) == display(ln[source_lang]):
                    (warnings if l in dub_langs else errors).append(
                        f"{where} {l} text is identical to {source_lang} (untranslated, or quoted verbatim)")
                if l in SCRIPTS and re.search(r"[0-9%&/=+]", display(ln[l])):
                    warnings.append(f"{where} {l}: digits/symbols ({display(ln[l])!r}) - spell them out as spoken")
            if source_lang in ln:
                for l in langs:
                    if l != source_lang:
                        r = len(display(ln[l])) / max(1, len(display(ln[source_lang])))
                        if not 0.55 <= r <= 1.8:
                            warnings.append(f"{where} {l} is {r:.2f}x the length of {source_lang}; "
                                            "check nothing was dropped or added")
    return {"errors": errors, "warnings": warnings}


# ------------------------------------------------------------------ script ingest
_DIRECTION = re.compile(r"^\s*(\[.*\]|\(.*\)|(VISUAL|ON[- ]SCREEN|SFX|MUSIC|NOTE|TIME|CUT TO|SCENE)\s*:.*)\s*$",
                        re.I | re.S)
_ABBREV = re.compile(r"\b(e\.g|i\.e|etc|vs|Mr|Mrs|Ms|Dr|St|No|approx)\.$", re.I)


def _strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            return text[end + 4:]
    return text


def parse_script(path: Path) -> dict:
    """Markdown / plain-text script -> title, sections (heading + narration paragraphs)
    and excluded direction paragraphs. Nothing is rewritten."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise InputError(f"script not found: {path}") from None
    except UnicodeDecodeError:
        raise InputError(f"{path.name} is not UTF-8 text; convert it (Markdown or .txt) first") from None
    text = re.sub(r"<!--.*?-->", "", _strip_front_matter(text), flags=re.S)
    title, sections, excluded = None, [], []
    heads = [(len(m.group(1)), m.group(2).strip()) for m in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.M)]
    levels = sorted({lv for lv, _ in heads})
    top = levels[0] if levels else None
    if top == 1 and sum(1 for lv, _ in heads if lv == 1) == 1 and len(levels) > 1:
        sec_level = levels[1]
    else:
        sec_level = top
    cur = None
    para: list[str] = []

    def flush():
        nonlocal para, cur
        if para:
            p = " ".join(x.strip() for x in para).strip()
            para = []
            if not p:
                return
            if _DIRECTION.match(p) or p.startswith(">"):
                excluded.append({"text": p, "reason": "direction/note (not narration)"})
                return
            if cur is None:
                cur = {"heading": None, "paragraphs": []}
                sections.append(cur)
            cur["paragraphs"].append(p)

    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            flush()
            lv, h = len(m.group(1)), m.group(2).strip()
            if lv == 1 and title is None and sec_level != 1:
                title = h
                continue
            if lv <= (sec_level or lv):
                cur = {"heading": h, "paragraphs": []}
                sections.append(cur)
            else:
                excluded.append({"text": h, "reason": "sub-heading"})
            continue
        if not line.strip():
            flush()
            continue
        para.append(re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", line))
    flush()
    sections = [s for s in sections if s["paragraphs"]]
    return {"title": title, "sections": sections, "excluded": excluded}


def split_sentences(p: str) -> list[str]:
    raw = sentences(p)
    out: list[str] = []
    for s in raw:   # re-join splits after abbreviations ("e.g. this")
        if out and _ABBREV.search(out[-1]):
            out[-1] += " " + s
        else:
            out.append(s)
    return out


def group_sentences(sents: list[str], max_chars: int = 170, max_sents: int = 2) -> list[str]:
    """Group sentences into narration lines (one voice clip / animation beat each)."""
    lines, cur = [], []
    for s in sents:
        joined = " ".join(cur + [s])
        if cur and (len(joined) > max_chars or (len(cur) >= max_sents and len(joined) > 100)):
            lines.append(" ".join(cur))
            cur = []
        cur.append(s)
    if cur:
        lines.append(" ".join(cur))
    return lines


def _heading_parts(h: str | None, idx: int) -> tuple[str, str]:
    if not h:
        return f"{idx:02d}", ""
    m = re.match(r"^\s*(?:part|chapter|section|scene)?\s*(\d{1,2})\s*[.):\-–]?\s*(.*)$", h, re.I)
    num, title = (f"{int(m.group(1)):02d}", m.group(2)) if m else (f"{idx:02d}", h)
    title = re.sub(r"\s*TIME:.*$", "", title, flags=re.I).strip()
    return num, title.split(":")[0].strip() or title


def ingest(prod, plan_sections: list) -> dict:
    """Create narration.json data (source language only) from the supplied script."""
    parsed = parse_script(prod.script)
    if not parsed["sections"]:
        raise InputError(f"{prod.script.name} contains no narration text")
    lang = prod.source_language
    by_num = {p.number: p for p in plan_sections}
    sections = []
    for i, s in enumerate(parsed["sections"], 1):
        num, title = _heading_parts(s["heading"], i)
        if not title and i - 1 < len(plan_sections):
            title = plan_sections[i - 1].short_title
        key = f"s{i:02d}"
        lines = []
        for p in s["paragraphs"]:
            for text in group_sentences(split_sentences(p)):
                lines.append({"key": f"{key}_{len(lines) + 1:02d}", lang: text})
        plan_ref = num if num in by_num else (plan_sections[i - 1].number if len(plan_sections) == len(parsed["sections"]) else None)
        sections.append({"key": key, "chapter": {"number": num, "title": title or f"Part {i}"},
                         "plan_section": plan_ref, "lines": lines})
    return {"schema": SCHEMA, "title": parsed["title"] or prod.title, "source_language": lang,
            "sections": sections, "excluded": parsed["excluded"]}


# ------------------------------------------------------------------ completeness
def _words(text: str) -> list[str]:
    t = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[—–]", " ", t)
    return [w for w in (re.sub(r"[^\w'ऀ-৿]", "", x).lower() for x in t.split()) if w]


def completeness(prod, narr: Narration) -> dict:
    """Compare the supplied script with the narration's source-language text.

    Guards against summarising, skipping or rewriting the script: every narration
    paragraph of the script must appear in narration.json, except paragraphs that are
    explicitly listed under `excluded` (with a reason, reported to the user)."""
    parsed = parse_script(prod.script)
    src_paras = [p for s in parsed["sections"] for p in s["paragraphs"]]
    excluded = [e["text"] for e in narr.data.get("excluded", [])]
    source = " ".join(p for p in src_paras if p not in excluded)
    lang = prod.source_language
    spoken = " ".join(display(ln.get(lang, "")) for _, ln in narr.lines())
    a, b = _words(source), _words(spoken)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    missing, added = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace") and i2 > i1:
            missing.append(" ".join(a[i1:i2]))
        if op in ("insert", "replace") and j2 > j1:
            added.append(" ".join(b[j1:j2]))
    matched = sum(bl.size for bl in sm.get_matching_blocks())
    return {"source_words": len(a), "narration_words": len(b),
            "coverage": matched / max(1, len(a)), "ratio": sm.ratio(),
            "missing": missing[:12], "added": added[:12], "excluded": len(excluded)}
