"""Tests for the check_36_version_pins_recorded auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

The enforcement closing the tiger-panther-game gap: generate-configs emits an
artifact whose version came from the plugin's baked floor whenever the
corresponding ``stack.versions.<token>`` decision was never recorded — silently.
check_36 makes that mechanical: artifact on disk + applicable token + no
recorded pin => WARNING finding naming the exact ``set-decision`` to run.
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks.check_36_version_pins_recorded import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str, decisions: dict) -> Path:
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    (state / "99-flat-index.json").write_text(
        json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
        encoding="utf-8",
    )
    return state


def _touch(state_dir: Path, fname: str, content: str = "{}") -> None:
    (state_dir.parent.parent / fname).write_text(content, encoding="utf-8")


class TestCheck36Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "36")
        self.assertEqual(NAME, "version_pins_recorded")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))

    def test_registered_in_all_checks(self):
        from architect_brain.checks import ALL_CHECKS

        self.assertIn("36", [getattr(c, "CHECK_ID", None) for c in ALL_CHECKS])


class TestCheck36Pass(unittest.TestCase):
    def test_no_artifacts_nothing_to_verify(self):
        # JS stack decided but nothing generated yet → pass (pre-scaffold).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {"stack.frontend.framework": "next.js"})
            self.assertTrue(run(state).passed)

    def test_all_applicable_pins_recorded_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {
                "stack.frontend.framework": "next.js",
                "stack.versions.next": "^16.2.6",
                "stack.versions.react": "^19.2.0",
                "stack.versions.node": "24",
                "stack.versions.typescript": "^6.0.0",
                "stack.versions.biome": "2.5.0",
            })
            _touch(state, "package.json")
            _touch(state, "biome.json")
            result = run(state)
            self.assertTrue(result.passed, [f.message for f in result.findings])

    def test_non_js_stack_ignores_js_artifacts(self):
        # A stray package.json in a pure-rust project owes no JS pins.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {"stack.backend.language": "rust"})
            _touch(state, "package.json")
            self.assertTrue(run(state).passed)


class TestCheck36Fail(unittest.TestCase):
    def test_biome_json_without_biome_pin_flagged(self):
        # THE tiger-panther defect: biome.json on disk, no stack.versions.biome.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {
                "stack.frontend.framework": "next.js",
                "stack.versions.next": "^16.2.6",
                "stack.versions.react": "^19.2.0",
                "stack.versions.node": "24",
                "stack.versions.typescript": "^6.0.0",
            })
            _touch(state, "package.json")
            _touch(state, "biome.json")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("stack.versions.biome", result.findings[0].message)
            self.assertIn("biome.json", result.findings[0].message)

    def test_compose_without_engine_pins_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {
                "stack.backend.language": "python",
                "stack.versions.python": "3.14",
                "stack.database.engine": "postgresql",
                "stack.cache.engine": "redis",
            })
            _touch(state, "pyproject.toml", "[project]\n")
            _touch(state, "docker-compose.yml", "services: {}\n")
            result = run(state)
            self.assertFalse(result.passed)
            missing = {m for f in result.findings for m in ("postgres", "redis") if m in f.message}
            self.assertEqual(missing, {"postgres", "redis"})

    def test_dockerfile_without_runtime_pin_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {"stack.backend.language": "python"})
            _touch(state, "Dockerfile", "FROM python:3.14-slim\n")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("stack.versions.python" in f.message for f in result.findings)
            )

    def test_int_version_pin_consistent_with_pin_emission(self):
        # tiger-panther: check 36's "recorded" predicate (truthiness) disagreed
        # with _pin's "usable" predicate (isinstance str) on a numeric pin — so an
        # int 17 read as "recorded" by check 36 (no warning) while _pin floored it
        # to postgres:18. A single shared `usable_pin` predicate keeps emission,
        # obligation, and enforcement from ever diverging.
        from architect_brain.configs import _pin, usable_pin

        flat = {"decisions": {
            "stack.database.engine": "postgresql", "stack.versions.postgres": 17,
        }}
        self.assertEqual(usable_pin(flat, "postgres"), "17")  # the shared predicate
        self.assertEqual(_pin(flat, "postgres"), "17")        # honored, not floored to 18
        # …and check 36 agrees the int pin is recorded (does not flag postgres):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {
                "stack.backend.language": "python",
                "stack.versions.python": "3.14",
                "stack.database.engine": "postgresql",
                "stack.versions.postgres": 17,
            })
            _touch(state, "pyproject.toml", "[project]\n")
            _touch(state, "docker-compose.yml", "services: {}\n")
            result = run(state)
            self.assertTrue(
                all("postgres" not in f.message for f in result.findings),
                [f.message for f in result.findings],
            )

    def test_float_pin_is_flagged_not_silently_floored(self):
        # A float pin is refused by usable_pin (ambiguous), so _pin uses the floor
        # — and check 36 must make that VISIBLE (a float is not a usable recorded
        # pin), the opposite of the int case. Confirms emission and obligation
        # still agree: _pin floors it, check 36 flags it.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {
                "stack.backend.language": "python",
                "stack.versions.python": "3.14",
                "stack.database.engine": "postgresql",
                "stack.versions.postgres": 17.0,  # float — refused
            })
            _touch(state, "pyproject.toml", "[project]\n")
            _touch(state, "docker-compose.yml", "services: {}\n")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertTrue(any("stack.versions.postgres" in f.message for f in result.findings))

    def test_finding_names_the_remedy(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {"stack.frontend.framework": "next.js"})
            _touch(state, "biome.json")
            result = run(state)
            self.assertFalse(result.passed)
            biome = [f for f in result.findings if "stack.versions.biome" in f.message]
            self.assertEqual(len(biome), 1)
            self.assertIn("set-decision stack.versions.biome", biome[0].message)


if __name__ == "__main__":
    unittest.main()
