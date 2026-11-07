"""Assembly of one language version: timeline -> concat -> voice track -> mix -> encode.

The timeline comes from the renders themselves: scene offsets from each rendered
video's real duration (ffprobe) and line start times from each scene's cue log, so
picture, voice and subtitles cannot drift apart.

The final MP4 has exactly one video and one audio stream. No subtitle filter is ever
applied and no subtitle stream is muxed: subtitles are delivered as separate files.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .audio import mix, place_voice
from .errors import StageFailed
from .log import log
from .util import atomic_write_json, probe_duration, read_json, rel, resolve, run, tmp_path


def timeline(prod, narr, lang: str, index: dict, man: dict) -> dict:
    by_sec = {s["section"]: s for s in index["scenes"]}
    offset, scenes, lines = 0.0, [], []
    for sec in narr.sections:
        r = by_sec.get(sec["key"])
        if not r:
            raise StageFailed(f"{lang}: no render for section {sec['key']}")
        vid = resolve(r["mp4"])
        cues = read_json(resolve(r["cues"]))
        dur = probe_duration(vid)
        if abs(dur - cues["duration"]) > 0.2:
            raise StageFailed(f"{lang}/{sec['key']}: video {dur:.2f}s vs cue log {cues['duration']:.2f}s - re-render")
        scenes.append({"section": sec["key"], "offset": round(offset, 4), "duration": dur, "mp4": r["mp4"]})
        for c in cues["cues"]:
            e = man["lines"][c["key"]]
            lines.append({"key": c["key"], "section": sec["key"], "start": round(offset + c["start"], 4),
                          "speech_start": round(offset + c["start"] + e["speech_start"], 4),
                          "speech_end": round(offset + c["start"] + e["speech_end"], 4)})
        offset += dur
    return {"lang": lang, "total": round(offset, 4), "scenes": scenes, "lines": lines}


def work_dir(prod, lang: str) -> Path:
    return prod.build_dir / "assemble" / lang


def assemble(prod, narr, lang: str, index: dict, man: dict, state) -> dict:
    work = work_dir(prod, lang)
    work.mkdir(parents=True, exist_ok=True)
    tl = timeline(prod, narr, lang, index, man)
    total = tl["total"]
    atomic_write_json(work / "timeline.json", tl)
    log.info(f"assemble {lang}: {len(tl['scenes'])} scenes, {len(tl['lines'])} lines, {total:.1f}s "
             f"({int(total // 60)}:{total % 60:04.1f})")

    state.progress(f"assemble:{lang}", 1, 4, "concat")
    concat = work / "concat.txt"
    concat.write_text("".join(f"file '{resolve(s['mp4']).as_posix()}'\n" for s in tl["scenes"]), encoding="utf-8")
    video = work / "video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-an", "-sn", "-c", "copy",
         video], what="ffmpeg concat")

    state.progress(f"assemble:{lang}", 2, 4, "mix")
    placements = [(ln["start"], resolve(man["lines"][ln["key"]]["file"]),
                   man["lines"][ln["key"]]["speech_start"], man["lines"][ln["key"]]["speech_end"]) for ln in tl["lines"]]
    voice, speech = place_voice(placements, total)
    stems = mix(voice, speech, total, prod.audio, work)

    state.progress(f"assemble:{lang}", 3, 4, "encode")
    final = work / "final.mp4"
    part = tmp_path(final)
    title = f"{prod.title}" + ("" if len(prod.versions) == 1 else f" ({prod.versions[lang].label.capitalize()})")
    v = prod.video
    vcodec = (["-c:v", "copy"] if v.encoder == "copy" else
              ["-c:v", "libx264", "-preset", v.preset, "-crf", str(v.crf), "-pix_fmt", "yuv420p", "-r", str(v.fps)])
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", video, "-i", stems["mix"], "-map", "0:v:0", "-map", "1:a:0",
           *vcodec, "-c:a", "aac", "-b:a", v.audio_bitrate, "-ar", "48000", "-ac", "2", "-sn", "-dn",
           "-t", f"{total:.3f}", "-movflags", "+faststart", "-metadata", f"title={title}",
           "-metadata:s:a:0", f"language={prod.versions[lang].audio_language}", part]
    log.info(f"  encoding ({'stream copy' if v.encoder == 'copy' else f'x264 crf {v.crf} {v.preset}'}) ...")
    run(cmd, log_file=work / "encode.log", what="ffmpeg encode")
    part.replace(final)
    video.unlink(missing_ok=True)
    Path(stems["mix"]).unlink(missing_ok=True)       # 24-bit mix is inside the MP4 now; stems are kept
    state.progress(f"assemble:{lang}", 4, 4, "done")
    return {"lang": lang, "final": rel(final), "total": total, "timeline": rel(work / "timeline.json"),
            "voice_stem": rel(stems["voice_stem"]),
            "music_stem": rel(stems["music_stem"]) if stems["music_stem"] else None,
            "encode": {"video": " ".join(vcodec), "audio": f"aac {v.audio_bitrate}", "subtitle_filter": None,
                       "subtitle_streams": 0}}


def clean(prod, lang: str) -> None:
    shutil.rmtree(work_dir(prod, lang), ignore_errors=True)
