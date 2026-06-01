"""Tests for `architect-brain set-phase` + `set-substep` subcommands.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


class TestCLISetPhase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def test_set_phase_advances_workflow_to_named_phase(self):
        exit_code = main([
            "set-phase",
            "--docs-dir", str(self.docs),
            "architecture",
        ])
        self.assertEqual(exit_code, 0)
        workflow = json.loads((self._state_dir() / "workflow.json").read_text())
        self.assertEqual(workflow["current_phase"], "architecture")

    def test_set_phase_from_field_reflects_prior_phase(self):
        main(["set-phase", "--docs-dir", str(self.docs), "vision"])
        main(["set-phase", "--docs-dir", str(self.docs), "architecture"])
        log_lines = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()
        second_event = json.loads(log_lines[1])
        self.assertEqual(second_event["type"], "PhaseAdvanced")
        self.assertEqual(second_event["payload"]["from"], "vision")
        self.assertEqual(second_event["payload"]["to"], "architecture")

    def test_set_phase_from_field_is_null_on_first_advance(self):
        main(["set-phase", "--docs-dir", str(self.docs), "vision"])
        log_line = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()[0]
        event = json.loads(log_line)
        self.assertIsNone(event["payload"]["from"])
        self.assertEqual(event["payload"]["to"], "vision")

    def test_set_phase_prints_ulid_to_stdout(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["set-phase", "--docs-dir", str(self.docs), "vision"])
        ulid_out = buf.getvalue().strip()
        self.assertEqual(len(ulid_out), 26)

    def test_set_phase_resets_substep_to_none(self):
        main(["set-substep", "--docs-dir", str(self.docs), "vision", "elicit_requirements"])
        main(["set-phase", "--docs-dir", str(self.docs), "architecture"])
        workflow = json.loads((self._state_dir() / "workflow.json").read_text())
        self.assertIsNone(workflow["substep"])


class TestCLISetSubstep(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def test_set_substep_records_phase_substep_status(self):
        exit_code = main([
            "set-substep",
            "--docs-dir", str(self.docs),
            "architecture", "boundaries",
        ])
        self.assertEqual(exit_code, 0)
        workflow = json.loads((self._state_dir() / "workflow.json").read_text())
        self.assertEqual(workflow["substep"]["phase"], "architecture")
        self.assertEqual(workflow["substep"]["substep"], "boundaries")
        self.assertEqual(workflow["substep"]["status"], "in_progress")

    def test_set_substep_custom_status(self):
        main([
            "set-substep",
            "--docs-dir", str(self.docs),
            "--status", "completed",
            "architecture", "boundaries",
        ])
        workflow = json.loads((self._state_dir() / "workflow.json").read_text())
        self.assertEqual(workflow["substep"]["status"], "completed")

    def test_set_substep_emits_substep_recorded_event(self):
        main(["set-substep", "--docs-dir", str(self.docs), "architecture", "boundaries"])
        log_line = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()[0]
        event = json.loads(log_line)
        self.assertEqual(event["type"], "SubstepRecorded")
        self.assertEqual(event["payload"]["phase"], "architecture")
        self.assertEqual(event["payload"]["substep"], "boundaries")
        self.assertEqual(event["payload"]["status"], "in_progress")

    def test_set_substep_prints_ulid_to_stdout(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["set-substep", "--docs-dir", str(self.docs), "architecture", "boundaries"])
        ulid_out = buf.getvalue().strip()
        self.assertEqual(len(ulid_out), 26)


if __name__ == "__main__":
    unittest.main()
