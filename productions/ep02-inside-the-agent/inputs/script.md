# Inside an AI Agent: Who Actually Runs the Loop?

<!-- Narration script (English): one paragraph per narration beat. Episode 02. -->

## 01. Who Runs the Loop?

In the last lesson, we learned what an AI agent is, and we saw its heart: the agent loop.

An agent receives a goal. It decides what to do next, and acts using tools.

Then it observes the result, and evaluates: is the goal reached yet?

If not, it repeats the loop, again and again, until the job is done.

Along the way, we said things like: the agent reads files, and the agent runs commands.

But we also learned something else in that lesson. An AI model only produces text.

So let's zoom in on the model. Say it needs to read a file.

It can write the words "read the file". But words alone can't open anything.

A model only produces text. So who opens the file? Who runs the command?

That's our question for today. We're going to open up the agent and look inside.

## 02. The Model Only Produces Text

Let's start with two simple facts about the model.

Fact one: text in, text out. You send the model some text, and it sends back new text. One round trip like this is called a call.

That's all a model can do. It has no hands, no eyes, and no connection to your computer.

Files, the terminal, the internet: they're all on the other side of a wall. The model can't reach any of them.

Fact two: the model doesn't remember anything by itself.

Let's test it. In the first call, we send: My name is Rahul.

The model replies: Hello, Rahul!

Then that call ends, and the model keeps nothing. It starts fresh, like a blank page.

Now we make a second call, completely separate. We ask: What is my name?

And the model says: I don't know.

Each call is independent. The model only knows what's in the text it receives right now.

Unless someone gives it the earlier conversation again, it has no idea what happened before.

But wait. When you chat with ChatGPT or Claude, they do remember what you said earlier. So how does that work?

## 03. Meet the Harness

The answer is the harness.

A harness is the ordinary program built around the model. It runs the agent loop, talks to the model, and actually performs the actions.

Here's a simple way to picture it.

Imagine a decision-maker in a closed room. There are no doors, only a small slot for passing paper.

Outside the room sits an assistant. The assistant slides in a note with the full situation so far.

The decision-maker reads it and writes back: Open the file named config.txt and tell me what it says.

The assistant opens the file, writes down what it says, and slides the whole updated note back in.

The decision-maker is the model. The assistant is the harness. And the file? That's a tool.

So what does the harness do? It stores the conversation, and sends it to the model.

It reads the model's reply, executes the tools the model asks for, and sends the results back.

It decides when to stop. And it enforces permissions and limits.

The model decides. The harness does the work.

So when we say AI agent, we really mean the model, the harness and the tools, working together.

That's why, as we said last time, a model on its own is not an agent.

## 04. The Conversation Is a List of Messages

So how does the harness make the model remember? With a list of messages.

The harness stores the whole conversation as a list. Each item in the list is a message, and every message has a role.

The first role is system. These are instructions from the developer that set the agent's behaviour and rules.

For example: You are a helpful coding agent. Ask before deleting any file. This message is often called the system prompt.

The second role is user. That's what the person asks. For example: My name is Rahul.

The third role is assistant. That's what the model replies. For example: Hello, Rahul!

And the fourth role is tool: results that come back from tools. We'll see these in action soon.

Now let's replay our memory test, the right way.

The list holds the system message, My name is Rahul, Hello Rahul, and the new question: What is my name?

This time, the harness sends the entire list to the model, as one bundle.

And the model replies: Your name is Rahul.

The harness adds this reply to the bottom of the list, as a new assistant message.

Here's the key idea. On every single call, the harness sends the whole conversation to the model again.

That's how the model seems to remember. The memory lives in the harness, not in the model.

And notice: with every call, the bundle gets a little bigger. Call one, call two, call three. Keep that in mind.

## 05. How the Model Learns About Tools

But there's another puzzle. The model can't see the computer. So how does it know which tools exist?

The answer: the harness tells it. Along with the messages, it sends a short description of every available tool.

A tool description has three parts. First, a name: read_file.

Second, a description: Reads the text inside a file.

And the third part: its parameters, the inputs it needs. Here there's just one: path, which file to read.

The harness can offer more tools. run_command runs a command in the terminal. edit_file changes the text of a file.

All these descriptions travel to the model together with the message list, on every call.

Notice something important. The model only sees these descriptions. It never sees the tool's actual program.

So the description matters a lot. If it's vague, like "does file stuff", the model can't be sure when to use it.

But a clear description, like "reads the text inside a file", lets the model pick the right tool with confidence.

Even then, the model can still make mistakes. It can pick the wrong tool, or give the wrong input.

## 06. Tool Calling, Step by Step

Now for the most important part of this lesson: tool calling. Let's go through it slowly, step by step.

Here's our task. The user asks: What port does the server use in config.txt?

Step one. The harness sends the system message, the user's question, and the tool descriptions to the model.

Step two. The model doesn't answer yet. It replies with a tool call: read_file, with the path config.txt.

Let's pause here. This tool call is only a request, written as text. Nothing has happened yet.

The harness adds this request to the list, as an assistant message.

Step three. The harness reads the reply, and sees a tool request.

Step four. The harness checks permission. Reading this file is allowed.

Step five. The harness executes the tool. The file opens, and its text comes out.

Step six. The harness adds the result to the list, as a tool message: port = 8080, host = localhost.

Step seven. The harness calls the model again, with the whole updated list.

Step eight. This time, the model replies with normal text: The server uses port 8080.

Step nine. If the model's reply contains no tool request, the harness treats it as the final answer and the loop stops.

Now let's map this onto the agent loop.

Decide: the model writes the tool request. Act: the harness executes the tool.

Observe: the result is added as a tool message. Evaluate: on the next call, the model reads the result and decides if more work is needed.

The model decides. The harness does.

The agent loop isn't magic. It's a simple program loop: ask the model, do what it requests, add the result, and ask again.

And if something goes wrong? Say config.txt doesn't exist.

The harness doesn't crash. It adds a tool message: Error: config.txt not found.

On the next call, the model reads that error, and requests another tool to search for the file. Errors are feedback too.

## 07. The Context Window

We've seen that the list grows with every call. But it can't grow forever.

Everything sent to the model in one call has to fit within a fixed limit: the system message, all the messages, the tool descriptions, and the tool results.

This limit is called the context window.

It's measured in tokens. A token is a small piece of text, often just part of a word.

Think of it like a desk of fixed size. Every paper the model needs must fit on the desk at the same time.

As the agent works, messages pile up, and the desk fills.

Then one huge tool result arrives. Say the agent reads a very large file. Suddenly, most of the desk is gone.

And soon, the desk is full.

What happens then? First, the request can simply fail.

Second, the harness can remove or shorten older messages to make room.

Third, it can replace older messages with a short summary.

There's also a cost. A longer context generally makes each call slower and more expensive.

So deciding what stays on the desk, and what goes, is one of the hardest problems in building agents.

It's called context management. And it's the topic of our next lesson.

## 08. When Does the Loop Stop?

A loop that never ends would be a problem. So how does the agent loop stop? There are four common ways.

One: the normal stop. The model replies without any tool request, so the task is considered finished.

Two: a step limit. Each trip around the loop is called an iteration. The harness allows only a maximum number of iterations, for example 20.

When the counter reaches the limit, the loop halts. This protects against a loop that never ends.

Three: human approval. Before a risky tool, like deleting a file or running a dangerous command, the harness pauses and asks you: allow this action?

Four: the model asks a question. If information is missing, the model replies with a question instead of guessing, and the loop waits for your answer.

Remember from the last lesson: agents are not magic. These safeguards are written into the harness by its developer. Human oversight is a deliberate part of the design.

## 09. The Bug-Fixing Agent, From the Inside

Now let's put it all together. Remember the bug-fixing agent from the last lesson? Let's replay it, this time at the level of messages.

The user writes: The program is crashing. Find the bug and fix it.

Call one. The model decides to run the tests first. It requests run_command: run tests.

The harness runs them. Tool result: Test failed, wrong result in total().

Call two. The model asks to read the file math_utils.py.

The harness reads it, and adds the code to the list as a tool message.

Call three. The model has spotted the bug. It requests edit_file on math_utils.py, with the fix.

The harness makes the change. Tool result: File updated successfully.

Call four. The model wants to check its work. It requests run_command: run tests, again.

Tool result: All tests passed.

Call five. This time there's no tool request, just a final message: Bug fixed. total() was adding the numbers incorrectly.

The harness shows this answer to the user, and the loop goes quiet.

Five calls. And on every single one, the model received the whole history again. That's why the context keeps growing.

## 10. Conclusion and What's Next

Today we looked inside an agent.

We saw that the model doesn't actually do any work by itself. It only makes decisions. The real work is done by the harness.

And the whole conversation is sent to the model again, from the start, every single time.

But one big problem is still left. The context window is limited.

The more work an agent does, the more messages pile up. And at some point, it runs out of space.

So how does an agent finish big tasks? How does it remember what's important, and let go of what isn't?

That's exactly what we'll learn in the next lesson: Context Management and Memory.
