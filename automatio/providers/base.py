from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import ProviderError
from ..log import log


@dataclass
class Synthesis:
    words: list                 # [[start_s, duration_s, word], ...] relative to the clip
    chars_billed: int = 0
    meta: dict = field(default_factory=dict)


class Provider:
    name = "base"
    paid = False                # spends money / credits per character
    network = True
    ext = "mp3"
    default_concurrency = 2
    credentials: tuple = ()

    def fingerprint(self, profile) -> str:
        raise NotImplementedError

    def send_text(self, spoken: str) -> str:
        """The exact text sent to the engine (e.g. edge-tts cannot speak [audio tags])."""
        return spoken

    def keeps_tags(self) -> bool:
        return False

    def estimate_credits(self, profile, text: str) -> float:
        return 0.0

    def latency(self, profile) -> float:
        """Seconds the word timings run ahead of the decoded audio (added to every word)."""
        return float(profile.get("latency", 0.0))

    def synthesize(self, text: str, out: Path, profile, *, previous_text=None, next_text=None) -> Synthesis:
        raise NotImplementedError

    def check(self, profile, online: bool = False) -> list[dict]:
        return []

    def preflight(self, profile, needed_credits: float) -> dict:
        """Called once before a paid batch. Returns info (e.g. credits left) or raises."""
        return {}


def with_retries(fn, *, what: str, attempts: int = 6, base: float = 2.0, cap: float = 60.0):
    """Call fn(); retry retryable ProviderErrors with exponential backoff + jitter,
    honouring Retry-After. Non-retryable errors propagate immediately."""
    for i in range(attempts):
        try:
            return fn()
        except ProviderError as e:
            if not e.retryable or i == attempts - 1:
                raise
            wait = e.retry_after if e.retry_after else min(cap, base * 2 ** i) * (0.75 + random.random() / 2)
            log.warning(f"  {what}: {e.message} - retrying in {wait:.0f}s ({i + 1}/{attempts - 1})")
            time.sleep(wait)
