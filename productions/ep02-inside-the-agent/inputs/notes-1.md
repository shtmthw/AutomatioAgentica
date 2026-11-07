# Production notes: Episode 02 (decisions made with the user, 2026-11-07)

These directions override the plan (VIDEO-PLAN-2) where they differ.

- **Script:** the plan supplies no narration script and asks the producer to write it.
  The user asked Claude to draft the English script from the plan; the user reviews and
  locks it before anything is rendered. The plan's required lines are kept word for word.
- **Deliverables:** as the plan says: ONE English video, plus (later) a Hindi voice-only
  MP3 and a Hindi SRT fitted to the English video's timeline. The video is English only.
- **Hindi is deferred:** ElevenLabs credits are short this cycle. Produce the English video
  now; the Hindi script, Hindi MP3 and Hindi SRT come later, when credits are available,
  fitted to `timings/en.json` of this video (a dub-track pipeline stage still has to be
  built for that). Until then this production has only the English version.
- **English voice:** the same English narrator as Video 1: edge-tts Andrew
  (`en-US-AndrewMultilingualNeural`, -5 %, profile `english-andrew`). This overrides the
  plan's "do not reuse its voice" (Continuity section).
- **Subtitles:** separate files only (standing guideline 1). This overrides the plan's
  Final Expectation #6 ("burn subtitles into the video"). Nothing is burned in.
- **Visual continuity:** the Episode 01 source is available, so its palette, fonts, icons,
  five component icons and loop diagram are reused (the plan's fallback palette is not
  used). Plan colours map onto the house tokens: MODEL = BLUE, HARNESS = AMBER,
  TOOLS = TEAL/GREEN, errors = RED; role tags SYSTEM grey, USER white, ASSISTANT blue,
  TOOL green.
- **Spoken forms (English):** tool names and file names are respelled for the voice only
  (`read_file` -> "read file", `config.txt` -> "config dot T X T", `8080` -> "eighty
  eighty", ...); subtitles and the screen keep the written form.
- **Deliverable names:** the plan's file names (`ep02_inside_the_agent_EN.mp4`,
  `ep02_EN.srt`, later `ep02_voiceover_HI.mp3`, `ep02_HI.srt`) are written inside
  `output/<slug>/`, next to the pipeline's standard layout.
