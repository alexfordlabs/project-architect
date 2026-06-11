"""Tests for `architect-brain append-event` + `replay` subcommands.

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


class TestCLIAppendEvent(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        # init state first
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def test_append_event_writes_one_line_to_events_jsonl(self):
        payload = json.dumps({"key": "stack.frontend.framework", "value": "next.js"})
        exit_code = main([
            "append-event",
            "--docs-dir", str(self.docs),
            "--type", "DecisionMade",
            "--phase", "stack",
            "--payload", payload,
        ])
        self.assertEqual(exit_code, 0)
        log = (self._state_dir() / "events.jsonl").read_text()
        self.assertEqual(len(log.strip().splitlines()), 1)

    def test_append_event_updates_concern_projection_on_disk(self):
        payload = json.dumps({"key": "stack.frontend.framework", "value": "next.js"})
        main([
            "append-event",
            "--docs-dir", str(self.docs),
            "--type", "DecisionMade",
            "--phase", "stack",
            "--payload", payload,
        ])
        stack = json.loads((self._state_dir() / "stack.json").read_text())
        self.assertEqual(stack["decisions"]["stack.frontend.framework"], "next.js")

    def test_append_event_updates_flat_index(self):
        payload = json.dumps({"key": "api.public", "value": True})
        main([
            "append-event",
            "--docs-dir", str(self.docs),
            "--type", "DecisionMade",
            "--phase", "api",
            "--payload", payload,
        ])
        flat = json.loads((self._state_dir() / "99-flat-index.json").read_text())
        self.assertEqual(flat["decisions"]["api.public"], True)

    def test_append_event_writes_realistic_timestamp(self):
        """_iso_now() produces a real ISO-8601 UTC timestamp, not a static stub.

        Anchors `ts` to a post-2024 ISO-8601 'Z' regex. Static stubs (e.g.
        a hard-coded "2020-01-01T00:00:00Z") would fail the > anchor; missing
        timezone suffix would fail the regex; non-UTC offset would too.
        """
        payload = json.dumps({"key": "stack.frontend.framework", "value": "next.js"})
        main([
            "append-event",
            "--docs-dir", str(self.docs),
            "--type", "DecisionMade",
            "--phase", "stack",
            "--payload", payload,
        ])
        line = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()[0]
        event = json.loads(line)
        self.assertRegex(
            event["ts"],
            r"^20[2-9][0-9]-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z$",
        )
        # Anchor: must be after 2024-01-01 (catches static "2020-..." stubs)
        self.assertGreater(event["ts"], "2024-01-01T00:00:00Z")

    def test_append_event_returns_ulid_to_stdout(self):
        payload = json.dumps({"key": "stack.frontend.framework", "value": "next.js"})
        buf = io.StringIO()
        with redirect_stdout(buf):
            main([
                "append-event",
                "--docs-dir", str(self.docs),
                "--type", "DecisionMade",
                "--phase", "stack",
                "--payload", payload,
            ])
        ulid_out = buf.getvalue().strip()
        # ULIDs are 26 chars, Crockford-base32
        self.assertEqual(len(ulid_out), 26)


class TestCLIReplay(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def test_replay_regenerates_projections_from_events_jsonl(self):
        # Append an event
        payload = json.dumps({"key": "stack.frontend.framework", "value": "next.js"})
        main([
            "append-event",
            "--docs-dir", str(self.docs),
            "--type", "DecisionMade",
            "--phase", "stack",
            "--payload", payload,
        ])
        # Wipe the projection file; verify replay reconstructs it
        (self._state_dir() / "stack.json").unlink()
        exit_code = main(["replay", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 0)
        stack = json.loads((self._state_dir() / "stack.json").read_text())
        self.assertEqual(stack["decisions"]["stack.frontend.framework"], "next.js")

    def test_replay_on_empty_log_produces_empty_projections(self):
        # init created empty events.jsonl; replay should produce empty projections
        exit_code = main(["replay", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 0)
        stack = json.loads((self._state_dir() / "stack.json").read_text())
        self.assertEqual(stack["decisions"], {})

    def test_replay_on_corrupt_log_exits_cleanly_not_traceback(self):
        # A malformed events.jsonl line must yield a clean non-zero exit + message,
        # NOT a raw JSONDecodeError traceback dumped into the user's transcript
        # (the CLI top-level handler — v8.0.1 robustness fix).
        import io
        from contextlib import redirect_stderr
        (self._state_dir() / "events.jsonl").write_text("{ this is not valid json\n")
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["replay", "--docs-dir", str(self.docs)])
        self.assertEqual(code, 1)
        self.assertIn("architect-brain", err.getvalue())


if __name__ == "__main__":
    unittest.main()
