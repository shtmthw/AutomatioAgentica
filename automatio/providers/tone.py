"""Offline test voice: deterministic tone bursts, one per word, with exact word timings.

Used by the automated pipeline test and for dry runs without network or
credentials. Never use it for a real production (it is not speech)."""
from __future__ import annotations

import numpy as np
import soundfile as sf

from .base import Provider, Synthesis

SR = 24000


class ToneProvider(Provider):
    name = "tone"
    paid = False
    network = False
    ext = "wav"
    default_concurrency = 4

    def fingerprint(self, profile) -> str:
        return f"tone-1|{profile.get('pitch_hz', 160)}|{profile.get('char_seconds', 0.055)}"

    def synthesize(self, text: str, out, profile, *, previous_text=None, next_text=None) -> Synthesis:
        f0 = float(profile.get("pitch_hz", 160))
        cs = float(profile.get("char_seconds", 0.055))
        words, t, chunks = [], 0.05, [np.zeros(int(0.05 * SR), np.float32)]
        for tok in text.split():
            core = tok.strip(",.?!।;:\"'()")
            if not core:
                continue
            d = max(0.16, cs * len(core))
            n = int(d * SR)
            tt = np.arange(n) / SR
            env = np.sin(np.pi * tt / d) ** 0.6
            burst = 0.3 * env * (np.sin(2 * np.pi * f0 * tt) + 0.4 * np.sin(2 * np.pi * 2 * f0 * tt))
            words.append([round(t, 4), round(d, 4), core])
            gap = 0.32 if tok[-1:] in ".?!।" else (0.18 if tok[-1:] in ",;:" else 0.07)
            chunks += [burst.astype(np.float32), np.zeros(int(gap * SR), np.float32)]
            t += d + gap
        sf.write(out, np.concatenate(chunks), SR, subtype="PCM_16", format="WAV")
        return Synthesis(words=words)
