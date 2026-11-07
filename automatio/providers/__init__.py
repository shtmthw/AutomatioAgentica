"""Text-to-speech providers. A provider turns one line of text into an audio clip
plus word timings, and knows how to fingerprint its settings for the cache."""
from __future__ import annotations

from ..errors import ConfigError
from .base import Provider, Synthesis


def get(name: str) -> Provider:
    if name == "elevenlabs":
        from .elevenlabs import ElevenLabsProvider
        return ElevenLabsProvider()
    if name == "edge":
        from .edge import EdgeProvider
        return EdgeProvider()
    if name == "tone":
        from .tone import ToneProvider
        return ToneProvider()
    raise ConfigError(f"unknown TTS provider {name!r} (available: elevenlabs, edge, tone)")


__all__ = ["get", "Provider", "Synthesis"]
