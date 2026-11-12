# Context and Memory: How an Agent Handles Long Tasks

<!-- Narration script (English): one paragraph per narration beat. Episode 03. Drafted from the plan; the plan's required lines are kept word for word. -->

## 01. The Desk Is Full

Welcome back. Last time, we opened up an AI agent and looked inside.

We saw that the model only reads text and writes text. On its own, it can't open a file or run a command.

The harness runs the loop. When the model asks for a tool, the harness executes it and adds the result to the conversation.

That conversation is a list of messages. And on every call, the harness sends the whole list to the model again.

All of it has to fit inside the context window, which is limited.

We called it the model's desk. And that desk has a fixed size.

But real tasks are long. An agent might need hundreds of steps to finish one job.

Watch. Call five. Call twenty. Call sixty. Every step adds more messages.

The meter climbs. Amber. Red. And then the window is full.

The task isn't finished. The desk is full. Now what?

How do real agents keep working? And how do they remember things from yesterday?

That's today's lesson: context and memory.

## 02. What Is Actually Filling the Context?

So first, what is actually filling the context window?

At the top is the system message. Small, and always there.

Then the tool descriptions. Also small, and always present.

User messages are usually thin, like a short question. The assistant's messages and tool calls are thin too.

But tool results can be very tall.

The model requests read_file, on a large file.

The harness adds the result as one tool message, and the meter jumps from 20% to 60% in one step.

Sort everything by type, and the picture is clear. In many agent tasks, tool results take the most space.

And remember: everything in the window is sent again on every call.

So one large tool result is paid for again and again, in time and in cost.

## 03. Why Not Just Use a Bigger Window?

So why not just make the window bigger?

Bigger windows help, but they don't solve the problem. Here's why.

One: it still has a limit. A long enough task fills even a big window.

Two: it gets slower and more expensive. More text in every call means each call costs more and takes longer.

Three: important details get harder to find. When the context is very long and cluttered, models often become less reliable at using the right piece of information.

Like the user's original goal: still in there, but lost among hundreds of other messages.

A bigger desk covered with a thousand papers doesn't help you work. A clean desk with the right ten papers does.

This is called context management: deciding what the model sees on each call. It's the harness's job, set up by the developers who build it.

The goal is not more context. The goal is the right context.

## 04. Technique 1: Keep Tool Results Small

Technique one: keep tool results small.

The cheapest way to save space is to not put unnecessary text into the context in the first place.

First, read only the part you need.

Before: read_file returns a whole five-thousand-line file.

After: the tool call asks only for lines 40 to 80, and a small card comes back.

Second, search instead of reading everything.

Before: the agent reads ten files to find where total() is. After: one search returns three short matching lines.

Third, the harness shortens very long output.

A run_command result can be thousands of lines. The harness keeps the beginning and the end, with a note in the middle: output shortened, 4,800 more lines.

That note matters. The harness must tell the model that text was cut.

Without it, the model thinks it has seen everything, and answers confidently from a wrong assumption.

With the note, the model knows something is missing, and asks for the part it needs.

## 05. Technique 2: Trim Old Messages

Technique two: trim old messages.

When the window gets full, the harness removes the oldest messages so new ones fit.

Here the window is at 95%, and a new message needs to come in.

The oldest messages slide out, the meter drops, and the new one fits.

The system message stays pinned at the top. And a tool call and its result always leave together, as a pair.

A gentler version empties only old, large tool results, and leaves a short note in their place.

But trimming has a danger. The first user message said: Fix the crash. Do not change the public function names.

That message gets trimmed away. A few steps later, the model renames a function. It can no longer see the instruction.

Trimming is simple and fast, but it's blind. It throws away old messages, important or not.

And once a message is out of the window, the model cannot see it any more.

## 06. Technique 3: Summarize Old Messages (Compaction)

Technique three: summarize old messages.

Instead of throwing old messages away, the harness replaces them with a short summary. This is commonly called compaction.

Step one: the harness notices the window is getting full. The meter crosses a threshold, in this example 80%.

Step two: the harness makes a separate call to the model, with the older messages and one instruction: Summarize the important points of this conversation so far.

Step three: the model writes the summary, as normal text. The harness only decides when to ask, and what to replace.

Step four: the harness swaps them. The older messages become one summary. The system message stays on top, and the newest messages stay as they are.

Step five: the meter drops to 25%, and the loop continues.

A good summary keeps the goal, the user's rules, what's done, what's left, and key facts like file names and errors.

But a summary is lossy. An old message said: the user wants error messages in simple words.

The summary left it out. So the model never sees it again, and stops following it.

Comparing the three: small tool results save space early, but you might miss a part you needed.

Trimming saves a lot, but can lose old instructions completely.

Summarizing saves a lot too, but can lose small details.

Every technique for saving space loses something. Context management is choosing what you can afford to lose.

## 07. Memory: Writing Things Down Outside the Window

All of this happens inside one conversation. What about tomorrow?

A session is one continuous conversation with the agent, from start to end.

In session one, Rahul says: In this project, always run the tests before you say a task is done. The agent follows it.

Then the session ends, and the context window is cleared.

In session two, the agent skips the tests. The rule is gone, because the message that held it is gone.

Memory is information the harness saves outside the context window, usually in ordinary files, so it can be brought back later.

The context window is the desk. Memory is a notebook in the drawer. The desk gets cleared every day. The notebook stays.

Now, session one again, with memory. Rahul adds: Remember this.

The model replies with a tool call to save_note, with the text: Always run tests before finishing a task.

The harness executes it. It saves the note in the notebook, and adds a tool message: Note saved.

The session ends. The messages are gone, but the notebook keeps its note.

In session two, before the first call, the harness puts the saved notes into the context window.

Rahul says: Fix the login bug.

The model fixes it, and before reporting back, it calls run_command to run the tests.

It's exactly the same model in both sessions. It didn't learn anything.

It follows the rule only because the harness put the note back into the text it received.

The model doesn't remember. The harness writes it down and brings it back.

Worth saving: facts, like how the tests are run. Rules, like: do not rename public functions.

And progress, like: login bug, cause found, fix not written yet.

## 08. Retrieval: Bring Back Only What You Need

Weeks pass, and the notebook now holds 300 notes.

If the harness loads them all at the start of a session, the window is at 70% before the user says a word.

Memory can overflow the context too.

The answer is retrieval: fetching only the notes that are relevant to the current task.

A few short core rules are always loaded, at the start of every session. Everything else stays in the notebook until it's needed.

Rahul says: Deploy the app to the test server.

The model replies with a tool call to search_notes, with the query: deploy.

The harness searches the notebook. Out of 300 notes, 2 match.

It adds a tool message with just those two notes, and the meter has barely moved.

It's the same tool-calling pattern as before. The model requests, the harness does. Memory is just another tool, plus a place to store text.

There are smarter ways to search notes than matching words. We'll meet those in a later lesson.

## 09. Full Replay: One Long Task Across Two Sessions

Now let's put it all together: one long task, across two sessions.

Session one. Rahul says: Fix all failing tests in this project. Don't rename public functions.

The model calls run_command to run the tests. The output is very long, so the harness shortens it. That's technique one.

Then read_file, for lines 40 to 80 only. Technique one again.

Then edit_file, and the file is updated.

The work goes on, call after call. By call forty, the meter is at 80%.

Compaction kicks in. That's technique three. The older messages become one summary, and the meter drops to 25%.

The model finds out why the login tests fail, and calls save_note: Login tests fail because of a wrong port in config.txt.

Rahul says: Let's stop for today. One more save_note, with the progress: 6 of 8 tests pass. Next: fix the port, then run tests.

The session ends. The notebook keeps its notes.

Session two. The harness loads the notes. The meter is at just 5%.

Rahul says: Continue from yesterday.

The model calls read_file on config.txt. The result: port = 8800. That's the wrong port.

Then edit_file to fix the port, and run_command to run the tests. All 8 tests passed.

And a final answer, with no tool call: All tests pass now. The last two failed because config.txt had the wrong port. No public functions were renamed.

Two things survived. The rule survived compaction, because the summary kept it.

And the progress survived the end of the session, because it was saved to memory.

## 10. Reality Check: Memory Can Be Wrong

A reality check before we finish. Memory is useful, but it isn't magic.

One: summaries lose details. What a summary leaves out is gone.

Two: notes can be out of date. A note says the server port is 8080, but config.txt now says 9090. If the agent trusts the old note, it makes a mistake.

Good agents check important facts again.

Three: notes can be wrong from the start. A wrong conclusion, once saved, gets repeated in later sessions.

Four: memory can hold private information. You should be able to see what is saved, and delete it.

More memory is not automatically better. Like context, the aim is the right information at the right time.

## 11. Conclusion and What's Next

Today we solved the problem from last time. The context window is limited, so the harness has to choose what the model sees.

It can keep tool results small, drop old messages, or replace them with a summary.

And for anything that must last longer than one conversation, it writes it down in memory, and brings it back when it's needed.

Remember the most important point. The model itself never remembers anything. It only sees the text that the harness gives it.

But there is still one thing we haven't looked at. So far, our agent decides just one step at a time.

What happens when the goal is really big, like building a whole app? How does an agent break a big goal into small steps, and keep track of them?

That's what we'll learn in the next lesson: Planning.
