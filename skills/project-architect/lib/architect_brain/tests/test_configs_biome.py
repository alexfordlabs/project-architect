"""Tests for architect_brain.configs.gen_biome_json."""

import json
import unittest

from architect_brain.configs import gen_biome_json


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenBiomeJson(unittest.TestCase):

    def test_valid_json_trailing_newline(self):
        out = gen_biome_json(_fi())
        self.assertTrue(out.endswith("\n"))
        json.loads(out)

    def test_has_schema_url(self):
        cfg = json.loads(gen_biome_json(_fi()))
        self.assertIn("$schema", cfg)
        self.assertIn("biomejs.dev", cfg["$schema"])

    def test_recommended_rules_enabled(self):
        cfg = json.loads(gen_biome_json(_fi()))
        self.assertTrue(cfg["linter"]["enabled"])
        self.assertTrue(cfg["linter"]["rules"]["recommended"])

    def test_formatter_present(self):
        cfg = json.loads(gen_biome_json(_fi()))
        self.assertTrue(cfg["formatter"]["enabled"])

    def test_deterministic(self):
        self.assertEqual(gen_biome_json(_fi()), gen_biome_json(_fi()))

    # ── schema version comes from researched state, not frozen ──
    def test_uses_recorded_biome_schema(self):
        cfg = json.loads(gen_biome_json(_fi({"stack.versions.biome": "2.1.0"})))
        self.assertIn("/2.1.0/", cfg["$schema"])

    def test_biome_schema_falls_back_to_floor(self):
        cfg = json.loads(gen_biome_json(_fi()))
        self.assertIn("/1.9.4/", cfg["$schema"])


if __name__ == "__main__":
    unittest.main()
