"""Credentials: resolution, masking and redaction.

Lookup order for a credential such as ELEVENLABS_API_KEY:
  1. the process environment (how most harnesses inject secrets)
  2. the env file named by AA_ENV_FILE, otherwise <repo>/.env (gitignored)

Values are never exported into os.environ, never written to state, logs,
reports or manifests, and every string the pipeline prints passes through
`redact()`. Subprocesses (manim, ffmpeg) get an environment with all
credential-like variables removed (`scrubbed_env`).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import ROOT

KNOWN = ("ELEVENLABS_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "AZURE_SPEECH_KEY", "GOOGLE_API_KEY")
_SECRETISH = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.I)
_PATTERNS = [
    re.compile(r"\bsk_[A-Za-z0-9]{16,}\b"),          # ElevenLabs
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{16,}\b"),  # Anthropic / OpenAI style
]


def env_file() -> Path:
    v = os.environ.get("AA_ENV_FILE")
    return Path(v).expanduser() if v else ROOT / ".env"


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m or line.lstrip().startswith("#"):
            continue
        val = m.group(2).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        else:
            val = val.split(" #")[0].strip()
        out[m.group(1)] = val
    return out


class Credentials:
    def __init__(self):
        self._loaded = False
        self._file: dict[str, str] = {}

    def _load(self):
        if not self._loaded:
            self._file = _parse_env_file(env_file())
            self._loaded = True

    def reload(self):
        self._loaded = False
        self._load()

    def get(self, name: str) -> str | None:
        self._load()
        v = os.environ.get(name) or self._file.get(name)
        return v or None

    def source(self, name: str) -> str | None:
        self._load()
        if os.environ.get(name):
            return "environment"
        if self._file.get(name):
            return str(env_file().name if env_file().parent == ROOT else env_file())
        return None

    def require(self, name: str, purpose: str) -> str:
        v = self.get(name)
        if not v:
            from .errors import MissingCredential
            raise MissingCredential(
                f"{name} is required for {purpose} but was not found.",
                remedy=(f"Provide {name} through the harness environment, or add a line "
                        f"`{name}=...` to {env_file()} (gitignored). Never paste it into a script or plan."),
                details={"credential": name})
        return v

    def secret_values(self) -> list[str]:
        self._load()
        vals = set()
        for k, v in list(os.environ.items()) + list(self._file.items()):
            if v and len(v) >= 8 and (k in KNOWN or _SECRETISH.search(k)):
                vals.add(v)
        return sorted(vals, key=len, reverse=True)


CREDS = Credentials()


def redact(text) -> str:
    """Remove every known secret value and anything that looks like an API key."""
    if text is None:
        return ""
    s = str(text)
    for v in CREDS.secret_values():
        if v in s:
            s = s.replace(v, "***")
    for p in _PATTERNS:
        s = p.sub("***", s)
    return s


def mask(value: str | None) -> str:
    if not value:
        return "(missing)"
    return f"{value[:3]}…({len(value)} chars)"


def scrubbed_env(extra: dict | None = None) -> dict:
    """os.environ without credential-like variables, for subprocesses."""
    env = {k: v for k, v in os.environ.items() if not (k in KNOWN or _SECRETISH.search(k))}
    if extra:
        env.update(extra)
    return env
