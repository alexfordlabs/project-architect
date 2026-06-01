"""Tests for architect_brain.golden_paths — load + accessors."""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.golden_paths import (
    GoldenPathError,
    decisions_for,
    list_paths,
    load_golden_paths,
)


def _write(tmp: str, obj) -> Path:
    p = Path(tmp) / "golden-paths.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


_VALID = {
    "schema_version": "4.0",
    "paths": [
        {
            "id": "modern_saas_2026",
            "label": "Modern SaaS (2026)",
            "description": "Next.js + PostgreSQL + Drizzle",
            "decisions": {"project.type": "web_app", "stack.frontend.framework": "next.js"},
        },
        {
            "id": "cli_rust",
            "label": "CLI in Rust",
            "description": "A command-line tool in Rust",
            "decisions": {"project.type": "cli", "stack.backend.language": "rust"},
        },
    ],
}


class TestLoadGoldenPaths(unittest.TestCase):

    def test_loads_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            gp = load_golden_paths(_write(tmp, _VALID))
            self.assertEqual(len(gp["paths"]), 2)

    def test_rejects_missing_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GoldenPathError):
                load_golden_paths(_write(tmp, {"schema_version": "4.0"}))

    def test_rejects_wrong_schema_version(self):
        bad = dict(_VALID, schema_version="3.0")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GoldenPathError):
                load_golden_paths(_write(tmp, bad))

    def test_rejects_path_missing_decisions(self):
        bad = json.loads(json.dumps(_VALID))
        del bad["paths"][0]["decisions"]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GoldenPathError) as ctx:
                load_golden_paths(_write(tmp, bad))
            self.assertIn("decisions", str(ctx.exception))

    def test_rejects_duplicate_ids(self):
        bad = json.loads(json.dumps(_VALID))
        bad["paths"][1]["id"] = "modern_saas_2026"   # dup
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GoldenPathError):
                load_golden_paths(_write(tmp, bad))

    def test_rejects_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "golden-paths.json"
            p.write_text("{not json", encoding="utf-8")
            with self.assertRaises(GoldenPathError):
                load_golden_paths(p)

    def test_decisions_for_returns_dict(self):
        dec = decisions_for("cli_rust", _VALID)
        self.assertEqual(dec["stack.backend.language"], "rust")

    def test_decisions_for_unknown_raises(self):
        with self.assertRaises(GoldenPathError):
            decisions_for("nope", _VALID)

    def test_list_paths(self):
        rows = list_paths(_VALID)
        self.assertEqual([r["id"] for r in rows], ["modern_saas_2026", "cli_rust"])
        self.assertIn("label", rows[0])
        self.assertIn("description", rows[0])


if __name__ == "__main__":
    unittest.main()
