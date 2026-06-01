"""Tests for architect_brain.catalog.load_catalog — JSON-load + validation."""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.catalog import CatalogError, load_catalog


def _write(tmp: str, obj) -> Path:
    p = Path(tmp) / "catalog.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


_VALID = {
    "schema_version": "4.0",
    "catalog_version": "8.0.0",
    "documents": {
        "PROJECT_OVERVIEW": {
            "conditions": ["ALWAYS"],
            "depends_on": [],
            "produces": ["docs/PROJECT_OVERVIEW.md"],
            "produced_by": "document-author",
            "template": "templates/PROJECT_OVERVIEW.md",
            "phase": "doc_generation",
            "concern": "vision",
        }
    },
}


class TestLoadCatalog(unittest.TestCase):

    def test_loads_valid_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = load_catalog(_write(tmp, _VALID))
            self.assertEqual(cat["catalog_version"], "8.0.0")
            self.assertIn("PROJECT_OVERVIEW", cat["documents"])

    def test_rejects_missing_documents_key(self):
        bad = {"schema_version": "4.0", "catalog_version": "8.0.0"}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CatalogError):
                load_catalog(_write(tmp, bad))

    def test_rejects_wrong_schema_version(self):
        bad = dict(_VALID, schema_version="3.0")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CatalogError):
                load_catalog(_write(tmp, bad))

    def test_rejects_document_missing_required_field(self):
        bad = json.loads(json.dumps(_VALID))
        del bad["documents"]["PROJECT_OVERVIEW"]["produced_by"]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CatalogError) as ctx:
                load_catalog(_write(tmp, bad))
            self.assertIn("produced_by", str(ctx.exception))

    def test_rejects_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "catalog.json"
            p.write_text("{not json", encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_catalog(p)


if __name__ == "__main__":
    unittest.main()
