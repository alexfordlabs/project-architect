"""Tests for the check_34_build_pass auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_34_build_pass
from architect_brain.checks.check_34_build_pass import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    project_root = state_dir.parent.parent = ``<tmp>``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_decisions(state_dir: Path, decisions: dict) -> None:
    """Write the flat decision map via 99-flat-index.json (load_decisions reads this)."""
    (state_dir / "99-flat-index.json").write_text(
        json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
        encoding="utf-8",
    )


def _write_tooling(state_dir: Path, payload: dict) -> None:
    """Write the tooling.json projection (the fallback source for build_outcome)."""
    body = {"schema_version": "4.0", "concern": "tooling"}
    body.update(payload)
    (state_dir / "tooling.json").write_text(json.dumps(body), encoding="utf-8")


class TestCheck34Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "34")
        self.assertEqual(NAME, "build_pass")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_34_build_pass.CHECK_ID, "34")
        self.assertEqual(check_34_build_pass.NAME, "build_pass")
        self.assertEqual(check_34_build_pass.SEVERITY, "BLOCKING")
        self.assertTrue(callable(check_34_build_pass.run))


class TestCheck34Degraded(unittest.TestCase):
    def test_empty_state_passes(self):
        # Fresh project: no flat index, no tooling projection → build not yet run.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "34")
            self.assertEqual(result.findings, ())

    def test_outcome_absent_passes(self):
        # Decisions exist but carry no build_outcome → not required pre-Phase-8.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"stack.language": "rust"})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_outcome_empty_string_passes(self):
        # Falsy recorded value (empty string) → treated as "not yet run".
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"tooling.build_outcome": ""})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_outcome_none_value_passes(self):
        # An explicit null recorded value is falsy → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"tooling.build_outcome": None})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_never_raises_on_missing_state_dir(self):
        # Defensive: a state_dir that does not exist must still return a CheckResult.
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does" / "not" / "exist"
            result = run(missing)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "34")

    def test_accepts_str_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"tooling.build_outcome": "green"})
            result = run(str(state))
            self.assertTrue(result.passed)


class TestCheck34Pass(unittest.TestCase):
    def test_green_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"tooling.build_outcome": "green"})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_exhausted_with_diagnostic_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(
                state, {"tooling.build_outcome": "exhausted_with_diagnostic"}
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_green_via_tooling_projection_fallback(self):
        # No flat decision; build_outcome lives on the tooling.json projection.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_tooling(state, {"build_outcome": "green"})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_flat_decision_takes_priority_over_projection(self):
        # The flat decision wins: green flat + failed projection → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"tooling.build_outcome": "green"})
            _write_tooling(state, {"build_outcome": "failed"})
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck34Fail(unittest.TestCase):
    def test_failed_outcome_fails_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"tooling.build_outcome": "failed"})
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "34")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("failed", result.findings[0].message)
            self.assertIn(
                "expected green|exhausted_with_diagnostic",
                result.findings[0].message,
            )

    def test_red_outcome_fails_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_decisions(state, {"tooling.build_outcome": "red"})
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("red", result.findings[0].message)

    def test_failed_via_projection_fallback_fails_blocking(self):
        # The fallback source participates in the fail path, not just pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_tooling(state, {"build_outcome": "failed"})
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("failed", result.findings[0].message)


if __name__ == "__main__":
    unittest.main()
