"""Tests for the check_26_scaffold_executed auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_26_scaffold_executed
from architect_brain.checks.check_26_scaffold_executed import (
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


def _write_workflow(state_dir: Path, current_phase) -> None:
    payload = {"schema_version": "4.0"}
    if current_phase is not None:
        payload["current_phase"] = current_phase
    (state_dir / "workflow.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_decisions(state_dir: Path, decisions: dict) -> None:
    (state_dir / "99-flat-index.json").write_text(
        json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
        encoding="utf-8",
    )


def _mkpaths(project_root: Path, rels) -> None:
    """Materialise each relative path under project_root (as a dir)."""
    for rel in rels:
        (project_root / rel).mkdir(parents=True, exist_ok=True)


class TestCheck26Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "26")
        self.assertEqual(NAME, "scaffold_executed")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_26_scaffold_executed.CHECK_ID, "26")
        self.assertTrue(callable(check_26_scaffold_executed.run))


class TestCheck26Degraded(unittest.TestCase):
    def test_empty_state_passes(self):
        # Fresh project: no workflow, no decisions → nothing to verify.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "26")
            self.assertEqual(result.findings, ())

    def test_pre_handoff_phase_passes(self):
        # v8-ADAPTATION: gate uses v8 phase keys. "architecture" is pre-handoff
        # → pass even though the layout names a missing path.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "architecture")
            _write_decisions(state, {"project_layout": {"core": "crates/never-made"}})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_kickoff_phase_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "kickoff")
            _write_decisions(state, {"project_layout": {"core": "crates/never-made"}})
            self.assertTrue(run(state).passed)

    def test_scaffold_deferred_passes(self):
        # Explicit opt-out: scaffold.deferred is True → pass even at handoff with
        # a missing path.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(
                state,
                {
                    "scaffold.deferred": True,
                    "project_layout": {"core": "crates/never-made"},
                },
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_scaffold_deferred_non_bool_does_not_pass_via_gate(self):
        # Only the boolean True defers. A truthy string "true" must NOT short-
        # circuit the deferral gate (spec says ``is True``), so verification runs.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "complete")
            _write_decisions(
                state,
                {
                    "scaffold.deferred": "true",
                    "project_layout": {"core": "crates/never-made"},
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")

    def test_empty_layout_passes(self):
        # At handoff but project_layout is an empty dict → cannot confirm → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(state, {"project_layout": {}})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_layout_absent_passes(self):
        # At handoff, no project_layout key at all → cannot confirm → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "complete")
            _write_decisions(state, {"some.other.key": "value"})
            result = run(state)
            self.assertTrue(result.passed)

    def test_layout_not_a_dict_passes(self):
        # project_layout recorded as something other than a non-empty dict.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(state, {"project_layout": ["crates/a", "crates/b"]})
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck26Pass(unittest.TestCase):
    def test_all_paths_exist_at_handoff_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            proj = Path(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(
                state,
                {"project_layout": {"core": "crates/demo-core", "app": "apps/web"}},
            )
            _mkpaths(proj, ["crates/demo-core", "apps/web"])
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_all_paths_exist_at_complete_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            proj = Path(tmp)
            _write_workflow(state, "complete")
            _write_decisions(state, {"project_layout": {"src": "src"}})
            _mkpaths(proj, ["src"])
            self.assertTrue(run(state).passed)

    def test_all_paths_exist_at_tooling_passes(self):
        # "tooling" is the first handoff-window phase per the spec gate set.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            proj = Path(tmp)
            _write_workflow(state, "tooling")
            _write_decisions(state, {"project_layout": {"src": "src"}})
            _mkpaths(proj, ["src"])
            self.assertTrue(run(state).passed)

    def test_layout_value_may_be_a_file(self):
        # Existence is by .exists() — a layout value may name a file, not a dir.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            proj = Path(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(state, {"project_layout": {"manifest": "Cargo.toml"}})
            (proj / "Cargo.toml").write_text("[package]\n", encoding="utf-8")
            self.assertTrue(run(state).passed)

    def test_tooling_prefixed_layout_key_used_as_fallback(self):
        # When project_layout is absent, tooling.project_layout is read instead.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            proj = Path(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(
                state, {"tooling.project_layout": {"core": "crates/demo-core"}}
            )
            _mkpaths(proj, ["crates/demo-core"])
            self.assertTrue(run(state).passed)


class TestCheck26Fail(unittest.TestCase):
    def test_missing_path_fails_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            proj = Path(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(
                state,
                {"project_layout": {"core": "crates/demo-core", "app": "apps/web"}},
            )
            # Only one of the two paths materialised.
            _mkpaths(proj, ["crates/demo-core"])
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "26")
            self.assertEqual(len(result.findings), 1)
            self.assertIn(
                "project_layout path missing on disk: apps/web",
                result.findings[0].message,
            )
            self.assertEqual(result.findings[0].location, "apps/web")

    def test_all_missing_paths_each_get_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "complete")
            _write_decisions(
                state,
                {"project_layout": {"a": "crates/a", "b": "crates/b", "c": "crates/c"}},
            )
            # Materialise none.
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 3)
            missing = {f.location for f in result.findings}
            self.assertEqual(missing, {"crates/a", "crates/b", "crates/c"})

    def test_tooling_fallback_missing_path_fails(self):
        # Fallback key participates in verification, not just pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, "handoff")
            _write_decisions(
                state, {"tooling.project_layout": {"core": "crates/never-made"}}
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "crates/never-made")


if __name__ == "__main__":
    unittest.main()
