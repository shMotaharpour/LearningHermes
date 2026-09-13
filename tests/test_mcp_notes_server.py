"""Tests for examples/mcp-notes-server/notes_mcp.py — the MCP server Chapter 11 writes.

Two layers, deliberately:

* in-process tests over handle() for the protocol rules and the tool behaviour;
* a subprocess test that speaks real line-delimited JSON-RPC over a real pipe, because
  the three ways a first MCP server breaks (stdout pollution, replying to a notification,
  a missing tools capability) are all invisible to an in-process test.

No agent, no Hermes, no network.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SERVER = (Path(__file__).resolve().parents[1] / "examples" / "mcp-notes-server"
          / "notes_mcp.py")

_spec = importlib.util.spec_from_file_location("notes_mcp", SERVER)
notes = importlib.util.module_from_spec(_spec)
sys.modules["notes_mcp"] = notes
_spec.loader.exec_module(notes)


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        original = notes.STORE
        notes.STORE = Path(self.temp.name) / "notes.json"
        self.addCleanup(lambda: setattr(notes, "STORE", original))


class ProtocolRuleTests(StoreTestCase):
    def test_notification_gets_no_reply(self):
        """Rule 2. An extra frame here desynchronises every later response."""
        self.assertIsNone(notes.handle(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertIsNone(notes.handle({"jsonrpc": "2.0", "method": "anything"}))

    def test_initialize_declares_the_tools_capability(self):
        """Rule 3. Without this a client may never call tools/list, silently."""
        result = notes.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})["result"]
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["protocolVersion"], notes.PROTOCOL_VERSION)
        self.assertIn("name", result["serverInfo"])

    def test_initialize_answers_the_protocol_version_hermes_sends(self):
        self.assertEqual(notes.PROTOCOL_VERSION, "2025-03-26")

    def test_unknown_method_is_a_jsonrpc_error(self):
        response = notes.handle({"jsonrpc": "2.0", "id": 9, "method": "nope"})
        self.assertEqual(response["error"]["code"], -32601)
        self.assertNotIn("result", response)

    def test_every_response_echoes_its_request_id(self):
        for method in ("initialize", "tools/list", "ping"):
            response = notes.handle({"jsonrpc": "2.0", "id": 77, "method": method})
            self.assertEqual(response["id"], 77, method)
            self.assertEqual(response["jsonrpc"], "2.0")


class ToolErrorTests(StoreTestCase):
    """Rule 4: a tool failure is a RESULT with isError, not a JSON-RPC error."""

    def call(self, name, arguments=None):
        return notes.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": name, "arguments": arguments or {}}})

    def test_failing_tool_returns_a_result_not_an_error(self):
        response = self.call("note_add", {"text": "   "})
        self.assertNotIn("error", response)
        self.assertTrue(response["result"]["isError"])
        self.assertIn("must not be empty", response["result"]["content"][0]["text"])

    def test_unknown_tool_is_a_result_and_names_the_alternatives(self):
        response = self.call("note_delete")
        self.assertNotIn("error", response)
        self.assertTrue(response["result"]["isError"])
        text = response["result"]["content"][0]["text"]
        self.assertIn("no such tool", text)
        self.assertIn("note_add", text)

    def test_bad_argument_names_are_reported_usefully(self):
        response = self.call("note_add", {"body": "wrong key"})
        self.assertTrue(response["result"]["isError"])
        self.assertIn("bad arguments", response["result"]["content"][0]["text"])

    def test_successful_call_is_not_flagged(self):
        response = self.call("note_add", {"text": "hello"})
        self.assertFalse(response["result"]["isError"])

    def test_content_is_always_a_list_of_typed_blocks(self):
        for response in (self.call("note_add", {"text": "x"}),
                         self.call("note_add", {"text": ""}),
                         self.call("nope")):
            content = response["result"]["content"]
            self.assertIsInstance(content, list)
            self.assertEqual(content[0]["type"], "text")
            self.assertIsInstance(content[0]["text"], str)


class SchemaTests(unittest.TestCase):
    def test_every_advertised_tool_has_a_handler(self):
        self.assertEqual({t["name"] for t in notes.TOOLS}, set(notes.HANDLERS))

    def test_schemas_are_well_formed_and_described(self):
        for tool in notes.TOOLS:
            self.assertTrue(tool["description"], tool["name"])
            self.assertEqual(tool["inputSchema"]["type"], "object")

    def test_required_and_declared_properties_are_real_arguments(self):
        import inspect
        for tool in notes.TOOLS:
            signature = inspect.signature(notes.HANDLERS[tool["name"]])
            schema = tool["inputSchema"]
            for name in schema.get("required", []):
                self.assertIn(name, signature.parameters, f"{tool['name']}.{name}")
            for name in schema.get("properties", {}):
                self.assertIn(name, signature.parameters, f"{tool['name']}.{name}")

    def test_required_arguments_have_no_default(self):
        """If it has a default it is optional, and the schema is lying."""
        import inspect
        for tool in notes.TOOLS:
            signature = inspect.signature(notes.HANDLERS[tool["name"]])
            for name in tool["inputSchema"].get("required", []):
                self.assertIs(signature.parameters[name].default,
                              inspect.Parameter.empty, f"{tool['name']}.{name}")


class ToolBehaviourTests(StoreTestCase):
    def test_add_then_list_then_search(self):
        notes.note_add("buy milk", "home")
        notes.note_add("ship chapter 11", "work")
        listed = notes.note_list()
        self.assertIn("ship chapter 11", listed)
        self.assertIn("buy milk", listed)
        self.assertEqual(notes.note_search("milk").count("\n"), 0)
        self.assertIn("buy milk", notes.note_search("MILK"))

    def test_list_is_newest_first(self):
        notes.note_add("first")
        notes.note_add("second")
        self.assertLess(notes.note_list().index("second"), notes.note_list().index("first"))

    def test_tag_filter_and_limit(self):
        notes.note_add("a", "work")
        notes.note_add("b", "home")
        self.assertNotIn("b", notes.note_list(tag="work"))
        self.assertEqual(len(notes.note_list(limit=1).splitlines()), 1)

    def test_empty_results_are_words_not_silence(self):
        self.assertEqual(notes.note_list(), "no notes")
        self.assertIn("no notes matching", notes.note_search("absent"))

    def test_ids_do_not_collide_after_a_reload(self):
        notes.note_add("one")
        notes.note_add("two")
        self.assertEqual(sorted(n["id"] for n in notes.load()), [1, 2])

    def test_a_corrupt_store_does_not_take_the_server_down(self):
        notes.STORE.parent.mkdir(parents=True, exist_ok=True)
        notes.STORE.write_text("{not json", encoding="utf-8")
        self.assertEqual(notes.load(), [])
        self.assertIn("saved note", notes.note_add("recovered"))


class StdioTests(unittest.TestCase):
    """The real thing: a subprocess, a real pipe, line-delimited JSON-RPC.

    This is the layer that catches stdout pollution, which no in-process test can see.
    """

    def converse(self, messages):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"PATH": "/usr/bin:/bin", "NOTES_MCP_STORE": str(Path(tmp) / "n.json")}
            proc = subprocess.run(
                [sys.executable, str(SERVER)],
                input="".join(json.dumps(m) + "\n" for m in messages),
                capture_output=True, text=True, timeout=60, env=env,
            )
        return proc

    def test_a_full_session_over_a_real_pipe(self):
        proc = self.converse([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "note_add", "arguments": {"text": "over the wire"}}},
        ])
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        # Four messages in, one of them a notification -> exactly three frames out.
        self.assertEqual(len(lines), 3, proc.stdout + proc.stderr)
        responses = [json.loads(ln) for ln in lines]
        self.assertEqual([r["id"] for r in responses], [1, 2, 3])
        self.assertEqual(len(responses[1]["result"]["tools"]), 3)
        self.assertFalse(responses[2]["result"]["isError"])

    def test_stdout_carries_nothing_but_json(self):
        """Rule 1. One stray print() corrupts the transport."""
        proc = self.converse([{"jsonrpc": "2.0", "id": 1, "method": "initialize"}])
        for line in proc.stdout.splitlines():
            if line.strip():
                json.loads(line)  # raises if anything non-JSON reached stdout

    def test_diagnostics_go_to_stderr(self):
        proc = self.converse([{"jsonrpc": "2.0", "id": 1, "method": "initialize"}])
        self.assertIn("notes-mcp", proc.stderr)
        self.assertNotIn("notes-mcp", proc.stdout)

    def test_malformed_line_gets_a_parse_error_and_the_server_keeps_going(self):
        proc = subprocess.run(
            [sys.executable, str(SERVER)],
            input='{not json\n{"jsonrpc": "2.0", "id": 2, "method": "ping"}\n',
            capture_output=True, text=True, timeout=60,
            env={"PATH": "/usr/bin:/bin", "NOTES_MCP_STORE": "/tmp/does-not-matter.json"},
        )
        responses = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertIsNone(responses[0]["id"])  # we never learned which request it was
        self.assertEqual(responses[1]["id"], 2)  # and the next one still works

    def test_blank_lines_are_ignored(self):
        proc = self.converse([{"jsonrpc": "2.0", "id": 1, "method": "ping"}])
        self.assertEqual(len([ln for ln in proc.stdout.splitlines() if ln.strip()]), 1)

    def test_selftest_mode_runs_clean(self):
        proc = subprocess.run([sys.executable, str(SERVER), "--selftest"],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no reply — correct", proc.stdout)


if __name__ == "__main__":
    unittest.main()
