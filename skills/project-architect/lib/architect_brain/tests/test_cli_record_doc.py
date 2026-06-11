"""Tests for `architect-brain record-doc` subcommand.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from architect_brain.__main__ import main


class TestCLIRecordDoc(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def test_record_doc_appends_to_docs_concern(self):
        # Write a fake doc file
        doc_path = self.docs / "PROJECT_OVERVIEW.md"
        doc_path.write_text("# Project Overview\n\nHello world.\n")

        exit_code = main([
            "record-doc",
            "--docs-dir", str(self.docs),
            "PROJECT_OVERVIEW", str(doc_path),
        ])
        self.assertEqual(exit_code, 0)

        docs = json.loads((self._state_dir() / "docs.json").read_text())
        completed = docs.get("completed", [])
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["name"], "PROJECT_OVERVIEW")
        self.assertEqual(completed[0]["path"], str(doc_path))

    def test_record_doc_computes_sha256_content_hash(self):
        doc_path = self.docs / "PROJECT_OVERVIEW.md"
        doc_content = "# Project Overview\n\nHello world.\n"
        doc_path.write_text(doc_content)

        expected_hash = hashlib.sha256(doc_content.encode()).hexdigest()

        main([
            "record-doc",
            "--docs-dir", str(self.docs),
            "PROJECT_OVERVIEW", str(doc_path),
        ])

        docs = json.loads((self._state_dir() / "docs.json").read_text())
        self.assertEqual(docs["completed"][0]["content_hash"], expected_hash)

    def test_record_doc_emits_doc_generated_event(self):
        doc_path = self.docs / "PROJECT_OVERVIEW.md"
        doc_path.write_text("# overview\n")

        main([
            "record-doc",
            "--docs-dir", str(self.docs),
            "PROJECT_OVERVIEW", str(doc_path),
        ])

        log_line = (self._state_dir() / "events.jsonl").read_text().strip().splitlines()[0]
        event = json.loads(log_line)
        self.assertEqual(event["type"], "DocGenerated")
        self.assertEqual(event["payload"]["name"], "PROJECT_OVERVIEW")
        self.assertEqual(event["payload"]["path"], str(doc_path))
        self.assertIn("content_hash", event["payload"])

    def test_record_doc_prints_ulid_to_stdout(self):
        doc_path = self.docs / "PROJECT_OVERVIEW.md"
        doc_path.write_text("# overview\n")

        buf = io.StringIO()
        with redirect_stdout(buf):
            main([
                "record-doc",
                "--docs-dir", str(self.docs),
                "PROJECT_OVERVIEW", str(doc_path),
            ])
        ulid_out = buf.getvalue().strip()
        self.assertEqual(len(ulid_out), 26)

    def test_record_doc_fails_gracefully_on_missing_file(self):
        """Missing file should produce non-zero exit + error to stderr, not a traceback."""
        nonexistent = self.docs / "MISSING.md"

        stderr_buf = io.StringIO()
        with redirect_stderr(stderr_buf):
            exit_code = main([
                "record-doc",
                "--docs-dir", str(self.docs),
                "MISSING", str(nonexistent),
            ])
        self.assertNotEqual(exit_code, 0)
        self.assertIn("file not found", stderr_buf.getvalue())
        self.assertIn(str(nonexistent), stderr_buf.getvalue())

    def test_record_doc_hash_changes_with_content(self):
        """Different content → different hash."""
        doc1 = self.docs / "A.md"
        doc2 = self.docs / "B.md"
        doc1.write_text("content A\n")
        doc2.write_text("content B\n")

        main(["record-doc", "--docs-dir", str(self.docs), "A", str(doc1)])
        main(["record-doc", "--docs-dir", str(self.docs), "B", str(doc2)])

        docs = json.loads((self._state_dir() / "docs.json").read_text())
        completed = docs["completed"]
        self.assertEqual(len(completed), 2)
        self.assertNotEqual(completed[0]["content_hash"], completed[1]["content_hash"])

    def test_record_doc_hash_stable_for_identical_content(self):
        """Same content twice → same hash (deterministic)."""
        doc_path = self.docs / "STABLE.md"
        doc_path.write_text("stable content\n")

        main(["record-doc", "--docs-dir", str(self.docs), "STABLE1", str(doc_path)])
        main(["record-doc", "--docs-dir", str(self.docs), "STABLE2", str(doc_path)])

        docs = json.loads((self._state_dir() / "docs.json").read_text())
        completed = docs["completed"]
        self.assertEqual(completed[0]["content_hash"], completed[1]["content_hash"])


if __name__ == "__main__":
    unittest.main()
