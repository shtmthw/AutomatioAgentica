# EPISODE 04: PLANNING — HOW AN AGENT HANDLES BIG GOALS

## Overall Objective

Create an 11–14 minute educational video (target: 13:00) that continues directly from Episode 03 ("Context and Memory").

Deliverables:
- **ONE final end-to-end video**, voiced and subtitled in **English**.
- **ONE separate Hindi voiceover MP3 file**. It is a highly accurate Hindi version of the complete English narration, timed to match the final video so it can be laid over the same video later.

The video itself contains English audio only. Hindi audio is never mixed into the video.

Episode 01 taught WHAT an agent is.
Episode 02 showed the harness, the message list and tool calling.
Episode 03 showed how the harness manages the limited context window and how memory works. It ended with a question: so far the agent decides one step at a time, so how does it break a really big goal into small steps and keep track of them?
Episode 04 answers that question.

The viewer should finish the video with a clear understanding of:
- Why deciding only one step at a time fails on big goals.
- What a **Plan** is: a list of steps, written by the model as ordinary text.
- What **Decomposition** means: breaking a big goal into small, clear, checkable steps.
- Where the plan lives: the harness stores it and sends it to the model on every call.
- How the agent loop works when there is a plan: pick the next step, do it, check it, mark it done.
- Why "done" must be backed by evidence from a tool result.
- What **Replanning** is: changing the plan when the agent learns something new.
- Why showing the plan to a human before starting is useful.
- That plans can be wrong, and that small tasks do not need one.

The audience is the same as before: beginners who have watched Episodes 01–03. The recap at the start is slightly longer than in Episode 03, because there is now more to catch up on. No programming knowledge is required. Small simplified "data cards" are allowed, but there must be no real source code on screen.

The ending should lead into Episode 05 (multiple agents working together).

## Language Rules

Only two languages may appear anywhere in this project: **English** and **Hindi**. No other language may be used in the narration, subtitles, on-screen text, or file names.

**The video (English):**
- Voiceover: conversational, clear, simple English, the way a friendly teacher explains to beginners. Use short sentences and avoid jargon beyond the technical terms being taught. Explain each technical term the first time it appears.
- Subtitles: English, matching the English voiceover exactly.
- On-screen text (labels, cards, titles, diagrams, summary lines): English only.

**The Hindi voiceover MP3:**
- It must be a highly accurate rendering of the final English narration. It conveys the same meaning, facts, examples, order and emphasis, sentence by sentence. Nothing may be added, dropped, simplified away or reinterpreted.
- Write it as natural, conversational Hindi, the way a teacher speaks to students in India, not as a stiff word-for-word translation. Avoid heavily Sanskritized or formal "news-reader" Hindi. Accuracy of meaning comes first; naturalness comes second.
- Keep technical terms in English (Model, Agent, Harness, Message, Tool, Tool Call, Context Window, Memory, Goal, Plan, Step, Decomposition, Replanning, Loop), and explain each one in simple Hindi at the same point where the English narration explains it.
- When the narration reads out or refers to on-screen English text (plan steps, card labels, tool names such as update_plan, example messages), say it in English exactly as it appears on screen, then explain it in Hindi if needed. The Hindi audio must always match what the viewer sees.
- Write the Hindi script from the final, locked English script. If the English script changes, update the Hindi script and regenerate the MP3.
- Review the Hindi script line by line against the English script before generating audio, and check it against the "Technical Accuracy Rules" section. Save this comparison as a side-by-side file (English line | Hindi line) so it can be checked.

**Plan and code:** English. File names, comments and folder names must be in English.

## Production Requirements

- Generate all animations programmatically using Python.
- Use a minimalistic, clean, modern educational animation style.
- Use simple shapes, typography, arrows, diagrams, and smooth transitions.
- Avoid unnecessary visual effects, screenshots, stock footage, and decorative elements.
- 16:9, 1920x1080, final output as 1080p MP4.
- Natural-sounding **ENGLISH MALE VOICEOVER** for the video: clear, calm and confident, with natural pacing. Use the same voice as the Episode 02 and 03 English videos.
- Separately, a natural-sounding **HINDI MALE VOICEOVER** exported as an MP3 file (see "Hindi Voiceover MP3"). It needs correct pronunciation of the English technical terms. Use the same voice as the Episode 02 and 03 Hindi MP3s.
- Synchronize animations with the narration.
- Use subtle background music, significantly quieter than the voice.
- Add English subtitles synchronized with the English voiceover.
- It should feel like a carefully produced technical lesson, not an advertisement.

## Continuity With Episodes 02 and 03

- If the Episode 02 and 03 project sources are available, reuse their components exactly as they were: Model Box, Harness Frame, Message Card, Message List, Tool Call Card, Context Window (with fill meter), Loop Diagram, Summary Card, Notebook (Memory) and Note Card. Reuse the colour palette, fonts, voices and music style.
- Reuse the same example world: the user is called Rahul, and the tools are read_file, run_command and edit_file.
- If the earlier sources are not available, follow the Visual Language section below and keep it consistent for the whole video.
- The PLAN PANEL (defined below) is the "home base" of this episode. Once it is introduced in Section 05, keep it visible in most scenes, and make sure it always shows the current state of the plan.

## Visual Language (Define Once, Reuse Everywhere)

Fallback palette, used only if the earlier palette cannot be reused:
- Background: very dark navy (#0F1420)
- Primary text: off-white (#EDEFF3)
- Muted text / lines: grey (#8A93A6)
- Accent for MODEL: blue (#4C8DFF)
- Accent for HARNESS: amber (#F2B33D)
- Accent for TOOLS: green (#3DD68C)
- Accent for MEMORY: purple (#A78BFA)
- Accent for PLAN: teal (#2DD4BF)
- Warnings / errors: soft red (#FF5C5C)

Components carried over (same meaning as before):
1. **MODEL BOX**: blue rounded rectangle labelled "AI MODEL". Text in, text out.
2. **HARNESS FRAME**: amber rounded rectangle surrounding the Model Box, labelled "HARNESS".
3. **MESSAGE CARD / MESSAGE LIST**: cards with role tags (SYSTEM grey, USER white, ASSISTANT blue, TOOL green), newest at the bottom.
4. **TOOL CALL CARD**: blue card with a dashed border: TOOL: name, INPUT: value. It is only a request.
5. **CONTEXT WINDOW**: tall container with a fill meter.
6. **LOOP DIAGRAM**: GOAL → DECIDE → ACT → OBSERVE → EVALUATE, with REPEAT back to DECIDE. The active stage glows.
7. **SUMMARY CARD** and **NOTEBOOK (MEMORY)**: used only briefly, in the recap and in Section 05.

New components for this episode. Build each one as a reusable function or class:
8. **GOAL CARD**: a wide card with a teal "GOAL" tag holding the user's big goal in one line. Once shown, it stays pinned at the top of the Plan Panel.
9. **PLAN PANEL**: a teal-outlined panel labelled "PLAN". It holds the Goal Card and a numbered list of Step Rows. It sits inside the Harness Frame, outside the Model Box.
10. **STEP ROW**: one line of the plan with a status icon on the left and short English text on the right. Status icons:
    - Pending: empty circle
    - In progress: circle with a moving teal arc
    - Done: teal tick
    - Changed or removed: struck-through text, dimmed
    - Newly added: the row glows for a moment and shows a small "NEW" tag
11. **EVIDENCE LINK**: a thin teal line that connects a "done" tick in the Plan Panel to the TOOL message that proves it (for example "All tests passed ✓").
12. **APPROVAL PROMPT**: a small dialog from the harness to the user: "Start with this plan? Approve / Change".
13. **STEP COUNTER**: a compact label such as "Step 2 of 5", shown near the Loop Diagram.

Data on cards must be short, readable and simplified. Do not show raw JSON, brackets-heavy syntax, or any vendor-specific API format.

## Technical Accuracy Rules (Must Not Be Violated)

The narration and visuals must never imply any of the following:
- That a plan is anything other than text written by the model. It is not a special ability and not a separate program.
- That the model remembers the plan by itself. The harness stores the plan and includes it in what it sends to the model. This is the same principle as in Episodes 02 and 03.
- That the plan runs by itself. In this lesson the agent loop from Episode 02 is unchanged. On every call the model still decides the next action. The plan is extra text in the context that guides those decisions.
- That having a plan guarantees a correct result. A plan can be wrong, incomplete or out of date.
- That a step is finished because the model marked it "done". A "done" mark is a claim by the model. It should be backed by a tool result.
- That a plan is fixed. It can and should change when the agent learns something new.
- That every task needs a plan. Small tasks do not.

Additional rules:
- The tool name update_plan is a simplified example. Do not present it as a standard name that every agent uses.
- Whenever the plan changes on screen (a step is ticked, added, edited or removed), show the model requesting the change through a TOOL CALL CARD first, and the harness applying it second. The Plan Panel must never change by itself.
- Whenever the model is called, the Plan Panel's content must be visibly included in the bundle travelling into the Model Box.
- Do not state real context window sizes, prices or product names for any specific agent or model.

Say these things clearly:
- "A plan is just text. But it is text that keeps the agent on track."
- "Done means checked, not just said."
- "A plan is a guide, not a script."

Do not introduce: named planning methods or papers, chain-of-thought or "reasoning" as a technical topic, tree search, sub-agents or multi-agent systems (only tease them at the very end), MCP, embeddings, fine-tuning, specific APIs or SDKs.

# VIDEO STRUCTURE

## 01. Recap and Hook: Busy, but Lost
TIME: 0:00–1:30

This opening is slightly longer than in earlier episodes. Spend about 55 seconds on the recap and about 35 seconds on the hook.

**Recap (about 55 seconds).** Build the full picture piece by piece, with one sentence each:
1. Show the Loop Diagram. "An agent works in a loop: decide, act, observe, evaluate, repeat." (Episode 01)
2. The Model Box appears, then the Harness Frame grows around it. "The model only writes text. The harness, the program around it, actually runs the tools." (Episode 02)
3. The Message List appears and travels into the Model Box as a bundle. "On every call, the harness sends the whole conversation to the model again." (Episode 02)
4. The Context Window appears with its meter. Older cards collapse into a Summary Card. "The context window is limited, so the harness trims or summarizes old messages." (Episode 03)
5. The Notebook appears and a Note Card flies in. "And what must last longer is saved in memory and brought back later." (Episode 03)

End the recap with all five pieces on screen as one tidy diagram, held for about 2 seconds.

**Hook (about 35 seconds).**
- USER card from Rahul: "Add a contact form to my website. It should save every message and show a thank-you note."
- The loop starts spinning quickly. A "Call #" counter runs up: #10, #30, #60. Tool call cards flash by.
- The agent reports: "Done! The contact form is ready."
- Show a simple checklist of what Rahul asked for:
  - Form page: ✓
  - Saves every message: ✗
  - Thank-you note: ✗
- On-screen question: "60 steps of hard work. Why is half the job missing?"

Narration idea: Our agent was not lazy. It worked hard at every step. But it only ever looked one step ahead, and along the way it lost sight of the whole job. Today we fix that.

Show the title card: **PLANNING**

## 02. Why One Step at a Time Is Not Enough
TIME: 1:30–2:30

Explain what "one step at a time" means: on each call the model looks at the conversation so far and picks the next action. That works well for small tasks, like the port number example from Episode 02.

Show three ways it fails on big goals, each with a short animation:

1. **Forgetting parts of the goal.** The goal has three parts. As the Message List grows long, the agent keeps working on part one and never returns to parts two and three.
2. **Wrong order.** The agent starts writing the "save message" part before looking at how the website is built. It has to throw that work away. Show wasted cards turning red and being discarded.
3. **Stopping too early or never stopping.** Without a clear list of what "finished" means, the agent either announces "Done!" too soon, or keeps polishing forever. Show one loop stopping early and another spinning endlessly.

Everyday analogy: cooking a large meal without a recipe. You are busy the whole time, but the rice is burning while you chop onions, and you forget the salad completely.

Bridge line: a person would solve this by writing a list first. An agent does exactly the same thing.

## 03. What Is a Plan?
TIME: 2:30–3:30

Definition on screen: **Plan = a list of steps to reach a goal.**

Show the model receiving Rahul's goal and writing a plan. The plan first appears as an ordinary ASSISTANT message, as plain text:

1. Look at how the website is organized
2. Create the contact form page
3. Save each submitted message
4. Show a thank-you note after sending
5. Test the whole thing

Make the central point, slowly:
- The plan is ordinary text, written by the model, just like any other reply.
- There is no special "planning part" added to the model. Show the Model Box labelled "SAME MODEL".
- What changes is the *first thing we ask the model to do*: before acting, write down the steps.

Explain why this simple idea helps:
- The whole job is visible at once, so no part gets forgotten.
- The order is decided before any work is done.
- "Finished" now has a clear meaning: every step is done.

Key line:
- English (video): "A plan is just text. But it is text that keeps the agent on track."
- Hindi (MP3): "Plan सिर्फ़ Text है। लेकिन यही Text Agent को सही रास्ते पर रखता है।"

## 04. Breaking a Big Goal Into Good Steps
TIME: 3:30–4:45

Introduce the term: **Decomposition = breaking a big goal into smaller steps.**

Animate the Goal Card splitting into five Step Rows.

Show what makes a step good, with a bad example turning into a good one each time:

1. **Small.** Bad: "Build the form and everything it needs." Good: "Create the contact form page."
2. **Clear.** Bad: "Handle the messages." Good: "Save each submitted message."
3. **Checkable.** Bad: "Make sure it works well." Good: "Run the tests and confirm they pass."

For "checkable", pause and explain: for every step, there should be a way to *see* that it is finished, such as a file that exists or a test that passes. This matters in Section 06.

Then show **order**:
- Draw arrows between steps: step 1 (look at the website) must come before step 2 and step 3. Step 5 (test) must come last.
- Show the wrong order from Section 02 once more, now corrected by the arrows.

Then show **the right size of plan**, with a three-position slider:
- Too little: "1. Build the contact form." This is the goal repeated. It helps nothing.
- Too much: forty tiny steps such as "open file", "move cursor". Long, wasteful, and it breaks as soon as anything is different from what was expected.
- About right: five to seven meaningful steps.

## 05. Where Does the Plan Live?
TIME: 4:45–6:15

Start with a problem the viewer can now predict from Episode 03:
- The plan was written as an ASSISTANT message early in the conversation.
- The Message List grows. The Context Window fills. Old messages are trimmed or summarized.
- The plan card slides out of the window and fades. Show a red warning: "The plan is gone."
- The agent drifts, exactly as in Section 02.

Solution: the plan should not be just another old message. The harness gives the model a tool for it.

Introduce the PLAN PANEL inside the Harness Frame, outside the Model Box.

Animate step by step, with step numbers on screen:

1. USER: Rahul's goal. The harness sends it to the model, along with the tool descriptions. One tool description is new: update_plan — "Creates or updates the list of steps for the current task".
2. The model replies with a TOOL CALL CARD: TOOL: update_plan, INPUT: the five steps.
3. The harness executes it: the Goal Card and five Step Rows appear in the Plan Panel, all with empty circles.
4. The harness adds a TOOL message: "Plan saved."
5. From now on, on every call, the harness includes the current plan in what it sends. Show the bundle travelling into the Model Box with three parts: the Message List, the tool descriptions, and the Plan Panel's content.

Then show why this is better than a plain message:
- **It survives.** Run the trimming and summarizing animation again. Old messages disappear, but the Plan Panel is untouched, because the harness stores it separately and adds it back every time.
- **It is always current.** The model sees the latest version of the plan on every call, not an old copy.
- **The user can see it.** Show the Plan Panel also displayed to Rahul, so he can watch progress.

Connect to earlier lessons: this is the same pattern again. The model does not remember the plan. The harness keeps it and brings it back. Briefly show the Notebook from Episode 03 beside the Plan Panel with the label "Same idea: saved outside, sent back in."

## 06. Working Through the Plan
TIME: 6:15–7:45

THIS IS THE MOST IMPORTANT SECTION OF THE VIDEO. Go slowly.

Layout: Plan Panel on the left, Loop Diagram in the centre with the Step Counter, Message List on the right.

First state what has *not* changed: the loop from Episode 02 is exactly the same. The model still decides one action per call. The only difference is that the plan is now in front of it every time.

Animate one full step in detail, with step numbers on screen. Use plan step 1, "Look at how the website is organized":

1. **Pick the next step.** The model reads the plan and replies with a TOOL CALL CARD: update_plan → step 1 "in progress". The harness applies it. The circle on step 1 gets the moving teal arc. Step Counter: "Step 1 of 5".
2. **Do the work.** One or more normal tool calls, as in Episode 02: ASSISTANT (tool call): run_command → "list files", then TOOL: a short file list. ASSISTANT (tool call): read_file → "index.html", then TOOL: a short result. The Loop Diagram cycles DECIDE → ACT → OBSERVE for each.
3. **Check the result.** The Loop Diagram's EVALUATE stage glows. The model now has what it needed: it knows where pages are kept.
4. **Mark it done.** TOOL CALL CARD: update_plan → step 1 "done". The harness applies it. A teal tick appears.
5. **Move on.** The next call starts with step 2.

Then run steps 2 and 3 quickly (a few seconds each) using the same rhythm, so the pattern is clear: in progress → work → check → done.

Now make the key point about "done". Show two versions of step 5, "Test the whole thing", side by side:

- **Wrong:** the model edits a file, then immediately requests update_plan → step 5 "done". No test was run. Show a red "?" on the tick and the label "Said, not checked."
- **Right:** ASSISTANT (tool call): run_command → "run tests". TOOL: "All tests passed ✓". Only then: update_plan → step 5 "done". Draw the EVIDENCE LINK from the tick to the TOOL message. Label: "Checked."

Explain: a tick in the plan is only a claim written by the model. The tool result is the proof. A good agent, and a well-built harness, tie every "done" to real evidence. This is why Section 04 asked for checkable steps.

Key line:
- English (video): "Done means checked, not just said."
- Hindi (MP3): "Done का मतलब है जाँचा हुआ, सिर्फ़ कहा हुआ नहीं।"

## 07. Replanning: When the Plan Meets Reality
TIME: 7:45–9:00

Start with a simple truth on screen: "The plan was written before the work began."

Explain: when the model wrote the plan, it had not yet looked at the project. So the plan is a best guess. As the agent works, tool results tell it things it did not know.

Define the term: **Replanning = changing the plan because of what the agent has learned.**

Animate one case in detail, step by step. The agent is on step 3, "Save each submitted message":

1. ASSISTANT (tool call): run_command → "search for where data is stored".
2. TOOL: "No storage found in this project."
3. The model sees the problem: the plan assumed there was already a place to save things. There is none.
4. The model replies with a TOOL CALL CARD: update_plan, with these changes:
   - Add a new step before step 3: "Create a file to store messages" (glows, "NEW" tag)
   - Keep step 3, now renumbered
5. The harness applies it. The Plan Panel reorders itself. The Step Counter changes from "Step 3 of 5" to "Step 3 of 6".
6. The loop continues with the new step.

Then show a second kind of discovery, more briefly: one that the agent should not decide alone.
- While creating storage, the model realizes there are two reasonable choices: a simple file, or a database that would need new software installed.
- This affects Rahul's project in a way he may care about. So instead of guessing, the model replies with a question: "Should I store messages in a simple file, or set up a database?"
- The loop pauses (as in Episode 02, Section 08). Rahul answers: "A simple file is fine." The plan continues.

Show a third, tiny case in a few seconds: a step turns out to be unnecessary (the website already shows a thank-you note after any form). The model requests update_plan to strike that step through.

Sum up with three small icons: **add** a step, **change** a step, **remove** a step.

Key line:
- English (video): "A plan is a guide, not a script."
- Hindi (MP3): "Plan एक Guide है, Script नहीं।"

Contrast two failures to avoid, shown as two small panels:
- Never replanning: the agent follows a broken plan straight into a wall.
- Always replanning: the agent rewrites its plan every step and never makes progress.

## 08. Showing the Plan to a Human First
TIME: 9:00–9:45

Idea: the cheapest moment to fix a mistake is before any work is done.

Animate:
1. Rahul gives the goal. The model writes the plan through update_plan. The Plan Panel fills.
2. Before any other tool is run, the harness shows the APPROVAL PROMPT: "Start with this plan? Approve / Change".
3. Rahul reads the plan and notices something missing. He replies: "Also send me an email when someone writes."
4. The model requests update_plan to add that step. The Plan Panel updates.
5. Rahul clicks Approve. The loop begins.

Show the comparison with two short timelines:
- Without approval: the agent works for 60 calls, and only then Rahul discovers the email part is missing. Much of the work must be redone.
- With approval: the gap is caught in the first minute, at almost no cost.

Connect to Episodes 01 and 02: this is human oversight again. Whether to ask for approval, and when, is a choice built into the harness by its developer. For small or low-risk tasks, the harness may skip it.

## 09. Full Replay: The Contact Form, Done Properly
TIME: 9:45–11:30

Replay the hook's task from start to finish, now with everything from this lesson. Keep it rhythmic, because the viewer knows every part.

Layout: Plan Panel on the left, Message List in the centre, Loop Diagram with Step Counter on the right. A small Context Window meter sits in a corner.

1. USER: "Add a contact form to my website. It should save every message and show a thank-you note."
2. ASSISTANT (tool call): update_plan → five steps. The Plan Panel fills.
3. APPROVAL PROMPT. Rahul: "Approve."
4. **Step 1: Look at how the website is organized.** In progress → run_command "list files" → read_file "index.html" → done ✓.
5. **Step 2: Create the contact form page.** In progress → edit_file "contact.html" → TOOL: "File created" → done ✓, with an Evidence Link to the TOOL message.
6. **Step 3: Save each submitted message.** In progress → search → TOOL: "No storage found in this project."
7. **Replan.** ASSISTANT asks Rahul: "Should I store messages in a simple file, or set up a database?" Rahul: "A simple file is fine." ASSISTANT (tool call): update_plan → add "Create a file to store messages". Step Counter becomes "of 6".
8. **New step: Create a file to store messages.** In progress → edit_file "messages.txt" → done ✓.
9. **Save each submitted message.** In progress → edit_file "contact.html" → done ✓.
10. Fast-forward montage. The Context Window meter reaches amber. Older messages collapse into a Summary Card. The meter drops. **The Plan Panel does not change at all.** Hold on this for a moment with the label "The plan survives."
11. **Show a thank-you note after sending.** In progress → edit_file → done ✓.
12. **Test the whole thing.** In progress → run_command "run tests" → TOOL: "1 test failed: message not saved when the name is empty."
13. The step stays "in progress". The model fixes it: edit_file "contact.html" → run_command "run tests" → TOOL: "All tests passed ✓". Now done ✓, with an Evidence Link to this TOOL message.
14. ASSISTANT (final text, no tool call): "The contact form is ready. It saves every message to messages.txt and shows a thank-you note. All tests pass."

End by bringing back the checklist from the hook, now complete:
- Form page: ✓
- Saves every message: ✓
- Thank-you note: ✓

Show the Model Box labelled "SAME MODEL" one last time, next to the hook's failed attempt. The model did not get smarter. It was given a way to keep the whole job in view.

## 10. Reality Check: Plans Are Not Magic
TIME: 11:30–12:15

Keep the tone of the earlier reality-check sections. Show four short points, each with one simple visual:

1. **A plan can be wrong.** If the model misunderstands the goal, it writes a neat plan for the wrong thing. Show a perfect row of ticks under a Goal Card with a red "wrong goal" mark. This is why human review helps.
2. **A tick is not proof.** The model can mark a step done when it is not. Show a tick with no Evidence Link, flashing "?".
3. **Small tasks do not need a plan.** For "What port does the server use?", writing a plan is slower and adds nothing. Show a tiny task buried under a needless five-step plan.
4. **The model can drift from its own plan.** Having a plan in the context makes drifting less likely, not impossible. Show the agent wandering off to an unrelated file while step 3 is still in progress.

Close the section with: a plan does not make the agent right. It makes the agent's work visible, so that both the agent and the human can catch mistakes earlier.

## 11. Conclusion and What's Next
TIME: 12:15–13:00

Summarize with five short English lines appearing one by one on screen:
1. One step at a time fails on big goals.
2. A plan is a list of steps, written by the model as plain text.
3. The harness keeps the plan and sends it on every call.
4. Done means checked, not just said.
5. A plan is a guide. It changes when the agent learns something new.

The narration should communicate something along these lines.

English (video):

"Today we gave our agent something simple but powerful: a plan. We saw that a plan is just a list of steps, written as plain text. The harness keeps it safe and shows it to the model on every call. The agent works through it step by step, checks each step with real evidence, and changes the plan when reality turns out to be different.

And notice what stayed the same. The model, the harness and the loop are exactly what we learned before. We only added one more piece of text.

But think about one of those steps. What if a single step is itself a huge job, as big as the whole task we did today? Could our agent hand that step over to another agent, and just wait for the result?

That's what we'll explore in the next lesson: agents working together."

Hindi (MP3), the accurate Hindi equivalent of the lines above:

"आज हमने अपने Agent को एक सीधी-सादी लेकिन बहुत काम की चीज़ दी: एक Plan। हमने देखा कि Plan बस Steps की एक List है, जो सादे Text में लिखी होती है। Harness उसे सँभालकर रखता है और हर Call पर Model को दिखाता है। Agent उस पर एक-एक Step करके चलता है, हर Step को असली सबूत से जाँचता है, और जब हक़ीक़त कुछ अलग निकलती है तो Plan बदल देता है।

और ध्यान दीजिए कि क्या नहीं बदला। Model, Harness और Loop बिल्कुल वही हैं जो हमने पहले सीखे थे। हमने बस Text का एक और टुकड़ा जोड़ा है।

लेकिन उन Steps में से किसी एक के बारे में सोचिए। अगर कोई एक Step ख़ुद ही एक बहुत बड़ा काम हो, उतना ही बड़ा जितना आज का पूरा Task था, तब क्या? क्या हमारा Agent वह Step किसी दूसरे Agent को सौंप सकता है, और बस Result का इंतज़ार कर सकता है?

अगले lesson में हम यही देखेंगे: Agents का मिलकर काम करना।"

Finish with a minimalistic title card in the same style as the earlier episodes:

AGENTIC AI
PLANNING

Fade in a smaller line underneath for 2 seconds: "Next: Agents Working Together"

# TIMING RULES

**Video (English):**
- Section timings are targets. Final total runtime must be between 11:00 and 14:00. Aim for about 13:00.
- Section 01 should run between 1:20 and 1:40. It is meant to be a little longer than Episode 03's one-minute opening, but it must not exceed 1:40.
- Write the English narration first, generate the English voiceover, measure each section's and each step's audio length, then time the animations to the audio. Drive the animation timings from a timing file (for example `timings/en.json`).
- Do not speed up or compress the voice to fit the timings.
- If a section's audio is more than 20% longer or shorter than its target, adjust that section's narration text and regenerate it, rather than stretching animations.
- Leave 0.5–1 second of silence between sections for transitions.
- Sections 06 and 07 are the most important. Section 06 must be at least 1:20 long and Section 07 at least 1:05 long. Do not rush them.

## Hindi Voiceover MP3

- The video's timing is final and is never changed to fit the Hindi audio. The Hindi audio is fitted to the video.
- The Hindi MP3 must have exactly the same total duration as the final video, so it can replace the English voice track without any editing.
- Align it to the video section by section, and within Sections 05, 06, 07, 08 and 09 step by step. Each Hindi section must start at the same timestamp as the matching English section. Take these timestamps from `timings/en.json`.
- Each Hindi segment must fit inside its English segment's time slot. If it is shorter, pad it with silence at the end of the slot. If it is longer, rewrite the Hindi more concisely while keeping the full meaning, then regenerate it. Do not drop content to make it fit. Speed it up by at most 5%, and only if rewording is not enough.
- Lines that refer to a specific on-screen moment (a step being ticked, a new step appearing, the approval prompt, an Evidence Link being drawn) must be spoken while that visual is on screen, just as in the English version.
- The MP3 contains voice only, with no background music, so the music can be mixed later at the same level as in the English video.
- Export it as MP3, 44.1 kHz or 48 kHz to match the video's audio sample rate, at 192 kbps or higher, normalized to a similar loudness as the English voice.
- Also export a Hindi .srt subtitle file timed to the Hindi MP3, but do not burn it into the video.

# FINAL EXPECTATIONS

1. Produce ONE complete, polished end-to-end educational video with English voiceover and English subtitles. Do not produce separate animation demos.
2. Produce ONE separate, highly accurate Hindi voiceover MP3 that matches the final video's timeline exactly (see "Hindi Voiceover MP3").
3. Write and organize the complete English narration and the complete Hindi narration, each saved as a separate text file per section. Also save the side-by-side English | Hindi comparison file.
4. Generate the English narration with a natural English male voice, and the Hindi narration with a natural Hindi male voice. Use the same voices as Episodes 02 and 03 if they are available.
5. Programmatically generate all animations and synchronize them with the English voiceover.
6. Burn properly synchronized English subtitles into the video, and export them as an .srt file. Export the Hindi subtitles as a separate .srt file only.
7. Keep all on-screen text in English.
8. Maintain visual consistency with Episodes 01–03.
9. Reuse the earlier components, and build the new ones (Goal Card, Plan Panel, Step Row, Evidence Link, Approval Prompt, Step Counter) as reusable components so later episodes can reuse them.
10. Drive the Plan Panel from a single plan state, so that the step statuses, numbering and Step Counter can never disagree with each other on screen.
11. Final output files:
    - `output/ep04_planning_EN.mp4` (1080p, English voiceover, music and subtitles)
    - `output/ep04_voiceover_HI.mp3` (Hindi voice only, same duration as the video)
    - `output/ep04_EN.srt`
    - `output/ep04_HI.srt`
12. Organize the Python source and assets cleanly, for example:
    - `scenes/` (one file per section)
    - `components/` (reusable visual elements)
    - `narration/en/` and `narration/hi/` (text per section)
    - `narration/en_hi_side_by_side.md`
    - `audio/en/`, `audio/hi/` and `audio/music/`
    - `timings/en.json`
    - `subtitles/`
    - `output/`
13. Before rendering, check the English narration and the visuals against the "Language Rules" and "Technical Accuracy Rules" sections. In particular, confirm that the Plan Panel never changes without a preceding update_plan tool call. Before exporting the MP3, check the Hindi script line by line against the English script. Then confirm that the MP3's duration equals the video's duration and that its section start times match `timings/en.json`.

Prioritize clarity and teaching quality over visual complexity. A beginner who watched Episodes 01–03 should be able to follow every step without any programming knowledge.
