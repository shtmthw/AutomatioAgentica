"""Capability check: what this environment (as granted by the harness) can and cannot do.

Offline by default. `--online` additionally contacts the providers (no credits are
spent: ElevenLabs account/voice lookups only, edge-tts voice list)."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

from . import build_root, cache_root, output_root, productions_dir
from .config import load_voices
from .secrets import CREDS, scrubbed_env


def _c(check, ok, detail, remedy=None, critical=True, warn=False):
    return {"check": check, "ok": bool(ok), "detail": detail, "remedy": remedy if not ok else None,
            "critical": critical, "warn": warn}


def run_doctor(online: bool = False) -> dict:
    out = []
    v = sys.version_info
    out.append(_c("python", v[:2] == (3, 12), f"{platform.python_implementation()} {platform.python_version()} "
                  f"({sys.executable})", "use the project venv: .venv/bin/python (Python 3.12)", critical=False))
    for mod in ("manim", "manimpango", "numpy", "soundfile", "edge_tts"):
        try:
            m = __import__(mod)
            out.append(_c(f"package {mod}", True, getattr(m, "__version__", "installed")))
        except Exception as e:
            out.append(_c(f"package {mod}", False, f"not importable: {e}",
                          "uv pip install --python .venv/bin/python -r pyproject.toml"))
    ff = shutil.which("ffmpeg")
    out.append(_c("ffmpeg", ff, ff or "not found", "install ffmpeg (with libx264)"))
    out.append(_c("ffprobe", shutil.which("ffprobe"), shutil.which("ffprobe") or "not found", "install ffmpeg"))
    if ff:
        env = scrubbed_env()
        ver = subprocess.run(["ffmpeg", "-hide_banner", "-version"], capture_output=True, text=True, env=env).stdout
        out[-2]["detail"] = ver.splitlines()[0] if ver else ff
        enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, env=env).stdout
        for e in ("libx264", "aac", "flac"):
            out.append(_c(f"encoder {e}", f" {e} " in enc, "available" if f" {e} " in enc else "missing",
                          "install an ffmpeg build with this encoder"))
        flt = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True, env=env).stdout
        out.append(_c("filter ebur128", " ebur128 " in flt, "available" if " ebur128 " in flt else "missing",
                      "install a full ffmpeg build"))
    try:
        import manimpango
        fonts = set(manimpango.list_fonts())
        for need, cands in (("Inter", ("Inter", "Inter Variable")),
                            ("JetBrains Mono", ("JetBrains Mono", "JetBrainsMono Nerd Font Mono", "JetBrainsMono NF")),
                            ("Noto Sans Devanagari", ("Noto Sans Devanagari", "Noto Sans Devanagari UI"))):
            hit = next((c for c in cands if c in fonts), None)
            out.append(_c(f"font {need}", hit, hit or "not installed (Manim would silently fall back)",
                          f"install the {need} font family", critical=False))
    except Exception as e:
        out.append(_c("fonts", False, f"cannot list fonts: {e}", critical=False))
    for name, d in (("productions dir", productions_dir()), ("build dir", build_root()), ("cache dir", cache_root()),
                    ("output dir", output_root())):
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".aa-write-test"
            probe.write_text("ok")
            probe.unlink()
            out.append(_c(f"write {name}", True, str(d)))
        except OSError as e:
            out.append(_c(f"write {name}", False, f"{d}: {e}", "grant the harness write access or set AA_*_DIR"))
    free = shutil.disk_usage(build_root()).free / 1e9
    out.append(_c("disk space", free > 5, f"{free:.0f} GB free at {build_root()}",
                  "free some space (a 10-minute production needs ~3 GB of intermediates)", critical=False))
    out.append(_c("cpu", True, f"{os.cpu_count()} cores (render.jobs defaults to 5)", critical=False))
    try:
        voices = load_voices()
        out.append(_c("voices.toml", True, f"{len(voices)} voice profile(s): {', '.join(voices)}"))
        from . import providers
        seen = set()
        for prof in voices.values():
            if prof.provider == "tone":
                continue
            for r in providers.get(prof.provider).check(prof, online=online):
                if r["check"] in seen:        # e.g. the same credential for several profiles
                    continue
                seen.add(r["check"])
                out.append(_c(f"[{prof.name}] {r['check']}", r["ok"], r["detail"], r.get("remedy"),
                              critical=False, warn=r.get("warn", False)))
    except Exception as e:
        out.append(_c("voices.toml", False, str(e), "restore voices.toml"))
    harness = "claude-code" if os.environ.get("CLAUDECODE") else ("unknown" if not os.environ.get("AA_HARNESS")
                                                                  else os.environ["AA_HARNESS"])
    out.append(_c("harness", True, f"{harness} (the pipeline only needs file access + process execution)",
                  critical=False))
    ok = all(c["ok"] for c in out if c["critical"])
    return {"ok": ok, "online": online, "checks": out,
            "credentials": {k: CREDS.source(k) or None for k in ("ELEVENLABS_API_KEY",)}}
