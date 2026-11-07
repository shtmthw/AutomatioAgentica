"""Microsoft neural voices through edge-tts (free, needs internet). Word timings come
from WordBoundary events. edge-tts word times run ~45 ms ahead of the decoded MP3
(measured in the previous production); profiles set `latency = 0.045` for that."""
from __future__ import annotations

import asyncio

from ..errors import MissingCapability, ProviderError
from ..narration import TAG
from .base import Provider, Synthesis, with_retries


class EdgeProvider(Provider):
    name = "edge"
    paid = False
    ext = "mp3"
    default_concurrency = 4

    def fingerprint(self, profile) -> str:
        return "|".join(["edge-1", profile.get("voice"), profile.get("rate", "+0%"), profile.get("pitch", "+0Hz")])

    def send_text(self, spoken: str) -> str:
        return TAG.sub(" ", spoken).strip()

    def synthesize(self, text: str, out, profile, *, previous_text=None, next_text=None) -> Synthesis:
        try:
            import edge_tts
        except ImportError:
            raise MissingCapability("edge-tts is not installed in this Python environment",
                                    remedy="uv pip install --python .venv/bin/python edge-tts") from None
        from ..util import tmp_path
        tmp = tmp_path(out)

        async def go():
            comm = edge_tts.Communicate(text, profile.get("voice"), rate=profile.get("rate", "+0%"),
                                        pitch=profile.get("pitch", "+0Hz"), boundary="WordBoundary")
            words = []
            with open(tmp, "wb") as f:
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        words.append([chunk["offset"] / 1e7, chunk["duration"] / 1e7, chunk["text"]])
            return words

        def call():
            try:
                words = asyncio.run(go())
            except Exception as e:      # network hiccups, service throttling
                raise ProviderError(f"edge-tts failed: {type(e).__name__}: {e}", retryable=True) from None
            if not words:
                raise ProviderError("edge-tts returned no word boundaries", retryable=True)
            return words

        words = with_retries(call, what="edge-tts", attempts=5)
        tmp.replace(out)
        return Synthesis(words=words)

    def check(self, profile, online: bool = False) -> list[dict]:
        res = []
        try:
            import edge_tts  # noqa: F401
            res.append({"check": "edge-tts package", "ok": True, "detail": "installed"})
        except ImportError:
            res.append({"check": "edge-tts package", "ok": False, "detail": "not installed",
                        "remedy": "uv pip install --python .venv/bin/python edge-tts"})
            return res
        if online:
            try:
                import edge_tts
                voices = asyncio.run(edge_tts.list_voices())
                names = {v["ShortName"] for v in voices}
                ok = profile.get("voice") in names
                res.append({"check": f"edge voice {profile.get('voice')}", "ok": ok,
                            "detail": "available" if ok else "not offered by the service any more"})
            except Exception as e:
                res.append({"check": "edge-tts service", "ok": False, "detail": f"unreachable: {e}"})
        return res
