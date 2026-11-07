# Production plan: What is Agentic AI? (introductory lesson)

Reconstructed for the pipeline from the finished production (README "Sections",
ANIMINFO.md §4 and §10, and the scenes). The original brief asked for a 7–9 minute
beginner lesson; the finished Hindi version runs 10:44 because the full script was kept.

## Overall objective

A long-form introductory lesson that explains Agentic AI to complete beginners: what an
AI model is, what an AI agent is, how it differs from a chatbot, how the agent loop works,
why agents need tools, a practical bug-fix example, the risks, and what comes next.
Clarity over visual complexity. It must feel like a carefully produced technical lesson,
not an advertisement.

## Production requirements

- All animation generated programmatically (Manim), 16:9, 1920x1080, 30 fps.
- Minimal, clean, modern style: dark canvas, thin outlines, dotted rounded zones,
  light italic labels, one accent colour per concept (blue model/decide, teal
  agent/act/success, amber environment/observe, violet feedback/evaluate, red errors).
- All on-screen text in English (both language versions share the visuals).
- Narration synchronised with the animation (voice first, animation follows).
- Subtle synthesised background music, ducked well under the voice.
- English subtitles as separate files.

## 01. Introduction: why Agentic AI matters
TIME: 0:00–1:01

Two scenarios on the same programming error (ZeroDivisionError). Scenario A: a person asks
an AI what the error means; the AI explains, but the problem stays. Scenario B: a person
asks an AI agent to find the error, understand it and fix it; the agent opens files, runs
commands, hits the error, fixes the code and re-runs the tests. Contrast "gives
information" vs "takes action", then the title "Agentic AI" and the question "How?".

## 02. What is an AI model?
TIME: 1:01–2:16

Data grid flowing into a chip-style model; "Large Language Model" -> LLM; learned from
countless texts (questions, explanations, answers). Input -> model -> output with a
question card and an answer card; the context zone ("what it can see"). Examples GPT,
Claude, Gemini. A model alone only produces text: it doesn't open files or run programs.
End on a question mark: where does the power to act come from?

## 03. What is an AI agent?
TIME: 2:16–3:36

Definition: a system that uses a model to work toward a goal (system zone, model chip,
goal target). Four steps as pills: makes decisions, acts with tools, checks results,
plans the next step. The five parts introduced one by one: goal, model (thinks & decides),
tools (file/terminal/browser), environment (project, data, web, computer), feedback (arc
back to the model, a token travelling act -> environment -> feedback). Model ≠ agent.

## 04. Chatbot vs AI agent
TIME: 3:36–4:34

Two zones side by side. Chatbot: a straight line of three steps and "done". Agent: goal,
work out what to do, pick the tool, take action, check the result, goal reached? with a
repeat loop, exits "goal reached" and "ask a human". Then the same chat window for both:
they look the same; the difference is that the agent can take action (tool icons wired
to it).

## 05. How does an agent actually work? (the most important section)
TIME: 4:34–6:21

The agent loop on one true circle: decide -> act -> observe -> evaluate, with a violet
repeat arc; goal enters from above, "done" exits left; a loop counter in the centre.
Weather example: "Will it rain in Delhi tomorrow?" - first website fails to load, goal not
reached, loop again, a different website returns "Chance of rain: 80%", goal reached,
answer. Closing: the agent adapted after each result (history rows), then the four steps
named again while the token runs one more lap.

## 06. Why agents need tools
TIME: 6:21–7:29

A model alone only emits text. Five tools wired to the model, each with a tiny demo:
filesystem (read/create/modify files), terminal ($ python app.py), browser (page loads),
API (request/response packets), database (row highlight, cell update). Then the key
distinction: the model decides and sends a request; the tool does the real work and
returns the result - "the brain" and "the hands".

## 07. Real example: an agent fixing a bug
TIME: 7:29–8:58

Project zone, editor and terminal. The user's request; a small calculator app that
averages numbers (explained for non-programmers). Loop by loop with a phase widget:
list files, open stats.py, run tests, ZeroDivisionError (empty list -> 0/0), insert the
guard (return 0 for an empty list), run tests again, all pass, a report card (problem,
fix, result). Finally all five parts tagged on screen and the loop widget spinning.

## 08. Reality check: agents are not magic
TIME: 8:58–9:50

"AI agents are powerful, but they are not magic." Four risks with icons (wrong
decisions, tools used incorrectly, important data changed or deleted, stuck in a loop).
Permissions, safeguards, human oversight. A boundary: allowed actions inside, blocked
ones outside; the agent tries to step out, the boundary stops it, a human approval gate.
"More power = more responsibility."

## 09. Conclusion: we are just getting started
TIME: 9:50–10:44

Recap cards (what an agent is, how it works, chatbot vs agent), the road ahead
(architecture, tool integration, context management, memory, planning, agentic systems),
"we'll also learn to build websites and apps" with a browser and a phone mockup building
themselves, and the title card AGENTIC AI / THE BEGINNING.
