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
        # Floor = newest stable at plugin-release time (2.5.0 as of 2026-06).
        cfg = json.loads(gen_biome_json(_fi()))
        self.assertIn("/2.5.0/", cfg["$schema"])

    def test_range_prefix_stripped_from_schema_url(self):
        # A pin recorded with a range operator still yields a bare-version URL.
        cfg = json.loads(gen_biome_json(_fi({"stack.versions.biome": "^2.5.0"})))
        self.assertIn("/2.5.0/", cfg["$schema"])

    # ── config shape tracks the pinned major (Biome 2.0 moved organizeImports) ──
    def test_2x_pin_emits_assist_shape_not_legacy_organize_imports(self):
        cfg = json.loads(gen_biome_json(_fi({"stack.versions.biome": "2.5.0"})))
        self.assertNotIn("organizeImports", cfg)
        self.assertEqual(
            cfg["assist"]["actions"]["source"]["organizeImports"], "on"
        )

    def test_2x_pin_uses_cross_2x_recommended_form(self):
        # `rules.recommended: true` is valid on every 2.x (and 1.x); the newer
        # `rules.preset` alias is 2.5-only — live-validated against a 2.4.15
        # binary, which rejects `preset` as an unknown key.
        cfg = json.loads(gen_biome_json(_fi({"stack.versions.biome": "2.5.0"})))
        self.assertEqual(cfg["linter"]["rules"], {"recommended": True})

    def test_floor_default_is_2x_shape(self):
        cfg = json.loads(gen_biome_json(_fi()))
        self.assertNotIn("organizeImports", cfg)
        self.assertIn("assist", cfg)

    def test_1x_pin_emits_legacy_organize_imports(self):
        cfg = json.loads(gen_biome_json(_fi({"stack.versions.biome": "1.9.4"})))
        self.assertTrue(cfg["organizeImports"]["enabled"])
        self.assertTrue(cfg["linter"]["rules"]["recommended"])
        self.assertNotIn("assist", cfg)


if __name__ == "__main__":
    unittest.main()
