"""
Export the narration (Hindi) and subtitles (English) as a readable Markdown script, with
section titles and (after a render) the timestamp of every line.

    python -m tools.export_script     # -> output/narration_script_bn.md
"""
from __future__ import annotations

import json

from agentic_video import config as C
from agentic_video.narration import SECTIONS


def fmt(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


def main():
    starts = {}
    offset = 0.0
    for _, _, sec in C.SCENES:
        p = C.CUES_DIR / f"{sec}.json"
        if not p.exists():
            starts = {}
            break
        cues = json.loads(p.read_text())
        for c in cues["cues"]:
            starts[c["key"]] = offset + c["start"]
        starts[sec] = offset
        offset += cues["duration"]

    out = ["# What is Agentic AI? (Hindi narration with English subtitles)", ""]
    if starts:
        out.append(f"Total length: **{fmt(offset)}**")
        out.append("")
    for sec, data in SECTIONS.items():
        num, title = data["chapter"]
        stamp = f"  `{fmt(starts[sec])}`" if sec in starts else ""
        out += [f"## {num}. {title}{stamp}", ""]
        for key, spoken, subtitle in data["lines"]:
            ts = f"`{fmt(starts[key])}` " if key in starts else ""
            out.append(f"- {ts}{spoken}  \n  *{subtitle}*")
        out.append("")
    path = C.OUTPUT / "narration_script_hi_en.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
