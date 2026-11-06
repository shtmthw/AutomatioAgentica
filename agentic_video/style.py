"""
Visual language for the whole video.

Dark, quiet canvas; thin outlines; dotted rounded "zones"; light italic Latin
labels; upright Hindi text. Each concept owns one accent colour and keeps it
for the whole video:

    BLUE   - AI model / chatbot / "decide"
    TEAL   - agent / action / success
    AMBER  - environment / observation / caution
    VIOLET - feedback / evaluation
    RED    - errors
"""
from manim import ITALIC, LIGHT, NORMAL, BOLD, Text, config as mconfig

BG = "#0b1114"
PANEL = "#0f171c"        # fill for cards and windows
PANEL_2 = "#121c22"
FG = "#e6ecef"
MUTED = "#8b98a1"
DIM = "#56636c"
FAINT = "#25313a"

BLUE = "#6cb4ee"
TEAL = "#6fd6b0"
AMBER = "#e3a857"
VIOLET = "#b49cf0"
RED = "#ef7a85"
GREEN = TEAL

def _pick_font(*candidates: str) -> str:
    """First installed font family among `candidates` (Pango names differ per system)."""
    try:
        import manimpango
        available = set(manimpango.list_fonts())
    except Exception:  # pragma: no cover
        return candidates[0]
    for c in candidates:
        if c in available:
            return c
    print(f"[style] none of {candidates} installed; using {candidates[-1]!r}")
    return candidates[-1]


# On-screen local-language text (Hindi, Devanagari). `bn()` below is the helper
# for local-language text; the name is historical (the first version was Bangla).
BN_FONT = _pick_font("Noto Sans Devanagari", "Noto Sans Devanagari UI", "Hind", "Noto Sans Devanagari")
EN_FONT = _pick_font("Inter", "Inter Variable", "Noto Sans", "DejaVu Sans")
MONO_FONT = _pick_font("JetBrains Mono", "JetBrainsMono Nerd Font Mono", "JetBrainsMono NF",
                       "Noto Sans Mono", "DejaVu Sans Mono")

# Type scale (manim font_size units)
H1 = 64
H2 = 44
BODY = 32
SMALL = 24
TINY = 19

STROKE = 1.8
ZONE_STROKE = 1.6

# Content must stay above this y so it never collides with subtitles.
SAFE_BOTTOM = -2.75
SAFE_TOP = 3.25


def has_bangla(s: str) -> bool:
    """True if `s` contains local-language script (Devanagari or Bengali)."""
    return any("\u0900" <= ch <= "\u09ff" for ch in s)


def bn(s: str, size: float = BODY, color: str = FG, weight=NORMAL, **kw) -> Text:
    """Upright body text (sentences, captions). Uses the Devanagari font when the
    text contains Hindi, otherwise Inter. (Labels use the italic `en()` style.)"""
    kw.setdefault("line_spacing", 0.9)
    font = BN_FONT if has_bangla(s) else EN_FONT
    return Text(s, font=font, font_size=size, color=color, weight=weight, **kw)


def en(s: str, size: float = BODY, color: str = FG, italic: bool = True, weight=LIGHT, **kw) -> Text:
    """Latin label in the reference style: light italic Inter."""
    return Text(s, font=EN_FONT, font_size=size, color=color,
                slant=ITALIC if italic else "NORMAL", weight=weight, **kw)


def mono(s: str, size: float = 20, color: str = FG, **kw) -> Text:
    return Text(s, font=MONO_FONT, font_size=size, color=color, **kw)


def txt(s: str, size: float = BODY, color: str = FG, **kw) -> Text:
    """Pick local-language (Hindi) or Latin styling automatically."""
    return bn(s, size, color, **kw) if has_bangla(s) else en(s, size, color, **kw)


def spaced(s: str, size: float = H1, color: str = FG, tracking: float = 0.45, weight=LIGHT):
    """Letter-spaced uppercase Latin title, built glyph by glyph on a shared baseline.

    `tracking` is the gap between letters as a fraction of the cap height.
    """
    from manim import VGroup, RIGHT, UP
    cap = Text("H", font=EN_FONT, font_size=size, weight=weight).height
    gap, space = cap * tracking, cap * (0.55 + tracking * 1.5)
    out, x = VGroup(), 0.0
    for ch in s:
        if ch == " ":
            x += space
            continue
        t = Text(ch, font=EN_FONT, font_size=size, color=color, weight=weight)
        t.shift(RIGHT * (x - t.get_left()[0]) + UP * (0 - t.get_bottom()[1]))
        out.add(t)
        x += t.width + gap
    return out.center()


def apply_canvas() -> None:
    mconfig.background_color = BG
