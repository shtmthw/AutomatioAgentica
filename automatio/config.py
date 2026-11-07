"""Configuration: the voice registry (voices.toml) and a production (production.toml).

Every setting has a default that reproduces the previous production ("What is
Agentic AI?", Nov 2026), so a production.toml only needs what differs.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from . import build_root, output_root, productions_dir, voices_file
from .errors import ConfigError, InputError

ISO639_2 = {"hi": "hin", "en": "eng", "bn": "ben", "ur": "urd", "ta": "tam", "te": "tel", "mr": "mar",
            "es": "spa", "fr": "fra", "de": "deu", "ar": "ara", "ja": "jpn", "zh": "zho"}
LABELS = {"hi": "hindi", "en": "english", "bn": "bangla", "ur": "urdu", "es": "spanish", "fr": "french"}


# ------------------------------------------------------------------ voices
@dataclass
class VoiceProfile:
    name: str
    language: str
    provider: str
    settings: dict
    pronunciation: dict = field(default_factory=dict)
    draft: str | None = None
    description: str = ""

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def public(self) -> dict:
        """Non-secret description for manifests and reports."""
        return {"profile": self.name, "provider": self.provider, "language": self.language,
                **{k: v for k, v in self.settings.items()}}


_PROFILE_META = {"language", "provider", "pronunciation", "draft", "description"}


def load_voices(path: Path | None = None) -> dict[str, VoiceProfile]:
    path = Path(path or voices_file())
    if not path.exists():
        raise ConfigError(f"voice registry not found: {path}", remedy="Restore voices.toml from git.")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path.name}: {e}") from e
    out = {}
    for name, d in data.items():
        if not isinstance(d, dict):
            continue
        for req in ("language", "provider"):
            if req not in d:
                raise ConfigError(f"{path.name}: voice [{name}] is missing `{req}`")
        out[name] = VoiceProfile(
            name=name, language=d["language"], provider=d["provider"],
            settings={k: v for k, v in d.items() if k not in _PROFILE_META},
            pronunciation=dict(d.get("pronunciation", {})), draft=d.get("draft"),
            description=d.get("description", ""))
    return out


# ------------------------------------------------------------------ production
@dataclass
class Version:
    lang: str
    voice: str
    label: str
    audio_language: str
    mode: str = "full"          # "full": own render timed to its narration; "dub": voiced over `follow`'s picture
    follow: str | None = None   # dub only: the master version whose picture, timeline and subtitles it reuses


@dataclass
class DubSettings:
    """How a dub version's lines are fitted onto the master timeline (see automatio/dub.py)."""
    max_speedup: float = 1.05   # time-stretch ceiling, used only where a segment would otherwise overflow
    max_lag: float = 1.0        # a line may start at most this much after the master line (warning above)
    max_spill: float = 1.0      # ... and run at most this far into the next master line (warning above)
    min_gap: float = 0.25       # real silence kept between two dub lines (measured on the audio)
    section_tail: float = 0.3   # a section's last line must end this long before the section ends
    anchors: list = field(default_factory=list)   # line keys that must start with their master line (steps)
    level_match: bool = True    # level every line to the same loudness before mixing (±6 dB at most)
    voice_chain: str = "highpass=f=70,deesser=i=0.35,acompressor=threshold=-21dB:ratio=2:attack=8:release=160"
    retakes: int = 2            # re-voice a paid clip whose ending is cut off, at most this often
    mp3_bitrate: str = "256k"


@dataclass
class VideoSettings:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    quality: str = "h"          # manim quality flag for the final render (l/m/h/p/k)
    encoder: str = "libx264"    # "libx264" (re-encode, as the previous production) or "copy"
    crf: int = 17
    preset: str = "slow"
    audio_bitrate: str = "192k"


@dataclass
class AudioSettings:
    voice_lufs: float = -16.0
    music_lufs: float = -33.0
    duck_db: float = 6.0
    line_gap: float = 0.35
    limiter_db: float = -1.5
    music: str = "ambient"      # "ambient" (synthesised, deterministic) or "none"
    loudness_tolerance: float = 1.0
    true_peak_max: float = -1.0


@dataclass
class SubtitleSettings:
    language: str = "en"
    formats: list = field(default_factory=lambda: ["srt", "vtt"])
    max_chars: int = 56
    hard_max: int = 68
    min_chars: int = 18
    lead: float = 0.08
    tail: float = 0.35
    min_duration: float = 0.9
    max_cps: float = 22.0       # reading speed warning threshold (characters per second)


@dataclass
class ReviewSettings:
    draft: bool = True          # free low-res draft (cheap voices) before paid voice + final render
    visual_review: bool = True  # agent inspects contact sheets of the draft
    draft_quality: str = "l"
    draft_fps: int = 15


@dataclass
class RenderSettings:
    jobs: int = 5
    timeout: int = 3600


@dataclass
class Production:
    slug: str
    dir: Path
    title: str
    source_language: str
    script: Path
    plan: Path
    notes: list
    narration_path: Path
    scenes_dir: Path
    versions: dict              # lang -> Version (ordered)
    subtitles: SubtitleSettings
    video: VideoSettings
    audio: AudioSettings
    review: ReviewSettings
    render: RenderSettings
    pronunciation: dict         # lang -> {word: spoken}
    budget: dict
    raw: dict
    voices: dict = field(default_factory=dict)
    dub: DubSettings = field(default_factory=DubSettings)

    @property
    def build_dir(self) -> Path:
        return build_root() / self.slug

    @property
    def output_dir(self) -> Path:
        return output_root() / self.slug

    @property
    def langs(self) -> list[str]:
        return list(self.versions)

    @property
    def full_langs(self) -> list[str]:
        """Versions rendered from the scenes (timed to their own narration)."""
        return [l for l, v in self.versions.items() if v.mode == "full"]

    @property
    def dub_langs(self) -> list[str]:
        """Versions voiced over a master version's picture and timeline."""
        return [l for l, v in self.versions.items() if v.mode == "dub"]

    @property
    def marker_langs(self) -> list[str]:
        """Languages whose narration must carry the cue markers (the ones scenes are timed to)."""
        return list(dict.fromkeys([self.source_language, *self.full_langs]))

    def profile(self, lang: str, draft: bool = False) -> VoiceProfile:
        v = self.versions[lang]
        prof = self.voices[v.voice]
        if draft and prof.draft:
            if prof.draft not in self.voices:
                raise ConfigError(f"voice [{prof.name}] names draft voice [{prof.draft}], which is not in voices.toml")
            return self.voices[prof.draft]
        return prof

    def pron_table(self, lang: str, profile: VoiceProfile) -> dict:
        t = dict(profile.pronunciation)
        t.update(self.pronunciation.get(lang, {}))
        return t

    def config_fingerprint_inputs(self) -> dict:
        """What an approval covers: languages, voices (exact provider settings), budget."""
        def ver(v):   # dub fields only when used, so existing approvals of full versions stay valid
            return {k: x for k, x in v.__dict__.items() if not (k in ("mode", "follow") and v.mode == "full")}
        return {"versions": {l: ver(v) for l, v in self.versions.items()},
                "voices": {l: self.profile(l).public() for l in self.langs},
                "subtitles": {"language": self.subtitles.language, "formats": self.subtitles.formats},
                "video": self.video.__dict__, "budget": self.budget,
                **({"dub": self.dub.__dict__} if self.dub_langs else {})}


def _section(cls, data: dict, name: str):
    known = {f.name for f in fields(cls)}
    unknown = set(data) - known
    if unknown:
        raise ConfigError(f"production.toml [{name}]: unknown setting(s) {sorted(unknown)}; allowed: {sorted(known)}")
    return cls(**data)


def find_production_dir(arg: str | None) -> Path:
    if arg:
        p = Path(arg).expanduser()
        if (p / "production.toml").exists():
            return p.resolve()
        q = productions_dir() / arg
        if (q / "production.toml").exists():
            return q.resolve()
        raise InputError(f"no production named {arg!r} (looked for {p}/production.toml and {q}/production.toml)",
                         remedy="Create one with `python -m automatio new <slug> --script FILE --plan FILE`.")
    found = sorted(productions_dir().glob("*/production.toml"))
    if len(found) == 1:
        return found[0].parent.resolve()
    names = [f.parent.name for f in found]
    raise InputError("which production? " + (f"available: {', '.join(names)}" if names else "none exist yet"),
                     remedy="Pass the production slug (or path) as an argument.")


def load_production(arg: str | None = None) -> Production:
    pdir = find_production_dir(arg)
    path = pdir / "production.toml"
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from e
    p = raw.get("production", {})
    if "title" not in p:
        raise ConfigError(f"{path}: [production] title is required")
    voices = load_voices()

    versions = {}
    for lang, v in (raw.get("versions") or {}).items():
        if "voice" not in v:
            raise ConfigError(f"{path}: [versions.{lang}] needs `voice` (a profile from voices.toml)")
        if v["voice"] not in voices:
            raise ConfigError(f"{path}: [versions.{lang}] voice {v['voice']!r} is not defined in voices.toml",
                              remedy=f"Defined voices: {', '.join(voices)}")
        if voices[v["voice"]].language != lang:
            raise ConfigError(f"{path}: [versions.{lang}] uses voice {v['voice']!r}, which speaks "
                              f"{voices[v['voice']].language!r}")
        mode = v.get("mode", "full")
        if mode not in ("full", "dub"):
            raise ConfigError(f"{path}: [versions.{lang}] mode must be 'full' or 'dub'")
        versions[lang] = Version(lang=lang, voice=v["voice"], label=v.get("label", LABELS.get(lang, lang)),
                                 audio_language=v.get("audio_language", ISO639_2.get(lang, "und")),
                                 mode=mode, follow=v.get("follow"))
    if not versions:
        raise ConfigError(f"{path}: at least one [versions.<lang>] section is required")
    for lang, ver in versions.items():
        if ver.mode == "dub":
            m = versions.get(ver.follow or "")
            if m is None or m.mode != "full":
                raise ConfigError(f"{path}: [versions.{lang}] is a dub; `follow` must name a full version "
                                  f"(got {ver.follow!r})", remedy='e.g. follow = "en"')

    subs = _section(SubtitleSettings, raw.get("subtitles", {}), "subtitles")
    bad = set(subs.formats) - {"srt", "vtt"}
    if bad:
        raise ConfigError(f"{path}: [subtitles] formats {sorted(bad)} not supported (use srt, vtt)")
    if raw.get("subtitles", {}).get("burn_in"):
        raise ConfigError("burned-in subtitles are disabled by policy: subtitles are always separate files")

    prod = Production(
        slug=p.get("slug", pdir.name), dir=pdir, title=p["title"],
        source_language=p.get("source_language", "en"),
        script=pdir / p.get("script", "inputs/script.md"),
        plan=pdir / p.get("plan", "inputs/plan.md"),
        notes=[pdir / n for n in p.get("notes", [])],
        narration_path=pdir / p.get("narration", "narration.json"),
        scenes_dir=pdir / p.get("scenes_dir", "scenes"),
        versions=versions, subtitles=subs,
        video=_section(VideoSettings, raw.get("video", {}), "video"),
        audio=_section(AudioSettings, raw.get("audio", {}), "audio"),
        review=_section(ReviewSettings, raw.get("review", {}), "review"),
        render=_section(RenderSettings, raw.get("render", {}), "render"),
        pronunciation=raw.get("pronunciation", {}),
        budget=raw.get("budget", {}), raw=raw, voices=voices,
        dub=_section(DubSettings, raw.get("dub", {}), "dub"))
    if prod.video.encoder not in ("libx264", "copy"):
        raise ConfigError(f"{path}: [video] encoder must be 'libx264' or 'copy'")
    for lang in prod.langs:
        prod.profile(lang, draft=True)   # validates draft references
    return prod
