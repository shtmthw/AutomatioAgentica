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

# The same for the English dub (tools/dub_en.py, voice "Andrew"). Subtitles keep
# the written form; only what Andrew says changes. A comma makes him pause there:
# where a sentence is split over two subtitles and the English is quicker than
# the subtitles, the wait goes to that comma instead of the middle of a phrase.
EN_PRONUNCIATION: dict[str, str] = {
    "The difference is whether": "The difference is, whether",
    "program's tests in the": "program's tests, in the",
    "set the boundary": "set the boundary,",
    "work with language are called": "work with language, are called",
}


def apply(text: str, table: dict[str, str] | None = None) -> str:
    """Return `text` with every dictionary word replaced by its spoken form."""
    table = PRONUNCIATION if table is None else table
    for word in sorted(table, key=len, reverse=True):
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", table[word], text)
    return text
