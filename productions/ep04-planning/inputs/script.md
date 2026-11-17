# Planning: How an Agent Handles Big Goals

<!-- Narration script (English): one paragraph per narration beat. Episode 04. Drafted from the plan; the plan's required lines ("A plan is just text. But it is text that keeps the agent on track.", "Done means checked, not just said.", "A plan is a guide, not a script.") and its closing narration are kept word for word. -->

## 01. Busy, but Lost

Welcome back. Let's rebuild what we've learned so far, one piece at a time.

First, the loop. An agent works in a loop: decide, act, observe, evaluate, and repeat.

At the centre is the model, which only writes text. The harness, the program around it, actually runs the tools.

The conversation is a list of messages. On every call, the harness sends the whole conversation to the model again.

But the context window is limited, so the harness trims or summarizes old messages.

And what must last longer is saved in memory, and brought back later.

Loop, model, harness, messages, context and memory. That's our agent so far.

Now let's give it a bigger job.

Rahul asks: Add a contact form to my website. It should save every message and show a thank-you note.

The agent gets to work. Call ten. Call thirty. Call sixty. Tool call after tool call.

Finally, it reports: Done! The contact form is ready.

Let's check what Rahul asked for. A form page: yes. Saving every message: no. A thank-you note: no.

Sixty steps of hard work. So why is half the job missing?

Our agent wasn't lazy. It worked hard at every step. But it only ever looked one step ahead, and along the way, it lost sight of the whole job.

Today, we fix that. Today's lesson: planning.

## 02. Why One Step at a Time Is Not Enough

What does one step at a time mean? On each call, the model looks at the conversation so far, and picks the next action.

For small tasks, that works well. Like finding which port the server uses: read one file, and answer.

But on big goals, it fails in three ways.

One: it forgets parts of the goal. As the list grows, it keeps working on part one, and never gets back to parts two and three.

Two: the wrong order. It writes the code that saves messages before looking at how the website is built, and that work is thrown away.

Three: it doesn't know what finished means. So it either says done too soon, or keeps polishing forever.

It's like cooking a big meal without a recipe. You're busy the whole time, but the rice burns while you chop onions, and you forget the salad.

A person would solve this by writing a list first. An agent does exactly the same thing.

## 03. What Is a Plan?

A plan is a list of steps to reach a goal.

We give the model Rahul's goal, and ask it to write a plan first. It replies with an ordinary assistant message, in plain text.

One: look at how the website is organized. Two: create the contact form page. Three: save each submitted message.

Four: show a thank-you note after sending. Five: test the whole thing.

Notice what this is: ordinary text, written by the model, just like any other reply.

There's no special planning part added to the model. It's the same model as before.

What changes is the first thing we ask it to do: before acting, write down the steps.

And that simple idea helps. The whole job is visible at once, so no part gets forgotten.

The order is decided before any work starts. And finished means every step is done.

A plan is just text. But it is text that keeps the agent on track.

## 04. Breaking a Big Goal Into Good Steps

Breaking a big goal into smaller steps has a name: decomposition.

Our goal splits into five steps. But what makes a step a good one? Three things.

First, it's small. Build the form and everything it needs is too big. Create the contact form page is one clear piece of work.

Second, it's clear. Handle the messages could mean anything. Save each submitted message says exactly what to do.

Third, it's checkable. Make sure it works well can't be checked. Run the tests and confirm they pass can.

For every step, there should be a way to see that it's finished, like a file that exists, or a test that passes.

Steps also have an order. Looking at the website comes before building the form. And testing comes last.

Remember the wrong order from before? Now the agent looks at the website first.

And a plan should be the right size. Too little, like build the contact form, just repeats the goal. It doesn't help.

Too much, like forty tiny steps such as open file and move cursor, is long and wasteful. And it breaks as soon as anything changes.

About right is five to seven meaningful steps.

## 05. Where Does the Plan Live?

So where does the plan live? Right now, it's just an assistant message, early in the conversation.

But the message list grows, and the context window fills up.

Old messages are trimmed, and the plan slides out of the window. The plan is gone, and the agent drifts.

The plan shouldn't be just another old message. So the harness gives the model a tool for it.

Step one: Rahul sends his goal. The harness passes it to the model, along with the tool descriptions.

One of them is new: update_plan. It creates or updates the list of steps. The name is just an example.

Step two: the model replies with a tool call. The tool is update_plan, and the input is the five steps.

Step three: the harness executes it. The goal and the five steps appear in the plan panel.

Step four: the harness adds a tool message: Plan saved.

Step five: from now on, every call carries the messages, the tool descriptions, and the current plan.

Why is this better? First, it survives. Old messages are trimmed, but the plan is untouched, because the harness stores it separately.

Second, the model always sees the latest version. Third, Rahul can watch the progress too.

Same pattern again: the model doesn't remember the plan. The harness keeps it and brings it back, like memory.

## 06. Working Through the Plan

Now the most important part: how the agent works through the plan.

First, what hasn't changed: the loop is the same, and the model still decides one action per call. The only difference: the plan is now in front of it, every time.

Let's follow step one closely: look at how the website is organized.

First, pick the next step. The model reads the plan, and calls update_plan to mark step one as in progress. The harness applies it.

Second, do the work with normal tool calls: run_command lists the files, and read_file reads index.html.

Decide, act, observe, once for each tool call.

Third, check the result: now it knows where the pages are kept.

Fourth, mark it done. Another update_plan call, and the harness puts a tick on step one.

Fifth, move on. The next call starts with step two.

Steps two and three follow the same rhythm. In progress, work, check, done.

Now, a closer look at done, with two versions of step five.

On the left, the model edits a file and marks step five done at once. No test was run. Said, not checked.

On the right, it calls run_command to run the tests first. All tests passed. Only then is the step marked done. Checked.

A tick in the plan is only a claim, written by the model. The tool result is the proof.

A good agent, and a well-built harness, tie every done to real evidence. That's why steps must be checkable.

Done means checked, not just said.

## 07. Replanning: When the Plan Meets Reality

The plan was written before the work began. So it's a best guess, and tool results will tell the agent new things.

Changing the plan because of what the agent has learned is called replanning.

On step three, save each submitted message, the model calls run_command to search for where data is stored.

The result: No storage found in this project. But the plan assumed there was one.

So the model calls update_plan to add a new step before step three: create a file to store messages.

The harness applies it. Now there are six steps, and the loop continues.

Some choices shouldn't be made alone: a simple file, or a database that needs new software?

That affects Rahul's project, so the model asks: Should I store messages in a simple file, or set up a database?

The loop pauses. Rahul answers: A simple file is fine.

And if the website already showed a thank-you note, the model would ask update_plan to remove that step.

Add a step, change a step, remove a step. A plan is a guide, not a script.

Avoid two failures. Never replanning: following a broken plan into a wall. Always replanning: rewriting the plan every step, and never making progress.

## 08. Showing the Plan to a Human First

The cheapest moment to fix a mistake is before any work is done.

Rahul gives his goal, and the model writes the plan with update_plan. Before any other tool runs, the harness asks Rahul: Start with this plan?

Rahul spots something missing: Also send me an email when someone writes. The model calls update_plan to add that step. Then Rahul approves, and the loop begins.

Without approval, Rahul finds the gap after sixty calls, and much of the work is redone. With approval, it's caught in the first minute.

This is human oversight again. When to ask is a choice built into the harness by its developer. Small, low-risk tasks may skip it.

## 09. Full Replay: The Contact Form, Done Properly

Now let's replay Rahul's task from the start, with everything we've learned.

Rahul asks for the contact form. The model calls update_plan with five steps. The harness asks, and Rahul approves.

Step one: look at how the website is organized. In progress. List the files, read index.html. Done.

Step two: create the contact form page. edit_file creates contact.html: File created. Done, with the evidence linked.

Step three: save each submitted message. The search finds no storage in this project.

The model asks Rahul: a simple file, or a database? A simple file. Then update_plan adds a new step.

The new step: create a file to store messages. edit_file creates messages.txt. Done.

Back to saving each message. edit_file updates contact.html. Done.

The context window fills, and older messages collapse into a summary. But the plan doesn't change. It survives.

Next, the thank-you note. edit_file, and done.

Last step: test the whole thing. The tests run, and one fails: message not saved when the name is empty.

The step stays in progress. The model fixes contact.html and runs the tests again. All tests passed. Now it's done, with the evidence linked.

And the final answer, with no tool call: The contact form is ready. It saves every message and shows a thank-you note. All tests pass.

Form page: yes. Saves every message: yes. Thank-you note: yes.

It's the same model as before. It didn't get smarter. It was given a way to keep the whole job in view.

## 10. Reality Check: Plans Are Not Magic

A quick reality check. Plans are useful, but they're not magic.

One: a plan can be wrong. If the model misunderstands the goal, it writes a neat plan for the wrong thing. That's why human review helps.

Two: a tick is not proof. The model can mark a step done when it isn't.

Three: small tasks don't need a plan. For a question like what port does the server use, a plan only slows things down.

Four: the model can drift from its own plan. A plan in the context makes that less likely, not impossible.

A plan doesn't make the agent right. It makes the agent's work visible, so both the agent and the human can catch mistakes earlier.

## 11. Conclusion and What's Next

Today we gave our agent something simple but powerful: a plan.

A plan is just a list of steps, written as plain text. The harness keeps it safe and shows it to the model on every call.

The agent works through it step by step, checks each step with real evidence, and changes the plan when reality turns out to be different.

And notice what stayed the same: the model, the harness and the loop. We only added one more piece of text.

But think about one of those steps. What if a single step is a huge job by itself, as big as the whole task we did today?

Could our agent hand that step over to another agent, and just wait for the result?

That's what we'll explore in the next lesson: agents working together.
