"""Narration: one clip per narration line and language, with word and marker timings.

Clips live in a content-addressed cache (cache/voice/<provider>/<hash>.<ext>) keyed by
the provider settings and the exact spoken text, so

  * re-runs, resumed runs and other productions reuse every clip already made,
  * editing one line re-voices only that line,
  * paid credits are never spent twice for the same text.

Paid providers additionally go through: budget check (approved budget minus what this
production already spent) -> provider preflight (credits, if the key can read them) ->
one "canary" line on its own (fails fast on key/plan/quota problems) -> the rest in
parallel. Every finished clip is recorded immediately, so an interrupted batch
resumes without paying again.
"""
from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from . import cache_root, providers
from .errors import AAError, BudgetExceeded, ProviderError
from .log import log
from .narration import Narration, compose, display, marker_times
from .util import atomic_write_json, fingerprint, now_iso, probe_duration, read_json, rel, resolve


def cache_dir(provider: str) -> Path:
    return cache_root() / "voice" / provider


@dataclass
class LineJob:
    section: str
    key: str
    spoken: str         # pronounced text, markers removed (what the alignment refers to)
    send: str           # exact text sent to the engine
    positions: dict     # marker -> char position in `spoken`
    subtitle: str       # subtitle-language display text of this line
    display: str        # this language's display text
    hash: str
    path: Path
    meta: Path
    prev: str | None = None
    next: str | None = None

    @property
    def cached(self) -> bool:
        return self.path.exists() and self.meta.exists()


def plan(prod, narr: Narration, lang: str, profile) -> list[LineJob]:
    prov = providers.get(profile.provider)
    table = prod.pron_table(lang, profile)
    fp = prov.fingerprint(profile)
    out: list[LineJob] = []
    for sec, ln in narr.lines():
        spoken, pos = compose(narr.spoken_source(ln, lang), table, strip_tags=not prov.keeps_tags())
        h = hashlib.sha1(f"{fp}|{spoken}".encode()).hexdigest()[:16]
        d = cache_dir(prov.name)
        out.append(LineJob(sec["key"], ln["key"], spoken, prov.send_text(spoken), pos,
                           display(ln[prod.subtitles.language]), display(ln[lang]), h,
                           d / f"{h}.{prov.ext}", d / f"{h}.json"))
    if profile.get("context", True):
        from .narration import TAG
        for i, j in enumerate(out):
            if i > 0 and out[i - 1].section == j.section:
                j.prev = TAG.sub(" ", out[i - 1].spoken).strip()
            if i + 1 < len(out) and out[i + 1].section == j.section:
                j.next = TAG.sub(" ", out[i + 1].spoken).strip()
    return out


def choose_profile(prod, narr: Narration, lang: str, draft: bool):
    """The voice for a run. Drafts must be free: a free final voice drafts itself, a paid
    voice whose clips are all cached drafts itself (costs nothing), otherwise its
    `draft` voice is used."""
    from .errors import ConfigError
    final = prod.profile(lang)
    if not draft or not providers.get(final.provider).paid:
        return final
    if all(j.cached for j in plan(prod, narr, lang, final)):
        return final
    if not final.draft:
        raise ConfigError(f"voice [{final.name}] is paid and has no `draft` voice in voices.toml",
                          remedy="Add a free draft voice (provider 'edge') or set [review] draft = false.")
    return prod.profile(lang, draft=True)


def stage_fingerprint(prod, lang: str, profile, jobs: list[LineJob]) -> str:
    prov = providers.get(profile.provider)
    return fingerprint("voice-2", prov.fingerprint(profile), prov.latency(profile),
                       [(j.section, j.key, j.hash, j.subtitle, sorted(j.positions.items())) for j in jobs])


def cost(prod, profile, jobs: list[LineJob]) -> dict:
    prov = providers.get(profile.provider)
    miss = [j for j in jobs if not j.cached]
    return {"provider": prov.name, "paid": prov.paid, "lines": len(jobs), "cached": len(jobs) - len(miss),
            "to_generate": len(miss), "chars": sum(len(j.send) for j in miss),
            "credits": round(sum(prov.estimate_credits(profile, j.send) for j in miss), 1)}


def _synth_one(prov, profile, job: LineJob) -> dict:
    job.path.parent.mkdir(parents=True, exist_ok=True)
    res = prov.synthesize(job.send, job.path, profile, previous_text=job.prev, next_text=job.next)
    meta = {"text": job.send, "fingerprint": prov.fingerprint(profile), "provider": prov.name,
            "words": res.words, "duration": probe_duration(job.path), "chars_billed": res.chars_billed,
            "created_at": now_iso(), **({"meta": res.meta} if res.meta else {})}
    atomic_write_json(job.meta, meta)
    return meta


def generate(prod, lang: str, profile, jobs: list[LineJob], state, *, approval: dict | None,
             progress=None) -> dict:
    """Synthesise all uncached lines. Returns {"generated": n, "credits": x}."""
    prov = providers.get(profile.provider)
    miss = [j for j in jobs if not j.cached]
    # identical text in several lines is generated once
    uniq: dict[str, LineJob] = {}
    for j in miss:
        uniq.setdefault(j.hash, j)
    miss = list(uniq.values())
    if not miss:
        return {"generated": 0, "credits": 0.0}
    need = sum(prov.estimate_credits(profile, j.send) for j in miss)
    if prov.paid:
        budget = float(((approval or {}).get("budget") or {}).get(prov.name, 0.0))
        spent = state.spent(prov.name)
        if need > budget - spent + 1e-6:
            raise BudgetExceeded(
                f"{lang}: {len(miss)} line(s) need ~{need:.0f} {prov.name} credits, but the approved budget "
                f"has {max(0.0, budget - spent):.0f} left ({budget:.0f} approved, {spent:.0f} spent).",
                remedy="Ask the user to approve a larger budget: "
                       f"`python -m automatio approve {prod.slug} --budget {prov.name}={int(need + spent + 1)}`",
                details={"provider": prov.name, "needed": need, "budget": budget, "spent": spent})
        info = prov.preflight(profile, need)
        log.info(f"  {prov.name}: {len(miss)} line(s), ~{need:.0f} credits"
                 + (f"; {info['credits_left']} credits left" if info.get("credits_left") is not None
                    else "; credit balance not readable with this key"))
    lock = threading.Lock()
    done = {"n": 0, "credits": 0.0}

    def finish(job, meta):
        with lock:
            done["n"] += 1
            if prov.paid:
                c = prov.estimate_credits(profile, job.send)
                done["credits"] += c
                state.add_spent(prov.name, c)
            if progress:
                progress(done["n"], len(miss), job.key)

    # canary: one line alone, so a bad key / plan / quota fails before a parallel batch
    first, rest = miss[0], miss[1:]
    finish(first, _synth_one(prov, profile, first))
    workers = int(profile.get("concurrency", prov.default_concurrency))
    errors: list[BaseException] = []
    stop = threading.Event()

    def task(job):
        if stop.is_set():
            return job, None
        try:
            return job, _synth_one(prov, profile, job)
        except BaseException as e:
            if isinstance(e, AAError) and not (isinstance(e, ProviderError) and e.retryable):
                stop.set()   # fatal for the batch (quota, permissions, key): don't start more requests
            errors.append(e)
            return job, None

    ex = ThreadPoolExecutor(max(1, workers))
    try:
        for fut in as_completed([ex.submit(task, j) for j in rest]):
            job, meta = fut.result()
            if meta is not None:
                finish(job, meta)
    except BaseException:
        stop.set()                                   # interrupted: never start queued (paid) requests
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    if errors:
        raise errors[0]
    return {"generated": done["n"], "credits": done["credits"]}


def build_manifest(prod, lang: str, profile, jobs: list[LineJob], *, draft: bool, fp: str) -> dict:
    prov = providers.get(profile.provider)
    lat = prov.latency(profile)
    lines = {}
    for j in jobs:
        meta = read_json(j.meta)
        words = [[round(s + lat, 4), d, w] for s, d, w in meta["words"]]
        lines[j.key] = {
            "key": j.key, "section": j.section, "file": rel(j.path), "hash": j.hash,
            "duration": meta["duration"], "speech_start": words[0][0], "speech_end": words[-1][0] + words[-1][1],
            "words": words, "markers": marker_times(j.spoken, words, j.positions),
            "display": j.display, "spoken": j.spoken, "subtitle": j.subtitle}
    return {"lang": lang, "draft": draft, "voice": profile.public(), "fingerprint": fp, "created_at": now_iso(),
            "lines": lines}


def manifest_path(prod, lang: str, draft: bool = False) -> Path:
    return prod.build_dir / ("draft-voice" if draft else "voice") / lang / "manifest.json"


def run_language(prod, narr: Narration, lang: str, state, *, draft: bool = False, approval=None) -> dict:
    """Voice one language (final or draft). Returns a summary dict."""
    profile = choose_profile(prod, narr, lang, draft)
    jobs = plan(prod, narr, lang, profile)
    fp = stage_fingerprint(prod, lang, profile, jobs)
    mpath = manifest_path(prod, lang, draft)
    existing = read_json(mpath)
    if existing and existing.get("fingerprint") == fp and all(j.cached for j in jobs):
        return {"lang": lang, "profile": profile.name, "manifest": rel(mpath), "generated": 0, "credits": 0.0,
                "cached": len(jobs), "fingerprint": fp, "skipped": True}
    c = cost(prod, profile, jobs)
    log.info(f"voice {lang}{' (draft)' if draft else ''}: {profile.name} [{profile.provider}] "
             f"{c['lines']} lines, {c['cached']} cached, {c['to_generate']} to generate")
    res = generate(prod, lang, profile, jobs, state, approval=approval,
                   progress=lambda d, t, k: state.progress(f"voice:{lang}", d, t, k))
    man = build_manifest(prod, lang, profile, jobs, draft=draft, fp=fp)
    atomic_write_json(mpath, man)
    total = sum(e["speech_end"] for e in man["lines"].values())
    return {"lang": lang, "profile": profile.name, "manifest": rel(mpath), "generated": res["generated"],
            "credits": round(res["credits"], 1), "cached": c["cached"], "fingerprint": fp,
            "speech_seconds": round(total, 1)}


# ------------------------------------------------------------------ helpers
def import_legacy(manifest: Path, clips_dir: Path, provider: str, fp_string: str) -> int:
    """Adopt clips of the pre-2.0 layout (assets/voice/manifest.json) into the cache.
    Their hashes already use the same (provider settings | spoken text) scheme."""
    from .util import link_or_copy
    old = read_json(manifest) or {}
    d = cache_dir(provider)
    n = 0
    for key, e in old.items():
        h = hashlib.sha1(f"{fp_string}|{e['tts']}".encode()).hexdigest()[:16]
        if h != e.get("hash"):
            continue
        src = clips_dir / e["file"]
        if not src.exists():
            continue
        dst = d / f"{h}{src.suffix}"
        if not dst.exists():
            link_or_copy(src, dst)
        if not (d / f"{h}.json").exists():
            atomic_write_json(d / f"{h}.json", {"text": e["tts"], "fingerprint": fp_string, "provider": provider,
                                                 "words": e["words"], "duration": e["duration"],
                                                 "imported_from": rel(src), "created_at": now_iso()})
        n += 1
    return n


def audition(profile, text: str, out_dir: Path, table: dict | None = None) -> Path:
    """Speak arbitrary text with a voice profile (cached like narration)."""
    prov = providers.get(profile.provider)
    spoken, _ = compose(text, table, strip_tags=not prov.keeps_tags())
    h = hashlib.sha1(f"{prov.fingerprint(profile)}|{spoken}".encode()).hexdigest()[:16]
    d = cache_dir(prov.name)
    job = LineJob("say", "say", spoken, prov.send_text(spoken), {}, "", text, h, d / f"{h}.{prov.ext}", d / f"{h}.json")
    if not job.cached:
        _synth_one(prov, profile, job)
    out_dir.mkdir(parents=True, exist_ok=True)
    import re
    slug = re.sub(r"[^\wऀ-৿-]+", "_", text).strip("_")[:40] or "sample"
    dst = out_dir / f"{profile.name}__{slug}.{prov.ext}"
    from .util import link_or_copy
    link_or_copy(job.path, dst)
    return dst


def load_manifest(prod, lang: str, draft: bool = False) -> dict | None:
    return read_json(manifest_path(prod, lang, draft))


def clip_path(entry: dict) -> Path:
    return resolve(entry["file"])
