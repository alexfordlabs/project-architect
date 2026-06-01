"""Tests for `architect-brain catalog cycle`."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


def _doc(depends_on):
    return {
        "conditions": ["ALWAYS"], "depends_on": depends_on,
        "produces": [], "produced_by": "document-author",
        "template": "t.md", "phase": "doc_generation", "concern": "vision",
    }


def _write_catalog(tmp: str, documents: dict) -> Path:
    p = Path(tmp) / "catalog.json"
    p.write_text(json.dumps({
        "schema_version": "4.0", "catalog_version": "8.0.0", "documents": documents,
    }), encoding="utf-8")
    return p


class TestCatalogCycleCLI(unittest.TestCase):

    def test_acyclic_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = _write_catalog(tmp, {"A": _doc([]), "B": _doc(["A"])})
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["catalog", "cycle", "--catalog", str(cat)])
            self.assertEqual(code, 0)
            self.assertIn("no cycles", buf.getvalue().lower())

    def test_cycle_returns_one_and_prints_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = _write_catalog(tmp, {"A": _doc(["B"]), "B": _doc(["A"])})
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["catalog", "cycle", "--catalog", str(cat)])
            self.assertEqual(code, 1)
            out = buf.getvalue()
            self.assertIn("A", out)
            self.assertIn("B", out)


if __name__ == "__main__":
    unittest.main()
