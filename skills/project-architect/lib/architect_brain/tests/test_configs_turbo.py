"""Tests for architect_brain.configs.gen_turbo_json."""

import json
import unittest

from architect_brain.configs import gen_turbo_json


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenTurboJson(unittest.TestCase):

    def test_valid_json_trailing_newline(self):
        out = gen_turbo_json(_fi())
        self.assertTrue(out.endswith("\n"))
        json.loads(out)

    def test_has_schema(self):
        cfg = json.loads(gen_turbo_json(_fi()))
        self.assertIn("$schema", cfg)
        self.assertIn("turbo.build", cfg["$schema"])

    def test_uses_tasks_key_not_pipeline(self):
        cfg = json.loads(gen_turbo_json(_fi()))
        self.assertIn("tasks", cfg)            # Turbo 2.x
        self.assertNotIn("pipeline", cfg)      # Turbo 1.x legacy

    def test_build_depends_on_topo(self):
        cfg = json.loads(gen_turbo_json(_fi()))
        self.assertIn("^build", cfg["tasks"]["build"]["dependsOn"])

    def test_deterministic(self):
        self.assertEqual(gen_turbo_json(_fi()), gen_turbo_json(_fi()))


if __name__ == "__main__":
    unittest.main()
