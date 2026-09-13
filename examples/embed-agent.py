#!/usr/bin/env python3
"""Embed the Hermes agent loop in your own Python — Chapter 12, task 4.

Run it from a Hermes checkout, which is the supported way to use Hermes as a library:

    git clone https://github.com/NousResearch/hermes-agent.git && cd hermes-agent
    uv sync
    uv run python /path/to/LearningHermes/examples/embed-agent.py

There is no published wheel: `pip install hermes-agent` is not the supported path, and a
script that assumes one will work on your machine and nowhere else.

Verified against the AIAgent surface in the Hermes source (`run_agent.py`,
`agent/turn_facade.py`) at v0.21.2. The four sections below are the four decisions you
actually make when you embed an agent, in the order you make them.
"""
from __future__ import annotations

import json
import os
import sys

try:
    from run_agent import AIAgent
except ImportError:
    sys.exit(
        "Could not import AIAgent.\n\n"
        "Run this from a Hermes checkout with its environment active:\n"
        "  cd hermes-agent && uv run python path/to/embed-agent.py\n"
    )


def one_shot() -> str:
    """`chat()` — the whole loop, one string back.

    chat() runs the full conversation loop internally: tool calls, retries, everything.
    You get the final text. Use it when your caller wants an answer, not a transcript.

    quiet_mode=True is not cosmetic. Without it the agent writes CLI spinners and
    progress indicators to your stdout, which is someone else's log file now.
    """
    agent = AIAgent(model=MODEL, quiet_mode=True)
    return agent.chat("What is 17 * 23? Reply with only the number.")


def scoped_tools() -> dict:
    """`enabled_toolsets` — least privilege, as a constructor argument.

    This is Chapter 05's lesson at the API boundary. An embedded agent inherits your
    process's credentials and filesystem, so the toolset is the blast radius. Two shapes:

        enabled_toolsets=["web"]        # allowlist: a minimal, locked-down agent
        disabled_toolsets=["terminal"]  # denylist: most capabilities, minus one

    Prefer the allowlist. A denylist silently grows whenever Hermes adds a toolset.
    """
    agent = AIAgent(model=MODEL, enabled_toolsets=["terminal"], quiet_mode=True)
    result = agent.run_conversation(
        user_message=f"How many files are directly inside {os.getcwd()}? Reply with only the number.",
        task_id="embed-demo-scoped",
    )
    return result


def multi_turn() -> str:
    """`conversation_history` — state is yours to hold.

    The library keeps no session for you: you pass `messages` from the previous result
    back in. That is a feature, not an omission — your web app already has a place to put
    conversation state, and it is not the agent's process memory.

    The agent copies the list internally, so your original is never mutated.
    """
    agent = AIAgent(model=MODEL, quiet_mode=True)
    first = agent.run_conversation("My name is Alice. Remember it.")
    second = agent.run_conversation(
        "What is my name? Reply with only the name.",
        conversation_history=first["messages"],
    )
    return second["final_response"]


def constrained() -> str:
    """`ephemeral_system_prompt` — behaviour without polluting your training data.

    An ephemeral prompt steers the turn but is NOT written to saved trajectories. That
    matters the moment you turn on save_trajectories=True to build a dataset: a prompt
    baked into every sample teaches the model your scaffolding instead of the task.
    """
    agent = AIAgent(
        model=MODEL,
        ephemeral_system_prompt=(
            "You are a terse SQL tutor. Answer in at most two sentences."
        ),
        quiet_mode=True,
    )
    return agent.chat("What does a LEFT JOIN do?")


MODEL = os.environ.get("EMBED_MODEL", "")  # empty = whatever your config resolves


def main() -> int:
    if "--list" in sys.argv:
        print("one-shot | scoped-tools | multi-turn | constrained")
        return 0

    print("== chat(): the whole loop, one string back")
    print(one_shot(), "\n")

    print("== enabled_toolsets: least privilege as a constructor argument")
    scoped = scoped_tools()
    print(scoped["final_response"])
    print(f"   (messages exchanged: {len(scoped['messages'])})\n")

    print("== conversation_history: multi-turn state is yours to hold")
    print(multi_turn(), "\n")

    print("== ephemeral_system_prompt: steer the turn, keep trajectories clean")
    print(constrained(), "\n")

    print("Inspect one turn's full message history to see the tool calls:")
    print(json.dumps(scoped["messages"][-2:], indent=2, default=str)[:800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
