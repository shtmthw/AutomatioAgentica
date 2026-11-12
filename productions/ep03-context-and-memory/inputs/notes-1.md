# Production notes: Episode 03 (decisions, 2026-11-12)

These directions override the plan (Episode 03, "Context and Memory") where they differ.

- **Hindi is deferred (user, 2026-11-12):** "skip the hindi voice over for now, just english".
  This production starts with the English version only. The Hindi voice-over MP3, the Hindi
  SRT and the English | Hindi side-by-side file come later, as a dub on this video's timeline
  (`[versions.hi] mode = "dub"`, `follow = "en"`, as in Episode 02). Adding the dub later
  does not re-render the English video or invalidate its visual review.
- **Script:** the plan gives narration ideas and some required lines, but no full script. The
  English script was drafted from the plan, keeping the plan's required lines word for word
  ("The goal is not more context. The goal is the right context.", "The model doesn't
  remember. The harness writes it down and brings it back.", "Every technique for saving
  space loses something.") and the plan's closing narration. The user reviews and locks it
  at the approval step, before anything is rendered.
- **English voice:** the same English narrator as Episodes 01 and 02: edge-tts Andrew
  (`en-US-AndrewMultilingualNeural`, -5 %, profile `english-andrew`), as the plan asks.
- **Subtitles:** separate files only (standing guideline 1, the same decision as Episode 02).
  This overrides the plan's Final Expectation #6 ("burn subtitles into the video").
- **Visual continuity:** the Episode 02 source is available, so its palette, fonts and
  components (`agentic_video/internals.py`) are reused. The plan's fallback palette is not
  used. Plan colours map onto the house tokens: MODEL = BLUE, HARNESS = AMBER,
  TOOLS = TEAL, MEMORY = VIOLET, errors = RED.
- **New components** (Sized Message Card, Summary Card, Placeholder Card, Notebook, Note Card,
  Session Divider, plus a counter and the technique tag) are written as reusable classes in
  `productions/ep03-context-and-memory/scenes/memory_kit.py`, not in `agentic_video/`:
  changing the shared library would re-render Episodes 01 and 02 and force new visual
  reviews. A later episode can import them or promote them into the library.
- **Folder layout:** the pipeline's standard layout is kept (scenes in `scenes/`, narration
  in `narration.json`). The plan's file names (`ep03_context_and_memory_EN.mp4`,
  `ep03_EN.srt`, `timings/en.json`, `narration/en/`) are produced by the deliver stage
  inside `output/ep03-context-and-memory/`.
- **Spoken forms (English):** tool names, file names and numbers are respelled for the voice
  only (`save_note` -> "save note", `config.txt` -> "config dot T X T", `8800` ->
  "eighty-eight hundred", ...). Subtitles and the screen keep the written form.

## Revision 2 (2026-11-12, user request: "fix overlaps, narration and stutters, slightly longer recap")

- **Longer recap (section 01):** three sentences added to the opening recap ("Welcome back.",
  "On its own, it can't open a file or run a command.", the harness adds the tool result to the
  conversation, the conversation is a list of messages). About ten seconds longer.
- **Smoother delivery:** ingest had split every paragraph of three or more sentences into separate
  voice clips, so quotes and short tags were spoken as separate clips with a reset intonation and a
  pause ("…said: Fix the crash." | "Do not change the public function names."). Those lines are merged
  back into one line each (139 -> 128 lines). Tool-call phrasing that repeated words when spoken
  ("requests run command: run tests", "edit file. File updated", "tool call: save note: …") was
  reworded ("calls run_command to run the tests", "edit_file, and the file is updated",
  "a tool call to save_note, with the text: …").
- **Natural pauses:** the house English voice (edge-tts Andrew) holds ~0.5 s at many commas and colons
  and sometimes hesitates mid-phrase ("Every step ... adds more messages"); it is deterministic, so
  re-voicing does not help. `tools/voice_pauses.py` shortens only the silence inside each clip (comma
  pauses to 0.30 s, mid-phrase hesitations to 0.10 s, sentence breaks to 0.60 s; cuts in true silence
  with 5 ms crossfades) and shifts the clip's word timings to match, so cues and subtitles stay exact.
  18.8 s of dead air removed; voice, speed, pitch and settings are unchanged.
- **Section transitions:** the chapter tag fades in with the first line instead of before it, and
  scenes fade out in 0.6 s (silence between sections ~1.1 s instead of ~1.9 s).
- **Overlap check:** scenes use `memory_kit.CheckedScene`, which prints an OVERLAP line to the render
  log for any text/card/pill of two different objects that overlap for more than 0.6 s.
