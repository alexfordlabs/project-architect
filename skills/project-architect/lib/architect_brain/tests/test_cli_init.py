"""Tests for `architect-brain init` and `architect-brain detect` subcommands.

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


class TestCLIInit(unittest.TestCase):

    def test_init_creates_state_dir_with_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            exit_code = main(["init", "--docs-dir", str(docs_dir)])
            self.assertEqual(exit_code, 0)

            state_dir = docs_dir / "_architect_state"
            self.assertTrue(state_dir.exists())
            self.assertEqual(
                (state_dir / "schema_version").read_text().strip(),
                "4.0",
            )

    def test_init_creates_empty_events_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            main(["init", "--docs-dir", str(docs_dir)])
            events_log = docs_dir / "_architect_state" / "events.jsonl"
            self.assertTrue(events_log.exists())
            self.assertEqual(events_log.read_text(), "")

    def test_init_writes_all_concern_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            main(["init", "--docs-dir", str(docs_dir)])
            state_dir = docs_dir / "_architect_state"
            for name in ["identity", "vision", "architecture", "stack", "cost",
                         "ai_agent", "api_contract", "docs", "workflow",
                         "tooling", "handoff"]:
                self.assertTrue(
                    (state_dir / f"{name}.json").exists(),
                    f"missing {name}.json",
                )
            self.assertTrue((state_dir / "99-flat-index.json").exists())

    def test_init_creates_intermediate_parent_dirs(self):
        """parents=True: missing docs/ AND missing intermediate dirs are created."""
        with tempfile.TemporaryDirectory() as tmp:
            # NOTE: does NOT pre-mkdir any of the intermediate directories
            deep = Path(tmp) / "missing" / "intermediate" / "docs"
            exit_code = main(["init", "--docs-dir", str(deep)])
            self.assertEqual(exit_code, 0)
            self.assertTrue((deep / "_architect_state" / "schema_version").exists())

    def test_init_default_docs_dir_uses_cwd(self):
        """When --docs-dir is omitted, default is './docs'."""
        with tempfile.TemporaryDirectory() as tmp:
            import os
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                Path("docs").mkdir()
                main(["init"])
                self.assertTrue((Path(tmp) / "docs" / "_architect_state" / "schema_version").exists())
            finally:
                os.chdir(orig_cwd)


class TestCLIDetect(unittest.TestCase):

    def test_detect_outputs_json_for_greenfield(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = main(["detect", "--docs-dir", str(docs_dir)])
            self.assertEqual(exit_code, 0)
            result = json.loads(buf.getvalue())
            self.assertEqual(result["situation"], "greenfield")

    def test_detect_outputs_json_for_v8_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / "docs"
            docs_dir.mkdir()
            # init first, then detect
            main(["init", "--docs-dir", str(docs_dir)])
            buf = io.StringIO()
            with redirect_stdout(buf):
                main(["detect", "--docs-dir", str(docs_dir)])
            result = json.loads(buf.getvalue())
            self.assertEqual(result["situation"], "v8_project")
            self.assertEqual(result["schema_version"], "4.0")


if __name__ == "__main__":
    unittest.main()
