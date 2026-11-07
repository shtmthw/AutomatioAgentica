"""ElevenLabs text-to-speech with character-level timestamps (standard library only).

Endpoint: POST /v1/text-to-speech/{voice_id}/with-timestamps returns audio_base64 plus a
character alignment, which becomes word timings. Each line is sent with its
neighbouring lines of the same section as previous_text / next_text, so the
delivery flows like one continuous read (as in the previous production).

Errors are classified so a harness can act on them:
  401 quota_exceeded       -> QuotaExceeded (blocked: buy credits / wait for reset)
  401 missing_permissions  -> ProviderBlocked (key lacks a permission)
  401 invalid key          -> InvalidCredential
  402 paid_plan_required   -> ProviderBlocked (e.g. Voice Library voice on the free plan)
  429 / 5xx / network      -> retried with exponential backoff (Retry-After honoured)
"""
from __future__ import annotations

import base64
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

from ..errors import InvalidCredential, ProviderBlocked, ProviderError, QuotaExceeded
from ..secrets import CREDS, redact
from .base import Provider, Synthesis, with_retries

API = "https://api.elevenlabs.io"
KEY = "ELEVENLABS_API_KEY"
_EXTRA = ("style", "use_speaker_boost", "speed", "seed", "apply_text_normalization")


def _detail(body: str) -> tuple[str, str]:
    try:
        d = json.loads(body).get("detail")
    except (ValueError, AttributeError):
        return "", body[:300]
    if isinstance(d, dict):
        return str(d.get("status") or d.get("code") or ""), str(d.get("message") or d)
    return "", str(d)[:300]


class ElevenLabsProvider(Provider):
    name = "elevenlabs"
    paid = True
    ext = "mp3"
    default_concurrency = 2      # free / starter plans allow 2-3 concurrent requests
    credentials = (KEY,)

    # ------------------------------------------------------------ http
    def _request(self, method: str, path: str, query: dict | None = None, body: dict | None = None,
                 timeout: float = 120):
        key = CREDS.require(KEY, "ElevenLabs narration")
        url = API + path + ("?" + urllib.parse.urlencode({k: v for k, v in (query or {}).items() if v is not None})
                            if query else "")
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "xi-api-key": key, "Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": "AutomatioAgentica/2"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return (json.loads(raw) if "json" in r.headers.get("Content-Type", "") else raw), dict(r.headers)
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            raise self._classify(e.code, text, e.headers) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            raise ProviderError(f"ElevenLabs unreachable: {redact(getattr(e, 'reason', e))}", retryable=True) from None

    def _classify(self, status: int, body: str, headers) -> ProviderError:
        code, msg = _detail(body)
        msg = redact(msg)
        ra = None
        try:
            ra = float(headers.get("Retry-After")) if headers and headers.get("Retry-After") else None
        except (TypeError, ValueError):
            pass
        # classify by ElevenLabs' error code first: the HTTP status varies (an invalid key is a 400)
        if code == "quota_exceeded":
            return QuotaExceeded(f"ElevenLabs credits exhausted: {msg}", status=status,
                                 remedy="Wait for the monthly credit reset or upgrade the plan, then run again "
                                        "(lines already generated are cached and are not paid for twice).")
        if code == "missing_permissions":
            return ProviderBlocked(f"ElevenLabs key is missing a permission: {msg}", status=status,
                                   remedy="elevenlabs.io -> API Keys -> edit the key: enable Text to Speech "
                                          "(and User: Read so credits can be checked before spending).")
        if status == 401 or code in ("invalid_api_key", "unauthorized", "invalid_authorization", "api_key_invalid"):
            e = InvalidCredential(f"ElevenLabs rejected the API key ({code or 'unauthorized'}): {msg}",
                                  remedy=f"Check {KEY} (harness environment or .env).")
            e.status, e.retryable, e.retry_after = status, False, None
            return e
        if status in (402, 403):
            return ProviderBlocked(f"ElevenLabs refused the request (HTTP {status} {code}): {msg}", status=status,
                                   remedy="This voice/model is not available on the current plan.")
        if status == 429 or status >= 500:
            return ProviderError(f"ElevenLabs HTTP {status} {code}: {msg}", status=status, retryable=True,
                                 retry_after=ra)
        err = ProviderError(f"ElevenLabs HTTP {status} {code}: {msg}", status=status)
        err.body = body
        return err

    # ------------------------------------------------------------ account
    def subscription(self) -> dict | None:
        """Plan/credits, or None when the key lacks the User: Read permission."""
        try:
            data, _ = self._request("GET", "/v1/user/subscription", timeout=30)
            return data
        except ProviderBlocked:
            return None

    def credits_left(self) -> int | None:
        s = self.subscription()
        if not s:
            return None
        return int(s.get("character_limit", 0)) - int(s.get("character_count", 0))

    # ------------------------------------------------------------ provider API
    def fingerprint(self, profile) -> str:
        # Same format as the previous production's cache keys, so its clips are reused.
        base = ["eleven-1", profile.get("model_id"), profile.get("voice_id"), profile.get("language_code") or "",
                str(profile.get("stability")), str(profile.get("similarity_boost"))]
        extra = [f"{k}={profile.get(k)}" for k in _EXTRA if profile.get(k) is not None]
        if profile.get("output_format", "mp3_44100_128") != "mp3_44100_128":
            extra.append(f"fmt={profile.get('output_format')}")
        return "|".join(base + extra)

    def keeps_tags(self) -> bool:
        return True

    def estimate_credits(self, profile, text: str) -> float:
        return len(text) * float(profile.get("credits_per_char", 1.0))

    def preflight(self, profile, needed_credits: float) -> dict:
        CREDS.require(KEY, "ElevenLabs narration")
        left = self.credits_left()
        if left is not None and left < needed_credits:
            raise QuotaExceeded(f"ElevenLabs has {left} credits left but this run needs ~{needed_credits:.0f}.",
                                remedy="Wait for the monthly reset or upgrade, then run again.")
        return {"credits_left": left}

    def synthesize(self, text: str, out, profile, *, previous_text=None, next_text=None) -> Synthesis:
        settings = {"stability": profile.get("stability"), "similarity_boost": profile.get("similarity_boost")}
        for k in ("style", "use_speaker_boost", "speed"):
            if profile.get(k) is not None:
                settings[k] = profile.get(k)
        body = {"text": text, "model_id": profile.get("model_id"), "voice_settings": settings}
        if profile.get("language_code"):
            body["language_code"] = profile.get("language_code")
        if profile.get("seed") is not None:
            body["seed"] = profile.get("seed")
        if profile.get("context", True):
            if previous_text:
                body["previous_text"] = previous_text
            if next_text:
                body["next_text"] = next_text
        query = {"output_format": profile.get("output_format", "mp3_44100_128")}
        path = f"/v1/text-to-speech/{profile.get('voice_id')}/with-timestamps"

        def call():
            try:
                data, headers = self._request("POST", path, query, body, timeout=300)
            except ProviderError as e:
                # some models reject the context fields: retry once without them
                if e.status == 400 and ("previous_text" in body or "next_text" in body):
                    body.pop("previous_text", None)
                    body.pop("next_text", None)
                    data, headers = self._request("POST", path, query, body, timeout=300)
                else:
                    raise
            return data, headers

        data, headers = with_retries(call, what="ElevenLabs")
        audio = base64.b64decode(data["audio_base64"])
        al = data.get("alignment") or data.get("normalized_alignment")
        if not al:
            raise ProviderError("ElevenLabs returned no alignment (word timings)")
        words = words_from_alignment(al)
        if not words:
            raise ProviderError("ElevenLabs alignment contained no words")
        from ..util import atomic_write_bytes
        atomic_write_bytes(out, audio)
        billed = headers.get("character-cost") or headers.get("Character-Cost")
        return Synthesis(words=words, chars_billed=int(billed) if billed and str(billed).isdigit() else len(text),
                         meta={"request_id": headers.get("request-id") or headers.get("Request-Id")})

    def check(self, profile, online: bool = False) -> list[dict]:
        res = []
        src = CREDS.source(KEY)
        res.append({"check": f"credential {KEY}", "ok": bool(src),
                    "detail": f"found in {src}" if src else "missing",
                    "remedy": None if src else f"set {KEY} in the harness environment or .env"})
        if online and src:
            try:
                s = self.subscription()
                if s is None:
                    res.append({"check": "ElevenLabs account", "ok": True, "warn": True,
                                "detail": "key accepted but restricted (no User: Read permission): the credit "
                                          "balance cannot be read; the first (canary) line of a paid batch "
                                          "verifies TTS access before the rest is generated"})
                else:
                    left = int(s.get("character_limit", 0)) - int(s.get("character_count", 0))
                    res.append({"check": "ElevenLabs account", "ok": True,
                                "detail": f"plan {s.get('tier')}, {left} credits left"})
            except ProviderError as e:
                res.append({"check": "ElevenLabs account", "ok": False, "detail": e.message, "remedy": e.remedy})
            try:
                v, _ = self._request("GET", f"/v1/voices/{profile.get('voice_id')}", timeout=30)
                res.append({"check": f"voice {profile.get('voice_id')}", "ok": True,
                            "detail": f"{v.get('name')} ({v.get('category')})"})
            except ProviderBlocked:
                res.append({"check": f"voice {profile.get('voice_id')}", "ok": True, "warn": True,
                            "detail": "cannot look voices up with this key (no Voices: Read); "
                                      "the voice is verified by synthesis"})
            except ProviderError as e:
                res.append({"check": f"voice {profile.get('voice_id')}", "ok": False, "detail": e.message})
        return res


def words_from_alignment(al: dict) -> list:
    """Character alignment -> [[start, duration, word], ...] (punctuation-only tokens and
    [audio tags] dropped). Unchanged from the previous production."""
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, s0, e0 = [], "", None, None
    for ch, a, b in zip(chars, st, en):
        if ch.isspace():
            if cur:
                words.append([s0, max(0.01, e0 - s0), cur])
            cur, s0 = "", None
            continue
        if s0 is None:
            s0 = a
        cur += ch
        e0 = b
    if cur:
        words.append([s0, max(0.01, e0 - s0), cur])
    out = []
    for s, d, w in words:
        core = w.strip(",।?!.;:—–-“”\"'()[]")
        if core and not re.fullmatch(r"\[[^\]]*\]", w):
            out.append([s, d, core])
    return out
