"""Tests for `architect-brain set-decision` subcommand.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


class TestCLISetDecision(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def test_set_decision_string_value_lands_in_concern(self):
        exit_code = main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "stack.frontend.framework", "Next.js",
        ])
        self.assertEqual(exit_code, 0)
        stack = json.loads((self._state_dir() / "stack.json").read_text())
        self.assertEqual(stack["decisions"]["stack.frontend.framework"], "Next.js")

    def test_set_decision_bool_value_parsed_correctly(self):
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "ai.enabled", "true",
        ])
        ai = json.loads((self._state_dir() / "ai_agent.json").read_text())
        self.assertEqual(ai["decisions"]["ai.enabled"], True)
        self.assertIsInstance(ai["decisions"]["ai.enabled"], bool)

    def test_set_decision_int_value_parsed_correctly(self):
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "team.size", "5",
        ])
        identity = json.loads((self._state_dir() / "identity.json").read_text())
        self.assertEqual(identity["decisions"]["team.size"], 5)
        self.assertIsInstance(identity["decisions"]["team.size"], int)

    def test_set_decision_null_value_parsed_correctly(self):
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "stack.backend.framework", "null",
        ])
        stack = json.loads((self._state_dir() / "stack.json").read_text())
        self.assertIsNone(stack["decisions"]["stack.backend.framework"])

    def test_set_decision_string_with_spaces_is_string(self):
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "vision.mission", "Build great software",
        ])
        vision = json.loads((self._state_dir() / "vision.json").read_text())
        self.assertEqual(vision["decisions"]["vision.mission"], "Build great software")

    def test_set_decision_event_appended_to_log(self):
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "stack.frontend.framework", "Next.js",
        ])
        log_lines = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(log_lines), 1)
        event = json.loads(log_lines[0])
        self.assertEqual(event["type"], "DecisionMade")
        self.assertEqual(event["payload"]["key"], "stack.frontend.framework")
        self.assertEqual(event["payload"]["value"], "Next.js")

    def test_set_decision_prints_ulid_to_stdout(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main([
                "set-decision",
                "--docs-dir", str(self.docs),
                "stack.frontend.framework", "Next.js",
            ])
        ulid_out = buf.getvalue().strip()
        self.assertEqual(len(ulid_out), 26)

    def test_set_decision_version_pin_kept_as_string(self):
        # stack.versions.* is always a STRING pin: a bare `17` must NOT json-coerce
        # to int 17 (which configs._pin would then discard to the floor) — the
        # tiger-panther postgres:17→18 silent-floor regression starts right here.
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "stack.versions.postgres", "17",
        ])
        stack = json.loads((self._state_dir() / "stack.json").read_text())
        self.assertEqual(stack["decisions"]["stack.versions.postgres"], "17")
        self.assertIsInstance(stack["decisions"]["stack.versions.postgres"], str)

    def test_set_decision_version_pin_preserves_trailing_zero_minor(self):
        # `1.10` json-parses to float 1.1 (the trailing-zero minor is lost);
        # version pins must round-trip verbatim as strings.
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "stack.versions.redis", "1.10",
        ])
        stack = json.loads((self._state_dir() / "stack.json").read_text())
        self.assertEqual(stack["decisions"]["stack.versions.redis"], "1.10")

    def test_set_decision_object_value_parsed_correctly(self):
        """JSON object values are preserved as dicts in the projection."""
        main([
            "set-decision",
            "--docs-dir", str(self.docs),
            "cost.budget", '{"monthly_usd": 100, "annual_usd": 1200}',
        ])
        cost = json.loads((self._state_dir() / "cost.json").read_text())
        self.assertEqual(cost["decisions"]["cost.budget"]["monthly_usd"], 100)


if __name__ == "__main__":
    unittest.main()
