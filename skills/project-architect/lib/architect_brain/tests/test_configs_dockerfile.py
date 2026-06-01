"""Tests for architect_brain.configs.gen_dockerfile."""

import unittest

from architect_brain.configs import gen_dockerfile


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenDockerfile(unittest.TestCase):

    def test_multi_stage(self):
        out = gen_dockerfile(_fi())
        self.assertGreaterEqual(out.count("FROM "), 2)
        self.assertIn(" AS build", out)

    def test_node_default(self):
        out = gen_dockerfile(_fi())
        self.assertIn("node:", out)

    def test_python_branch(self):
        out = gen_dockerfile(_fi({"stack.backend.language": "python"}))
        self.assertIn("python:", out)
        self.assertNotIn("node:", out)

    def test_distroless_runtime_when_supply_chain_security(self):
        out = gen_dockerfile(_fi({"constraints.supply_chain_security": True}))
        self.assertIn("distroless", out)

    def test_no_distroless_by_default(self):
        self.assertNotIn("distroless", gen_dockerfile(_fi()))

    def test_trailing_newline_and_deterministic(self):
        out = gen_dockerfile(_fi({"stack.backend.language": "python", "constraints.supply_chain_security": True}))
        self.assertTrue(out.endswith("\n"))
        fi = _fi({"stack.backend.language": "python", "constraints.supply_chain_security": True})
        self.assertEqual(gen_dockerfile(fi), gen_dockerfile(fi))

    # ── v8.0.1: runtime image tags come from researched state, not frozen ──
    def test_uses_recorded_node_image_tag(self):
        out = gen_dockerfile(_fi({"stack.versions.node": "24"}))
        self.assertIn("node:24-slim", out)

    def test_uses_recorded_python_image_tag(self):
        out = gen_dockerfile(_fi({
            "stack.backend.language": "python", "stack.versions.python": "3.13",
        }))
        self.assertIn("python:3.13-slim", out)

    def test_node_image_falls_back_to_floor(self):
        self.assertIn("node:22-slim", gen_dockerfile(_fi()))

    def test_python_image_falls_back_to_floor(self):
        self.assertIn("python:3.11-slim", gen_dockerfile(_fi({"stack.backend.language": "python"})))


if __name__ == "__main__":
    unittest.main()
