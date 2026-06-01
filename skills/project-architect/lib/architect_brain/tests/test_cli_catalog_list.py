"""Tests for `architect-brain catalog list`."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


def _doc(conditions, depends_on=None, phase="doc_generation"):
    return {
        "conditions": conditions,
        "depends_on": depends_on or [],
        "produces": [], "produced_by": "document-author",
        "template": "t.md", "phase": phase, "concern": "vision",
    }


CATALOG = {
    "schema_version": "4.0",
    "catalog_version": "8.0.0",
    "documents": {
        "PROJECT_OVERVIEW": _doc(["ALWAYS"]),
        "ARCHITECTURE_DECISIONS": _doc(["ALWAYS"], ["PROJECT_OVERVIEW"]),
        "AGENT_DESIGN": _doc(["ai.enabled == true"], ["ARCHITECTURE_DECISIONS"], phase="architecture"),
        "MOBILE_SPECIFIC": _doc(["project.type == 'mobile_app'"]),
    },
}


def _setup(tmp: str, decisions: dict) -> tuple[Path, Path]:
    docs_dir = Path(tmp) / "docs"
    state_dir = docs_dir / "_architect_state"
    state_dir.mkdir(parents=True)
    (state_dir / "99-flat-index.json").write_text(
        json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
        encoding="utf-8",
    )
    catalog_path = Path(tmp) / "catalog.json"
    catalog_path.write_text(json.dumps(CATALOG), encoding="utf-8")
    return docs_dir, catalog_path


class TestCatalogListCLI(unittest.TestCase):

    def test_lists_applicable_docs_in_topo_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir, catalog_path = _setup(tmp, {"ai.enabled": True})
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main([
                    "catalog", "list",
                    "--docs-dir", str(docs_dir),
                    "--catalog", str(catalog_path),
                ])
            self.assertEqual(code, 0)
            lines = buf.getvalue().split()
            self.assertEqual(
                lines,
                ["PROJECT_OVERVIEW", "ARCHITECTURE_DECISIONS", "AGENT_DESIGN"],
            )

    def test_excludes_false_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir, catalog_path = _setup(tmp, {"ai.enabled": False, "project.type": "web_app"})
            buf = io.StringIO()
            with redirect_stdout(buf):
                main(["catalog", "list", "--docs-dir", str(docs_dir), "--catalog", str(catalog_path)])
            out = buf.getvalue()
            self.assertNotIn("AGENT_DESIGN", out)
            self.assertNotIn("MOBILE_SPECIFIC", out)

    def test_phase_filter_preserves_topo_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir, catalog_path = _setup(tmp, {"ai.enabled": True})
            buf = io.StringIO()
            with redirect_stdout(buf):
                main([
                    "catalog", "list", "--phase", "architecture",
                    "--docs-dir", str(docs_dir), "--catalog", str(catalog_path),
                ])
            self.assertEqual(buf.getvalue().split(), ["AGENT_DESIGN"])


if __name__ == "__main__":
    unittest.main()
