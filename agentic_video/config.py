"""Project-wide paths and production settings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ASSETS = ROOT / "assets"
VOICE_DIR = ASSETS / "voice"
VOICE_MANIFEST = VOICE_DIR / "manifest.json"
MUSIC_DIR = ASSETS / "music"

BUILD = ROOT / "build"
CUES_DIR = BUILD / "cues"          # per-scene cue timings written by the scenes
RENDER_DIR = BUILD / "media"       # manim output
OUTPUT = ROOT / "output"

# ---- Voice -----------------------------------------------------------------
# "elevenlabs": ElevenLabs Eleven v4 (natural, needs ELEVENLABS_API_KEY in .env)
# "edge":       Microsoft Pradeep via edge-tts (free, offline-cached fallback)
import os
TTS_ENGINE = os.environ.get("AGENTIC_TTS_ENGINE", "elevenlabs")   # override per run, e.g. AGENTIC_TTS_ENGINE=edge

# ElevenLabs (see tools/eleven.py: `python -m tools.eleven voices` to browse voices)
ELEVEN_MODEL = "eleven_v4"     # newest model; supports Hindi + [audio tags]
ELEVEN_VOICE_ID = "pNInz6obpgDQGcFmaJgB"   # "Adam" (ElevenLabs built-in voice; works on the free API)
ELEVEN_LANGUAGE = "hi"
ELEVEN_STABILITY = 0.5         # lower = more expressive, higher = steadier
ELEVEN_SIMILARITY = 0.75

# edge-tts fallback (free): native Hindi male voice
VOICE = "hi-IN-MadhurNeural"
VOICE_RATE = "-6%"       # slightly slower than default: calm, teaching pace
VOICE_PITCH = "-2Hz"     # a touch deeper
# How individual words are pronounced (both engines): agentic_video/pronunciation.py

# Silence inserted after every narration line (seconds) before the next one.
LINE_GAP = 0.35

# ---- Video ----------------------------------------------------------------
FPS = 30
WIDTH, HEIGHT = 1920, 1080

# Scenes in playback order (module, class name, section key)
SCENES = [
    ("scenes.s01_intro", "S01Intro", "s01"),
    ("scenes.s02_model", "S02Model", "s02"),
    ("scenes.s03_agent", "S03Agent", "s03"),
    ("scenes.s04_compare", "S04Compare", "s04"),
    ("scenes.s05_loop", "S05Loop", "s05"),
    ("scenes.s06_tools", "S06Tools", "s06"),
    ("scenes.s07_bugfix", "S07BugFix", "s07"),
    ("scenes.s08_reality", "S08Reality", "s08"),
    ("scenes.s09_outro", "S09Outro", "s09"),
]

# ---- Audio mix ------------------------------------------------------------
VOICE_LUFS = -16.0       # target integrated loudness of the narration
MUSIC_LUFS = -33.0       # music loudness before ducking (~17 LU under the voice)
DUCK_DB = 6.0            # extra attenuation of the music while the voice speaks
BURN_SUBTITLES = True    # burn the English subtitles into the main MP4 (an .srt is always written)
FINAL_NAME = "agentic_ai_intro_hi_1080p"
AUDIO_LANG, SUB_LANG = "hin", "eng"   # metadata: Hindi narration, English subtitles
SUB_FONT = "Inter"                   # subtitle font (English)
