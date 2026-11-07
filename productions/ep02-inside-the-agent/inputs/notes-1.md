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

## Update 2026-11-08 (pipeline 2.1)

- The dub-track stage exists now: `[versions.hi] mode = "dub"`, `follow = "en"` (see
  production.toml). The English video is delivered. The Hindi dub waits for ElevenLabs
  credits (32 of 140 lines voiced; the monthly quota was exhausted on 2026-11-07).
- The plan's deliverable names and folders are produced by the pipeline (`[deliver]` in
  production.toml): `ep02_inside_the_agent_EN.mp4`, `ep02_EN.srt`, `timings/en.json`,
  `narration/en/`, `narration/hi/`, `narration/en_hi_side_by_side.md`, and once the dub is
  voiced, `ep02_voiceover_HI.mp3` and `ep02_HI.srt` (Hindi subtitles timed to the Hindi voice,
  `[subtitles] own_language`). Chapters and topics come from `topic` fields in narration.json.
- Before the remaining paid lines are voiced, the dub forecast (`check dub`) found that
  s09_05 could not fit its slot. Its Hindi was tightened without dropping content:
  "Harness tests चलाता है। Tool result: ..." -> "Harness के चलाने पर Tool result: ...".
  The on-screen quote stays verbatim.

