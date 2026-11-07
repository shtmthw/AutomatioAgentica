# What is Agentic AI?

<!-- Narration script (English): one paragraph per narration beat. -->

## 01. Introduction

Imagine you're running a program, and suddenly an error appears.

You ask an AI: what does this error mean?

The AI explains nicely where the problem might be.

But the job of actually fixing it is still left to you.

Now picture the same situation a little differently.

You tell an AI agent: find the error, understand its cause, and fix it.

The agent opens the project's files by itself and runs commands.

It hits an error, fixes the code based on it, and then checks again.

The first AI gives us information. The second one takes action itself to reach the goal.

That difference is the core idea of Agentic AI. But how is this actually possible? Let's start from the very beginning.

## 02. What is an AI model?

Before we understand agents, we need to understand what an AI model really is.

An AI model is a program that has learned from a huge amount of data.

Models that work with language are called Large Language Models, or LLMs for short.

By reading countless texts, they've learned how people ask questions, explain things, and give answers.

The way it works is very simple. You give it some text, which is called the input.

The model reads that input and tries to understand it.

Everything the model can see at once is called its context.

Then the model generates new text and gives it back. That's the output.

GPT, Claude and Gemini are all examples of large language models.

But notice one thing. On its own, a model only produces text. It doesn't open files or run programs by itself.

So where does the power to actually do things come from?

## 03. What is an AI agent?

This is where the AI agent comes in.

An AI agent is a system that uses an AI model to work toward a goal.

It makes decisions, acts using tools, looks at the results, and then decides what to do next.

An agent has five basic parts. Let's look at them one by one.

First, the goal. What are we actually trying to achieve?

Second, the model. This is the agent's thinking part, which reasons and makes decisions.

Third, tools. Through them, the agent can work with outside systems.

Fourth, the environment. The world or system the agent works inside, like your computer or a project.

And fifth, feedback. The information that comes back after an action.

Notice that the model is just one part of the whole system. An AI model on its own and a complete AI agent are not the same thing.

## 04. Chatbot vs AI agent

Now let's compare. A regular chatbot, and an AI agent.

A chatbot receives a question.

It generates an answer to that question.

And it hands the answer back to you. That's it, job done.

An agent, on the other hand, receives a goal.

It works out what needs to be done to reach that goal.

It picks the right tool for the job.

Then it performs the actual work.

It observes the result of that work.

And it keeps going like this until the goal is reached, or until it needs a human's help.

One important point. You can talk to an agent through a chat window too.

So the difference isn't how it looks. The difference is whether the system can take action itself and move toward a goal.

## 05. How does an agent work?

Now for the most important part. How does an agent actually work?

At its core is a cycle called the agent loop.

Step one: receive the goal. The user gives the agent an instruction.

For example: tell me whether it will rain in Delhi tomorrow.

Step two: decide. The model decides what the next action should be.

Here it thinks: let's check a weather website.

Step three: act. The agent uses a tool to do that work. Here, it opens the website with a browser.

Step four: observe. The tool returns a result. But it turns out the page didn't even load.

Step five: evaluate. The agent checks: has the goal been reached? No, not yet.

So the loop starts again.

This time, the agent decides to try a different website.

The browser works again. And this time the result comes back: an eighty percent chance of rain.

Checking again, the goal has been reached. So the agent gives you the answer.

Notice that the agent didn't know every step from the start. After each result, it adjusted its next decision.

That's the agent loop. Decide, act, observe, evaluate, and if needed, again.

## 06. Why agents need tools

We keep talking about tools. But why does an agent need them?

Because a model on its own can only produce text. To work with the outside world, it needs tools.

Take the filesystem. With it, files can be read, new files created, and existing files changed.

With a terminal, commands and programs can be run.

With a browser, information can be fetched from websites.

With an API, it can talk to another service, like a weather or maps service.

And with a database, structured information can be searched and updated.

There's an important distinction here.

The model decides which tool is needed and what should be done. It only sends a request.

The tool does the actual work. Then it sends the result back to the model.

Put simply, the model is the brain, and the tools are the hands.

## 07. Real example: fixing a bug

Now let's see everything together in a real example.

The user tells the agent: the program is crashing, find the cause and fix it.

The program is a small calculator app that computes the average of some numbers.

First, the agent looks at the list of files in the project.

From the names, the calculation seems to live in stats.py. So the agent opens it and reads the code.

Then it runs the program's tests in the terminal to see the problem for itself.

A test fails. The error is ZeroDivisionError, a division by zero.

The agent looks closely at the error. When the list has no numbers, the program tries to divide by zero.

So it makes a small change to the code. If the list is empty, return zero right away.

Then it runs the tests again.

This time all the tests pass. The agent checks and confirms the goal is reached.

Finally, the agent reports what the problem was, what it changed, and that everything works now.

See? Goal, model, tools, environment and feedback, all five parts worked together here. And at every step, the agent loop went around again.

## 08. Reality check: not magic

But one thing is important to remember. AI agents are powerful, but they're not magic.

An agent can make wrong decisions.

It can use tools incorrectly.

It can even change, or delete, important files or data.

Sometimes it repeats the same action and gets stuck in a loop.

That's why an agent needs permissions. It needs safeguards. And it needs human oversight.

We are the ones who set the boundary of what an agent can and cannot do.

Remember: the more power you give an AI, the greater your responsibility to keep that power under control.

## 09. Conclusion

Now you understand what an AI agent really is, how it works, and how it differs from a regular chatbot.

But so far, we've only seen the most basic ideas of Agentic AI.

In the upcoming lessons, we'll go much deeper.

We'll see how an agent's architecture works, along with tool integration, context management, memory, planning, and how agentic systems are built.

And that's not all: we'll also learn to build websites and apps ourselves.

This was just the beginning of our journey into Agentic AI.
