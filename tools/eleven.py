"""
ElevenLabs client (standard library only) + helper commands.

The API key is read from the environment variable ELEVENLABS_API_KEY or from
a `.env` file in the project root (gitignored):

    ELEVENLABS_API_KEY=sk_...

Commands
--------
    # what does my account allow? (credits left, models available)
    .venv/bin/python -m tools.eleven account

    # browse the Voice Library like in the video (Voices -> filter language/category).
    # Downloads each voice's free preview MP3 to output/samples/voices/ (no credits used).
    .venv/bin/python -m tools.eleven voices --gender male --use-case narration

    # hear candidate voices read OUR script (uses ~150 credits per voice)
    .venv/bin/python -m tools.eleven sample <voice_id> [<voice_id> ...]

    # then put the chosen voice in agentic_video/config.py (ELEVEN_VOICE_ID) and run
    .venv/bin/python -m tools.build all -j 5
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from agentic_video import config as C

API = "https://api.elevenlabs.io"


# ------------------------------------------------------------------ auth / http
def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY")
    env = C.ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            m = re.match(r"\s*ELEVENLABS_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
            if m:
                key = m.group(1)
    if not key:
        raise SystemExit(
            "No ElevenLabs API key found.\n"
            f"Create {env} containing a line:  ELEVENLABS_API_KEY=your_key\n"
            "(elevenlabs.io -> profile icon -> API Keys -> Create key)")
    return key


class ElevenError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"ElevenLabs HTTP {status}: {body[:400]}")
        self.status, self.body = status, body


def _request(method: str, path: str, query: dict | None = None, body: dict | None = None, timeout=120):
    url = API + path + ("?" + urllib.parse.urlencode({k: v for k, v in (query or {}).items() if v is not None})
                        if query else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "xi-api-key": api_key(), "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "")
            return json.loads(raw) if "json" in ctype else raw
    except urllib.error.HTTPError as e:
        raise ElevenError(e.code, e.read().decode("utf-8", "replace")) from None


# ------------------------------------------------------------------ account
def subscription() -> dict:
    return _request("GET", "/v1/user/subscription")


def credits_left() -> int:
    s = subscription()
    return int(s.get("character_limit", 0)) - int(s.get("character_count", 0))


def models() -> list:
    return _request("GET", "/v1/models")


# ------------------------------------------------------------------ voices
def search_shared(language="bn", gender=None, use_case=None, search=None, page_size=30) -> list:
    q = {"page_size": page_size, "language": language, "gender": gender, "use_cases": use_case,
         "search": search, "sort": "usage_character_count_1y"}
    return _request("GET", "/v1/shared-voices", q).get("voices", [])


def my_voices() -> list:
    return _request("GET", "/v1/voices").get("voices", [])


def add_shared(public_owner_id: str, voice_id: str, name: str) -> str:
    """Add a Voice Library voice to "My Voices" (as the video does with '+'); returns its voice_id."""
    r = _request("POST", f"/v1/voices/add/{public_owner_id}/{voice_id}", body={"new_name": name})
    return r.get("voice_id", voice_id)


# ------------------------------------------------------------------ speech
def tts_with_timestamps(text: str, voice_id: str, model_id: str, language_code: str | None,
                        stability: float, similarity: float, previous_text: str | None = None,
                        next_text: str | None = None, seed: int | None = None,
                        output_format: str = "mp3_44100_128"):
    """Return (mp3 bytes, alignment dict with characters/start/end times)."""
    body = {"text": text, "model_id": model_id,
            "voice_settings": {"stability": stability, "similarity_boost": similarity}}
    if language_code:
        body["language_code"] = language_code
    if previous_text:
        body["previous_text"] = previous_text
    if next_text:
        body["next_text"] = next_text
    if seed is not None:
        body["seed"] = seed
    r = _request("POST", f"/v1/text-to-speech/{voice_id}/with-timestamps",
                 {"output_format": output_format}, body, timeout=300)
    return base64.b64decode(r["audio_base64"]), (r.get("alignment") or r.get("normalized_alignment"))


def words_from_alignment(al: dict) -> list:
    """Character alignment -> [[start, duration, word], ...] (punctuation-only tokens dropped)."""
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
        if core and not re.fullmatch(r"\[[^\]]*\]", w):   # skip audio tags like [warmly]
            out.append([s, d, core])
    return out


# ------------------------------------------------------------------ CLI
SAMPLE_TEXT = ("अब आते हैं सबसे ज़रूरी हिस्से पर। एक AI Agent असल में काम कैसे करता है? "
               "इसके केंद्र में एक चक्र है, जिसे Agent Loop कहते हैं।")


def _cli():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("account")
    v = sub.add_parser("voices")
    v.add_argument("--language", default="bn")
    v.add_argument("--gender", default="male")
    v.add_argument("--use-case", default=None, help="e.g. narration, informative_educational")
    v.add_argument("--search", default=None)
    v.add_argument("--n", type=int, default=12)
    s = sub.add_parser("sample")
    s.add_argument("voice_ids", nargs="+")
    s.add_argument("--text", default=SAMPLE_TEXT)
    a = ap.parse_args()

    if a.cmd == "account":
        try:
            sub_ = subscription()
            print(f"plan: {sub_.get('tier')}  credits used {sub_.get('character_count')} / "
                  f"{sub_.get('character_limit')}  -> left {credits_left()}")
        except ElevenError as e:
            print(f"account/credits: not readable with this key (HTTP {e.status}; needs 'User: Read')")
        try:
            for m in models():
                langs = {l.get("language_id") for l in m.get("languages", [])}
                if m.get("can_do_text_to_speech"):
                    print(f"  {m['model_id']:28s} bengali={'bn' in langs}  {m.get('name','')}")
        except ElevenError as e:
            print(f"models: not readable with this key (HTTP {e.status}; needs 'Models: Read')")
    elif a.cmd == "voices":
        out = C.OUTPUT / "samples" / "voices"
        out.mkdir(parents=True, exist_ok=True)
        voices = search_shared(a.language, a.gender, a.use_case, a.search, page_size=a.n)
        if not voices:
            print("no voices found - try without --use-case, or --gender ''")
        for vo in voices:
            name = vo.get("name", "?")
            print(f"{vo['voice_id']}  owner={vo.get('public_owner_id')}  {name} | {vo.get('accent','')} | "
                  f"{vo.get('age','')} | {vo.get('use_case','')} | {(vo.get('description') or '')[:90]}")
            url = vo.get("preview_url")
            if url:
                fn = out / (re.sub(r"[^\w-]+", "_", name)[:40] + f"__{vo['voice_id']}.mp3")
                try:
                    urllib.request.urlretrieve(url, fn)
                except Exception as e:  # previews are optional
                    print("   (preview download failed:", e, ")")
        print(f"\nfree previews saved in {out}")
    elif a.cmd == "sample":
        out = C.OUTPUT / "samples" / "voices"
        out.mkdir(parents=True, exist_ok=True)
        from agentic_video.pronunciation import apply as pronounce
        text = pronounce(a.text)
        print(f"{len(text)} characters per sample; credits left before: {credits_left()}")
        for vid in a.voice_ids:
            audio, _ = tts_with_timestamps(text, vid, C.ELEVEN_MODEL, C.ELEVEN_LANGUAGE,
                                           C.ELEVEN_STABILITY, C.ELEVEN_SIMILARITY)
            fn = out / f"script_sample__{vid}.mp3"
            fn.write_bytes(audio)
            print(fn)


if __name__ == "__main__":
    _cli()
