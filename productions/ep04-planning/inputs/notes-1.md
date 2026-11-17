# Production notes: Episode 04 (decisions, 2026-11-13)

These directions override the plan (Episode 04, "Planning") where they differ.

- **Hindi is deferred (user, 2026-11-13):** "skip the hindi voiceover, just english for now".
  This production starts with the English version only. The Hindi voice-over MP3
  (`ep04_voiceover_HI.mp3`), the Hindi SRT (`ep04_HI.srt`), the per-section Hindi texts and the
  English | Hindi side-by-side file come later, as a dub on this video's timeline
  (`[versions.hi] mode = "dub"`, `follow = "en"`, as in Episode 02), with dub anchors on the
  numbered steps of sections 05-09. Adding the dub later does not re-render the English video
  or invalidate its visual review.
- **Script:** the plan gives narration ideas and required lines, but no full script. The
  English script was drafted from the plan, keeping its required lines word for word
  ("A plan is just text. But it is text that keeps the agent on track.", "Done means checked,
  not just said.", "A plan is a guide, not a script.") and the plan's closing narration
  (lightly trimmed: "We saw that" dropped). The user reviews and locks it at the approval step.
- **English voice:** the same English narrator as Episodes 01-03: edge-tts Andrew
  (`en-US-AndrewMultilingualNeural`, -5 %, profile `english-andrew`).
- **Subtitles:** separate files only (standing guideline 1, the same decision as Episodes 02
  and 03). This overrides the plan's Final Expectation #6 ("burn English subtitles into the video").
- **Visual continuity:** the Episode 02/03 sources are available, so their palette, fonts and
  components are reused (`agentic_video/internals.py`, and Episode 03's `memory_kit.py`, copied
  unchanged into this production's `scenes/`). The plan's fallback palette is not used. Plan
  colours map onto the house tokens: MODEL = BLUE, HARNESS = AMBER, TOOLS = TEAL (the house
  mint green), MEMORY = VIOLET, errors = RED. PLAN gets its own accent, a cyan (`PLAN` in
  `plan_kit.py`), because the house TEAL already means TOOLS.
- **New components** (Goal Card, Plan Panel, Step Row, Evidence Link, Approval Prompt, Step
  Counter) are reusable classes in `productions/ep04-planning/scenes/plan_kit.py`, not in
  `agentic_video/` (changing the shared library would re-render Episodes 01-03). The Plan Panel
  is driven by one `PlanState` (steps, statuses, numbering, current step), so the step rows,
  their numbers and the Step Counter are always derived from the same data.
- **Rule check in code:** `PlanPanel.apply()` only accepts a change together with the
  update_plan Tool Call Card that requested it (already on screen), so the panel cannot change
  on screen without a preceding tool call.
- **Folder layout:** the pipeline's standard layout is kept (scenes in `scenes/`, narration in
  `narration.json`). The plan's file names (`ep04_planning_EN.mp4`, `ep04_EN.srt`,
  `timings/en.json`, `narration/en/`) are produced by the deliver stage inside
  `output/ep04-planning/`.
- **Spoken forms (English):** tool names and file names are respelled for the voice only
  (`update_plan` -> "update plan", `index.html` -> "index dot H T M L", ...). Subtitles and the
  screen keep the written form.
- **Section 07 vs 09:** in the plan, Section 07 removes the thank-you step while Section 09 still
  does it. Section 07's removal is narrated as a conditional ("if the website already showed a
  thank-you note, the model would ask update_plan to remove that step"), so the two sections do
  not contradict each other. Section 08's email step is a separate example and is not part of
  the Section 09 replay.

## Revision 1 (2026-11-13, during production)

- **Script tightened to fit the runtime cap.** With the scenes built, the approved script ran 14:35
  (plan: 11:00–14:00, aim 13:00) and Section 06 was just over its +20 % limit. About 160 words were
  cut across all sections (repetition and sub-clauses only; every step, example, on-screen beat and
  the three required lines kept). `inputs/script.md` and `narration.json` were changed together, so
  the completeness check still passes. Draft runtime after the trim: 13:49.
- **Fragment lines merged.** Ingest split some paragraphs into very short clips ("It doesn't help.",
  "Said, not checked."); they were merged back into their sentences (144 -> 121 lines) to avoid
  intonation resets (the Episode 03 lesson).
- **Chapter titles** restored to their full form for sections 07, 09 and 10.

## Revision 2 (2026-11-13, user request: "fix the stuttery voice, the animation bugs such as lines not pointing where they should, perfectly timed subtitles, thumbnail in the exact colours of the previous episodes")

- **Voice:** `tools/voice_pauses.py` removed 22.7 s of in-clip hesitations (mid-phrase gaps up to 0.45 s,
  comma pauses up to 0.6 s); speech, speed and pitch untouched. Three lines whose animations outlasted the
  voice (s02_06, s06_11, s09_10) were tightened, so no dead air remains between lines except the recap hold.
  Runtime 13:49 -> about 13:24.
- **Animations:** goal->steps lines in s04 drawn as a tree into each step's circle (they converged across
  the text); "comes before" arcs connect step 1 into steps 2 and 3; straight input arrow in s03; tool-call and
  result cards wrap at one font size instead of shrinking; wider message lists in s06/s09; evidence links ring
  the tick and curve to the proof message; update_plan description no longer cut by its NEW tag; the context
  meter in s05 is computed from the drawn cards; "no evidence" layout in s10.
- **Subtitles:** the pipeline's English (same-language) subtitles are now word-timed on every line, including
  lines with respelled terms, and broken at sentence ends, colons, commas and conjunctions (never after
  "the/of/to"), with no flash cues (`automatio/subtitles.py`). The Hindi (cross-language) path is unchanged.
- **Thumbnail:** `scenes/thumbnail.py` is Episode 03's script with only the subtitle changed ("Planning").
