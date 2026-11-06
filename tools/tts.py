"""
Generate one narration clip per line and a manifest with durations and word
timings (used for animation sync and subtitles).

Engines (agentic_video/config.py -> TTS_ENGINE):
  "elevenlabs"  ElevenLabs Eleven v4 with the voice in ELEVEN_VOICE_ID.
                Each line is sent with its neighbouring lines as context
                (previous_text / next_text) so the delivery flows naturally.
  "edge"        Microsoft Pradeep via edge-tts (free fallback).

What is spoken can differ from what is shown (subtitles never change):
  * agentic_video/pronunciation.py   - word -> spoken form, applied everywhere
  * a 3-tuple line in narration.py   - a full spoken override for one line
  * [audio tags] such as [warmly]    - spoken by ElevenLabs as emotion, removed
                                        from subtitles automatically

Clips are cached: a line is regenerated only when its spoken text or the
voice settings change, so edits cost credits only for the edited lines.

    python -m tools.tts            # build missing / changed lines
    python -m tools.tts --force    # rebuild everything
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess

from agentic_video import config as C
from agentic_video.narration import all_lines
from agentic_video.pronunciation import apply as pronounce

TAG = re.compile(r"\s*\[[^\]]+\]\s*")


def strip_tags(text: str) -> str:
    return TAG.sub(" ", text).strip()


def engine_id() -> str:
    if C.TTS_ENGINE == "elevenlabs":
        return "|".join(["eleven-1", C.ELEVEN_MODEL, C.ELEVEN_VOICE_ID, C.ELEVEN_LANGUAGE or "",
                         str(C.ELEVEN_STABILITY), str(C.ELEVEN_SIMILARITY)])
    return "|".join(["edge-1", C.VOICE, C.VOICE_RATE, C.VOICE_PITCH])


def _hash(spoken: str) -> str:
    return hashlib.sha1(f"{engine_id()}|{spoken}".encode()).hexdigest()[:16]


def _probe_duration(path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip())


# ------------------------------------------------------------------ engines
async def synth_edge(text: str, out, retries: int = 5) -> list:
    """Speak `text` with Pradeep (edge-tts) into `out` (mp3); return word timings."""
    import edge_tts
    for attempt in range(retries):
        try:
            comm = edge_tts.Communicate(text, C.VOICE, rate=C.VOICE_RATE, pitch=C.VOICE_PITCH,
                                        boundary="WordBoundary")
            words = []
            with open(out, "wb") as f:
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        words.append([chunk["offset"] / 1e7, chunk["duration"] / 1e7, chunk["text"]])
            if not words:
                raise RuntimeError("no word boundaries returned")
            return words
        except Exception as e:  # network hiccups: back off and retry
            if attempt == retries - 1:
                raise
            print(f"  retry ({e})")
            await asyncio.sleep(2 * (attempt + 1))


def synth_eleven(text: str, out, previous_text=None, next_text=None, retries: int = 4) -> list:
    """Speak `text` with ElevenLabs into `out` (mp3); return word timings."""
    import time
    from tools import eleven
    for attempt in range(retries):
        try:
            audio, al = eleven.tts_with_timestamps(
                text, C.ELEVEN_VOICE_ID, C.ELEVEN_MODEL, C.ELEVEN_LANGUAGE,
                C.ELEVEN_STABILITY, C.ELEVEN_SIMILARITY, previous_text, next_text)
            with open(out, "wb") as f:
                f.write(audio)
            words = eleven.words_from_alignment(al)
            if not words:
                raise RuntimeError("no alignment returned")
            return words
        except eleven.ElevenError as e:
            # context fields not accepted by this model -> retry once without them
            if e.status == 400 and (previous_text or next_text) and "text" in e.body:
                previous_text = next_text = None
                continue
            if e.status in (401, 402, 403) or attempt == retries - 1:
                raise
            print(f"  retry ({e})")
            time.sleep(3 * (attempt + 1))


async def synth(text: str, out, previous_text=None, next_text=None) -> list:
    if C.TTS_ENGINE == "elevenlabs":
        return await asyncio.to_thread(synth_eleven, text, out, previous_text, next_text)
    return await synth_edge(strip_tags(text), out)


# ------------------------------------------------------------------ main
async def main(force: bool = False) -> None:
    C.VOICE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(C.VOICE_MANIFEST.read_text()) if C.VOICE_MANIFEST.exists() else {}
    lines = list(all_lines())
    spoken = [pronounce(t) for _, _, _, t in lines]

    todo = []
    for i, (sec, key, text, _) in enumerate(lines):
        h = _hash(spoken[i])
        mp3 = C.VOICE_DIR / f"{key}.mp3"
        if not force and key in manifest and manifest[key].get("hash") == h and mp3.exists():
            manifest[key]["text"] = strip_tags(text)
        else:
            todo.append(i)

    if C.TTS_ENGINE == "elevenlabs" and todo:
        from tools import eleven
        if not C.ELEVEN_VOICE_ID:
            raise SystemExit("Choose a voice first: `python -m tools.eleven voices`, then set "
                             "ELEVEN_VOICE_ID in agentic_video/config.py")
        need = sum(len(spoken[i]) for i in todo)
        try:
            left = eleven.credits_left()
        except eleven.ElevenError:
            left = None   # key without "User: Read" permission - can't check, carry on
        print(f"ElevenLabs: {len(todo)} line(s), {need} characters to generate; "
              f"{left if left is not None else 'unknown (key cannot read account)'} credits left")
        if left is not None and need > left:
            raise SystemExit("Not enough ElevenLabs credits for this run.")

    sem = asyncio.Semaphore(2 if C.TTS_ENGINE == "elevenlabs" else 4)

    async def work(i):
        sec, key, text, _ = lines[i]
        mp3 = C.VOICE_DIR / f"{key}.mp3"
        prev_t = strip_tags(spoken[i - 1]) if i > 0 and lines[i - 1][0] == sec else None
        next_t = strip_tags(spoken[i + 1]) if i + 1 < len(lines) and lines[i + 1][0] == sec else None
        async with sem:
            words = await synth(spoken[i], mp3, prev_t, next_t)
        stale = C.VOICE_DIR / f"{key}.wav"
        if stale.exists():
            stale.unlink()
        manifest[key] = {
            "section": sec, "text": strip_tags(text), "tts": strip_tags(spoken[i]), "hash": _hash(spoken[i]),
            "engine": C.TTS_ENGINE, "file": mp3.name, "duration": _probe_duration(mp3),
            "speech_start": words[0][0], "speech_end": words[-1][0] + words[-1][1], "words": words,
        }
        print(f"  built {key}")

    await asyncio.gather(*(work(i) for i in todo))
    ordered = {k: manifest[k] for _, k, _, _ in lines}
    C.VOICE_MANIFEST.write_text(json.dumps(ordered, ensure_ascii=False, indent=1))
    total = sum(v["speech_end"] + C.LINE_GAP for v in ordered.values())
    print(f"{len(ordered)} lines, ~{total / 60:.1f} min of narration (+ animation pauses)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    asyncio.run(main(ap.parse_args().force))
