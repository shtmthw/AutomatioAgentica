"""Production plan parsing. The plan is free-form Markdown (like the brief for the
previous video); we only extract numbered sections and their TIME ranges, which
drive scene tasks and the planned-vs-actual timing report. The full text goes to
the agent that authors the scenes."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import InputError

_HEAD = re.compile(r"^(#{1,4})\s+(?:part|chapter|section|scene)?\s*(\d{1,2})\s*[.):\-–]?\s*(.+?)\s*$", re.I | re.M)
_TIME = re.compile(r"TIME\s*:\s*(\d+):(\d{2})\s*[–\-—to]+\s*(\d+):(\d{2})", re.I)


@dataclass
class PlanSection:
    number: str
    title: str
    start: float | None
    end: float | None
    body: str

    @property
    def short_title(self) -> str:
        return self.title.split(":")[0].strip()

    @property
    def target(self) -> float | None:
        return None if self.start is None or self.end is None else self.end - self.start


def parse_plan(path: Path) -> list[PlanSection]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise InputError(f"production plan not found: {path}") from None
    heads = list(_HEAD.finditer(text))
    out = []
    for i, m in enumerate(heads):
        body = text[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)].strip()
        t = _TIME.search(body)
        start = end = None
        if t:
            start = int(t.group(1)) * 60 + int(t.group(2))
            end = int(t.group(3)) * 60 + int(t.group(4))
        out.append(PlanSection(f"{int(m.group(2)):02d}", m.group(3).strip(), start, end, body))
    return out


def plan_section_text(path: Path, number: str | None) -> str:
    if not number:
        return ""
    for s in parse_plan(path):
        if s.number == number:
            return f"## {s.number}. {s.title}\n{s.body}"
    return ""
