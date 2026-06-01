"""Tests for `architect-brain record-adr` + `reserve-adr` subcommands.

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


class TestCLIRecordADR(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def _flat_index(self) -> dict:
        return json.loads((self._state_dir() / "99-flat-index.json").read_text())

    def test_record_adr_appends_to_flat_index(self):
        exit_code = main([
            "record-adr",
            "--docs-dir", str(self.docs),
            "0001", "Use Next.js 15", "Accepted",
        ])
        self.assertEqual(exit_code, 0)
        adrs = self._flat_index()["adrs"]
        self.assertEqual(len(adrs), 1)
        self.assertEqual(adrs[0]["id"], "0001")
        self.assertEqual(adrs[0]["title"], "Use Next.js 15")
        self.assertEqual(adrs[0]["status"], "Accepted")

    def test_record_adr_with_supersedes(self):
        main([
            "record-adr",
            "--docs-dir", str(self.docs),
            "0001", "First decision", "Accepted",
        ])
        main([
            "record-adr",
            "--docs-dir", str(self.docs),
            "--supersedes", "0001",
            "0002", "Revised decision", "Accepted",
        ])
        adrs = self._flat_index()["adrs"]
        self.assertEqual(len(adrs), 2)
        self.assertEqual(adrs[1]["supersedes"], ["0001"])

    def test_record_adr_with_multiple_supersedes(self):
        main([
            "record-adr",
            "--docs-dir", str(self.docs),
            "--supersedes", "0001",
            "--supersedes", "0002",
            "0003", "Consolidates A and B", "Accepted",
        ])
        adrs = self._flat_index()["adrs"]
        self.assertEqual(adrs[0]["supersedes"], ["0001", "0002"])

    def test_record_adr_emits_adr_filed_event(self):
        main([
            "record-adr",
            "--docs-dir", str(self.docs),
            "0001", "Use Next.js 15", "Accepted",
        ])
        log_line = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()[0]
        event = json.loads(log_line)
        self.assertEqual(event["type"], "ADRFiled")
        self.assertEqual(event["payload"]["id"], "0001")
        self.assertEqual(event["payload"]["title"], "Use Next.js 15")
        self.assertEqual(event["payload"]["status"], "Accepted")

    def test_record_adr_prints_ulid_to_stdout(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main([
                "record-adr",
                "--docs-dir", str(self.docs),
                "0001", "Test", "Accepted",
            ])
        ulid_out = buf.getvalue().strip()
        self.assertEqual(len(ulid_out), 26)


class TestCLIReserveADR(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def _flat_index(self) -> dict:
        return json.loads((self._state_dir() / "99-flat-index.json").read_text())

    def test_reserve_adr_creates_reserved_status_entry(self):
        exit_code = main([
            "reserve-adr",
            "--docs-dir", str(self.docs),
            "0007",
        ])
        self.assertEqual(exit_code, 0)
        adrs = self._flat_index()["adrs"]
        self.assertEqual(len(adrs), 1)
        self.assertEqual(adrs[0]["id"], "0007")
        self.assertEqual(adrs[0]["status"], "Reserved")

    def test_reserve_adr_default_title(self):
        main([
            "reserve-adr",
            "--docs-dir", str(self.docs),
            "0007",
        ])
        adrs = self._flat_index()["adrs"]
        self.assertIn("0007", adrs[0]["title"])

    def test_reserve_adr_custom_title(self):
        main([
            "reserve-adr",
            "--docs-dir", str(self.docs),
            "--title", "Planned: caching strategy decision",
            "0007",
        ])
        adrs = self._flat_index()["adrs"]
        self.assertEqual(adrs[0]["title"], "Planned: caching strategy decision")

    def test_reserve_adr_emits_adr_filed_event(self):
        main([
            "reserve-adr",
            "--docs-dir", str(self.docs),
            "0007",
        ])
        log_line = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()[0]
        event = json.loads(log_line)
        self.assertEqual(event["type"], "ADRFiled")
        self.assertEqual(event["payload"]["status"], "Reserved")

    def test_reserve_adr_then_record_adr_supersedes_in_flat_index(self):
        """Reserving an ADR then recording it should produce two flat-index entries."""
        # First reserve
        main(["reserve-adr", "--docs-dir", str(self.docs), "0007"])
        # Then record a real ADR (different id, no supersedes; reserved entry persists)
        main([
            "record-adr",
            "--docs-dir", str(self.docs),
            "0008", "Real decision", "Accepted",
        ])
        adrs = self._flat_index()["adrs"]
        self.assertEqual(len(adrs), 2)
        # Order: reserved first (was appended first), then accepted
        statuses = [adr["status"] for adr in adrs]
        self.assertEqual(statuses, ["Reserved", "Accepted"])


if __name__ == "__main__":
    unittest.main()
