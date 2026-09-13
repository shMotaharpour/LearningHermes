# `examples/agent-loop/` — the loop, from scratch

`miniagent.py` is a complete agent loop in ~120 lines of standard library Python. Chapter 01
uses it to make one argument: **the loop is small**, and almost everything a production
agent adds — Hermes included — is engineering around those forty lines rather than a
different idea.

```bash
python3 miniagent.py --demo        # scripted, offline, no API key, no cost
python3 -m unittest discover -s ../../tests -k agent_loop
```

To run it against a real model, point it at any OpenAI-compatible endpoint — `hermes serve`
(Chapter 12), OpenRouter, or a local server:

```bash
export AGENT_BASE_URL=https://openrouter.ai/api/v1
export AGENT_API_KEY=sk-...
export AGENT_MODEL=openai/gpt-4o-mini
python3 miniagent.py "how many lines are in notes.txt?"
```

It prints the trajectory to stderr, so you watch the loop happen rather than reading about
it.

## What to read, in order

1. **`run()`** — the loop. Ask the model; if it returned tool calls, execute them and
   append each result as a `role: "tool"` message; ask again. If it returned no tool calls,
   that is the answer. Forty lines.
2. **`SCHEMAS` next to `TOOLS`** — a tool is a JSON schema the model reads plus a function
   the loop calls. They live together because a schema that no longer matches its function
   is a bug the model cannot see.
3. **`_safe()`** — the model chooses the filename argument, so containment lives in the
   tool. `../../.ssh/id_rsa` is a normal-looking string.
4. **The transport seam** — `HttpTransport` vs `ScriptedTransport`. The loop never knows
   which it has, so every failure branch is testable offline and for free.

## The four things that make it an agent rather than a demo

The happy path is the easy part. These are the branches, and each one is pinned by a test
in `tests/test_agent_loop.py`:

| Situation | What the loop does | Why |
|---|---|---|
| Model invents a tool name | returns `error: no such tool 'x'. Available: ...` | Models recover from a named error. They cannot recover from a traceback. |
| Tool raises | returns `error: TypeError: ...` as the tool result | Same reason. A crash ends the run; a message starts the next turn. |
| Arguments are not valid JSON | error re-enters the conversation | The model wrote them, so the model is who must fix them. |
| Model never stops calling tools | cut off at `max_steps` | Termination is "the model chose to stop". Without a cap that is not a guarantee. |

## What it leaves out, deliberately

Streaming, parallel tool execution across turns, retries and provider failover, context
compression, approval gates, persistence, cost accounting, multi-agent delegation. Every
one of those is a chapter in this course, and every one of them is a modification of
`run()` — which is the argument for reading `run()` first.
