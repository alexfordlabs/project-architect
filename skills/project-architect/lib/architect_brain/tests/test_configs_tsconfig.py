"""Tests for architect_brain.configs.gen_tsconfig."""

import json
import unittest

from architect_brain.configs import gen_tsconfig


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenTsconfig(unittest.TestCase):

    def test_valid_json_trailing_newline(self):
        out = gen_tsconfig(_fi())
        self.assertTrue(out.endswith("\n"))
        json.loads(out)

    def test_strict_mode_on(self):
        cfg = json.loads(gen_tsconfig(_fi()))
        self.assertTrue(cfg["compilerOptions"]["strict"])

    def test_modern_safety_flags(self):
        opts = json.loads(gen_tsconfig(_fi()))["compilerOptions"]
        self.assertTrue(opts["noUncheckedIndexedAccess"])
        self.assertEqual(opts["moduleResolution"], "bundler")
        self.assertEqual(opts["target"], "ES2022")

    def test_deterministic(self):
        self.assertEqual(gen_tsconfig(_fi()), gen_tsconfig(_fi()))


if __name__ == "__main__":
    unittest.main()
