"""Capability check: what this environment (as granted by the harness) can and cannot do.

Offline by default. `--online` additionally contacts the providers (no credits are
spent: ElevenLabs account/voice lookups only, edge-tts voice list)."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

from . import build_root, cache_root, local_dir, output_root, productions_dir
from .config import default_voices, load_voices, local_voices_file
from .secrets import CREDS, scrubbed_env

# What to install, per package manager (scripts/setup.sh installs the same lists).
PACKAGES = {
    "pacman": {"ffmpeg": "ffmpeg", "cairo": "cairo pango pkgconf base-devel", "Inter": "inter-font",
               "JetBrains Mono": "ttf-jetbrains-mono", "Noto Sans Devanagari": "noto-fonts", "uv": "uv"},
    "apt": {"ffmpeg": "ffmpeg", "cairo": "libcairo2-dev libpango1.0-dev pkg-config build-essential python3-dev",
            "Inter": "fonts-inter", "JetBrains Mono": "fonts-jetbrains-mono", "Noto Sans Devanagari": "fonts-noto-core",
            "uv": None},
    "dnf": {"ffmpeg": "ffmpeg (from RPM Fusion; Fedora's ffmpeg-free lacks libx264)",
            "cairo": "cairo-devel pango-devel pkgconf-pkg-config gcc python3-devel", "Inter": "rsms-inter-fonts",
            "JetBrains Mono": "jetbrains-mono-fonts", "Noto Sans Devanagari": "google-noto-sans-devanagari-fonts",
            "uv": "uv"},
    "brew": {"ffmpeg": "ffmpeg", "cairo": "cairo pango pkg-config", "Inter": "--cask font-inter",
             "JetBrains Mono": "--cask font-jetbrains-mono", "Noto Sans Devanagari": "--cask font-noto-sans-devanagari",
             "uv": "uv"},
}
_INSTALL = {"pacman": "sudo pacman -S --needed", "apt": "sudo apt-get install", "dnf": "sudo dnf install",
            "brew": "brew install"}


def package_manager() -> str | None:
    for pm, exe in (("brew", "brew"), ("pacman", "pacman"), ("apt", "apt-get"), ("dnf", "dnf")):
        if shutil.which(exe):
            return pm
    return None


def install_hint(item: str, fallback: str) -> str:
    """A concrete install command for this machine, or the generic remedy."""
    pm = package_manager()
    pkg = PACKAGES.get(pm, {}).get(item)
    if not pkg:
        return fallback
    return f"{_INSTALL[pm]} {pkg}  (or run scripts/setup.sh)"


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
                          "run scripts/setup.sh (or: uv pip install --python .venv/bin/python -r pyproject.toml --extra mcp)"))
    ff = shutil.which("ffmpeg")
    out.append(_c("ffmpeg", ff, ff or "not found", install_hint("ffmpeg", "install ffmpeg (with libx264)")))
    out.append(_c("ffprobe", shutil.which("ffprobe"), shutil.which("ffprobe") or "not found",
                  install_hint("ffmpeg", "install ffmpeg")))
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
        for f, use in (("rubberband", "dub time-stretch"), ("deesser", "dub voice chain")):
            out.append(_c(f"filter {f}", f" {f} " in flt, ("available" if f" {f} " in flt else "missing") + f" ({use})",
                          f"install an ffmpeg build with {f} (only needed for dub versions)", critical=False))
    try:
        import manimpango
        fonts = set(manimpango.list_fonts())
        for need, cands in (("Inter", ("Inter", "Inter Variable")),
                            ("JetBrains Mono", ("JetBrains Mono", "JetBrainsMono Nerd Font Mono", "JetBrainsMono NF")),
                            ("Noto Sans Devanagari", ("Noto Sans Devanagari", "Noto Sans Devanagari UI"))):
            hit = next((c for c in cands if c in fonts), None)
            out.append(_c(f"font {need}", hit, hit or "not installed (Manim would silently fall back)",
                          install_hint(need, f"install the {need} font family"), critical=False))
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
    try:
        import mcp  # noqa: F401
        from importlib.metadata import version
        out.append(_c("package mcp", True, f"{version('mcp')} (MCP server: python -m automatio.mcp_server)",
                      critical=False))
    except Exception:
        out.append(_c("package mcp", False, "not installed (only needed for the MCP server)",
                      "uv pip install --python .venv/bin/python -r pyproject.toml --extra mcp", critical=False))
    loc = local_dir()
    active = [f.name for f in (local_voices_file(), loc / "GUIDELINES.md") if f.exists()]
    if active:
        dv = default_voices()
        out.append(_c("local overrides", True, f"{loc}: {', '.join(active)} (new uses "
                      + ", ".join(f"{k}={v}" for k, v in dv.items()) + ")", critical=False, warn=False))
    else:
        out.append(_c("local overrides", True, "none: house voices and guidelines (see local/README.md)",
                      critical=False))
    harness = "claude-code" if os.environ.get("CLAUDECODE") else ("unknown" if not os.environ.get("AA_HARNESS")
                                                                  else os.environ["AA_HARNESS"])
    out.append(_c("harness", True, f"{harness} (the pipeline only needs file access + process execution)",
                  critical=False))
    ok = all(c["ok"] for c in out if c["critical"])
    return {"ok": ok, "online": online, "checks": out,
            "credentials": {k: CREDS.source(k) or None for k in ("ELEVENLABS_API_KEY",)}}
