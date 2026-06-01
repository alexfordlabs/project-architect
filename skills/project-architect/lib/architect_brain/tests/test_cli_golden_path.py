"""Tests for the `architect-brain golden-path` subcommand group."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


class TestGoldenPathListCLI(unittest.TestCase):

    def test_list_shows_paths(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["golden-path", "list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("modern_saas_2026", out)
        self.assertIn("Modern SaaS", out)
        self.assertIn("agentic_system", out)


class TestGoldenPathApplyCLI(unittest.TestCase):

    def test_apply_writes_decisions_into_flat_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            main(["init", "--docs-dir", str(docs_dir)])
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = main(["golden-path", "apply", "modern_saas_2026", "--docs-dir", str(docs_dir)])
            self.assertEqual(code, 0)
            flat = json.loads((docs_dir / "_architect_state" / "99-flat-index.json").read_text())
            self.assertEqual(flat["decisions"]["stack.frontend.framework"], "next.js")
            self.assertEqual(flat["decisions"]["project.type"], "web_app")

    def test_apply_emits_goldenpathapplied_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            main(["init", "--docs-dir", str(docs_dir)])
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                main(["golden-path", "apply", "cli_rust", "--docs-dir", str(docs_dir)])
            log = (docs_dir / "_architect_state" / "events.jsonl").read_text()
            self.assertIn("GoldenPathApplied", log)
            self.assertIn("DecisionMade", log)

    def test_apply_unknown_id_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            main(["init", "--docs-dir", str(docs_dir)])
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = main(["golden-path", "apply", "bogus_path", "--docs-dir", str(docs_dir)])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
