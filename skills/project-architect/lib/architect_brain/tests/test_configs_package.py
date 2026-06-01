"""Tests for architect_brain.configs.gen_package_json."""

import json
import unittest

from architect_brain.configs import gen_package_json


def _fi(decisions):
    return {"schema_version": "4.0", "decisions": decisions, "adrs": []}


class TestGenPackageJson(unittest.TestCase):

    def test_valid_json_with_trailing_newline(self):
        out = gen_package_json(_fi({}))
        self.assertTrue(out.endswith("\n"))
        json.loads(out)  # must parse

    def test_default_name_is_app(self):
        pkg = json.loads(gen_package_json(_fi({})))
        self.assertEqual(pkg["name"], "app")

    def test_uses_project_name_decision(self):
        pkg = json.loads(gen_package_json(_fi({"project.name": "my-thing"})))
        self.assertEqual(pkg["name"], "my-thing")

    def test_nextjs_stack_emits_next_scripts_and_deps(self):
        pkg = json.loads(gen_package_json(_fi({"stack.frontend.framework": "next.js"})))
        self.assertEqual(pkg["scripts"]["dev"], "next dev")
        self.assertIn("next", pkg["dependencies"])

    def test_non_nextjs_has_no_next_dependency(self):
        pkg = json.loads(gen_package_json(_fi({})))
        self.assertNotIn("next", pkg.get("dependencies", {}))

    def test_deterministic(self):
        fi = _fi({"project.name": "x", "stack.frontend.framework": "next.js"})
        self.assertEqual(gen_package_json(fi), gen_package_json(fi))

    # ── v8.0.1: version pins come from researched state, not frozen constants ──
    def test_uses_recorded_next_version_pin(self):
        pkg = json.loads(gen_package_json(_fi({
            "stack.frontend.framework": "next.js",
            "stack.versions.next": "^16.2.6",
        })))
        self.assertEqual(pkg["dependencies"]["next"], "^16.2.6")

    def test_recorded_react_version_drives_react_and_react_dom(self):
        pkg = json.loads(gen_package_json(_fi({
            "stack.frontend.framework": "next.js",
            "stack.versions.react": "^19.2.0",
        })))
        self.assertEqual(pkg["dependencies"]["react"], "^19.2.0")
        self.assertEqual(pkg["dependencies"]["react-dom"], "^19.2.0")

    def test_falls_back_to_floor_when_no_recorded_version(self):
        # No stack.versions.* recorded => conservative plugin floor (deterministic).
        pkg = json.loads(gen_package_json(_fi({"stack.frontend.framework": "next.js"})))
        self.assertEqual(pkg["dependencies"]["next"], "^15.0.0")
        self.assertEqual(pkg["dependencies"]["react"], "^19.0.0")
        self.assertEqual(pkg["dependencies"]["react-dom"], "^19.0.0")

    def test_recorded_pin_still_deterministic(self):
        fi = _fi({"stack.frontend.framework": "next.js", "stack.versions.next": "^16.2.6"})
        self.assertEqual(gen_package_json(fi), gen_package_json(fi))


if __name__ == "__main__":
    unittest.main()
