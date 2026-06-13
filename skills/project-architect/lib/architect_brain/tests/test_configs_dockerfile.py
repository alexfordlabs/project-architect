"""Tests for architect_brain.configs.gen_dockerfile + dockerfile_language."""

import unittest

from architect_brain.configs import dockerfile_language, gen_dockerfile


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestDockerfileLanguage(unittest.TestCase):
    """Which runtime (if any) a Dockerfile can honestly be generated for.

    Guards the v9.1 fix: a rust/go/unknown stack must NOT silently receive a
    node Dockerfile (the old unconditional default), and a stack with no
    language decided gets no Dockerfile at all.
    """

    def test_python_backend(self):
        self.assertEqual(
            dockerfile_language(_fi({"stack.backend.language": "python"})), "python"
        )

    def test_typescript_backend_is_node_runtime(self):
        self.assertEqual(
            dockerfile_language(_fi({"stack.backend.language": "typescript"})), "node"
        )

    def test_javascript_frontend_is_node_runtime(self):
        self.assertEqual(
            dockerfile_language(_fi({"stack.frontend.language": "javascript"})), "node"
        )

    def test_frontend_framework_implies_node(self):
        self.assertEqual(
            dockerfile_language(_fi({"stack.frontend.framework": "next.js"})), "node"
        )

    def test_rust_is_not_containerized_by_us(self):
        self.assertIsNone(dockerfile_language(_fi({"stack.backend.language": "rust"})))

    def test_go_is_not_containerized_by_us(self):
        self.assertIsNone(dockerfile_language(_fi({"stack.backend.language": "go"})))

    def test_no_language_no_dockerfile(self):
        self.assertIsNone(dockerfile_language(_fi()))

    def test_backend_language_wins_over_frontend_framework(self):
        # e.g. the ai_rag_app golden path: next.js frontend + python backend →
        # the deploy artifact is the python service.
        self.assertEqual(
            dockerfile_language(_fi({
                "stack.frontend.framework": "next.js",
                "stack.backend.language": "python",
            })),
            "python",
        )


class TestGenDockerfile(unittest.TestCase):

    def test_multi_stage(self):
        out = gen_dockerfile(_fi({"stack.backend.language": "typescript"}))
        self.assertGreaterEqual(out.count("FROM "), 2)
        self.assertIn(" AS build", out)

    def test_node_for_typescript(self):
        out = gen_dockerfile(_fi({"stack.backend.language": "typescript"}))
        self.assertIn("node:", out)

    def test_python_branch(self):
        out = gen_dockerfile(_fi({"stack.backend.language": "python"}))
        self.assertIn("python:", out)
        self.assertNotIn("node:", out)

    def test_unsupported_language_raises(self):
        # No more silent node fallback: a rust stack must never get a node image.
        with self.assertRaises(ValueError):
            gen_dockerfile(_fi({"stack.backend.language": "rust"}))

    def test_no_language_raises(self):
        with self.assertRaises(ValueError):
            gen_dockerfile(_fi())

    def test_distroless_runtime_when_supply_chain_security(self):
        out = gen_dockerfile(_fi({
            "stack.backend.language": "typescript",
            "constraints.supply_chain_security": True,
        }))
        self.assertIn("distroless", out)

    def test_no_distroless_by_default(self):
        self.assertNotIn(
            "distroless", gen_dockerfile(_fi({"stack.backend.language": "typescript"}))
        )

    def test_trailing_newline_and_deterministic(self):
        fi = _fi({"stack.backend.language": "python", "constraints.supply_chain_security": True})
        out = gen_dockerfile(fi)
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(gen_dockerfile(fi), gen_dockerfile(fi))

    # ── v8.0.1: runtime image tags come from researched state, not frozen ──
    def test_uses_recorded_node_image_tag(self):
        out = gen_dockerfile(_fi({
            "stack.backend.language": "typescript", "stack.versions.node": "26",
        }))
        self.assertIn("node:26-slim", out)

    def test_uses_recorded_python_image_tag(self):
        out = gen_dockerfile(_fi({
            "stack.backend.language": "python", "stack.versions.python": "3.13",
        }))
        self.assertIn("python:3.13-slim", out)

    # Floors = newest stable / active-LTS at plugin-release time (2026-06):
    # node 24 (Active LTS), python 3.14.
    def test_node_image_falls_back_to_floor(self):
        self.assertIn(
            "node:24-slim", gen_dockerfile(_fi({"stack.backend.language": "typescript"}))
        )

    def test_python_image_falls_back_to_floor(self):
        self.assertIn(
            "python:3.14-slim", gen_dockerfile(_fi({"stack.backend.language": "python"}))
        )


if __name__ == "__main__":
    unittest.main()
