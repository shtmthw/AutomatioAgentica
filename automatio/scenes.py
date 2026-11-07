"""Scene discovery and static checks (no rendering).

Convention: every section of narration.json has one scene class in the production's
scenes/ folder:

    class S05Loop(VoiceScene):
        SECTION = "s05"

The static check parses the files (AST, nothing is executed) and verifies that each
section has exactly one scene, that literal line keys and cue markers exist in every
language, and flags habits that break multi-language rendering (word cues in one
language, non-English on-screen text, imports of removed modules). Dynamic keys and
cues are verified for real by the draft render (VoiceScene checks coverage and order).
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .narration import DEVANAGARI, Narration, markers_in

_TEXT_FUNCS = {"bn", "en", "txt", "mono", "Text", "Pill", "Bubble", "spaced", "labeled_icon", "chapter_tag"}
_REMOVED = {"agentic_video.config", "agentic_video.narration", "agentic_video.pronunciation"}


@dataclass
class SceneRef:
    section: str
    file: Path
    cls: str


def _str(node) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def discover(scenes_dir: Path) -> tuple[dict[str, list[SceneRef]], list[str]]:
    """section -> scene classes found; plus parse errors."""
    found: dict[str, list[SceneRef]] = {}
    errors = []
    for py in sorted(Path(scenes_dir).glob("*.py")):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        except SyntaxError as e:
            errors.append(f"{py.name}:{e.lineno}: syntax error: {e.msg}")
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in node.bases}
            if "VoiceScene" not in bases:
                continue
            sec = None
            for st in node.body:
                if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SECTION" for t in st.targets):
                    sec = _str(st.value)
            if sec:
                found.setdefault(sec, []).append(SceneRef(sec, py, node.name))
    return found, errors


class _Walker(ast.NodeVisitor):
    """Collects say()/narrate() keys, cue()/word() calls (with their enclosing say key),
    string literals passed to text helpers, and imports."""

    def __init__(self):
        self.say_keys: list[tuple[str | None, int]] = []
        self.cues: list[tuple[str | None, str | None, int]] = []     # (line key, marker, lineno)
        self.words: list[tuple[str | None, str | None, int]] = []
        self.texts: list[tuple[str, int]] = []
        self.imports: list[tuple[str, int]] = []
        self._ctx: list[tuple[str, str | None]] = []                 # (var, key)

    def visit_Import(self, node):
        for a in node.names:
            self.imports.append((a.name, node.lineno))

    def visit_ImportFrom(self, node):
        self.imports.append((node.module or "", node.lineno))

    def visit_With(self, node):
        pushed = 0
        for item in node.items:
            c = item.context_expr
            if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "say"
                    and c.args):
                key = _str(c.args[0])
                self.say_keys.append((key, node.lineno))
                var = item.optional_vars.id if isinstance(item.optional_vars, ast.Name) else None
                self._ctx.append((var, key))
                pushed += 1
        self.generic_visit(node)
        for _ in range(pushed):
            self._ctx.pop()

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Attribute):
            if f.attr == "narrate" and node.args:
                self.say_keys.append((_str(node.args[0]), node.lineno))
            if f.attr in ("cue", "word") and isinstance(f.value, ast.Name):
                key = next((k for v, k in reversed(self._ctx) if v == f.value.id), "?")
                if key != "?":
                    arg = _str(node.args[0]) if node.args else None
                    (self.cues if f.attr == "cue" else self.words).append((key, arg, node.lineno))
        name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
        if name in _TEXT_FUNCS:
            for a in node.args[:1]:
                s = _str(a)
                if s:
                    self.texts.append((s, node.lineno))
        self.generic_visit(node)


def check(prod, narr: Narration) -> dict:
    """Static validation of all scenes. Returns {"errors", "warnings", "scenes": {sec: SceneRef}}."""
    errors, warnings = [], []
    found, perr = discover(prod.scenes_dir)
    errors += perr
    scenes: dict[str, SceneRef] = {}
    langs = list(dict.fromkeys([prod.source_language, *prod.langs]))
    for sec in narr.sections:
        k = sec["key"]
        refs = found.get(k, [])
        if not refs:
            errors.append(f"[{k}] no scene: add a VoiceScene subclass with SECTION = \"{k}\" in "
                          f"{prod.scenes_dir.name}/")
            continue
        if len(refs) > 1:
            errors.append(f"[{k}] {len(refs)} scenes claim this section: " + ", ".join(f"{r.file.name}:{r.cls}" for r in refs))
            continue
        ref = scenes[k] = refs[0]
        src = ref.file.read_text(encoding="utf-8")
        w = _Walker()
        w.visit(ast.parse(src))
        line_keys = [ln["key"] for ln in sec["lines"]]
        lines = {ln["key"]: ln for ln in sec["lines"]}
        literal = [key for key, _ in w.say_keys if key]
        dynamic = [ln for key, ln in w.say_keys if key is None]
        for key in literal:
            if key not in lines:
                errors.append(f"{ref.file.name}: say({key!r}) - no such line in section {k}")
        if not dynamic:
            missing = [x for x in line_keys if x not in literal]
            if missing:
                errors.append(f"{ref.file.name}: lines never said: {missing}")
            if literal != [x for x in line_keys if x in literal]:
                errors.append(f"{ref.file.name}: lines are said out of order: {literal}")
        for key, name, lineno in w.cues:
            if key and name and key in lines:
                for l in langs:
                    if name not in markers_in(lines[key].get(l, "")):
                        errors.append(f"{ref.file.name}:{lineno} cue({name!r}) but {key} has no {{{name}}} marker "
                                      f"in its {l} text")
        for key, word, lineno in w.words:
            warnings.append(f"{ref.file.name}:{lineno} word({word!r}) in {key}: word cues break when the "
                            f"word is not spoken in every language - use a {{marker}} and cue()")
        for mod, lineno in w.imports:
            if mod in _REMOVED:
                errors.append(f"{ref.file.name}:{lineno} imports {mod}, which no longer exists "
                              "(settings now come from the pipeline)")
        for s, lineno in w.texts:
            if DEVANAGARI.search(s):
                warnings.append(f"{ref.file.name}:{lineno} on-screen text {s!r} is not English: both language "
                                "versions share the same visuals, and the house style is English on-screen text")
    for sec, refs in found.items():
        if sec not in {s["key"] for s in narr.sections}:
            warnings.append(f"scene(s) {[r.cls for r in refs]} have SECTION={sec!r}, which is not in narration.json")
    return {"errors": errors, "warnings": warnings, "scenes": scenes}


def thumbnail_ref(prod) -> SceneRef | None:
    p = prod.scenes_dir / "thumbnail.py"
    if not p.exists():
        return None
    tree = ast.parse(p.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Thumbnail":
            return SceneRef("thumbnail", p, "Thumbnail")
    return None
