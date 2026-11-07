"""AutomatioAgentica: a harness-driven, resumable video production pipeline.

A connected agent harness (Claude Code or any agent with filesystem + process
tools) drives this package through its CLI (`python -m automatio ...`). The
pipeline does the deterministic production work (voice, render, mix, encode,
subtitles, validation, packaging) and hands the creative steps (translation,
scene authoring, visual review) back to the harness as explicit agent tasks.

Directory roots can be moved with environment variables (useful for harnesses
that only grant access to some folders):

    AA_PRODUCTIONS_DIR  productions (inputs + agent-authored scenes)   ./productions
    AA_BUILD_DIR        per-production working state and intermediates  ./build
    AA_CACHE_DIR        content-addressed voice / render / music cache  ./cache
    AA_OUTPUT_DIR       final deliverables                              ./output
    AA_VOICES_FILE      voice registry                                  ./voices.toml
    AA_ENV_FILE         credentials file (KEY=value lines)              ./.env
"""
from __future__ import annotations

import os
from pathlib import Path

__version__ = "2.0.0"

ROOT = Path(__file__).resolve().parent.parent


def _env_path(name: str, default: Path) -> Path:
    v = os.environ.get(name)
    return Path(v).expanduser().resolve() if v else default


def productions_dir() -> Path:
    return _env_path("AA_PRODUCTIONS_DIR", ROOT / "productions")


def build_root() -> Path:
    return _env_path("AA_BUILD_DIR", ROOT / "build")


def cache_root() -> Path:
    return _env_path("AA_CACHE_DIR", ROOT / "cache")


def output_root() -> Path:
    return _env_path("AA_OUTPUT_DIR", ROOT / "output")


def voices_file() -> Path:
    return _env_path("AA_VOICES_FILE", ROOT / "voices.toml")
