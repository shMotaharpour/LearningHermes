#!/usr/bin/env python3
"""A complete agent loop in ~120 lines. Chapter 01.

    python3 miniagent.py --demo                      # offline, scripted, no API key
    python3 miniagent.py "how many lines in notes.txt?"   # against a real model

The point of this file is how SMALL the loop is. `run()` below is about forty lines, and
it is the whole idea: ask the model, run whatever tools it asks for, hand the results back,
ask again. Everything else in this file — and most of what Hermes adds on top — is
engineering around those forty lines: safety, budgets, error handling, observability.

Standard library only. `urllib.request` talks to any OpenAI-compatible endpoint, which
includes `hermes serve` (Chapter 12), OpenRouter, and most local servers.

    export AGENT_BASE_URL=https://openrouter.ai/api/v1
    export AGENT_API_KEY=sk-...
    export AGENT_MODEL=openai/gpt-4o-mini
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

# --- tools ---------------------------------------------------------------------------
#
# A tool is two things: a JSON schema the model reads, and a Python function the loop
# calls. Keeping them next to each other is the only way they stay in sync — a schema that
# describes a function it no longer matches is a bug the model cannot see.

WORKDIR = Path.cwd()


def _safe(name: str) -> Path:
    """Resolve `name` inside WORKDIR, or refuse.

    The model chooses this argument, and the model can be talked into things by whatever it
    read a moment ago. `../../.ssh/id_rsa` is a normal-looking string. Containment belongs
    here, in the tool, because it is the only place that cannot be argued with.
    """
    target = (WORKDIR / name).resolve()
    if target != WORKDIR.resolve() and WORKDIR.resolve() not in target.parents:
        raise ValueError(f"refusing to touch {name!r}: outside the working directory")
    return target


def list_files() -> str:
    entries = sorted(p.name for p in WORKDIR.iterdir() if p.is_file())
    return "\n".join(entries) if entries else "(no files)"


def read_file(name: str, max_bytes: int = 4000) -> str:
    path = _safe(name)
    if not path.is_file():
        return f"no such file: {name}"
    text = path.read_text(encoding="utf-8", errors="replace")
    # Truncation is not politeness. An untruncated read is an unbounded amount of someone
    # else's text entering your context window and your invoice.
    return text[:max_bytes] + ("\n...[truncated]" if len(text) > max_bytes else "")


def count_lines(name: str) -> str:
    path = _safe(name)
    if not path.is_file():
        return f"no such file: {name}"
    return str(len(path.read_text(encoding="utf-8", errors="replace").splitlines()))


TOOLS: dict[str, Callable[..., str]] = {
    "list_files": list_files,
    "read_file": read_file,
    "count_lines": count_lines,
}

SCHEMAS = [
    {"type": "function", "function": {
        "name": "list_files",
        "description": "List the files in the working directory.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a UTF-8 text file from the working directory.",
        "parameters": {"type": "object",
                       "properties": {"name": {"type": "string"}},
                       "required": ["name"]},
    }},
    {"type": "function", "function": {
        "name": "count_lines",
        "description": "Count the lines in a text file in the working directory.",
        "parameters": {"type": "object",
                       "properties": {"name": {"type": "string"}},
                       "required": ["name"]},
    }},
]

SYSTEM = (
    "You are a terse assistant with file tools. Use them rather than guessing. "
    "When you have the answer, state it plainly and stop calling tools."
)


# --- transport -----------------------------------------------------------------------
#
# One seam, and it is what makes the loop testable. The loop never knows whether an answer
# came from a model or a fixture, so every branch below — budget exhaustion, a tool that
# raises, a hallucinated tool name — can be tested offline, deterministically, for free.


class HttpTransport:
    """POST /chat/completions against any OpenAI-compatible endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model

    def __call__(self, messages: list[dict]) -> dict:
        body = json.dumps({"model": self.model, "messages": messages,
                           "tools": SCHEMAS}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.load(response)
        return payload["choices"][0]["message"]


class ScriptedTransport:
    """Replays a fixed list of assistant messages. Raises if the loop asks for more."""

    def __init__(self, replies: list[dict]):
        self.replies, self.seen = list(replies), []

    def __call__(self, messages: list[dict]) -> dict:
        self.seen.append(list(messages))
        if not self.replies:
            raise AssertionError("the loop asked for more turns than the script provides")
        return self.replies.pop(0)


# --- the loop ------------------------------------------------------------------------


def run(prompt: str, transport, max_steps: int = 8, trace=None) -> dict:
    """Ask, act, repeat. This is the whole agent.

    Returns {"answer", "steps", "messages"}.
    """
    messages: list[dict] = [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": prompt}]

    for step in range(1, max_steps + 1):
        message = transport(messages)
        messages.append(message)
        calls = message.get("tool_calls") or []

        # Termination: the model stopped asking for tools. That is the ONLY natural exit —
        # which is why the step budget below is not optional.
        if not calls:
            return {"answer": message.get("content") or "", "steps": step,
                    "messages": messages}

        for call in calls:
            name = call["function"]["name"]
            raw = call["function"].get("arguments") or "{}"
            if trace:
                trace(f"  step {step}: {name}({raw})")
            try:
                args = json.loads(raw)
                if not isinstance(args, dict):
                    raise ValueError("arguments must be a JSON object")
                result = TOOLS[name](**args)
            except KeyError:
                # The model invented a tool. Telling it so is more useful than crashing:
                # models recover from a named error and cannot recover from a traceback.
                result = f"error: no such tool {name!r}. Available: {', '.join(TOOLS)}"
            except Exception as exc:
                result = f"error: {type(exc).__name__}: {exc}"
            if trace:
                trace(f"    -> {result.splitlines()[0][:80] if result else '(empty)'}")
            # The result re-enters the conversation as a message the model can read. This
            # is the whole trick, and it is also why every iteration costs more than the
            # last: the transcript only grows.
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "name": name, "content": result})

    # Budget exhausted. A model that keeps calling tools will do so forever; an agent
    # without a cap is an unbounded bill with a plausible explanation.
    return {"answer": f"stopped after {max_steps} steps without a final answer",
            "steps": max_steps, "messages": messages}


# --- demo ----------------------------------------------------------------------------

DEMO_SCRIPT = [
    {"role": "assistant", "content": None, "tool_calls": [
        {"id": "c1", "type": "function",
         "function": {"name": "list_files", "arguments": "{}"}}]},
    {"role": "assistant", "content": None, "tool_calls": [
        {"id": "c2", "type": "function",
         "function": {"name": "count_lines", "arguments": '{"name": "notes.txt"}'}}]},
    {"role": "assistant", "content": "notes.txt has 3 lines."},
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt", nargs="?", help="what to ask the agent")
    parser.add_argument("--demo", action="store_true",
                        help="run the scripted transcript offline — no API key, no cost")
    parser.add_argument("--max-steps", type=int, default=8)
    args = parser.parse_args()

    trace = lambda line: print(line, file=sys.stderr)  # noqa: E731

    if args.demo:
        import tempfile
        global WORKDIR
        with tempfile.TemporaryDirectory() as tmp:
            WORKDIR = Path(tmp)
            (WORKDIR / "notes.txt").write_text("a\nb\nc\n", encoding="utf-8")
            print("loop (scripted — the model's turns are fixtures):", file=sys.stderr)
            out = run("how many lines in notes.txt?", ScriptedTransport(DEMO_SCRIPT),
                      max_steps=args.max_steps, trace=trace)
        print(f"\nanswer: {out['answer']}")
        print(f"steps: {out['steps']}, messages: {len(out['messages'])}")
        return 0

    if not args.prompt:
        parser.error("give a prompt, or use --demo")
    base_url = os.environ.get("AGENT_BASE_URL")
    api_key = os.environ.get("AGENT_API_KEY")
    model = os.environ.get("AGENT_MODEL")
    if not (base_url and api_key and model):
        print("set AGENT_BASE_URL, AGENT_API_KEY and AGENT_MODEL — or use --demo.",
              file=sys.stderr)
        return 2

    try:
        out = run(args.prompt, HttpTransport(base_url, api_key, model),
                  max_steps=args.max_steps, trace=trace)
    except urllib.error.HTTPError as exc:
        print(f"provider returned {exc.code}: {exc.read()[:300].decode(errors='replace')}",
              file=sys.stderr)
        return 1
    print(f"\nanswer: {out['answer']}")
    print(f"steps: {out['steps']}, messages: {len(out['messages'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
