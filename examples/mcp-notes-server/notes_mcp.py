#!/usr/bin/env python3
"""A minimal MCP server over stdio. Chapter 11.

    python3 notes_mcp.py --selftest          # drive the protocol without an agent
    hermes mcp add notes --command python3 --args /abs/path/notes_mcp.py
    hermes mcp test notes

An MCP stdio server is a program that reads line-delimited JSON-RPC 2.0 from stdin and
writes responses to stdout. That is the entire transport. No SDK, no framework — this file
is standard library only, so nothing hides what the protocol actually requires.

It stores notes in a JSON file and exposes three tools: note_add, note_list, note_search.

Verified against the handshake Hermes sends (tools/mcp_tool_transport.py at v0.21.2):
protocol version 2025-03-26, then `initialize` -> `notifications/initialized` ->
`tools/list` -> `tools/call`.

FOUR RULES, and three of them are how a first MCP server breaks:

1. STDOUT IS THE PROTOCOL. One stray print() and the transport is corrupt — the client
   reads your debug line where a JSON-RPC frame should be. All logging goes to stderr.
2. NEVER REPLY TO A NOTIFICATION. A JSON-RPC message with no "id" is a notification. Send
   a response to `notifications/initialized` and you have put an extra frame on the wire
   that the client will read as the answer to its NEXT request. Every later reply is off
   by one, and the symptom looks like nonsense rather than a protocol error.
3. DECLARE capabilities.tools. Per the spec, a client may skip `tools/list` entirely when
   `InitializeResult.capabilities.tools` is absent. Omit it and your tools simply never
   appear, with no error anywhere.
4. A TOOL FAILURE IS NOT A PROTOCOL FAILURE. A tool that cannot do its job returns a
   normal result with isError: true, so the model reads the reason and recovers. A
   JSON-RPC error means the REQUEST was malformed. Confusing the two turns a recoverable
   situation into a dead connection — the same lesson as Chapter 01's loop.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {"name": "notes", "version": "1.0.0"}

STORE = Path(os.environ.get("NOTES_MCP_STORE", Path.home() / ".hermes" / "notes-mcp.json"))

TOOLS = [
    {
        "name": "note_add",
        "description": "Save a short note. Returns the note's id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The note body."},
                "tag": {"type": "string", "description": "Optional single-word tag."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "note_list",
        "description": "List saved notes, newest first. Optionally filter by tag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string"},
                "limit": {"type": "integer", "description": "Default 20."},
            },
        },
    },
    {
        "name": "note_search",
        "description": "Find notes containing a substring, case-insensitive.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]


def log(message: str) -> None:
    """Rule 1: diagnostics go to stderr, never stdout."""
    print(f"[notes-mcp] {message}", file=sys.stderr, flush=True)


# --- storage -------------------------------------------------------------------------

def load() -> list[dict]:
    if not STORE.is_file():
        return []
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError) as exc:
        log(f"store unreadable ({exc}); starting empty")
        return []


def save(notes: list[dict]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(notes, indent=2), encoding="utf-8")


# --- tools ---------------------------------------------------------------------------

def note_add(text: str, tag: str = "") -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("text must not be empty")
    notes = load()
    note = {"id": (max((n["id"] for n in notes), default=0) + 1),
            "text": text, "tag": (tag or "").strip()}
    notes.append(note)
    save(notes)
    return f"saved note {note['id']}"


def note_list(tag: str = "", limit: int = 20) -> str:
    notes = load()
    if tag:
        notes = [n for n in notes if n.get("tag") == tag]
    notes = list(reversed(notes))[:max(1, int(limit))]
    if not notes:
        return "no notes"
    return "\n".join(f"{n['id']}: {n['text']}" + (f"  [{n['tag']}]" if n.get("tag") else "")
                     for n in notes)


def note_search(query: str) -> str:
    query = (query or "").strip().lower()
    if not query:
        raise ValueError("query must not be empty")
    hits = [n for n in load() if query in n["text"].lower()]
    if not hits:
        return f"no notes matching {query!r}"
    return "\n".join(f"{n['id']}: {n['text']}" for n in hits)


HANDLERS = {"note_add": note_add, "note_list": note_list, "note_search": note_search}


# --- protocol ------------------------------------------------------------------------

def ok(request_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def err(request_id, code: int, message: str) -> dict:
    """A JSON-RPC error means the REQUEST was wrong. See rule 4."""
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def call_tool(name: str, arguments: dict) -> dict:
    """Rule 4: a failing tool returns a RESULT carrying isError, not a JSON-RPC error."""
    handler = HANDLERS.get(name)
    if handler is None:
        return {"content": [{"type": "text",
                             "text": f"no such tool: {name}. Available: {', '.join(HANDLERS)}"}],
                "isError": True}
    try:
        text = handler(**(arguments or {}))
    except TypeError as exc:
        return {"content": [{"type": "text", "text": f"bad arguments: {exc}"}], "isError": True}
    except Exception as exc:
        return {"content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                "isError": True}
    return {"content": [{"type": "text", "text": text}], "isError": False}


def handle(message: dict):
    """Return a response dict, or None when nothing must be sent."""
    request_id = message.get("id")
    method = message.get("method")

    # Rule 2: no "id" means a notification. Answer nothing, ever.
    if request_id is None:
        log(f"notification: {method}")
        return None

    if method == "initialize":
        return ok(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            # Rule 3: without this key a client may never call tools/list.
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        })
    if method == "tools/list":
        return ok(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        return ok(request_id, call_tool(params.get("name", ""), params.get("arguments") or {}))
    if method == "ping":
        return ok(request_id, {})
    return err(request_id, -32601, f"method not found: {method}")


def serve(stdin=None, stdout=None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    log(f"ready; store={STORE}")
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            # Parse errors carry a null id: we never learned which request this was.
            stdout.write(json.dumps(err(None, -32700, "parse error")) + "\n")
            stdout.flush()
            continue
        response = handle(message)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
    return 0


def selftest() -> int:
    """Drive the whole protocol in-process: no agent, no Hermes, no network."""
    import tempfile
    global STORE
    with tempfile.TemporaryDirectory() as tmp:
        STORE = Path(tmp) / "notes.json"
        script = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                        "clientInfo": {"name": "selftest", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "note_add", "arguments": {"text": "ship the chapter",
                                                          "tag": "work"}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "note_search", "arguments": {"query": "ship"}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
             "params": {"name": "note_add", "arguments": {"text": ""}}},
            {"jsonrpc": "2.0", "id": 6, "method": "nonsense/method"},
        ]
        replied = 0
        for message in script:
            response = handle(message)
            label = message.get("method")
            if response is None:
                print(f"  {label}: (no reply — correct, it is a notification)")
                continue
            replied += 1
            if "error" in response:
                print(f"  {label}: JSON-RPC error {response['error']['code']}"
                      f" — {response['error']['message']}")
            elif label == "tools/list":
                print(f"  {label}: {len(response['result']['tools'])} tools")
            elif label == "tools/call":
                result = response["result"]
                flag = "isError" if result["isError"] else "ok"
                print(f"  {label}: [{flag}] {result['content'][0]['text']}")
            else:
                print(f"  {label}: protocol {response['result']['protocolVersion']}, "
                      f"tools capability declared: "
                      f"{'tools' in response['result']['capabilities']}")
        print(f"\n{replied} replies for {len(script)} messages "
              f"(one message was a notification and correctly got none).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--selftest", action="store_true",
                        help="exercise the protocol in-process and exit")
    args = parser.parse_args()
    return selftest() if args.selftest else serve()


if __name__ == "__main__":
    sys.exit(main())
