"""Tests for examples/agent-loop/miniagent.py — the loop Chapter 01 builds.

Every test runs offline through ScriptedTransport. That is the point of the transport
seam, and it is worth noticing as a design lesson: the loop is fully testable without a
model, a key, or a network, so its failure modes can be pinned rather than hoped about.

The failure modes are the chapter's real content. A loop that works on the happy path is
a demo; a loop that survives a hallucinated tool name, a raising tool, malformed arguments
and a model that never stops is an agent.
"""
import sys
import tempfile
import unittest
from pathlib import Path

LOOP_DIR = Path(__file__).resolve().parents[1] / "examples" / "agent-loop"
sys.path.insert(0, str(LOOP_DIR))

import miniagent as M  # noqa: E402


def call(tool_id, name, arguments="{}"):
    return {"id": tool_id, "type": "function",
            "function": {"name": name, "arguments": arguments}}


def asks(*calls):
    return {"role": "assistant", "content": None, "tool_calls": list(calls)}


def answers(text):
    return {"role": "assistant", "content": text}


class LoopTestCase(unittest.TestCase):
    """Each test gets a fresh working directory, since the tools are scoped to it."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workdir = Path(self.temp.name)
        (self.workdir / "notes.txt").write_text("a\nb\nc\n", encoding="utf-8")
        (self.workdir / "empty.txt").write_text("", encoding="utf-8")
        original = M.WORKDIR
        M.WORKDIR = self.workdir
        self.addCleanup(lambda: setattr(M, "WORKDIR", original))


class TerminationTests(LoopTestCase):
    def test_an_answer_with_no_tool_calls_ends_the_loop(self):
        out = M.run("hi", M.ScriptedTransport([answers("hello")]))
        self.assertEqual(out["answer"], "hello")
        self.assertEqual(out["steps"], 1)

    def test_tool_result_is_fed_back_and_the_loop_continues(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "count_lines", '{"name": "notes.txt"}')),
            answers("3 lines"),
        ])
        out = M.run("how many lines?", transport)
        self.assertEqual(out["answer"], "3 lines")
        self.assertEqual(out["steps"], 2)
        tool_messages = [m for m in out["messages"] if m.get("role") == "tool"]
        self.assertEqual(len(tool_messages), 1)
        self.assertEqual(tool_messages[0]["content"], "3")
        # The result must be linked to the call that produced it, or the model cannot
        # tell which answer belongs to which question.
        self.assertEqual(tool_messages[0]["tool_call_id"], "c1")

    def test_several_sequential_steps(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "list_files")),
            asks(call("c2", "read_file", '{"name": "notes.txt"}')),
            asks(call("c3", "count_lines", '{"name": "notes.txt"}')),
            answers("done"),
        ])
        out = M.run("investigate", transport)
        self.assertEqual(out["steps"], 4)
        self.assertEqual([m["name"] for m in out["messages"] if m.get("role") == "tool"],
                         ["list_files", "read_file", "count_lines"])

    def test_parallel_tool_calls_in_one_turn_all_execute(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "count_lines", '{"name": "notes.txt"}'),
                 call("c2", "count_lines", '{"name": "empty.txt"}')),
            answers("3 and 0"),
        ])
        out = M.run("both", transport)
        results = [m["content"] for m in out["messages"] if m.get("role") == "tool"]
        self.assertEqual(results, ["3", "0"])

    def test_context_grows_every_iteration(self):
        """Why a long loop costs more than a short one: the transcript only grows."""
        transport = M.ScriptedTransport([
            asks(call("c1", "list_files")),
            asks(call("c2", "list_files")),
            answers("ok"),
        ])
        M.run("x", transport)
        lengths = [len(snapshot) for snapshot in transport.seen]
        self.assertEqual(lengths, sorted(lengths))
        self.assertGreater(lengths[-1], lengths[0])


class BudgetTests(LoopTestCase):
    def test_a_model_that_never_stops_is_cut_off(self):
        """Without this cap an agent is an unbounded bill with a plausible explanation."""
        transport = M.ScriptedTransport([asks(call(f"c{i}", "list_files")) for i in range(10)])
        out = M.run("loop forever", transport, max_steps=3)
        self.assertEqual(out["steps"], 3)
        self.assertIn("stopped after 3 steps", out["answer"])

    def test_budget_of_one_still_allows_a_direct_answer(self):
        out = M.run("hi", M.ScriptedTransport([answers("hello")]), max_steps=1)
        self.assertEqual(out["answer"], "hello")


class ToolFailureTests(LoopTestCase):
    """A tool failure must re-enter the conversation, never raise out of the loop."""

    def test_hallucinated_tool_name_is_reported_to_the_model(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "send_email", '{"to": "x"}')),
            answers("sorry, I cannot do that"),
        ])
        out = M.run("email someone", transport)
        result = [m for m in out["messages"] if m.get("role") == "tool"][0]["content"]
        self.assertIn("no such tool", result)
        # The message names what IS available, so the next turn can recover.
        self.assertIn("list_files", result)
        self.assertEqual(out["answer"], "sorry, I cannot do that")

    def test_malformed_arguments_do_not_crash_the_loop(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "count_lines", "{not json")),
            answers("recovered"),
        ])
        out = M.run("x", transport)
        result = [m for m in out["messages"] if m.get("role") == "tool"][0]["content"]
        self.assertTrue(result.startswith("error:"))
        self.assertEqual(out["answer"], "recovered")

    def test_non_object_arguments_are_rejected(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "count_lines", '"notes.txt"')),
            answers("recovered"),
        ])
        out = M.run("x", transport)
        result = [m for m in out["messages"] if m.get("role") == "tool"][0]["content"]
        self.assertIn("JSON object", result)

    def test_wrong_argument_name_is_reported_not_raised(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "count_lines", '{"path": "notes.txt"}')),
            answers("recovered"),
        ])
        out = M.run("x", transport)
        result = [m for m in out["messages"] if m.get("role") == "tool"][0]["content"]
        self.assertIn("error: TypeError", result)

    def test_missing_file_is_an_ordinary_result_not_an_error(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "count_lines", '{"name": "nope.txt"}')),
            answers("it is not there"),
        ])
        out = M.run("x", transport)
        result = [m for m in out["messages"] if m.get("role") == "tool"][0]["content"]
        self.assertEqual(result, "no such file: nope.txt")


class ContainmentTests(LoopTestCase):
    """The model chooses these arguments, so the tool is where containment lives."""

    def test_parent_traversal_is_refused(self):
        with self.assertRaises(ValueError):
            M._safe("../../etc/passwd")

    def test_absolute_path_outside_workdir_is_refused(self):
        with self.assertRaises(ValueError):
            M._safe("/etc/passwd")

    def test_a_refusal_reaches_the_model_as_a_result(self):
        transport = M.ScriptedTransport([
            asks(call("c1", "read_file", '{"name": "../../etc/passwd"}')),
            answers("I cannot read that"),
        ])
        out = M.run("read the host's keys", transport)
        result = [m for m in out["messages"] if m.get("role") == "tool"][0]["content"]
        self.assertIn("outside the working directory", result)

    def test_ordinary_names_resolve(self):
        self.assertEqual(M._safe("notes.txt"), (self.workdir / "notes.txt").resolve())

    def test_nested_path_inside_workdir_is_allowed(self):
        (self.workdir / "sub").mkdir()
        (self.workdir / "sub" / "x.txt").write_text("hi\n", encoding="utf-8")
        self.assertEqual(M.count_lines("sub/x.txt"), "1")


class ToolTests(LoopTestCase):
    def test_read_file_truncates(self):
        big = "x" * 9000
        (self.workdir / "big.txt").write_text(big, encoding="utf-8")
        out = M.read_file("big.txt", max_bytes=100)
        self.assertIn("[truncated]", out)
        self.assertLess(len(out), 300)

    def test_read_file_does_not_mark_short_files_truncated(self):
        self.assertNotIn("[truncated]", M.read_file("notes.txt"))

    def test_list_files_reports_an_empty_directory(self):
        for path in self.workdir.iterdir():
            path.unlink()
        self.assertEqual(M.list_files(), "(no files)")

    def test_count_lines_of_an_empty_file(self):
        self.assertEqual(M.count_lines("empty.txt"), "0")


class SchemaTests(unittest.TestCase):
    """A schema that no longer matches its function is a bug the model cannot see."""

    def test_every_schema_has_an_implementation(self):
        named = {s["function"]["name"] for s in M.SCHEMAS}
        self.assertEqual(named, set(M.TOOLS))

    def test_every_schema_describes_itself(self):
        for schema in M.SCHEMAS:
            fn = schema["function"]
            self.assertTrue(fn["description"], f"{fn['name']} has no description")
            self.assertEqual(schema["type"], "function")
            self.assertEqual(fn["parameters"]["type"], "object")

    def test_required_parameters_are_real_function_arguments(self):
        import inspect
        for schema in M.SCHEMAS:
            fn = schema["function"]
            signature = inspect.signature(M.TOOLS[fn["name"]])
            for name in fn["parameters"].get("required", []):
                self.assertIn(name, signature.parameters,
                              f"{fn['name']} schema requires {name!r}, which it does not take")

    def test_declared_properties_are_real_function_arguments(self):
        import inspect
        for schema in M.SCHEMAS:
            fn = schema["function"]
            signature = inspect.signature(M.TOOLS[fn["name"]])
            for name in fn["parameters"].get("properties", {}):
                self.assertIn(name, signature.parameters,
                              f"{fn['name']} schema declares {name!r}, which it does not take")


class DemoTests(unittest.TestCase):
    def test_the_demo_script_drives_the_loop_to_an_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = M.WORKDIR
            try:
                M.WORKDIR = Path(tmp)
                (M.WORKDIR / "notes.txt").write_text("a\nb\nc\n", encoding="utf-8")
                out = M.run("how many lines in notes.txt?",
                            M.ScriptedTransport(M.DEMO_SCRIPT))
            finally:
                M.WORKDIR = original
        self.assertEqual(out["answer"], "notes.txt has 3 lines.")
        self.assertEqual(out["steps"], 3)

    def test_scripted_transport_complains_rather_than_hanging(self):
        with self.assertRaises(AssertionError):
            M.run("x", M.ScriptedTransport([asks(call("c1", "list_files"))]))


if __name__ == "__main__":
    unittest.main()
