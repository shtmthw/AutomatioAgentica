# EPISODE 03: CONTEXT AND MEMORY — HOW AN AGENT HANDLES LONG TASKS

## Overall Objective

Create an 11–14 minute educational video (target: 13:00) that continues directly from Episode 02 ("Inside the Agent").

Deliverables:
- **ONE final end-to-end video**, voiced and subtitled in **English**.
- **ONE separate Hindi voiceover MP3 file**. It is a highly accurate Hindi version of the complete English narration, timed to match the final video so it can be laid over the same video later.

The video itself contains English audio only. Hindi audio is never mixed into the video.

Episode 01 taught WHAT an agent is.
Episode 02 opened the agent and showed the harness, the message list, tool calling and the limited context window. It ended with a question: the context window fills up as the agent works, so how does an agent finish big tasks and remember what matters?
Episode 03 answers that question.

The viewer should finish the video with a clear understanding of:
- What actually fills the context window, and why tool results are usually the biggest part.
- Why a bigger context window does not solve the problem by itself.
- What **Context Management** means: deciding what the model sees on each call.
- Three basic techniques: keeping tool results small, trimming old messages, and summarizing old messages (**Compaction**).
- That every one of these techniques loses some information, and what the trade-off is.
- What **Memory** is: text the harness saves outside the context window and brings back later.
- How memory survives between sessions even though the model itself remembers nothing.
- What **Retrieval** is: bringing back only the notes that are needed.

The audience is the same as before: beginners who have watched Episodes 01 and 02. Recap briefly. No programming knowledge is required. Small simplified "data cards" are allowed, but there must be no real source code on screen.

The ending should lead into Episode 04 (Planning).

## Language Rules

Only two languages may appear anywhere in this project: **English** and **Hindi**. No other language may be used in the narration, subtitles, on-screen text, or file names.

**The video (English):**
- Voiceover: conversational, clear, simple English, the way a friendly teacher explains to beginners. Use short sentences and avoid jargon beyond the technical terms being taught. Explain each technical term the first time it appears.
- Subtitles: English, matching the English voiceover exactly.
- On-screen text (labels, cards, titles, diagrams, summary lines): English only.

**The Hindi voiceover MP3:**
- It must be a highly accurate rendering of the final English narration. It conveys the same meaning, facts, examples, order and emphasis, sentence by sentence. Nothing may be added, dropped, simplified away or reinterpreted.
- Write it as natural, conversational Hindi, the way a teacher speaks to students in India, not as a stiff word-for-word translation. Avoid heavily Sanskritized or formal "news-reader" Hindi. Accuracy of meaning comes first; naturalness comes second.
- Keep technical terms in English (Model, Agent, Harness, Message, Tool, Tool Call, Context Window, Token, Context Management, Compaction, Summary, Memory, Session, Retrieval), and explain each one in simple Hindi at the same point where the English narration explains it.
- When the narration reads out or refers to on-screen English text (card labels, tool names such as save_note, example messages), say it in English exactly as it appears on screen, then explain it in Hindi if needed. The Hindi audio must always match what the viewer sees.
- Write the Hindi script from the final, locked English script. If the English script changes, update the Hindi script and regenerate the MP3.
- Review the Hindi script line by line against the English script before generating audio, and check it against the "Technical Accuracy Rules" section. Save this comparison as a side-by-side file (English line | Hindi line) so it can be checked.

**Plan and code:** English. File names, comments and folder names must be in English.

## Production Requirements

- Generate all animations programmatically using Python.
- Use a minimalistic, clean, modern educational animation style.
- Use simple shapes, typography, arrows, diagrams, and smooth transitions.
- Avoid unnecessary visual effects, screenshots, stock footage, and decorative elements.
- 16:9, 1920x1080, final output as 1080p MP4.
- Natural-sounding **ENGLISH MALE VOICEOVER** for the video: clear, calm and confident, with natural pacing. Use the same voice as Episode 02's English video.
- Separately, a natural-sounding **HINDI MALE VOICEOVER** exported as an MP3 file (see "Hindi Voiceover MP3"). It needs correct pronunciation of the English technical terms. Use the same voice as Episode 02's Hindi MP3.
- Synchronize animations with the narration.
- Use subtle background music, significantly quieter than the voice.
- Add English subtitles synchronized with the English voiceover.
- It should feel like a carefully produced technical lesson, not an advertisement.

## Continuity With Episode 02

- If the Episode 02 project source is available, reuse its components exactly as they were: Model Box, Harness Frame, Message Card, Message List, Tool Card, Tool Call Card, Context Window (with its fill meter) and Loop Diagram. Reuse its colour palette, fonts, voices and music style.
- Reuse the same example world: the user is called Rahul, the tools are read_file, run_command and edit_file, and the project contains config.txt and math_utils.py.
- If the Episode 02 source is not available, follow the Visual Language section below and keep it consistent for the whole video.
- The CONTEXT WINDOW with its fill meter is the "home base" of this episode. Keep it on screen in most scenes, and make sure the meter always reflects what is currently inside the window.

## Visual Language (Define Once, Reuse Everywhere)

Fallback palette, used only if Episode 02's palette cannot be reused:
- Background: very dark navy (#0F1420)
- Primary text: off-white (#EDEFF3)
- Muted text / lines: grey (#8A93A6)
- Accent for MODEL: blue (#4C8DFF)
- Accent for HARNESS: amber (#F2B33D)
- Accent for TOOLS: green (#3DD68C)
- Accent for MEMORY: purple (#A78BFA)
- Warnings / errors: soft red (#FF5C5C)

Components carried over from Episode 02 (same meaning as before):
1. **MODEL BOX**: blue rounded rectangle labelled "AI MODEL". Text in, text out. It never touches files or storage directly.
2. **HARNESS FRAME**: amber rounded rectangle surrounding the Model Box, labelled "HARNESS".
3. **MESSAGE CARD**: a card with a coloured role tag (SYSTEM grey, USER white, ASSISTANT blue, TOOL green) and short English text.
4. **MESSAGE LIST**: Message Cards stacked vertically, newest at the bottom.
5. **TOOL CALL CARD**: blue card with a dashed border: TOOL: name, INPUT: value. It is only a request.
6. **CONTEXT WINDOW**: a tall container outline holding the Message Cards that will be sent to the model, with a fill meter on the side. The meter turns amber above about 80% and red at 100%.

New components for this episode. Build each one as a reusable function or class:
7. **SIZED MESSAGE CARD**: a Message Card whose height is proportional to how much text it holds. A short user question is a thin card. A large file read is a very tall green TOOL card. Use this whenever the scene is about how much space something takes.
8. **SUMMARY CARD**: a compact card with an amber "SUMMARY" tag. It replaces many older cards. Inside it, show 3–4 short bullet lines.
9. **PLACEHOLDER CARD**: a thin, dimmed card with the text "[old tool result removed]" or "[output shortened: 4,800 more lines]".
10. **NOTEBOOK (MEMORY STORE)**: a purple notebook icon labelled "MEMORY". It sits inside the Harness Frame but clearly *outside* both the Model Box and the Context Window. It represents files saved on disk.
11. **NOTE CARD**: a small purple card holding one saved note in one short line.
12. **SESSION DIVIDER**: a full-width vertical line or wipe labelled "SESSION 1 ENDS" / "SESSION 2 STARTS". When it passes, the Message List and Context Window are emptied. The Notebook is not affected.

Data on cards must be short, readable and simplified. Do not show raw JSON, brackets-heavy syntax, or any vendor-specific API format.

## Technical Accuracy Rules (Must Not Be Violated)

The narration and visuals must never imply any of the following:
- That the model remembers anything by itself, within a session or between sessions. "Memory" is text that the harness saves outside the model and puts back into the context later.
- That saving a note changes, trains or updates the model. The model stays exactly the same. Only the text sent to it changes.
- That a bigger context window removes the need for context management.
- That trimming or summarizing is free. Both lose information, and a summary can leave out or misstate a detail.
- That the harness writes summaries by itself. A summary is written by the model in a separate call that the harness makes. The harness then swaps the old messages for that summary.
- That the model can see messages that were removed from the context window. Once a message is removed, the model cannot see it on later calls.
- That memory is always correct. A saved note can be wrong or out of date.

Additional rules:
- A tool call and its tool result belong together. When trimming, remove or keep them as a pair. Never show a TOOL result left in the list without the ASSISTANT tool call that requested it.
- The SYSTEM message is never trimmed or summarized away in any animation.
- Do not state real context window sizes or prices for any specific model, because these change. When a number is needed, use a round illustrative one and label it on screen as "example" (for instance, "Example limit: 100,000 tokens").
- The new tool names (save_note, search_notes) are simplified examples. Do not present them as standard names that every agent uses.

Say these things clearly:
- "The goal is not more context. The goal is the right context."
- "The model doesn't remember. The harness writes it down and brings it back."
- "Every technique for saving space loses something."

Do not introduce: embeddings, vector databases, RAG by name, MCP, fine-tuning, prompt caching, sub-agents, specific APIs or SDKs, or planning algorithms. Those belong in later episodes.

# VIDEO STRUCTURE

## 01. Recap and Hook: The Desk Is Full
TIME: 0:00–1:00

Open on the Episode 02 picture: the Model Box inside the Harness Frame, with the Message List beside it.

Recap in about 25 seconds, with each point lighting up its component:
- The model only reads text and writes text.
- The harness runs the loop and executes the tools.
- On every call, the harness sends the whole conversation again.
- All of it must fit inside the context window, which is limited.

Then the hook:
- Show the Context Window with the meter at about 20%. A "Call #" counter starts ticking: Call #5, #20, #60.
- Cards keep dropping in. The meter climbs to amber, then red, then hits 100%.
- The next card bounces off the top and a red "CONTEXT FULL" label appears.
- On-screen question: "The task isn't finished. The desk is full. Now what?"

Narration idea: Last time we saw that the model's desk has a fixed size. But real tasks are long. An agent might need hundreds of steps. So how do real agents keep working? And how do they remember things from yesterday? That is today's lesson.

Show the title card: **CONTEXT & MEMORY**

## 02. What Is Actually Filling the Context?
TIME: 1:00–2:00

Show the Context Window using SIZED MESSAGE CARDS, and label each group as it appears:
1. SYSTEM message: small, always at the top.
2. Tool descriptions: small to medium, always present.
3. USER messages: thin cards.
4. ASSISTANT messages and tool calls: thin cards.
5. TOOL results: often very tall cards.

Animate one concrete moment: the model requests read_file on a large file. A huge green TOOL card drops in and the meter jumps from 20% to 60% in one step.

Then show a simple horizontal bar that sorts the content by type. The green TOOL section is clearly the largest. Label it: "In many agent tasks, tool results take the most space."

Remind the viewer of the Episode 02 fact: everything inside the window is sent again on every call. Show the "Call #" counter increasing and the same tall card being sent each time. So one large tool result is paid for again and again, in time and in cost.

## 03. Why Not Just Use a Bigger Window?
TIME: 2:00–3:00

Pose the obvious question on screen: "Why not just make the window bigger?"

Animate the Context Window stretching taller. Then give three reasons, one at a time:
1. **It still has a limit.** However big the window is, a long enough task fills it. Show the stretched window filling up again.
2. **It gets slower and more expensive.** More text per call means each call costs more and takes longer. Show a small clock and a small coin counter growing with the meter.
3. **Important details get harder to find.** When the context is very long and cluttered, models often become less reliable at using the right piece of information. Animate one important card (for example the user's original goal) getting visually lost among hundreds of dim cards.

Desk analogy, continued from Episode 02: a bigger desk covered with a thousand papers does not help you work. A clean desk with the right ten papers does.

Define the term on screen: **Context Management = deciding what the model sees on each call.**
Stress that this is the harness's job, done by the developer who builds the harness.

Key line:
- English (video): "The goal is not more context. The goal is the right context."
- Hindi (MP3): "लक्ष्य ज़्यादा Context नहीं है। लक्ष्य सही Context है।"

## 04. Technique 1: Keep Tool Results Small
TIME: 3:00–4:15

Show a technique counter in a corner: "TECHNIQUE 1 of 3". Keep this counter through Sections 04–06.

Idea: the cheapest way to save space is to not put unnecessary text into the context in the first place.

Show three simple ways, each with a short before/after animation and the meter reacting:

1. **Read only the needed part.**
   Before: read_file returns a whole 5,000-line file as one enormous card.
   After: the tool call asks for a small part (INPUT: path = "math_utils.py", lines = 40–80), and a small card comes back.

2. **Search instead of reading everything.**
   Before: the agent reads ten files one by one to find where total() is.
   After: a single search request returns three short matching lines.

3. **The harness shortens very long output.**
   A run_command result is thousands of lines long. The harness keeps the beginning and the end and inserts a PLACEHOLDER line in the middle: "[output shortened: 4,800 more lines]".

Explain why the placeholder matters: the harness must *tell* the model that text was cut. Otherwise the model would believe it has seen everything. Animate both versions briefly: without the note, the model answers confidently with a wrong assumption (red "?"). With the note, the model asks for the specific missing part.

## 05. Technique 2: Trim Old Messages
TIME: 4:15–5:15

Counter: "TECHNIQUE 2 of 3".

Idea: when the window gets full, the harness removes the oldest messages so that new ones fit.

Animate:
- The Context Window is at 95%. A new card needs to come in.
- The oldest cards under the SYSTEM message slide out of the window and fade. The meter drops. The new card fits.
- The SYSTEM message stays pinned at the top with a small pin icon.
- When a card pair is removed, show the ASSISTANT tool call and its TOOL result leaving together, joined by a small bracket.

Show a gentler version of the same idea: instead of removing whole messages, the harness empties only old, large TOOL results and leaves a PLACEHOLDER CARD "[old tool result removed]". The conversation stays readable, but the space is freed.

Then show the danger:
- The very first USER card says: "Fix the crash. Do not change the public function names."
- It gets trimmed away.
- Several steps later, the model renames a function, because it can no longer see that instruction. Show a red warning icon.

Narration point: trimming is simple and fast, but it is blind. It throws away old messages whether they were important or not. And once a message is out of the window, the model cannot see it any more.

## 06. Technique 3: Summarize Old Messages (Compaction)
TIME: 5:15–6:45

Counter: "TECHNIQUE 3 of 3".

Idea: instead of throwing old messages away, replace them with a short summary. This is commonly called **Compaction**.

Animate each step, with a step number visible on screen:

1. **The harness notices the window is getting full.** The meter crosses an example threshold line marked "80%".
2. **The harness makes a separate call to the model.** It sends the older messages together with one instruction card: "Summarize the important points of this conversation so far."
3. **The model writes a summary** as normal text.
4. **The harness swaps the messages.** The older cards collapse into one SUMMARY CARD. The SYSTEM message stays on top. The most recent few messages stay unchanged below the summary.
5. **The meter drops** (for example from 80% to 25%) and the agent loop continues as usual.

Show the SUMMARY CARD contents clearly:
- Goal: fix the crash, keep public function names
- Done: found bug in total(), fixed it
- Still to do: fix failing login test
- Key facts: tests run with "run tests"; server port is 8080

Explain what a good summary keeps: the goal, the rules the user gave, what has been done, what is left, and key facts such as file names and errors.

Stress two accuracy points:
- The summary is written by the model, in a call that the harness makes. The harness decides *when* to summarize and *what* to replace.
- A summary is lossy. Animate one small detail from an old message (for example "the user wants error messages in simple words") fading out because the summary did not include it. Later the model does not follow it, because it never sees it again.

End with a three-row comparison table that builds on screen:

| Technique | Saves space | What you risk |
| --- | --- | --- |
| Small tool results | Yes, early | Missing a part you needed |
| Trimming | Yes, a lot | Losing old instructions completely |
| Summarizing | Yes, a lot | Losing small details |

Key line: "Every technique for saving space loses something. Context management is choosing what you can afford to lose."

## 07. Memory: Writing Things Down Outside the Window
TIME: 6:45–8:30

Transition question on screen: "All of this is inside one conversation. What about tomorrow?"

First show the problem with a SESSION DIVIDER:
- Define **Session**: one continuous conversation with the agent, from start to end.
- Session 1: Rahul tells the agent "In this project, always run the tests before you say a task is done." The agent follows it.
- The Session Divider wipes across. The Message List and the Context Window are emptied.
- Session 2: the agent finishes a task without running the tests. Rahul's rule is gone, because the message that contained it is gone.

Now introduce **Memory**. Bring in the NOTEBOOK, placed inside the Harness Frame but outside the Model Box and outside the Context Window.

Definition (say this clearly): Memory is information the harness saves outside the context window, usually in ordinary files, so it can be brought back later.

Extend the desk analogy: the context window is the desk. Memory is a notebook in the drawer. The desk gets cleared every day. The notebook stays.

Replay Session 1 with memory, step by step:
1. USER: "In this project, always run the tests before you say a task is done. Remember this."
2. The model replies with a TOOL CALL CARD: TOOL: save_note, INPUT: text = "Always run tests before finishing a task."
3. The harness executes it: a NOTE CARD flies into the Notebook.
4. The harness adds a TOOL message: "Note saved."
5. The Session Divider wipes across. The Message List and Context Window are emptied. **The Notebook keeps its Note Card.**

Session 2:
6. A new session starts with an empty Message List.
7. Before the first call, the harness takes the saved notes from the Notebook and places them into the Context Window, next to the SYSTEM message, as a small purple block labelled "NOTES FROM MEMORY".
8. USER: "Fix the login bug."
9. The model fixes it, then requests run_command → "run tests" before reporting. A small purple line connects this action back to the note.

Pause and make the central point. Show the Model Box with the label "UNCHANGED" in both sessions:
- The model did not learn anything. It is exactly the same model in Session 2.
- It follows the rule only because the harness put the note back into the text it received.

Key line:
- English (video): "The model doesn't remember. The harness writes it down and brings it back."
- Hindi (MP3): "Model याद नहीं रखता। Harness लिखकर रखता है और वापस लाता है।"

Briefly list what is worth saving, as three Note Cards appearing in the Notebook:
- Facts about the user or project ("Tests run with: run tests")
- Rules and preferences ("Do not rename public functions")
- Progress on long tasks ("Login bug: cause found, fix not written yet")

## 08. Retrieval: Bring Back Only What You Need
TIME: 8:30–9:30

Show the new problem: weeks pass, and the Notebook now holds 300 Note Cards.
- The harness tries to load all of them at the start of a session. The Context Window is at 70% before the user has said anything. The meter turns amber.
- On-screen text: "Memory can overflow the context too."

Introduce **Retrieval**: fetching only the notes that are relevant to the current task.

Show two ways notes can enter the context:
1. **Always loaded**: a few short, important notes (core rules) that the harness adds at the start of every session. Show 3 Note Cards pinned next to the SYSTEM message.
2. **Loaded on demand**: everything else stays in the Notebook until needed.

Animate on-demand retrieval, step by step:
1. USER: "Deploy the app to the test server."
2. The model replies with a TOOL CALL CARD: TOOL: search_notes, INPUT: query = "deploy".
3. The harness searches the Notebook. Out of 300 notes, 2 light up.
4. The harness adds a TOOL message containing only those 2 notes.
5. The model continues the task using them. The meter has barely moved.

Narration point: this is the same tool-calling pattern from Episode 02. The model requests, the harness does. Memory is just another tool, plus a place to store text.

Mention in one sentence that there are smarter ways to search notes than matching words, and that those come in a later lesson. Do not name or explain them.

## 09. Full Replay: One Long Task Across Two Sessions
TIME: 9:30–11:30

Bring everything together in one continuous example. Keep it rhythmic, because the viewer now knows every part.

Layout: Message List on the left, Context Window with meter in the centre, Notebook on the right. A small label at the top shows which technique is active when one is used.

**SESSION 1**

1. USER: "Fix all failing tests in this project. Don't rename public functions."
2. ASSISTANT (tool call): run_command → "run tests"
3. TOOL: a very long test output. The harness shortens it: beginning, "[output shortened: 2,300 more lines]", end. Label: TECHNIQUE 1. Meter: 15%.
4. ASSISTANT (tool call): read_file → "math_utils.py", lines 40–80. Small result. Label: TECHNIQUE 1.
5. ASSISTANT (tool call): edit_file → "math_utils.py". TOOL: "File updated successfully".
6. Fast-forward montage: many more tool calls and results stream in. "Call #" counter runs up to about 40. Meter climbs to 80% and turns amber.
7. Compaction triggers. Label: TECHNIQUE 3. The older cards collapse into a SUMMARY CARD:
   - Goal: fix all failing tests, don't rename public functions
   - Done: total() fixed, 6 of 8 tests pass
   - Still to do: 2 login tests
   Meter drops to 25%.
8. ASSISTANT (tool call): save_note → "Login tests fail because of a wrong port in config.txt. Not fixed yet." A Note Card flies into the Notebook.
9. USER: "Let's stop for today."
10. ASSISTANT (tool call): save_note → "Progress: 6 of 8 tests pass. Next: fix port in config.txt, then run tests." Another Note Card flies into the Notebook.

The SESSION DIVIDER wipes across. The Message List and Context Window are emptied. The Notebook keeps its notes.

**SESSION 2**

11. The harness loads the notes into the Context Window as "NOTES FROM MEMORY". Meter: 5%.
12. USER: "Continue from yesterday."
13. ASSISTANT (tool call): read_file → "config.txt". TOOL: "port = 8800, host = localhost".
14. ASSISTANT (tool call): edit_file → "config.txt". TOOL: "File updated successfully".
15. ASSISTANT (tool call): run_command → "run tests". TOOL: "All 8 tests passed ✓".
16. ASSISTANT (final text, no tool call): "All tests pass now. The last two failed because config.txt had the wrong port. No public functions were renamed."

Highlight the two things that survived:
- The rule "don't rename public functions" survived compaction because the summary kept it.
- The progress survived the end of the session because it was saved to memory.

Show the Model Box labelled "UNCHANGED" one last time.

## 10. Reality Check: Memory Can Be Wrong
TIME: 11:30–12:15

Keep the tone of Episode 01's "Agents Are Not Magic" section. Show four short points, each with one simple visual:

1. **Summaries lose details.** A Summary Card with one bullet fading out.
2. **Notes can be out of date.** A Note Card says "Server port is 8080", but config.txt now says 9090. The agent trusts the old note and makes a mistake. Good agents check important facts again instead of trusting old notes blindly.
3. **Notes can be wrong from the start.** If the agent saves a wrong conclusion, it will keep repeating that mistake in later sessions.
4. **Memory can hold private information.** Show the Notebook with a small lock and an eye icon. The user should be able to see what is saved and delete it.

Close the section with: more memory is not automatically better. Just like context, the aim is the right information at the right time.

## 11. Conclusion and What's Next
TIME: 12:15–13:00

Summarize with five short English lines appearing one by one on screen:
1. The context window fills up, mostly with tool results.
2. Context management means choosing what the model sees on each call.
3. Keep tool results small, trim old messages, or summarize them. Each one loses something.
4. Memory is text saved outside the context and brought back later.
5. The model never changes. Only the text it receives changes.

The narration should communicate something along these lines.

English (video):

"Today we solved the problem from last time. The context window is limited, so the harness has to choose what the model sees. It can keep tool results small, drop old messages, or replace them with a summary. And for anything that must last longer than one conversation, it writes it down in memory and brings it back when it's needed.

Remember the most important point. The model itself never remembers anything. It only sees the text that the harness gives it.

But there is still one thing we haven't looked at. So far our agent decides just one step at a time. What happens when the goal is really big, like building a whole app? How does an agent break a big goal into small steps and keep track of them?

That's what we'll learn in the next lesson: Planning."

Hindi (MP3), the accurate Hindi equivalent of the lines above:

"आज हमने पिछली बार की समस्या हल की। Context Window सीमित है, इसलिए Harness को चुनना पड़ता है कि Model क्या देखेगा। वह Tool Results को छोटा रख सकता है, पुराने Messages हटा सकता है, या उनकी जगह एक Summary रख सकता है। और जो भी चीज़ एक बातचीत से ज़्यादा समय तक रहनी चाहिए, उसे वह Memory में लिख लेता है और ज़रूरत पड़ने पर वापस लाता है।

सबसे ज़रूरी बात याद रखिए। Model ख़ुद कभी कुछ याद नहीं रखता। वह सिर्फ़ वही Text देखता है जो Harness उसे देता है।

लेकिन एक चीज़ अभी भी बाकी है जिसे हमने नहीं देखा। अब तक हमारा Agent एक बार में सिर्फ़ एक क़दम का फ़ैसला लेता है। जब Goal सच में बहुत बड़ा हो, जैसे एक पूरा App बनाना, तब क्या होता है? Agent एक बड़े Goal को छोटे-छोटे Steps में कैसे तोड़ता है और उनका हिसाब कैसे रखता है?

अगले lesson में हम यही सीखेंगे: Planning।"

Finish with a minimalistic title card in the same style as the earlier episodes:

AGENTIC AI
CONTEXT & MEMORY

Fade in a smaller line underneath for 2 seconds: "Next: Planning"

# TIMING RULES

**Video (English):**
- Section timings are targets. Final total runtime must be between 11:00 and 14:00. Aim for about 13:00.
- Write the English narration first, generate the English voiceover, measure each section's and each step's audio length, then time the animations to the audio. Drive the animation timings from a timing file (for example `timings/en.json`).
- Do not speed up or compress the voice to fit the timings.
- If a section's audio is more than 20% longer or shorter than its target, adjust that section's narration text and regenerate it, rather than stretching animations.
- Leave 0.5–1 second of silence between sections for transitions.
- Sections 06 and 07 are the most important. Section 06 must be at least 1:20 long and Section 07 at least 1:30 long. Do not rush them.

## Hindi Voiceover MP3

- The video's timing is final and is never changed to fit the Hindi audio. The Hindi audio is fitted to the video.
- The Hindi MP3 must have exactly the same total duration as the final video, so it can replace the English voice track without any editing.
- Align it to the video section by section, and within Sections 06, 07, 08 and 09 step by step. Each Hindi section must start at the same timestamp as the matching English section. Take these timestamps from `timings/en.json`.
- Each Hindi segment must fit inside its English segment's time slot. If it is shorter, pad it with silence at the end of the slot. If it is longer, rewrite the Hindi more concisely while keeping the full meaning, then regenerate it. Do not drop content to make it fit. Speed it up by at most 5%, and only if rewording is not enough.
- Lines that refer to a specific on-screen moment (a card appearing, a step number, the meter dropping, a note flying into the Notebook) must be spoken while that visual is on screen, just as in the English version.
- The MP3 contains voice only, with no background music, so the music can be mixed later at the same level as in the English video.
- Export it as MP3, 44.1 kHz or 48 kHz to match the video's audio sample rate, at 192 kbps or higher, normalized to a similar loudness as the English voice.
- Also export a Hindi .srt subtitle file timed to the Hindi MP3, but do not burn it into the video.

# FINAL EXPECTATIONS

1. Produce ONE complete, polished end-to-end educational video with English voiceover and English subtitles. Do not produce separate animation demos.
2. Produce ONE separate, highly accurate Hindi voiceover MP3 that matches the final video's timeline exactly (see "Hindi Voiceover MP3").
3. Write and organize the complete English narration and the complete Hindi narration, each saved as a separate text file per section. Also save the side-by-side English | Hindi comparison file.
4. Generate the English narration with a natural English male voice, and the Hindi narration with a natural Hindi male voice. Use the same voices as Episode 02 if they are available.
5. Programmatically generate all animations and synchronize them with the English voiceover.
6. Burn properly synchronized English subtitles into the video, and export them as an .srt file. Export the Hindi subtitles as a separate .srt file only.
7. Keep all on-screen text in English.
8. Maintain visual consistency with Episodes 01 and 02.
9. Reuse the Episode 02 components, and build the new ones (Sized Message Card, Summary Card, Placeholder Card, Notebook, Note Card, Session Divider) as reusable components so later episodes can reuse them.
10. Make sure the Context Window's fill meter is always computed from the cards currently inside the window, so it never disagrees with what is shown.
11. Final output files:
    - `output/ep03_context_and_memory_EN.mp4` (1080p, English voiceover, music and subtitles)
    - `output/ep03_voiceover_HI.mp3` (Hindi voice only, same duration as the video)
    - `output/ep03_EN.srt`
    - `output/ep03_HI.srt`
12. Organize the Python source and assets cleanly, for example:
    - `scenes/` (one file per section)
    - `components/` (reusable visual elements)
    - `narration/en/` and `narration/hi/` (text per section)
    - `narration/en_hi_side_by_side.md`
    - `audio/en/`, `audio/hi/` and `audio/music/`
    - `timings/en.json`
    - `subtitles/`
    - `output/`
13. Before rendering, check the English narration and the visuals against the "Language Rules" and "Technical Accuracy Rules" sections. Before exporting the MP3, check the Hindi script line by line against the English script. Then confirm that the MP3's duration equals the video's duration and that its section start times match `timings/en.json`.

Prioritize clarity and teaching quality over visual complexity. A beginner who watched Episodes 01 and 02 should be able to follow every step without any programming knowledge.
