"""The production state machine.

    validate -> approve* -> ingest -> translate+ -> scenes+ -> draft -> review+ -> voice -> render
             -> assemble -> subtitles -> verify -> deliver
    (* gate: the user approves the configuration and budget through the harness;
     + agent task: the harness agent does creative work, the pipeline validates it)

`run` executes stages in order until it finishes, or stops with an outcome the harness
acts on (needs_agent / needs_approval / blocked / failed). Every stage is fingerprinted
by its inputs, so re-running skips everything already done and resumes after an
interruption; per-language parts are tracked separately (e.g. render:hi, render:en).
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from . import narration as N
from . import render as R
from . import subtitles as SUB
from . import tasks as T
from . import voice as V
from .assemble import assemble as do_assemble, timeline as build_timeline
from .config import load_production
from .deliver import deliver as do_deliver, report_md
from .errors import EXIT, AAError, InputError, MissingCapability, StageFailed, ValidationFailed
from .log import log
from .plan import parse_plan
from .scenes import check as check_scenes, thumbnail_ref
from .secrets import CREDS, redact
from .state import RunLock, State
from .util import (atomic_write_text, file_fp, fingerprint, now_iso, read_json, rel, resolve, tree_fp, which)
from . import providers

STAGES = [("validate", "auto"), ("approve", "gate"), ("ingest", "auto"), ("translate", "agent"),
          ("scenes", "agent"), ("draft", "auto"), ("review", "agent"), ("voice", "auto"), ("render", "auto"),
          ("assemble", "auto"), ("subtitles", "auto"), ("verify", "auto"), ("deliver", "auto")]
STAGE_IDS = [s for s, _ in STAGES]
_HERE = Path(__file__).resolve().parent


def code_fp(*modules: str) -> str:
    """Fingerprint of pipeline modules whose logic shapes a stage's output, so a code fix
    re-runs that stage. (Voice clips stay content-addressed: code changes never re-spend credits.)"""
    return tree_fp([_HERE / f"{m}.py" for m in modules])


@dataclass
class Outcome:
    state: str                  # done | needs_agent | needs_approval | blocked | failed | locked | usage
    stage: str | None = None
    message: str = ""
    task: dict | None = None
    approval: dict | None = None
    error: dict | None = None
    data: dict = field(default_factory=dict)

    @property
    def exit_code(self) -> int:
        return EXIT.get(self.state, 1)

    def to_dict(self) -> dict:
        d = {"ok": self.state == "done", "state": self.state, "stage": self.stage, "message": redact(self.message)}
        for k in ("task", "approval", "error"):
            if getattr(self, k):
                d[k] = getattr(self, k)
        if self.data:
            d.update(self.data)
        return d


class _Agent(Exception):
    def __init__(self, task: dict):
        self.task = task


class _Approval(Exception):
    def __init__(self, info: dict):
        self.info = info


class Pipeline:
    def __init__(self, production: str | None):
        self.prod = load_production(production)
        self.state = State(self.prod.build_dir)
        self._narr = None

    # ------------------------------------------------------------ helpers
    @property
    def narr(self):
        if self._narr is None or self._narr_fp != (file_fp(self.prod.narration_path) if self.prod.narration_path.exists() else None):
            self._narr = N.load_narration(self.prod.narration_path)
            self._narr_fp = file_fp(self.prod.narration_path) if self._narr else None
            if self._narr is None:
                raise InputError(f"{rel(self.prod.narration_path)} does not exist yet (run the ingest stage)")
        return self._narr

    _narr_fp = None

    def narr_fp(self) -> str:
        return file_fp(self.prod.narration_path)

    def render_narr_fp(self) -> str:
        """The narration as the renders see it: lines and the text of the rendered (and subtitle)
        languages only. Editing a dub language never invalidates the renders or their review."""
        if not self.prod.dub_langs:
            return self.narr_fp()            # unchanged for productions without a dub
        keep = set(self.prod.marker_langs) | {self.prod.subtitles.language}

        def view(ln):
            out = {k: v for k, v in ln.items() if k == "key" or k in keep}
            sp = {l: v for l, v in (ln.get("spoken") or {}).items() if l in keep}
            if sp:
                out["spoken"] = sp
            return out
        return fingerprint([(s["key"], s.get("chapter"), [view(ln) for ln in s["lines"]]) for s in self.narr.sections])

    def scenes_fp(self) -> str:
        files = sorted(self.prod.scenes_dir.glob("*.py")) if self.prod.scenes_dir.exists() else []
        return fingerprint(tree_fp(files) if files else "-", R.lib_fp())

    def _do(self, sid: str, fp: str, fn, force: bool = False) -> dict:
        """Run fn() unless `sid` is fresh for `fp`; record status and result in the state."""
        if not force and self.state.fresh(sid, fp):
            return self.state.stage(sid)
        self.state.mark(sid, "running")
        self.state.event("stage_start", stage=sid)
        t0 = time.time()
        try:
            res = fn() or {}
        except _Agent as a:
            self.state.mark(sid, "waiting_agent", task=a.task)
            raise
        except _Approval as a:
            self.state.mark(sid, "waiting_approval", approval=a.info)
            raise
        except AAError as e:
            self.state.mark(sid, "failed", error=e.to_dict())
            self.state.event("stage_failed", stage=sid, error=e.to_dict())
            raise
        except Exception as e:
            err = {"code": "internal_error", "message": redact(f"{type(e).__name__}: {e}"),
                   "details": {"traceback": redact(traceback.format_exc()).splitlines()[-12:]}}
            self.state.mark(sid, "failed", error=err)
            self.state.event("stage_failed", stage=sid, error=err)
            raise
        except BaseException:                      # SIGINT / SIGTERM: resumable, nothing is lost
            self.state.mark(sid, "interrupted")
            self.state.event("stage_interrupted", stage=sid)
            raise
        res = dict(res)
        res["seconds"] = round(time.time() - t0, 1)
        res.pop("status", None)
        self.state.mark(sid, "done", fp=fp, **res)
        self.state.event("stage_done", stage=sid, seconds=res["seconds"])
        return self.state.stage(sid)

    def enabled(self, sid: str) -> bool:
        if sid == "draft":
            return self.prod.review.draft
        if sid == "review":
            return self.prod.review.draft and self.prod.review.visual_review
        return True

    # ------------------------------------------------------------ estimate
    def estimate(self) -> dict:
        """Paid-provider cost of the voice stage (exact when the text exists)."""
        out = {}
        narr = N.load_narration(self.prod.narration_path) if self.prod.narration_path.exists() else None
        for lang in self.prod.langs:
            prof = self.prod.profile(lang)
            prov = providers.get(prof.provider)
            if not prov.paid:
                continue
            if narr and all((ln.get(lang) or "").strip() for _, ln in narr.lines()):
                c = V.cost(self.prod, prof, V.plan(self.prod, narr, lang, prof))
                est = {"credits": c["credits"], "lines_to_generate": c["to_generate"], "cached_lines": c["cached"],
                       "exact": True}
            else:
                src = narr if narr else None
                if src:
                    chars = sum(len(N.display(ln.get(self.prod.source_language, ""))) for _, ln in src.lines())
                else:
                    parsed = N.parse_script(self.prod.script)
                    chars = sum(len(p) for s in parsed["sections"] for p in s["paragraphs"])
                est = {"credits": round(chars * 1.0 * float(prof.get("credits_per_char", 1.0))), "exact": False,
                       "basis": f"{chars} source characters (Hindi ≈ 0.99x English length)"}
            agg = out.setdefault(prov.name, {"credits": 0.0, "by_language": {}})
            agg["credits"] += est["credits"]
            agg["by_language"][lang] = est
        for v in out.values():
            v["recommended_budget"] = int(v["credits"] * 1.15 + 50) if v["credits"] else 0
        return out

    def config_summary(self) -> dict:
        p = self.prod
        return {"title": p.title, "source_language": p.source_language,
                "versions": {l: {"label": v.label, "voice": p.profile(l).public(),
                                 **({"mode": f"dub over {v.follow} (same picture, timeline and subtitles)"}
                                    if v.mode == "dub" else {})} for l, v in p.versions.items()},
                "subtitles": f"{p.subtitles.language} as {'+'.join(p.subtitles.formats)} files (never burned in)",
                "video": f"{p.video.width}x{p.video.height}@{p.video.fps} {p.video.encoder}"
                         + (f" crf {p.video.crf}" if p.video.encoder != 'copy' else ""),
                "draft_before_paid_voice": p.review.draft, "visual_review": p.review.visual_review}

    # ------------------------------------------------------------ stages
    def s_validate(self, force=False):
        p = self.prod
        errors, warnings = [], []
        for label, path in (("script", p.script), ("production plan", p.plan)):
            if not path.exists():
                errors.append(f"{label} not found: {rel(path)}")
        for n in p.notes:
            if not n.exists():
                warnings.append(f"notes file not found: {rel(n)}")
        for tool in ("ffmpeg", "ffprobe"):
            if not which(tool):
                raise MissingCapability(f"`{tool}` is not available", remedy="Install ffmpeg (with libx264).")
        try:
            import manim  # noqa: F401
        except ImportError:
            raise MissingCapability("manim is not installed in this Python environment",
                                    remedy="uv pip install --python .venv/bin/python -r pyproject.toml") from None
        blocked = []
        for lang in p.langs:
            for prof in {x.name: x for x in (p.profile(lang), p.profile(lang, draft=True))}.values():
                prov = providers.get(prof.provider)
                for cred in prov.credentials:
                    if not CREDS.get(cred):
                        blocked.append((lang, prof.name, cred))
        if p.subtitles.language not in dict.fromkeys([p.source_language, *p.langs]):
            warnings.append(f"subtitle language {p.subtitles.language!r} is neither the source nor a version "
                            "language; its text must be supplied in narration.json")
        if errors:
            raise InputError("; ".join(errors), remedy="Put the files in the production folder or fix the paths "
                                                       "in production.toml.")
        unverified = []
        if blocked:
            # not fatal yet: cached clips may make the credential unnecessary; voice stage decides
            warnings += [f"{lang}: voice {prof} needs {cred}, which is not set" for lang, prof, cred in blocked]
        for lang in p.langs:
            prof = p.profile(lang)
            if prof.provider == "elevenlabs" and CREDS.get("ELEVENLABS_API_KEY"):
                unverified.append("ElevenLabs credit balance is checked only if the key has User: Read; "
                                  "otherwise the first (canary) request is the availability check.")
        plan = parse_plan(p.plan)
        return {"summary": f"inputs ok; {len(plan)} plan section(s); voices: "
                           + ", ".join(f"{l}={p.profile(l).name}" for l in p.langs),
                "warnings": warnings, "unverified": unverified,
                "inputs": {"script": file_fp(p.script), "plan": file_fp(p.plan)}}

    def approval_fp(self) -> str:
        return fingerprint(self.prod.config_fingerprint_inputs())

    def s_approve(self, force=False):
        ap = self.state.approval
        if ap and ap.get("fingerprint") == self.approval_fp():
            return {"summary": f"approved {ap.get('approved_at')} by {ap.get('by')}; budget {ap.get('budget')}"}
        est = self.estimate()
        budget_args = " ".join(f"--budget {k}={v['recommended_budget']}" for k, v in est.items())
        info = {"reason": "the configuration changed since it was approved" if ap else "not yet approved",
                "config": self.config_summary(), "estimate": est,
                "command": f"python -m automatio approve {self.prod.slug} {budget_args}".strip(),
                "instructions": "Show the configuration and estimate to the user and ask for approval. Run the "
                                "command only after the user explicitly approves (it records who approved and "
                                "the budget cap for paid voices)."}
        raise _Approval(info)

    def s_ingest(self, force=False):
        p = self.prod
        if not p.narration_path.exists():
            data = N.ingest(p, parse_plan(p.plan))
            N.Narration(p.narration_path, data).save()
            self._narr = None
            n = sum(len(s["lines"]) for s in data["sections"])
            log.info(f"ingest: {len(data['sections'])} section(s), {n} line(s) from {p.script.name}")
        comp = N.completeness(p, self.narr)
        if comp["coverage"] < 0.985 or comp["ratio"] < 0.97:
            raise _Agent(T.narration_fix_task(p, self.narr, comp))
        warn = []
        if comp["missing"] or comp["added"]:
            warn.append(f"narration differs slightly from the script (coverage {comp['coverage'] * 100:.1f}%): "
                        f"missing {comp['missing'][:3]} added {comp['added'][:3]}")
        if self.narr.data.get("excluded"):
            warn.append(f"{len(self.narr.data['excluded'])} script paragraph(s) excluded as non-narration: "
                        + "; ".join(f"“{e['text'][:60]}” ({e.get('reason')})" for e in self.narr.data["excluded"][:5]))
        return {"summary": f"{len(self.narr.sections)} section(s), {sum(1 for _ in self.narr.lines())} line(s); "
                           f"script coverage {comp['coverage'] * 100:.1f}%", "warnings": warn,
                "completeness": comp}

    def s_translate(self, force=False):
        p = self.prod
        rep = N.validate(self.narr, langs=p.langs, subtitle_lang=p.subtitles.language, source_lang=p.source_language,
                         marker_langs=p.marker_langs, dub_langs=p.dub_langs)
        if rep["errors"]:
            raise _Agent(T.translate_task(p, self.narr, rep))
        return {"summary": f"all lines present in {', '.join(dict.fromkeys([p.source_language, *p.langs]))}",
                "warnings": rep["warnings"][:40]}

    def s_scenes(self, force=False):
        rep = check_scenes(self.prod, self.narr)
        if rep["errors"]:
            man = None
            for lang in self.prod.langs:
                man = V.load_manifest(self.prod, lang) or V.load_manifest(self.prod, lang, draft=True) or man
            raise _Agent(T.scenes_task(self.prod, self.narr, rep, man))
        return {"summary": f"{len(rep['scenes'])} scene(s) pass the static check", "warnings": rep["warnings"][:40],
                "scenes": {k: f"{rel(r.file)}:{r.cls}" for k, r in rep["scenes"].items()}}

    def _voice_lang(self, lang: str, draft: bool) -> dict:
        sid = f"draft:voice:{lang}" if draft else f"voice:{lang}"
        prof = V.choose_profile(self.prod, self.narr, lang, draft)
        jobs = V.plan(self.prod, self.narr, lang, prof)
        fp = V.stage_fingerprint(self.prod, lang, prof, jobs)
        mp = V.manifest_path(self.prod, lang, draft)
        fresh = self.state.fresh(sid, fp) and mp.exists() and all(j.cached for j in jobs)
        return self._do(sid, fp, lambda: self._voice_run(lang, draft), force=not fresh)

    def _voice_run(self, lang, draft):
        r = V.run_language(self.prod, self.narr, lang, self.state, draft=draft, approval=self.state.approval)
        prof = V.choose_profile(self.prod, self.narr, lang, draft)
        r["summary"] = (f"{prof.name}: {r['generated']} generated, {r['cached']} cached"
                        + (f", {r['credits']:.0f} credits" if r.get("credits") else "")
                        + (f", {r.get('speech_seconds', 0) / 60:.1f} min of speech" if r.get("speech_seconds") else ""))
        return r

    def _sid(self, kind: str, lang: str) -> str:
        return f"draft:render:{lang}" if kind == "draft" else f"render:{lang}"

    def _render(self, kind: str, langs: list[str], force: bool = False) -> dict:
        mans = {l: V.manifest_path(self.prod, l, draft=(kind == "draft")) for l in langs}
        fps = {}
        todo = []
        for l in langs:
            man = read_json(mans[l])
            fps[l] = fingerprint(kind, man["fingerprint"], self.scenes_fp(), self.render_narr_fp(),
                                 R.resolution(self.prod, kind), self.prod.audio.line_gap)
            sid = self._sid(kind, l)
            if force or not (self.state.fresh(sid, fps[l]) and R.index_path(self.prod, l, kind).exists()):
                todo.append(l)
        if todo:
            for l in todo:
                self.state.mark(self._sid(kind, l), "running")
            try:
                idx = R.render_all(self.prod, self.narr, todo, mans, kind=kind, state=self.state,
                                   use_cache=not force)
            except AAError as e:
                for l in todo:
                    self.state.mark(self._sid(kind, l), "failed", error=e.to_dict())
                raise
            except BaseException:
                for l in todo:
                    self.state.mark(self._sid(kind, l), "interrupted")
                raise
            for l in todo:
                man = read_json(mans[l])
                sheets = R.sheets_for(self.prod, l, kind, idx[l], man)
                lint = [dict(x, section=s["section"]) for s in idx[l]["scenes"] for x in s.get("lint", [])]
                rendered = sum(1 for s in idx[l]["scenes"] if not s["cached"])
                self.state.mark(self._sid(kind, l), "done", fp=fps[l], index=rel(R.index_path(self.prod, l, kind)),
                                sheets=sheets, lint=lint, summary=f"{len(idx[l]['scenes'])} scenes "
                                f"({rendered} rendered, {len(idx[l]['scenes']) - rendered} cached), "
                                f"{len(lint)} layout warning(s)")
        return {l: self.state.stage(self._sid(kind, l)) for l in langs}

    def s_draft(self, force=False):
        for lang in self.prod.full_langs:          # dub versions are not rendered
            self._voice_lang(lang, draft=True)
        res = self._render("draft", self.prod.full_langs, force=force)
        return {"summary": "; ".join(f"{l}: {r['summary']}" for l, r in res.items()),
                "fingerprint_parts": {l: r["fingerprint"] for l, r in res.items()}}

    def review_fp(self) -> str:
        return fingerprint([self.state.stage(f"draft:render:{l}").get("fingerprint") for l in self.prod.full_langs])

    def s_review(self, force=False):
        s = self.state.stage("review")
        if s.get("reviewed_at") and s.get("reviewed_fingerprint") == self.review_fp() and not force:
            return {"summary": s.get("summary", "reviewed"), "notes": s.get("notes")}
        sheets = {l: self.state.stage(f"draft:render:{l}").get("sheets", []) for l in self.prod.full_langs}
        lint = {l: self.state.stage(f"draft:render:{l}").get("lint", []) for l in self.prod.full_langs}
        raise _Agent(T.review_task(self.prod, sheets, lint))

    def complete_review(self, notes: str) -> dict:
        for l in self.prod.full_langs:
            if self.state.stage(f"draft:render:{l}").get("status") != "done":
                raise ValidationFailed(f"the draft for {l} is not rendered/fresh - run the pipeline first")
        cur = self.review_fp()
        # the draft must reflect the current scenes and narration
        for l in self.prod.full_langs:
            man = read_json(V.manifest_path(self.prod, l, draft=True))
            exp = fingerprint("draft", man["fingerprint"], self.scenes_fp(), self.render_narr_fp(),
                              R.resolution(self.prod, "draft"), self.prod.audio.line_gap)
            if exp != self.state.stage(f"draft:render:{l}").get("fingerprint"):
                raise ValidationFailed("scenes or narration changed after the draft was rendered; run the "
                                       "pipeline (it re-renders the draft) and review the new sheets")
        self.state.mark("review", "done", fp=cur, notes=notes, reviewed_at=now_iso(), reviewed_fingerprint=cur,
                        summary=f"reviewed: {notes[:140]}")
        return self.state.stage("review")

    def s_voice(self, force=False):
        out = {}
        for lang in self.prod.langs:
            out[lang] = self._voice_lang(lang, draft=False)
        retakes = {l: r for l in self.prod.dub_langs if (r := self._retake(l))}
        return {"summary": "; ".join(f"{l}: {r.get('summary', '')}" for l, r in out.items())
                + "".join(f"; {l}: re-took {len(r)} clip(s) with cut-off endings" for l, r in retakes.items()),
                **({"retakes": retakes} if retakes else {})}

    def _retake(self, lang: str) -> dict:
        """Paid clips whose ending the provider cut off are voiced again (at most `dub.retakes`
        times per text, recorded in the state so a stubborn line never loops). The rejected clip
        is kept under build/<slug>/voice-rejected/."""
        from . import dub
        prof = self.prod.profile(lang)
        if not providers.get(prof.provider).paid or self.prod.dub.retakes <= 0:
            return {}
        jobs = V.plan(self.prod, self.narr, lang, prof)
        done = self.state.data.setdefault("retakes", {}).setdefault(lang, {})
        took = {}
        for attempt in range(self.prod.dub.retakes):
            bad = [j for j in jobs if j.cached and done.get(j.hash, 0) < self.prod.dub.retakes
                   and dub.clip_issues(j.path, (read_json(j.meta) or {}).get("words"))]
            if not bad:
                break
            rej = self.prod.build_dir / "voice-rejected" / lang
            rej.mkdir(parents=True, exist_ok=True)
            for j in bad:
                n = done.get(j.hash, 0)
                for f in (j.path, j.meta):
                    f.replace(rej / f"{j.key}.{j.hash}.take{n}{f.suffix}")
                done[j.hash] = n + 1
                took[j.key] = done[j.hash]
            self.state.save()
            log.info(f"  {lang}: re-voicing {len(bad)} clip(s) with a cut-off ending: {[j.key for j in bad]}")
            V.generate(self.prod, lang, prof, bad, self.state, approval=self.state.approval)
        if took:
            fp = V.stage_fingerprint(self.prod, lang, prof, jobs)
            from .util import atomic_write_json
            atomic_write_json(V.manifest_path(self.prod, lang),
                              V.build_manifest(self.prod, lang, prof, jobs, draft=False, fp=fp))
        return took

    def s_render(self, force=False):
        res = self._render("final", self.prod.full_langs, force=force)
        return {"summary": "; ".join(f"{l}: {r['summary']}" for l, r in res.items())}

    def _parts(self, lang: str) -> tuple[dict, dict]:
        ver = self.prod.versions[lang]
        idx = read_json(R.index_path(self.prod, ver.follow if ver.mode == "dub" else lang, "final"))
        man = V.load_manifest(self.prod, lang)
        if not idx or not man:
            raise StageFailed(f"{lang}: render/voice results missing; run the pipeline from the start")
        return idx, man

    def s_assemble(self, force=False):
        out = {}
        for lang in self.prod.full_langs:
            idx, man = self._parts(lang)
            v = self.prod.video
            fp = fingerprint("assemble-1", idx["fingerprint"], man["fingerprint"], self.prod.audio.__dict__,
                             v.__dict__, self.prod.title, self.prod.versions[lang].__dict__,
                             code_fp("assemble", "audio", "music"))
            sid = f"assemble:{lang}"
            fresh = self.state.fresh(sid, fp) and resolve(self.state.stage(sid).get("final", "missing")).exists()
            r = self._do(sid, fp, lambda: self._assemble_one(lang, idx, man), force=force or not fresh)
            out[lang] = r
        for lang in self.prod.dub_langs:
            out[lang] = self._assemble_dub(lang, force)
        return {"summary": "; ".join(f"{l}: {r.get('total', 0) / 60:.2f} min" for l, r in out.items())}

    def _assemble_dub(self, lang, force=False):
        from . import dub
        ver = self.prod.versions[lang]
        master = self.state.stage(f"assemble:{ver.follow}")
        man = V.load_manifest(self.prod, lang)
        if master.get("status") != "done" or not man:
            raise StageFailed(f"{lang}: the {ver.follow} assembly and the {lang} voice are needed first")
        clips = [(k, e["hash"], e["duration"], e["speech_end"]) for k, e in sorted(man["lines"].items())]
        fp = fingerprint("dub-2", file_fp(resolve(master["final"])), master.get("fingerprint"), man["fingerprint"], clips,
                         self.prod.audio.__dict__, self.prod.dub.__dict__, self.prod.video.audio_bitrate,
                         self.prod.title, ver.__dict__, code_fp("dub", "audio", "music"))
        sid = f"assemble:{lang}"
        st = self.state.stage(sid)
        fresh = (self.state.fresh(sid, fp) and resolve(st.get("final", "missing")).exists()
                 and resolve(st.get("voiceover_mp3", "missing")).exists())

        def go():
            r = dub.assemble(self.prod, self.narr, lang, master, man, self.state)
            sm = r["fit"]
            r["summary"] = (f"{r['total']:.1f}s dub over {ver.follow}: {sm['sped_up']} line(s) sped up "
                            f"(max x{sm['max_speed']:.3f}), max lag {sm['max_lag']:.2f}s, "
                            f"{len(sm['overflow'])} overflow(s) -> {r['final']}")
            r["warnings"] = ([f"segment does not fit: {o}" for o in sm["overflow"]]
                             + ([f"lag over {self.prod.dub.max_lag}s: {sm['lag_over']}"] if sm["lag_over"] else [])
                             + ([f"spill over {self.prod.dub.max_spill}s: {sm['spill_over']}"] if sm["spill_over"] else []))
            return r
        return self._do(sid, fp, go, force=force or not fresh)

    def _assemble_one(self, lang, idx, man):
        r = do_assemble(self.prod, self.narr, lang, idx, man, self.state)
        r["summary"] = f"{r['total']:.1f}s -> {r['final']}"
        return r

    def s_subtitles(self, force=False):
        out = {}
        for lang in self.prod.full_langs:
            idx, man = self._parts(lang)
            fp = fingerprint("subs-1", idx["fingerprint"], man["fingerprint"], self.prod.subtitles.__dict__,
                             code_fp("subtitles", "narration"))
            sid = f"subtitles:{lang}"
            files = self.state.stage(sid).get("files", {})
            fresh = self.state.fresh(sid, fp) and all(resolve(f).exists() for f in files.values())
            out[lang] = self._do(sid, fp, lambda: self._subs_one(lang, idx, man), force=force or not fresh)
        for lang in self.prod.dub_langs:
            m = self.prod.versions[lang].follow
            ms = self.state.stage(f"subtitles:{m}")
            fp = fingerprint("subs-dub-1", ms.get("fingerprint"), ms.get("files"))
            out[lang] = self._do(f"subtitles:{lang}", fp, lambda: {
                "files": ms["files"], "cues": ms.get("cues"), "timing": f"shared with {m}",
                "summary": f"{ms.get('cues')} cues, shared with the {m} version (same picture and line slots)"},
                force=force)
        return {"summary": "; ".join(f"{l}: {r.get('cues')} cues" for l, r in out.items())}

    def _subs_one(self, lang, idx, man):
        tl = build_timeline(self.prod, self.narr, lang, idx, man)
        placed = [(ln["start"], man["lines"][ln["key"]]) for ln in tl["lines"]]
        same = lang == self.prod.subtitles.language
        cues = SUB.build(placed, same_language=same, settings=self.prod.subtitles)
        d = self.prod.build_dir / "subtitles" / lang
        files = {}
        for fmt in self.prod.subtitles.formats:
            path = d / f"subtitles-{self.prod.subtitles.language}.{fmt}"
            atomic_write_text(path, SUB.srt_text(cues) if fmt == "srt" else SUB.vtt_text(cues))
            files[fmt] = rel(path)
        issues = SUB.check(cues, tl["total"], self.prod.subtitles)
        return {"files": files, "cues": len(cues), "timing": "word-level" if same else "sentence-aligned",
                "summary": f"{len(cues)} cues ({'word-level' if same else 'sentence-aligned to the narration'})",
                "warnings": [f"cue {i['cue']}: {i['issue']}" for i in issues][:30]}

    def s_verify(self, force=False):
        from .verify import verify
        out, failed = {}, []
        for lang in self.prod.langs:
            asm = self.state.stage(f"assemble:{lang}")
            subs = self.state.stage(f"subtitles:{lang}")
            idx, man = self._parts(lang)
            fp = fingerprint("verify-1", file_fp(resolve(asm["final"])),
                             [file_fp(resolve(f)) for f in subs["files"].values()], self.prod.audio.__dict__,
                             self.prod.video.__dict__, self.prod.subtitles.__dict__, code_fp("verify", "audio"),
                             *([code_fp("dub"), file_fp(resolve(asm["voiceover_mp3"]))]
                               if self.prod.versions[lang].mode == "dub" else []))
            sid = f"verify:{lang}"
            r = self._do(sid, fp, lambda: self._verify_one(verify, lang, asm, subs, man), force=force)
            out[lang] = r
            if r.get("result", {}).get("status") == "fail":
                failed.append(lang)
        if failed:
            bad = {l: [c for c in out[l]["result"]["checks"] if c["status"] == "fail"] for l in failed}
            raise ValidationFailed("verification failed for " + ", ".join(failed) + ": "
                                   + "; ".join(f"{l}: " + ", ".join(f"{c['check']} ({c['detail']})" for c in cs)
                                               for l, cs in bad.items()),
                                   remedy="Fix the cause and run again; see `python -m automatio report`.",
                                   details={"failed": bad})
        return {"summary": "; ".join(f"{l}: {r['result']['status']}" for l, r in out.items())}

    def _verify_one(self, verify, lang, asm, subs, man):
        res = verify(self.prod, self.narr, lang, asm, subs["files"], man)
        if self.prod.versions[lang].mode == "dub":
            from . import dub
            for c in res["checks"]:
                if c["check"] == "sync":         # the subtitles are the master's: report, never block
                    cov = (c.get("data") or {}).get("speech_coverage", 0)
                    c["status"] = "pass" if cov >= 0.85 else "warn"
                    c["detail"] = f"{self.prod.versions[lang].label} speech under the shared subtitles: " + c["detail"]
            res["checks"] += dub.checks(self.prod, lang, asm, res)
            res["status"] = "fail" if any(c["status"] == "fail" for c in res["checks"]) else (
                "warn" if any(c["status"] == "warn" for c in res["checks"]) else "pass")
        if res["status"] == "fail":
            # recorded as a result (not an exception) so the report shows every check
            pass
        warns = [f"{c['check']}: {c['detail']}" for c in res["checks"] if c["status"] == "warn"]
        return {"result": res, "summary": f"{res['status']} ({sum(c['status'] == 'pass' for c in res['checks'])}"
                                          f"/{len(res['checks'])} checks pass)", "warnings": warns}

    def s_deliver(self, force=False):
        per = {}
        for lang in self.prod.langs:
            idx, man = self._parts(lang)
            per[lang] = {"assemble": self.state.stage(f"assemble:{lang}"),
                         "subtitles": self.state.stage(f"subtitles:{lang}")["files"],
                         "verify": self.state.stage(f"verify:{lang}")["result"],
                         "manifest": man, "index": idx,
                         "sheets": self.state.stage(f"render:{lang}").get("sheets", [])
                         if self.prod.versions[lang].mode == "full" else []}
        thumb = None
        ref = thumbnail_ref(self.prod)
        warn = []
        if ref:
            try:
                thumb = R.render_thumbnail(self.prod, ref)
            except AAError as e:
                warn.append(f"thumbnail not rendered: {e.message}")
        man = do_deliver(self.prod, self.narr, per, self.state, thumb)
        return {"summary": f"delivered to {rel(self.prod.output_dir)}/ ("
                           + ", ".join(f"{v['label']}/" for v in man["versions"].values()) + ")",
                "output": rel(self.prod.output_dir), "warnings": warn}

    # ------------------------------------------------------------ loop
    COMPOSITE = ("draft", "voice", "render", "assemble", "subtitles", "verify", "deliver")

    def _stage_fp(self, sid: str) -> str:
        p = self.prod
        if sid == "ingest":
            return fingerprint(file_fp(p.script), self.narr_fp() if p.narration_path.exists() else "-")
        if sid == "translate":
            return fingerprint(self.narr_fp(), p.langs, p.subtitles.language, p.source_language)
        if sid == "scenes":
            return fingerprint(self.narr_fp(), self.scenes_fp())
        if sid == "approve":
            return self.approval_fp()
        if sid == "review":
            return self.review_fp()
        return fingerprint(sid, now_iso())      # validate + composite stages: always (re)check their parts

    def run(self, until: str | None = None, only: str | None = None, force: tuple = ()) -> Outcome:
        with RunLock(self.prod.build_dir, f"run {self.prod.slug}"):
            for f in force:
                self.state.invalidate(f)
            self.state.event("run_start", until=until, only=only, force=list(force))
            for sid, kind in STAGES:
                if only and sid != only:
                    continue
                if not self.enabled(sid):
                    if self.state.stage(sid).get("status") != "skipped":
                        self.state.mark(sid, "skipped", summary="disabled in production.toml")
                else:
                    fn = getattr(self, f"s_{sid}")
                    forced = sid in force
                    always = sid in self.COMPOSITE or sid in ("validate", "approve", "review")
                    try:
                        self._do(sid, self._stage_fp(sid), lambda: fn(force=forced), force=forced or always)
                    except _Agent as a:
                        return Outcome("needs_agent", sid, a.task["summary"], task=a.task)
                    except _Approval as a:
                        return Outcome("needs_approval", sid, "the production configuration needs the user's "
                                       "approval", approval=a.info)
                    except AAError as e:
                        return Outcome(e.outcome, sid, e.message, error=e.to_dict())
                    except Exception as e:
                        return Outcome("failed", sid, f"internal error in {sid}: {type(e).__name__}: {redact(e)}",
                                       error={"code": "internal_error", "message": redact(str(e)),
                                              "details": {"traceback": redact(traceback.format_exc()).splitlines()[-12:]}})
                if until and sid == until:
                    return Outcome("done", sid, f"stopped after {sid} as requested", data={"partial": True})
            if only:
                return Outcome("done", only, f"ran {only}", data={"partial": True})
            self.state.event("run_done")
            atomic_write_text(self.prod.output_dir / "report.md",
                              report_md(self.prod, self.state, read_json(self.prod.output_dir / "manifest.json")))
            return Outcome("done", "deliver", f"complete: {rel(self.prod.output_dir)}/",
                           data={"output": rel(self.prod.output_dir)})

    # ------------------------------------------------------------ status / next
    def status(self) -> dict:
        st = self.state.data.get("stages", {})
        rows = []
        for sid, kind in STAGES:
            subs = {k: v for k, v in st.items() if k.startswith(sid + ":")}
            s = st.get(sid, {})
            rows.append({"stage": sid, "kind": kind, "status": s.get("status", "pending") if self.enabled(sid)
                         else "skipped", "summary": s.get("summary", ""), "finished_at": s.get("finished_at"),
                         "parts": {k: v.get("status") for k, v in subs.items()}})
        from .state import RunLock as _RL
        holder = _RL(self.prod.build_dir, "").holder()
        return {"production": self.prod.slug, "title": self.prod.title, "dir": rel(self.prod.dir),
                "stages": rows, "running": holder, "progress": self.state.read_progress() if holder else None,
                "approval": {k: v for k, v in (self.state.approval or {}).items() if k != "fingerprint"} or None,
                "spent": self.state.data.get("spent", {}), "output": rel(self.prod.output_dir)}

    def next_action(self) -> dict:
        """What the harness should do now (no side effects besides validation)."""
        st = self.state.data.get("stages", {})
        holder = RunLock(self.prod.build_dir, "").holder()
        if holder:
            return {"action": "wait", "why": f"a run is in progress (pid {holder['pid']})",
                    "progress": self.state.read_progress()}
        for sid, kind in STAGES:
            s = st.get(sid, {})
            if not self.enabled(sid):
                continue
            status = s.get("status")
            if status == "waiting_agent":
                return {"action": "agent_task", "stage": sid, "task": s.get("task"),
                        "why": "the pipeline is waiting for creative work by the agent"}
            if status == "waiting_approval":
                return {"action": "ask_user_approval", "stage": sid, "approval": s.get("approval"),
                        "why": "the user must approve the configuration and budget"}
            if status == "failed":
                err = s.get("error", {})
                blocked = err.get("code") in ("missing_credential", "invalid_credential", "missing_capability",
                                              "provider_blocked", "quota_exceeded")
                return {"action": "report_to_user" if blocked else "fix_and_rerun", "stage": sid, "error": err,
                        "command": f"python -m automatio run {self.prod.slug}"}
            if status != "done" and status != "skipped":
                return {"action": "run", "stage": sid, "command": f"python -m automatio run {self.prod.slug}",
                        "why": f"stage {sid} is {status or 'pending'}"}
        return {"action": "done", "why": "all stages complete", "output": rel(self.prod.output_dir),
                "command": f"python -m automatio run {self.prod.slug}  # re-checks; skips everything fresh"}
