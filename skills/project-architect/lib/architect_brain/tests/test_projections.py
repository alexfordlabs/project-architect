"""Tests for architect_brain.projections — concern projections + apply_event routing.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import unittest

from architect_brain.projections import (
    CONCERN_NAMES,
    apply_event,
    empty_projections,
)
from architect_brain.events import EventEnvelope


class TestProjections(unittest.TestCase):

    def test_concern_names_include_all_v8_concerns(self):
        expected = {
            "identity", "vision", "architecture", "stack", "cost",
            "ai_agent", "api_contract", "docs", "workflow",
            "tooling", "handoff",
        }
        self.assertEqual(set(CONCERN_NAMES), expected)

    def test_empty_projections_has_all_concerns(self):
        p = empty_projections()
        for name in CONCERN_NAMES:
            self.assertIn(name, p)
            self.assertEqual(p[name].get("schema_version"), "4.0")
            self.assertEqual(p[name].get("decisions"), {})

    def test_empty_projections_includes_flat_index(self):
        p = empty_projections()
        self.assertIn("_flat_index", p)
        self.assertEqual(p["_flat_index"]["schema_version"], "4.0")
        self.assertEqual(p["_flat_index"]["decisions"], {})
        self.assertEqual(p["_flat_index"]["adrs"], [])

    def test_workflow_projection_includes_router_fields(self):
        p = empty_projections()
        self.assertIn("current_phase", p["workflow"])
        self.assertIn("substep", p["workflow"])
        self.assertIn("locked", p["workflow"])
        self.assertEqual(p["workflow"]["audits"], [])

    def test_decision_made_event_lands_in_correct_concern(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZABCDEFG1234567890123",
            ts="2026-05-27T15:23:11Z",
            by="orchestrator",
            phase="stack",
            type="DecisionMade",
            payload={"key": "stack.frontend.framework", "value": "next.js"},
        )
        apply_event(event, p)
        self.assertEqual(
            p["stack"]["decisions"]["stack.frontend.framework"],
            "next.js",
        )
        # Flat-index projection also receives the decision.
        self.assertEqual(
            p["_flat_index"]["decisions"]["stack.frontend.framework"],
            "next.js",
        )

    def test_decision_routes_ai_to_ai_agent_concern(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T00:00:00Z", by="o",
            phase="ai", type="DecisionMade",
            payload={"key": "ai.enabled", "value": True},
        )
        apply_event(event, p)
        self.assertEqual(p["ai_agent"]["decisions"]["ai.enabled"], True)

    def test_decision_routes_api_to_api_contract_concern(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T00:00:00Z", by="o",
            phase="api", type="DecisionMade",
            payload={"key": "api.public", "value": True},
        )
        apply_event(event, p)
        self.assertEqual(p["api_contract"]["decisions"]["api.public"], True)

    def test_adr_filed_event_appends_to_flat_index(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T15:23:11Z", by="orchestrator",
            phase="stack", type="ADRFiled",
            payload={"id": "0007", "title": "Use Next.js 15", "status": "Accepted"},
        )
        apply_event(event, p)
        self.assertEqual(len(p["_flat_index"]["adrs"]), 1)
        adr = p["_flat_index"]["adrs"][0]
        self.assertEqual(adr["id"], "0007")
        self.assertEqual(adr["title"], "Use Next.js 15")
        self.assertEqual(adr["status"], "Accepted")
        self.assertEqual(adr["date"], "2026-05-27")
        self.assertEqual(adr["phase"], "stack")

    def test_adr_superseded_event_marks_predecessor(self):
        p = empty_projections()
        # File first ADR
        apply_event(EventEnvelope(
            id="01HX1", ts="2026-05-27T00:00:00Z", by="o",
            phase="stack", type="ADRFiled",
            payload={"id": "0001", "title": "First", "status": "Accepted"},
        ), p)
        # Supersede it
        apply_event(EventEnvelope(
            id="01HX2", ts="2026-05-28T00:00:00Z", by="o",
            phase="stack", type="ADRSuperseded",
            payload={"id": "0001", "by": "0002"},
        ), p)
        adr = p["_flat_index"]["adrs"][0]
        self.assertEqual(adr["status"], "Superseded")
        self.assertEqual(adr["superseded_by"], ["0002"])

    def test_phase_advanced_event_updates_workflow(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase=None, type="PhaseAdvanced",
            payload={"from": "vision", "to": "architecture"},
        )
        apply_event(event, p)
        self.assertEqual(p["workflow"]["current_phase"], "architecture")
        self.assertIsNone(p["workflow"]["substep"])

    def test_substep_recorded_event_updates_workflow(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase="architecture", type="SubstepRecorded",
            payload={"phase": "architecture", "substep": "boundaries", "status": "in_progress"},
        )
        apply_event(event, p)
        self.assertEqual(p["workflow"]["substep"]["substep"], "boundaries")
        self.assertEqual(p["workflow"]["substep"]["status"], "in_progress")

    def test_doc_generated_event_appends_to_docs_concern(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T00:00:00Z", by="document-author",
            phase="docs", type="DocGenerated",
            payload={"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md", "content_hash": "abc123"},
        )
        apply_event(event, p)
        self.assertEqual(len(p["docs"]["completed"]), 1)
        self.assertEqual(p["docs"]["completed"][0]["name"], "PROJECT_OVERVIEW")

    def test_audit_completed_event_appends_to_workflow_audits(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T00:00:00Z", by="auditor",
            phase=None, type="AuditCompleted",
            payload={"result": "passed", "checks_passed": 34, "checks_failed": 0},
        )
        apply_event(event, p)
        self.assertEqual(len(p["workflow"]["audits"]), 1)
        self.assertEqual(p["workflow"]["audits"][0]["result"], "passed")

    def test_lock_set_event_locks_workflow(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase="lock", type="LockSet",
            payload={"phase": "lock", "locked_at": "2026-05-27T00:00:00Z", "audit_result": "passed"},
        )
        apply_event(event, p)
        self.assertTrue(p["workflow"]["locked"])
        self.assertEqual(p["workflow"]["locked_at"], "2026-05-27T00:00:00Z")

    def test_empty_projections_workflow_has_version_field(self):
        # Shape stability: workflow.version exists (None) regardless of lock history,
        # so consumers (the /iterate-design version-bump flow) can read it safely.
        p = empty_projections()
        self.assertIn("version", p["workflow"])
        self.assertIsNone(p["workflow"]["version"])

    def test_lock_set_defaults_to_locked_true_when_payload_omits_locked(self):
        # Backwards-compatible: a LockSet with no explicit `locked` still locks.
        p = empty_projections()
        event = EventEnvelope(
            id="01HXY1", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase="lock", type="LockSet",
            payload={"locked_at": "2026-05-27T00:00:00Z"},
        )
        apply_event(event, p)
        self.assertTrue(p["workflow"]["locked"])

    def test_lock_set_without_locked_at_stamps_from_event_ts(self):
        # locked_at is optional in the payload; on a lock the binary stamps it from
        # the event ts (its own clock) — never a model-typed literal.
        p = empty_projections()
        event = EventEnvelope(
            id="01HXY2", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase="lock", type="LockSet",
            payload={"locked": True},
        )
        apply_event(event, p)  # must not raise
        self.assertTrue(p["workflow"]["locked"])
        self.assertEqual(p["workflow"]["locked_at"], "2026-05-27T00:00:00Z")

    def test_unlock_without_locked_at_clears_it(self):
        # An unlock (locked=false) with no explicit locked_at clears locked_at to null.
        p = empty_projections()
        apply_event(EventEnvelope(
            id="01HXY6", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase="lock", type="LockSet", payload={"locked": True, "version": "v1.0"},
        ), p)
        self.assertEqual(p["workflow"]["locked_at"], "2026-05-27T00:00:00Z")
        apply_event(EventEnvelope(
            id="01HXY7", ts="2026-05-28T00:00:00Z", by="orchestrator",
            phase="iteration", type="LockSet", payload={"locked": False, "version": "v1.1-draft"},
        ), p)
        self.assertFalse(p["workflow"]["locked"])
        self.assertIsNone(p["workflow"]["locked_at"])

    def test_lock_set_stores_version_when_present(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXY3", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase="lock", type="LockSet",
            payload={"locked": True, "locked_at": "2026-05-27T00:00:00Z", "version": "v1.0"},
        )
        apply_event(event, p)
        self.assertEqual(p["workflow"]["version"], "v1.0")

    def test_lock_set_honors_locked_false_to_unlock(self):
        # The /iterate-design flow unlocks a locked design via LockSet{locked:false},
        # bumping the design version and clearing locked_at.
        p = empty_projections()
        lock = EventEnvelope(
            id="01HXY4", ts="2026-05-27T00:00:00Z", by="orchestrator",
            phase="lock", type="LockSet",
            payload={"locked": True, "locked_at": "2026-05-27T00:00:00Z", "version": "v1.0"},
        )
        apply_event(lock, p)
        self.assertTrue(p["workflow"]["locked"])
        self.assertEqual(p["workflow"]["version"], "v1.0")

        unlock = EventEnvelope(
            id="01HXY5", ts="2026-05-28T00:00:00Z", by="orchestrator",
            phase="iteration", type="LockSet",
            payload={"locked": False, "locked_at": None, "version": "v1.1-draft"},
        )
        apply_event(unlock, p)
        self.assertFalse(p["workflow"]["locked"])
        self.assertIsNone(p["workflow"]["locked_at"])
        self.assertEqual(p["workflow"]["version"], "v1.1-draft")


import tempfile
from pathlib import Path

from architect_brain.projections import replay
from architect_brain.events import append_event
from architect_brain.ulid import new_ulid


class TestReplay(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def _append(self, etype, payload, phase=None):
        e = EventEnvelope(
            id=new_ulid(),
            ts="2026-05-27T15:23:11Z",
            by="orchestrator",
            phase=phase,
            type=etype,
            payload=payload,
        )
        append_event(self.log_path, e)

    def test_replay_empty_log_returns_empty_projections(self):
        p = replay(self.log_path)
        self.assertEqual(p["stack"]["decisions"], {})
        self.assertEqual(p["_flat_index"]["decisions"], {})

    def test_replay_missing_log_returns_empty_projections(self):
        # File doesn't exist at all — replay handles gracefully.
        missing = Path(self.tmp.name) / "nonexistent.jsonl"
        p = replay(missing)
        for name in CONCERN_NAMES:
            self.assertEqual(p[name].get("decisions"), {})

    def test_replay_reconstructs_decisions(self):
        self._append("DecisionMade",
                     {"key": "stack.frontend.framework", "value": "next.js"},
                     phase="stack")
        self._append("DecisionMade",
                     {"key": "stack.backend.language", "value": "typescript"},
                     phase="stack")
        p = replay(self.log_path)
        self.assertEqual(p["stack"]["decisions"]["stack.frontend.framework"], "next.js")
        self.assertEqual(p["stack"]["decisions"]["stack.backend.language"], "typescript")
        self.assertEqual(p["_flat_index"]["decisions"]["stack.frontend.framework"], "next.js")

    def test_replay_phase_advance_records_workflow_state(self):
        self._append("PhaseAdvanced", {"from": "vision", "to": "architecture"})
        p = replay(self.log_path)
        self.assertEqual(p["workflow"]["current_phase"], "architecture")

    def test_replay_equals_incremental_fold(self):
        """The central correctness invariant: replay(E) == fold(apply_event, E, empty())."""
        # Append a varied sequence of events
        self._append("DecisionMade", {"key": "stack.frontend.framework", "value": "next.js"}, phase="stack")
        self._append("DecisionMade", {"key": "ai.enabled", "value": True}, phase="vision")
        self._append("PhaseAdvanced", {"from": "vision", "to": "architecture"})
        self._append("ADRFiled", {"id": "0001", "title": "Choose Next.js", "status": "Accepted"}, phase="stack")
        self._append("DecisionMade", {"key": "api.public", "value": False}, phase="api")
        self._append("SubstepRecorded", {"phase": "architecture", "substep": "boundaries", "status": "in_progress"}, phase="architecture")
        self._append("DocGenerated", {"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md", "content_hash": "abc"}, phase="docs")
        self._append("ADRSuperseded", {"id": "0001", "by": "0002"})
        self._append("AuditCompleted", {"result": "passed", "checks_passed": 34, "checks_failed": 0})
        self._append("LockSet", {"phase": "lock", "locked_at": "2026-05-27T00:00:00Z", "audit_result": "passed"}, phase="lock")

        # Method A: full replay from empty
        via_replay = replay(self.log_path)

        # Method B: incremental fold
        from architect_brain.events import read_events
        via_fold = empty_projections()
        for event in read_events(self.log_path):
            apply_event(event, via_fold)

        # Invariant: same result
        self.assertEqual(via_replay, via_fold,
                         "REPLAY INVARIANT VIOLATED: replay(E) != fold(apply_event, E, empty())")

    def test_replay_lock_unlock_relock_sequence(self):
        # The /iterate-design lifecycle: lock v1.0 → unlock to v1.1-draft → relock v1.1.
        # Final replayed state must reflect the LAST LockSet (locked, version v1.1).
        self._append("LockSet", {"locked": True, "locked_at": "2026-05-27T00:00:00Z", "version": "v1.0"}, phase="lock")
        self._append("LockSet", {"locked": False, "locked_at": None, "version": "v1.1-draft"}, phase="iteration")
        self._append("LockSet", {"locked": True, "locked_at": "2026-05-29T00:00:00Z", "version": "v1.1"}, phase="lock")

        via_replay = replay(self.log_path)
        self.assertTrue(via_replay["workflow"]["locked"])
        self.assertEqual(via_replay["workflow"]["locked_at"], "2026-05-29T00:00:00Z")
        self.assertEqual(via_replay["workflow"]["version"], "v1.1")


import json

from architect_brain.projections import projections_to_disk


class TestProjectionsToDisk(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.tmp.name) / "_architect_state"

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_one_file_per_concern_plus_flat_index(self):
        p = empty_projections()
        p["stack"]["decisions"]["stack.frontend.framework"] = "next.js"
        p["_flat_index"]["decisions"]["stack.frontend.framework"] = "next.js"

        projections_to_disk(self.state_dir, p)

        # One file per concern.
        for name in CONCERN_NAMES:
            file_path = self.state_dir / f"{name}.json"
            self.assertTrue(file_path.exists(), f"missing {name}.json")
            data = json.loads(file_path.read_text())
            self.assertEqual(data["schema_version"], "4.0")

        # Flat index has the special filename 99-flat-index.json.
        flat_path = self.state_dir / "99-flat-index.json"
        self.assertTrue(flat_path.exists())
        flat = json.loads(flat_path.read_text())
        self.assertEqual(flat["decisions"]["stack.frontend.framework"], "next.js")

    def test_writes_schema_version_probe_file(self):
        p = empty_projections()
        projections_to_disk(self.state_dir, p)
        version_file = self.state_dir / "schema_version"
        self.assertEqual(version_file.read_text().strip(), "4.0")

    def test_creates_state_dir_if_missing(self):
        p = empty_projections()
        nonexistent = Path(self.tmp.name) / "deeply" / "nested" / "_architect_state"
        projections_to_disk(nonexistent, p)
        self.assertTrue(nonexistent.exists())
        self.assertTrue((nonexistent / "identity.json").exists())

    def test_output_is_deterministic_byte_identical(self):
        """Same projections produce byte-identical files (sort_keys + indent stable)."""
        p = empty_projections()
        p["stack"]["decisions"]["stack.b"] = "later"
        p["stack"]["decisions"]["stack.a"] = "first"

        first_dir = Path(self.tmp.name) / "first"
        second_dir = Path(self.tmp.name) / "second"
        projections_to_disk(first_dir, p)
        projections_to_disk(second_dir, p)

        for name in list(CONCERN_NAMES) + ["99-flat-index", "schema_version"]:
            suffix = ".json" if name != "schema_version" else ""
            f1 = (first_dir / f"{name}{suffix}").read_bytes()
            f2 = (second_dir / f"{name}{suffix}").read_bytes()
            self.assertEqual(f1, f2, f"non-deterministic output for {name}")

    def test_decisions_in_files_have_sorted_keys(self):
        p = empty_projections()
        p["stack"]["decisions"]["stack.z"] = "last"
        p["stack"]["decisions"]["stack.a"] = "first"
        p["stack"]["decisions"]["stack.m"] = "middle"
        projections_to_disk(self.state_dir, p)
        stack_file = (self.state_dir / "stack.json").read_text()
        # Find positions of each key
        pos_a = stack_file.index('"stack.a"')
        pos_m = stack_file.index('"stack.m"')
        pos_z = stack_file.index('"stack.z"')
        self.assertLess(pos_a, pos_m)
        self.assertLess(pos_m, pos_z)


class TestDecisionsIndex(unittest.TestCase):
    """Wave 2.11: ADR ledger elevated to its own decisions/index.json projection."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.tmp.name) / "_architect_state"

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_projections_includes_decisions_index(self):
        p = empty_projections()
        self.assertIn("_decisions_index", p)
        self.assertEqual(p["_decisions_index"]["schema_version"], "4.0")
        self.assertEqual(p["_decisions_index"]["adrs"], [])

    def test_adr_filed_event_appends_to_decisions_index(self):
        p = empty_projections()
        event = EventEnvelope(
            id="01HXYZ", ts="2026-05-27T15:23:11Z", by="orchestrator",
            phase="stack", type="ADRFiled",
            payload={"id": "0007", "title": "Use Next.js 15", "status": "Accepted"},
        )
        apply_event(event, p)
        self.assertEqual(len(p["_decisions_index"]["adrs"]), 1)
        adr = p["_decisions_index"]["adrs"][0]
        self.assertEqual(adr["id"], "0007")
        self.assertEqual(adr["title"], "Use Next.js 15")
        self.assertEqual(adr["status"], "Accepted")

    def test_adr_superseded_marks_in_decisions_index(self):
        p = empty_projections()
        apply_event(EventEnvelope(
            id="01HX1", ts="2026-05-27T00:00:00Z", by="o",
            phase="stack", type="ADRFiled",
            payload={"id": "0001", "title": "First", "status": "Accepted"},
        ), p)
        apply_event(EventEnvelope(
            id="01HX2", ts="2026-05-28T00:00:00Z", by="o",
            phase="stack", type="ADRSuperseded",
            payload={"id": "0001", "by": "0002"},
        ), p)
        adr = p["_decisions_index"]["adrs"][0]
        self.assertEqual(adr["status"], "Superseded")
        self.assertEqual(adr["superseded_by"], ["0002"])

    def test_projections_to_disk_writes_decisions_index_json(self):
        p = empty_projections()
        apply_event(EventEnvelope(
            id="01HXYZ", ts="2026-05-27T15:23:11Z", by="o",
            phase="stack", type="ADRFiled",
            payload={"id": "0007", "title": "Test", "status": "Accepted"},
        ), p)
        projections_to_disk(self.state_dir, p)
        index_path = self.state_dir / "decisions" / "index.json"
        self.assertTrue(index_path.exists())
        data = json.loads(index_path.read_text())
        self.assertEqual(data["schema_version"], "4.0")
        self.assertEqual(len(data["adrs"]), 1)
        self.assertEqual(data["adrs"][0]["id"], "0007")

    def test_projections_to_disk_creates_decisions_subdir(self):
        """The decisions/ subdir is created if missing."""
        p = empty_projections()
        projections_to_disk(self.state_dir, p)
        self.assertTrue((self.state_dir / "decisions").exists())
        self.assertTrue((self.state_dir / "decisions" / "index.json").exists())

    def test_flat_index_still_has_adrs_for_backcompat(self):
        """During Wave 2.11, _flat_index.adrs is still populated alongside the new projection."""
        p = empty_projections()
        apply_event(EventEnvelope(
            id="01HXYZ", ts="2026-05-27T15:23:11Z", by="o",
            phase="stack", type="ADRFiled",
            payload={"id": "0007", "title": "Test", "status": "Accepted"},
        ), p)
        self.assertEqual(len(p["_flat_index"]["adrs"]), 1)
        self.assertEqual(len(p["_decisions_index"]["adrs"]), 1)

    def test_decisions_index_writes_regenerated_at_stamp(self):
        """projections_to_disk stamps decisions/index.json with regenerated_at (UTC ISO)."""
        p = empty_projections()
        projections_to_disk(self.state_dir, p)
        data = json.loads((self.state_dir / "decisions" / "index.json").read_text())
        self.assertIn("regenerated_at", data)
        stamp = data["regenerated_at"]
        # Shape check: YYYY-MM-DDTHH:MM:SSZ
        self.assertRegex(stamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_flat_index_and_decisions_index_dicts_are_independent(self):
        """Mutating an ADR in _flat_index must not leak into _decisions_index (and vice versa)."""
        p = empty_projections()
        apply_event(EventEnvelope(
            id="01HXYZ", ts="2026-05-27T15:23:11Z", by="o",
            phase="stack", type="ADRFiled",
            payload={"id": "0007", "title": "Test", "status": "Accepted"},
        ), p)
        # Mutate the flat-index copy
        p["_flat_index"]["adrs"][0]["status"] = "Mutated"
        p["_flat_index"]["adrs"][0]["superseded_by"].append("XXXX")
        # Decisions-index copy must be untouched
        self.assertEqual(p["_decisions_index"]["adrs"][0]["status"], "Accepted")
        self.assertEqual(p["_decisions_index"]["adrs"][0]["superseded_by"], [])


if __name__ == "__main__":
    unittest.main()
