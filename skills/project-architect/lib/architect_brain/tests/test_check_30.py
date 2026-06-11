"""Tests for the check_30_decisions_index_fresh auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from architect_brain.events import EventEnvelope, append_event
from architect_brain.projections import projections_to_disk, replay
from architect_brain.checks import check_30_decisions_index_fresh
from architect_brain.checks.check_30_decisions_index_fresh import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _adr_event(adr_id: str, title: str, *, ulid: str) -> EventEnvelope:
    return EventEnvelope(
        id=ulid,
        ts="2026-05-29T12:00:00Z",
        by="orchestrator",
        phase="stack",
        type="ADRFiled",
        payload={"id": adr_id, "title": title, "status": "Accepted"},
    )


def _materialise(state: Path, events: list[EventEnvelope]) -> None:
    """Write an events.jsonl + materialise a consistent projection set on disk."""
    log = state / "events.jsonl"
    for event in events:
        append_event(log, event)
    projections = replay(log)
    projections_to_disk(state, projections)


class TestCheck30Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "30")
        self.assertEqual(NAME, "decisions_index_fresh")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_30_decisions_index_fresh.CHECK_ID, "30")
        self.assertEqual(check_30_decisions_index_fresh.NAME, "decisions_index_fresh")
        self.assertEqual(check_30_decisions_index_fresh.SEVERITY, "BLOCKING")
        self.assertTrue(hasattr(check_30_decisions_index_fresh, "run"))


class TestCheck30Pass(unittest.TestCase):
    def test_consistent_state_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [
                    _adr_event("0001", "Use Next.js 15", ulid="01J0000000000000000000000A"),
                    _adr_event("0002", "Use Postgres", ulid="01J0000000000000000000000B"),
                ],
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "30")
            self.assertEqual(result.findings, ())

    def test_empty_state_passes(self):
        # No events, no index.json on disk → both empty → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_materialised_empty_state_passes(self):
        # Replay of an empty log + projections_to_disk → empty adrs both sides.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            (state / "events.jsonl").write_text("", encoding="utf-8")
            projections_to_disk(state, replay(state / "events.jsonl"))
            result = run(state)
            self.assertTrue(result.passed)

    def test_volatile_regenerated_at_is_ignored(self):
        # Tamper ONLY the regenerated_at stamp → still passes (it's volatile).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [_adr_event("0001", "X", ulid="01J0000000000000000000000A")],
            )
            index_path = state / "decisions" / "index.json"
            data = json.loads(index_path.read_text(encoding="utf-8"))
            data["regenerated_at"] = "1999-01-01T00:00:00Z"
            index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)

    def test_accepts_str_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [_adr_event("0001", "X", ulid="01J0000000000000000000000A")],
            )
            self.assertTrue(run(str(state)).passed)


class TestCheck30Fail(unittest.TestCase):
    def test_added_adr_on_disk_fails_blocking(self):
        # Disk index has an EXTRA adr the event log never recorded → drift.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [_adr_event("0001", "X", ulid="01J0000000000000000000000A")],
            )
            index_path = state / "decisions" / "index.json"
            data = json.loads(index_path.read_text(encoding="utf-8"))
            data["adrs"].append(
                {
                    "id": "9999",
                    "title": "Phantom",
                    "status": "Accepted",
                    "date": "2026-05-29",
                    "phase": "stack",
                    "supersedes": [],
                    "superseded_by": [],
                }
            )
            index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "30")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("drifts from replay", result.findings[0].message)
            self.assertIn("expected 1", result.findings[0].message)
            self.assertIn("on-disk 2", result.findings[0].message)

    def test_removed_adr_on_disk_fails_blocking(self):
        # Disk index is MISSING an adr the event log recorded → drift.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [
                    _adr_event("0001", "A", ulid="01J0000000000000000000000A"),
                    _adr_event("0002", "B", ulid="01J0000000000000000000000B"),
                ],
            )
            index_path = state / "decisions" / "index.json"
            data = json.loads(index_path.read_text(encoding="utf-8"))
            data["adrs"] = data["adrs"][:1]  # drop one
            index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertIn("expected 2", result.findings[0].message)
            self.assertIn("on-disk 1", result.findings[0].message)

    def test_mutated_adr_field_fails_blocking(self):
        # Same count, but an adr's field differs from replay → drift.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [_adr_event("0001", "Original Title", ulid="01J0000000000000000000000A")],
            )
            index_path = state / "decisions" / "index.json"
            data = json.loads(index_path.read_text(encoding="utf-8"))
            data["adrs"][0]["title"] = "Tampered Title"
            index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")

    def test_schema_version_drift_fails_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [_adr_event("0001", "X", ulid="01J0000000000000000000000A")],
            )
            index_path = state / "decisions" / "index.json"
            data = json.loads(index_path.read_text(encoding="utf-8"))
            data["schema_version"] = "3.0"
            index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")


class TestCheck30Unreplayable(unittest.TestCase):
    def test_unreplayable_log_fails_blocking(self):
        # replay uses the STRICT reader and raises on a corrupt log; the check
        # must catch it and surface a BLOCKING finding (not crash the auditor).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            (state / "events.jsonl").write_text("{not json}\n", encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "30")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("unreplayable", result.findings[0].message.lower())

    def test_replay_exception_is_caught(self):
        # Belt-and-braces: even an unexpected replay error is contained.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise(
                state,
                [_adr_event("0001", "X", ulid="01J0000000000000000000000A")],
            )
            with mock.patch(
                "architect_brain.checks.check_30_decisions_index_fresh.replay",
                side_effect=RuntimeError("boom"),
            ):
                result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertIn("boom", result.findings[0].message)

    def test_does_not_raise_on_missing_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does" / "not" / "exist"
            result = run(missing)  # must return a CheckResult, not raise
            self.assertTrue(result.passed)  # empty == empty


if __name__ == "__main__":
    unittest.main()
