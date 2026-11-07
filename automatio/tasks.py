"""Agent tasks: the creative steps the pipeline hands to the connected harness.

When a stage needs judgement (translation, scene authoring, visual review, fixing a
narration that drifted from the script) the pipeline writes a self-contained task
file to build/<slug>/tasks/<id>.md and stops with outcome `needs_agent`. The harness
agent does the work with its own tools, validates it with the given `check` command
and runs the pipeline again. Any agent that can read/write files and run commands
can perform these tasks; nothing here is specific to one harness.
"""
from __future__ import annotations

from .narration import display, markers_in
from .plan import plan_section_text
from .util import atomic_write_text, rel

LANG_NAMES = {"hi": "Hindi", "en": "English", "bn": "Bangla", "ur": "Urdu", "es": "Spanish", "fr": "French"}
CPS = {"hi": 11.5, "en": 14.5}      # measured speaking rates of the house voices (chars/s)


def _cmd(prod, *a) -> str:
    return " ".join(["python -m automatio", *a, prod.slug])


def _write(prod, tid: str, title: str, body: str, *, check: str | None, summary: str, items=None) -> dict:
    path = prod.build_dir / "tasks" / f"{tid}.md"
    atomic_write_text(path, f"# Agent task: {title}\n\n{body.strip()}\n")
    return {"id": tid, "kind": "agent", "title": title, "file": rel(path), "summary": summary,
            "check": check, "then": _cmd(prod, "run"), "items": items or []}


def _dub_section(prod, narr, forecasts: dict | None) -> str:
    """Translate-task guidance for dub languages: the time each line has on the master timeline."""
    if not prod.dub_langs:
        return ""
    out = ["## Dub languages: write to fit", "",
           f"{', '.join(prod.dub_langs)} {'is a dub' if len(prod.dub_langs) == 1 else 'are dubs'}: voiced over the "
           "master's picture and timeline, never re-timed. Write each line **concise but complete** so it fits the "
           "slot of its master line (sections and anchored steps must start on time). The house Hindi voice "
           "speaks about 1.3x as long as the English voice on the same content. Each sentence end costs about "
           "0.55 s and each comma about 0.4 s, so avoid needless commas. Dub lines need no cue markers.", ""]
    for lang, f in (forecasts or {}).items():
        out += [f"Forecast for {lang} ({f['model']}); `python -m automatio check dub {prod.slug}` shows it "
                "again after every edit:", "", "| segment | slot | speech | forecast |", "|---|---|---|---|"]
        out += [f"| {s['lines'][0]}..{s['lines'][-1]} | {s['window']:.1f}s | {s['need']:.1f}s | {s['status']} "
                f"(x{s['speed']:.2f}, {s['slack']:+.1f}s) |"
                for s in f["segments"] if s["status"] != "fits"] or ["| all segments | | | fit |"]
        out.append("")
    return "\n".join(out)


def translate_task(prod, narr, report: dict, forecasts: dict | None = None) -> dict:
    src = prod.source_language
    targets = [l for l in dict.fromkeys([*prod.langs, prod.subtitles.language]) if l != src]
    missing = []
    for _, ln in narr.lines():
        for l in targets:
            if not (ln.get(l) or "").strip():
                missing.append((ln["key"], l, display(ln[src])))
    tables = []
    for l in targets:
        prof = prod.profile(l)
        pron = prod.pron_table(l, prof)
        tables.append(f"- **{l}** ({LANG_NAMES.get(l, l)}): voice `{prof.name}` ({prof.provider}); pronunciation "
                      f"dictionary applied automatically: {pron or 'none'}")
    rows = "\n".join(f"| {k} | {l} | {t} |" for k, l, t in missing[:400])
    errs = "\n".join(f"- {e}" for e in report["errors"][:60])
    body = f"""
Production **{prod.title}** (`{prod.slug}`). Fill in the translations in
`{rel(narr.path)}`: every line object needs a `"<lang>"` field for each target language.
Edit the JSON in place; keep keys, order and the `{src}` text unchanged.

Targets:
{chr(10).join(tables)}

## How to translate (house style of the previous production)
1. **Natural, conversational, standard {', '.join(LANG_NAMES.get(l, l) for l in targets)}** for a beginner audience - a calm
   teacher talking, not a literal word-for-word rendering. Adapt idioms; keep every piece of information.
2. **Keep technical terms in English, in Latin script** (Agent, Model, Tool, Tools, Context, Feedback, Browser,
   Terminal, File, Code, API, Database, Website, Loop, Error ...). Where the English introduces a term,
   add its meaning once with "यानी ..." (e.g. "Context कहते हैं, यानी संदर्भ").
3. **Same number of sentences as the `{prod.subtitles.language}` line, in the same order** - subtitle sentence i is shown
   while sentence i is spoken. End sentences with "।" (or "?" / "!"); commas are free.
4. **Copy every cue marker** such as `{{error}}` into the translation, directly before the word that carries
   the same meaning. Same marker names, every language (they cue the animation).
5. **Write what is spoken**: numbers and symbols as words ("80%" -> "अस्सी प्रतिशत"), no "/", "&", "%", digits
   or file extensions read as code (write "stats नाम की File" for stats.py).
6. Do not respell words the dictionary above already handles (write "AI", not "एआई").
7. **Never summarise, shorten, merge or skip** anything. Long-form stays long-form.

Context: the production plan `{rel(prod.plan)}`{''.join(f', notes `{rel(n)}`' for n in prod.notes)}.

{_dub_section(prod, narr, forecasts)}
## Done when
`{_cmd(prod, 'check', 'translate')}` reports no errors. Then run `{_cmd(prod, 'run')}`.

## Current problems
{errs or '- none besides the missing lines below'}

## Lines missing a translation ({len(missing)})
| key | lang | {src} text |
|---|---|---|
{rows}
"""
    return _write(prod, "translate", f"translate the narration into {', '.join(LANG_NAMES.get(l, l) for l in targets)}",
                  body, check=_cmd(prod, "check", "translate"),
                  summary=f"{len(missing)} line translation(s) missing, {len(report['errors'])} error(s)",
                  items=[f"{k}:{l}" for k, l, _ in missing[:50]])


def scenes_task(prod, narr, report: dict, man: dict | None) -> dict:
    need = sorted({e.split("]")[0].strip("[") for e in report["errors"] if e.startswith("[")})
    done = sorted(report.get("scenes", {}))
    blocks = []
    for sec in narr.sections:
        if sec["key"] not in need and sec["key"] in done and not any(sec["key"] in e for e in report["errors"]):
            continue
        ch = sec.get("chapter") or {}
        lines = []
        total = 0.0
        for ln in sec["lines"]:
            est = {l: (man["lines"][ln["key"]]["speech_end"] if man and l == man.get("lang") and ln["key"] in man["lines"]
                       else len(display(ln.get(l, ""))) / CPS.get(l, 13)) for l in prod.langs}
            total += max(est.values())
            marks = markers_in(ln.get(prod.source_language, ""))
            lines.append(f"- `{ln['key']}` (~{' / '.join(f'{l} {est[l]:.1f}s' for l in prod.langs)})"
                         + (f" markers: {', '.join('{' + m + '}' for m in marks)}" if marks else "") + "\n"
                         + "\n".join(f"    - {l}: {ln.get(l, '(missing)')}" for l in dict.fromkeys([prod.source_language, *prod.langs])))
        plan = plan_section_text(prod.plan, sec.get("plan_section")) or "(no matching plan section; follow the overall plan)"
        blocks.append(f"### {sec['key']} - {ch.get('number', '')} {ch.get('title', '')}  (~{total / 60:.1f} min)\n\n"
                      f"Plan:\n\n```\n{plan.strip()[:4000]}\n```\n\nLines:\n" + "\n".join(lines))
    errs = "\n".join(f"- {e}" for e in report["errors"][:80])
    warns = "\n".join(f"- {w}" for w in report["warnings"][:40])
    body = f"""
Production **{prod.title}** (`{prod.slug}`). Write the Manim scenes in `{rel(prod.scenes_dir)}/`: one
`VoiceScene` per section, animating the production plan for that section in the house style.

**Read `docs/SCENE_AUTHORING.md` first** (visual language, component API, cue markers, Manim pitfalls).
The previous production is the reference implementation: `productions/agentic-ai-intro/scenes/`.

Skeleton (`{rel(prod.scenes_dir)}/s01_intro.py`):

```python
from agentic_video.prelude import *


class S01Intro(VoiceScene):
    SECTION = "s01"

    def construct(self):
        self.show_chapter()
        title = en("Agentic AI", 84, FG)
        with self.say("s01_01") as v:                 # every line, once, in order
            self.wait_until(v.cue("error") - 0.3)      # marker {{error}} in EVERY language of s01_01
            self.play(FadeIn(title, shift=UP * 0.1), run_time=0.8)
        self.clear_all(0.8)
```

Rules:
- One scene per section, `SECTION = "<key>"`; every line said once, in order (`self.say` / `self.narrate`).
- Cue animations with markers: put `{{name}}` before the cue word in **every language** of that line in
  `{rel(narr.path)}`, then `self.wait_until(v.cue("name") - 0.3)`. Never `v.word("<Hindi word>")`.
- On-screen text in **English** (both versions share the visuals). Content between y = -2.75 and 3.25
  (subtitle area below). Keep boxes tight to their content.
- Do not shorten the narration to fit an animation; animations follow the voice.
- Dense or repetitive lines get extra visuals: keyword pop-ups on cue words, small diagrams,
  highlights; something new every ~5-8 s. Pop-ups are keywords, never the spoken sentence
  (no burned-in captions; subtitles are separate files only).
- Coding or complex parts: recreate them with Terminal / CodeEditor / Browser. If one truly
  needs a real screen recording, tell the user (the pipeline can't insert footage yet).
- End the video with a recap of all topics (visual-only if the script has no recap lines).
  No timestamps on screen (they differ between the language versions).
  See "Production guidelines" in AGENTS.md.

Check statically: `{_cmd(prod, 'check', 'scenes')}`. Look at a quick render:
`python -m automatio preview {prod.slug} <section> [--lang hi]` -> contact sheet path (read the image).
When all scenes pass, run `{_cmd(prod, 'run')}` (the draft render then checks every cue in every language).

## Problems found
{errs or '- none'}

## Warnings
{warns or '- none'}

## Sections
{chr(10).join(blocks)}
"""
    return _write(prod, "scenes", "write the scenes", body, check=_cmd(prod, "check", "scenes"),
                  summary=f"{len(report['errors'])} scene problem(s); sections needing work: {need or 'see file'}",
                  items=need)


def review_task(prod, sheets: dict, lint: dict) -> dict:
    sh = "\n".join(f"- {l}: " + ", ".join(f"`{p}`" for p in ps) for l, ps in sheets.items())
    li = "\n".join(f"- [{l}] {x['section']}/{x['line']} t={x['t']}s: {x['issue']} - {x['mobject']} {x['texts']}"
                   for l, xs in lint.items() for x in xs[:40]) or "- none"
    body = f"""
The draft of **{prod.title}** is rendered (low resolution, draft voices where the final voice is paid).
Before the paid narration and the final 1080p render, review every contact sheet (one frame per
narration line, taken at 92% of the line when its animations have settled). Open the images:

{sh}

Look for: text overflowing its box or the frame; overlapping or colliding elements; unreadable or tiny
text; boxes much larger than their content; empty or cluttered frames; an element that should be on
screen for this line but is missing (cue too late) or a frame caught mid-transition; content below the
subtitle safe line; anything inconsistent with the house style or the production plan.

Layout warnings recorded by the renderer:
{li}

Fix scenes as needed, re-render one section with `python -m automatio preview {prod.slug} <section> --lang <lang>`
and look at its sheet again. When satisfied, record the review:

`python -m automatio complete review {prod.slug} --notes "<what you checked and fixed>"`
"""
    return _write(prod, "review", "visual review of the draft", body, check=None,
                  summary=f"inspect {sum(len(v) for v in sheets.values())} contact sheet(s); "
                          f"{sum(len(v) for v in lint.values())} layout warning(s)",
                  items=[p for ps in sheets.values() for p in ps])


def narration_fix_task(prod, narr, comp: dict) -> dict:
    miss = "\n".join(f"- “{m}”" for m in comp["missing"]) or "- none"
    add = "\n".join(f"- “{m}”" for m in comp["added"]) or "- none"
    body = f"""
`{rel(narr.path)}` no longer matches the supplied script `{rel(prod.script)}`
({comp['coverage'] * 100:.1f}% of the script's words are in the narration, similarity {comp['ratio']:.3f}).
The narration must carry the **whole** script: no summarising, no skipped sentences.

Missing from the narration (in script order):
{miss}

In the narration but not in the script:
{add}

Fix the `{prod.source_language}` text of the affected lines (and their translations), or - only if a
paragraph is genuinely not narration (a stage direction, a note) - list it under `"excluded"` with a
`"reason"`; exclusions are reported to the user. Then run `{_cmd(prod, 'run')}`.
"""
    return _write(prod, "narration", "bring the narration back in line with the script", body, check=None,
                  summary=f"script coverage {comp['coverage'] * 100:.1f}%", items=comp["missing"][:10])


def dub_fit_task(prod, narr, lang: str, forecast: dict, bad: list) -> dict:
    """Stop before paying: segments forecast not to fit their master slots even if every unvoiced
    line comes out shorter than predicted."""
    lines = {ln["key"]: ln for _, ln in narr.lines()}
    blocks = []
    for sg in bad:
        rows = "\n".join(f"| {k} | {forecast['lines'][k]['seconds']:.1f}s"
                         f"{'' if forecast['lines'][k]['measured'] else ' (forecast)'} | "
                         f"{forecast['lines'][k]['slot']:.1f}s | {display(lines[k][lang])} |" for k in sg["lines"])
        blocks.append(f"### {sg['section']}: {sg['lines'][0]}..{sg['lines'][-1]} - needs ~{sg['need']:.1f}s, "
                      f"slot {sg['window']:.1f}s\n\n| line | speech | own slot | {lang} text |\n|---|---|---|---|\n"
                      f"{rows}")
    body = f"""
The {LANG_NAMES.get(lang, lang)} dub of **{prod.title}** would not fit the {prod.versions[lang].follow} master's
timeline: the segments below need more time than their slots, even at the maximum time-stretch
({(prod.dub.max_speedup - 1) * 100:.0f}% faster) and even if every line not voiced yet came out 5% shorter than
forecast ({forecast['model']}). Voicing them now would spend paid credits on lines that have to be rewritten
and voiced again.

A dub line cannot start before its master line, so a line longer than its **own slot** (from its master
line's start to the next one) pushes the lines after it; the last line of a segment must fit its own slot.
Rewrite the {lang} text of these lines in `{rel(narr.path)}` **shorter, keeping the full meaning** (never drop
content): fewer filler words and commas, shorter synonyms, no repeated subject. Lines already voiced keep their
measured length; shortening them makes them paid again, so prefer the forecast ones.

Check: `{_cmd(prod, 'check', 'dub')}` (no errors left), then `{_cmd(prod, 'run')}`.

{chr(10).join(blocks)}
"""
    return _write(prod, f"dub-fit-{lang}", f"shorten the {LANG_NAMES.get(lang, lang)} dub lines that cannot fit", body,
                  check=_cmd(prod, "check", "dub"),
                  summary=f"{len(bad)} {lang} segment(s) forecast not to fit their slots; shorten before voicing",
                  items=[k for sg in bad for k in sg["lines"]])
