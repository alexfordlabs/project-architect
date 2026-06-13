"""Tests for `architect-brain reconcile-adrs` + `check-state` subcommands.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from architect_brain.__main__ import main


class TestCLIReconcileADRs(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _decisions_dir(self) -> Path:
        d = self.docs / "_architect_state" / "decisions"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_adr(self, num, title, status="Accepted"):
        adr_md = f'''---
type: adr
schema_version: "4.0"
id: "{num}"
title: "{title}"
status: "{status}"
date: "2026-05-28"
decision_makers:
  - "Alexander Ford"
plugin_version: "8.0.0"
---

# ADR-{num}: {title}

## Decision Outcome

Chosen.
'''
        (self._decisions_dir() / f"{num}-{title.lower().replace(' ', '-')}.md").write_text(adr_md)

    def test_reconcile_rebuilds_index_from_disk_adrs(self):
        self._write_adr("0001", "Use Next.js")
        self._write_adr("0002", "Use Postgres")
        exit_code = main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 0)
        index = json.loads((self._decisions_dir() / "index.json").read_text())
        self.assertEqual(len(index["adrs"]), 2)
        ids = [a["id"] for a in index["adrs"]]
        self.assertEqual(ids, ["0001", "0002"])  # sorted

    def test_reconcile_extracts_frontmatter_fields(self):
        self._write_adr("0007", "Use Next.js 15", status="Accepted")
        main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        index = json.loads((self._decisions_dir() / "index.json").read_text())
        adr = index["adrs"][0]
        self.assertEqual(adr["id"], "0007")
        self.assertEqual(adr["title"], "Use Next.js 15")
        self.assertEqual(adr["status"], "Accepted")
        self.assertEqual(adr["date"], "2026-05-28")

    def test_reconcile_sorts_by_id(self):
        self._write_adr("0003", "Third")
        self._write_adr("0001", "First")
        self._write_adr("0002", "Second")
        main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        index = json.loads((self._decisions_dir() / "index.json").read_text())
        self.assertEqual([a["id"] for a in index["adrs"]], ["0001", "0002", "0003"])

    def test_reconcile_unquoted_numeric_id_does_not_crash(self):
        # v9.2 fix (tiger-panther bug: TypeError '<' between str and int).
        # YAML parses an UNQUOTED `id: 0001` as int 1; mixed with quoted-string
        # ids in sibling files, the sort crashed. Ids normalize to the
        # canonical zero-padded string form instead.
        self._write_adr("0001", "First")          # quoted -> str
        d = self._decisions_dir()
        (d / "0002-second.md").write_text(
            "---\n"
            "type: adr\n"
            'schema_version: "4.0"\n'
            "id: 0002\n"                # unquoted -> yaml int
            'title: "Second"\n'
            'status: "Accepted"\n'
            'date: "2026-06-13"\n'
            "---\n\n# Second\n",
            encoding="utf-8",
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        self.assertEqual(code, 0)
        index = json.loads(
            (d / "index.json").read_text(encoding="utf-8")
        )
        self.assertEqual([a["id"] for a in index["adrs"]], ["0001", "0002"])

    def test_reconcile_unquoted_date_does_not_crash(self):
        # tiger-panther bug (post-v9.2): the v9.2 fix handled the unquoted-`id`
        # (int) half of the YAML-coercion class, but pyyaml also parses an
        # UNQUOTED `date: 2026-06-12` into a datetime.date — which json.dumps
        # cannot serialize ("Object of type date is not JSON serializable"),
        # crashing reconcile-adrs on every real project. The plugin's own ADR
        # emitter writes unquoted dates; the test fixtures had masked the bug by
        # quoting every date. Normalize date/datetime to the index's ISO string.
        d = self._decisions_dir()
        (d / "0001-first.md").write_text(
            "---\n"
            "type: adr\n"
            'schema_version: "4.0"\n'
            "id: 0001\n"                 # unquoted -> yaml int (already handled)
            'title: "First"\n'
            'status: "Accepted"\n'
            "date: 2026-06-12\n"          # unquoted -> yaml datetime.date (THE bug)
            "---\n\n# First\n",
            encoding="utf-8",
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        self.assertEqual(code, 0)
        index = json.loads((d / "index.json").read_text(encoding="utf-8"))
        adr = next(a for a in index["adrs"] if a["id"] == "0001")
        self.assertEqual(adr["date"], "2026-06-12")  # normalized to ISO string

    def test_reconcile_unquoted_datetime_normalizes_to_isoformat(self):
        # Defense for the wider class: an unquoted full timestamp parses to a
        # datetime; it must also round-trip to an ISO string rather than crash.
        d = self._decisions_dir()
        (d / "0001-first.md").write_text(
            "---\n"
            "type: adr\n"
            'schema_version: "4.0"\n'
            'id: "0001"\n'
            'title: "First"\n'
            'status: "Accepted"\n'
            "date: 2026-06-12 09:30:00\n"   # unquoted -> yaml datetime.datetime
            "---\n\n# First\n",
            encoding="utf-8",
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        self.assertEqual(code, 0)
        index = json.loads((d / "index.json").read_text(encoding="utf-8"))
        adr = next(a for a in index["adrs"] if a["id"] == "0001")
        self.assertTrue(adr["date"].startswith("2026-06-12"))
        self.assertIsInstance(adr["date"], str)

    def test_reconcile_normalizes_numeric_supersedes(self):
        d = self._decisions_dir()
        (d / "0003-third.md").write_text(
            "---\n"
            "type: adr\n"
            'schema_version: "4.0"\n'
            "id: 0003\n"
            'title: "Third"\n'
            'status: "Accepted"\n'
            'date: "2026-06-13"\n'
            "supersedes: [1]\n"          # yaml int in the chain
            "---\n\n# Third\n",
            encoding="utf-8",
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        self.assertEqual(code, 0)
        index = json.loads((d / "index.json").read_text(encoding="utf-8"))
        third = next(a for a in index["adrs"] if a["id"] == "0003")
        self.assertEqual(third["supersedes"], ["0001"])

    def test_reconcile_empty_decisions_dir_writes_empty_index(self):
        exit_code = main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 0)
        index = json.loads((self._decisions_dir() / "index.json").read_text())
        self.assertEqual(index["adrs"], [])

    def test_reconcile_writes_schema_version_and_regenerated_at(self):
        self._write_adr("0001", "Test")
        main(["reconcile-adrs", "--docs-dir", str(self.docs)])
        index = json.loads((self._decisions_dir() / "index.json").read_text())
        self.assertEqual(index["schema_version"], "4.0")
        self.assertIn("regenerated_at", index)


class TestCLICheckState(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def test_check_state_passes_on_fresh_init(self):
        """A freshly-init'd state directory validates clean."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(["check-state", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 0)
        self.assertIn("valid", buf.getvalue().lower())

    def test_check_state_passes_after_set_decision(self):
        main(["set-decision", "--docs-dir", str(self.docs), "stack.frontend.framework", "Next.js"])
        exit_code = main(["check-state", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 0)

    def test_check_state_fails_on_corrupted_projection(self):
        """Corrupt a projection file → check-state returns 1 + reports the error."""
        # Break the stack.json: remove the required 'concern' field
        stack_path = self._state_dir() / "stack.json"
        data = json.loads(stack_path.read_text())
        del data["concern"]
        stack_path.write_text(json.dumps(data))

        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(["check-state", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 1)
        self.assertIn("stack", buf.getvalue())

    def test_check_state_fails_on_wrong_schema_version(self):
        stack_path = self._state_dir() / "stack.json"
        data = json.loads(stack_path.read_text())
        data["schema_version"] = "3.0"
        stack_path.write_text(json.dumps(data))
        exit_code = main(["check-state", "--docs-dir", str(self.docs)])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
