"""
Pronunciation dictionary: how the narrator (Pradeep) should SAY a word.

Each entry maps a word as it is written in the script (and in the subtitles)
to the spelling that is sent to the voice. Subtitles always keep the original
spelling; only the audio changes.

    "AI": "एआई",          # say "E-AYE"

Rules:
- Matching is case-sensitive and whole-word ("AI" won't touch "Email").
- Suffixes after a hyphen keep working: "AI-wala" becomes "एआई-wala".
- Longer entries win over shorter ones ("AI Agent" before "AI").

To try a pronunciation before rebuilding:
    .venv/bin/python -m tools.say "आपने एक AI Agent से कहा"
Then apply it to the video:
    .venv/bin/python -m tools.build all
"""
import re

PRONUNCIATION: dict[str, str] = {
    "AI": "एआई",
    # Examples (uncomment / add your own):
    # "LLM": "एल एल एम",
    # "API": "ए पी आई",
    # "Claude": "क्लॉड",
}


def apply(text: str, table: dict[str, str] | None = None) -> str:
    """Return `text` with every dictionary word replaced by its spoken form."""
    table = PRONUNCIATION if table is None else table
    for word in sorted(table, key=len, reverse=True):
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", table[word], text)
    return text
