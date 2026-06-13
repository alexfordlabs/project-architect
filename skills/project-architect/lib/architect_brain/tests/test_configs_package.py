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
        # No stack.versions.* recorded => floor = newest stable at plugin-release
        # time (next 16 / react 19 as of 2026-06), still deterministic.
        pkg = json.loads(gen_package_json(_fi({"stack.frontend.framework": "next.js"})))
        self.assertEqual(pkg["dependencies"]["next"], "^16.0.0")
        self.assertEqual(pkg["dependencies"]["react"], "^19.0.0")
        self.assertEqual(pkg["dependencies"]["react-dom"], "^19.0.0")

    def test_recorded_pin_still_deterministic(self):
        fi = _fi({"stack.frontend.framework": "next.js", "stack.versions.next": "^16.2.6"})
        self.assertEqual(gen_package_json(fi), gen_package_json(fi))

    # ── devDependencies: every tool the scripts invoke is declared + pinned ──
    def test_nextjs_devdeps_declare_biome_and_typescript(self):
        pkg = json.loads(gen_package_json(_fi({"stack.frontend.framework": "next.js"})))
        dev = pkg["devDependencies"]
        self.assertEqual(dev["@biomejs/biome"], "2.5.0")  # exact pin (Biome convention)
        self.assertEqual(dev["typescript"], "^6.0.0")
        self.assertEqual(dev["@types/node"], "^24.0.0")

    def test_nextjs_devdeps_include_react_types_tracking_react_pin(self):
        pkg = json.loads(gen_package_json(_fi({
            "stack.frontend.framework": "next.js",
            "stack.versions.react": "^19.2.0",
        })))
        dev = pkg["devDependencies"]
        self.assertEqual(dev["@types/react"], "^19.2.0")
        self.assertEqual(dev["@types/react-dom"], "^19.2.0")

    def test_plain_ts_devdeps_declare_toolchain(self):
        # The non-framework branch's scripts run tsc + biome + node --test:
        # all three need declared, pinned devDependencies.
        pkg = json.loads(gen_package_json(_fi({})))
        dev = pkg["devDependencies"]
        self.assertEqual(dev["@biomejs/biome"], "2.5.0")
        self.assertEqual(dev["typescript"], "^6.0.0")
        self.assertEqual(dev["@types/node"], "^24.0.0")

    def test_devdeps_track_recorded_pins(self):
        pkg = json.loads(gen_package_json(_fi({
            "stack.versions.biome": "2.6.1",
            "stack.versions.typescript": "^6.1.0",
            "stack.versions.node": "26",
        })))
        dev = pkg["devDependencies"]
        self.assertEqual(dev["@biomejs/biome"], "2.6.1")
        self.assertEqual(dev["typescript"], "^6.1.0")
        self.assertEqual(dev["@types/node"], "^26.0.0")

    def test_types_node_derived_from_node_major_only(self):
        # A node pin with minor/patch (or a docker-ish tag) still yields a
        # major-line @types/node range.
        pkg = json.loads(gen_package_json(_fi({"stack.versions.node": "24.16.0"})))
        self.assertEqual(pkg["devDependencies"]["@types/node"], "^24.0.0")


if __name__ == "__main__":
    unittest.main()
