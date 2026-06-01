"""Tests for the v3.1 -> 4.0 migrator (architect_brain.migration + the CLI).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Exercises every function in migration.py plus the `architect-brain migrate`
CLI. The end-to-end test works on a COPY of the fixture in a tempdir because
``migrate`` mutates the project's docs/ in place.
"""

from __future__ import annotations

import io
import json
import shutil
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from architect_brain import migration
from architect_brain.events import ALLOWED_EVENT_TYPES, EventEnvelope
from architect_brain.projections import replay


# Repo root = test_file.parents[5]
#   tests -> architect_brain -> lib -> project-architect -> skills -> repo
_REPO_ROOT = Path(__file__).resolve().parents[5]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "migration" / "v71-rust-cli"


def _load_fixture_state() -> dict:
    return json.loads(
        (_FIXTURE / "docs" / "_architect_state.json").read_text(encoding="utf-8")
    )


def _copy_fixture(dest_parent: Path) -> Path:
    """Copy the fixture project into dest_parent and return the docs/ dir."""
    project = dest_parent / "project"
    shutil.copytree(_FIXTURE, project)
    return project / "docs"


class TestFlattenDecisions(unittest.TestCase):

    def test_flatten_nested_to_dotted(self):
        nested = {
            "project": {"name": "rustcli", "type": "cli_tool"},
            "tech_stack": {"language": "rust", "cli_framework": "clap"},
        }
        flat = migration.flatten_decisions(nested)
        self.assertEqual(flat["project.name"], "rustcli")
        self.assertEqual(flat["project.type"], "cli_tool")
        self.assertEqual(flat["tech_stack.language"], "rust")
        self.assertEqual(flat["tech_stack.cli_framework"], "clap")

    def test_array_leaf_is_preserved_not_descended(self):
        nested = {
            "tech_stack": {
                "language": "rust",
                "language_alternatives_considered": ["go", "zig"],
            }
        }
        flat = migration.flatten_decisions(nested)
        self.assertEqual(
            flat["tech_stack.language_alternatives_considered"], ["go", "zig"]
        )

    def test_deeply_nested_scalar(self):
        nested = {
            "architecture": {
                "performance_targets": {"cold_start_seconds_max": 0.05}
            }
        }
        flat = migration.flatten_decisions(nested)
        self.assertEqual(
            flat["architecture.performance_targets.cold_start_seconds_max"], 0.05
        )

    def test_preserve_flat_does_not_translate_to_stack_namespace(self):
        # The migrator must NOT rewrite tech_stack.* to stack.* (preserve-flat).
        flat = migration.flatten_decisions({"tech_stack": {"language": "rust"}})
        self.assertIn("tech_stack.language", flat)
        self.assertNotIn("stack.language", flat)

    def test_empty(self):
        self.assertEqual(migration.flatten_decisions({}), {})

    def test_round_trip_on_fixture(self):
        state = _load_fixture_state()
        flat = migration.flatten_decisions(state["decisions"])
        # The expected dotted keys all appear.
        for key in (
            "project.name",
            "tech_stack.language",
            "tech_stack.language_alternatives_considered",
            "architecture.pattern",
            "architecture.performance_targets.binary_size_mb_max",
        ):
            self.assertIn(key, flat)


class TestPhaseMap(unittest.TestCase):

    def test_confirmed_head_mappings(self):
        cases = {
            "preflight": "preflight",
            "phase_0a": "kickoff",
            "phase_0": "kickoff",
            "phase_1": "vision",
            "phase_2": "stack",
            "phase_2.5": "cost",
            "phase_3": "architecture",
            "complete": "complete",
        }
        for v7, v8 in cases.items():
            self.assertEqual(migration.phase_v7_to_v8(v7), v8, msg=v7)

    def test_tail_mappings(self):
        # The v8 tail order is unchanged from v7: docs/iteration/lock/tooling/handoff.
        cases = {
            "phase_4": "docs",
            "phase_5": "iteration",
            "phase_6": "lock",
            "phase_7": "tooling",
            "phase_8": "handoff",
        }
        for v7, v8 in cases.items():
            self.assertEqual(migration.phase_v7_to_v8(v7), v8, msg=v7)

    def test_v8_reorder_pins_stack_and_architecture(self):
        # The v8 head reorder is the load-bearing invariant: Tech-stack (v7
        # phase_2) and Architecture (v7 phase_3) must map to DISTINCT v8 keys,
        # NOT be swapped. Pin both directly so a phase_2<->phase_3 swap
        # mutation in _PHASE_MAP cannot survive.
        self.assertEqual(migration.phase_v7_to_v8("phase_2"), "stack")
        self.assertEqual(migration.phase_v7_to_v8("phase_3"), "architecture")
        # And they are not collapsed onto each other.
        self.assertNotEqual(
            migration.phase_v7_to_v8("phase_2"),
            migration.phase_v7_to_v8("phase_3"),
        )

    def test_unknown_phase_passes_through(self):
        self.assertEqual(migration.phase_v7_to_v8("phase_99"), "phase_99")

    def test_all_mapped_values_are_valid_v8_ladder_keys(self):
        from architect_brain.ui import _PHASE_LADDER

        for v7 in (
            "preflight", "phase_0a", "phase_0", "phase_1", "phase_2",
            "phase_2.5", "phase_3", "phase_4", "phase_5", "phase_6",
            "phase_7", "phase_8", "complete",
        ):
            self.assertIn(migration.phase_v7_to_v8(v7), _PHASE_LADDER)


class TestSynthesizeEvents(unittest.TestCase):

    def setUp(self):
        self.state = _load_fixture_state()
        self.events = migration.synthesize_events(self.state)

    def test_all_events_validate(self):
        for ev in self.events:
            self.assertIsInstance(ev, EventEnvelope)
            self.assertIn(ev.type, ALLOWED_EVENT_TYPES)

    def test_exactly_one_upgraded_first(self):
        upgraded = [e for e in self.events if e.type == "Upgraded"]
        self.assertEqual(len(upgraded), 1)
        self.assertEqual(self.events[0].type, "Upgraded")
        self.assertEqual(self.events[0].payload["to_schema"], "4.0")
        self.assertEqual(self.events[0].payload["from_schema"], "3.0")
        self.assertEqual(self.events[0].payload["from_plugin"], "7.2.0")

    def test_one_decision_event_per_flattened_key(self):
        flat = migration.flatten_decisions(self.state["decisions"])
        decisions = [e for e in self.events if e.type == "DecisionMade"]
        self.assertEqual(len(decisions), len(flat))
        # Keys are sorted for determinism.
        keys = [e.payload["key"] for e in decisions]
        self.assertEqual(keys, sorted(flat.keys()))

    def test_adr_events_include_filed_and_reserved(self):
        adrs = [e for e in self.events if e.type == "ADRFiled"]
        # 2 filed + 1 reserved = 3
        self.assertEqual(len(adrs), 3)
        ids = {e.payload["id"] for e in adrs}
        self.assertEqual(ids, {"0001", "0002", "0003"})
        reserved = [e for e in adrs if e.payload["status"] == "Reserved"]
        self.assertEqual(len(reserved), 1)
        self.assertEqual(reserved[0].payload["id"], "0003")
        # A filed ADR carries its provenance phase.
        first = next(e for e in adrs if e.payload["id"] == "0001")
        self.assertEqual(first.phase, "phase_2")

    def test_one_doc_event_per_generated_doc(self):
        docs = [e for e in self.events if e.type == "DocGenerated"]
        self.assertEqual(len(docs), 2)
        names = {e.payload["name"] for e in docs}
        self.assertEqual(names, {"PROJECT_OVERVIEW", "ARCHITECTURE"})
        for e in docs:
            self.assertIn("content_hash", e.payload)

    def test_phase_advanced_events_present_and_first_from_null(self):
        advances = [e for e in self.events if e.type == "PhaseAdvanced"]
        self.assertGreaterEqual(len(advances), 1)
        self.assertIsNone(advances[0].payload["from"])
        # No two consecutive PhaseAdvanced events repeat the same v8 phase.
        for prev, cur in zip(advances, advances[1:]):
            self.assertNotEqual(prev.payload["to"], cur.payload["to"])
        # The trajectory ends at the current phase (complete).
        self.assertEqual(advances[-1].payload["to"], "complete")

    def test_phase_trajectory_orders_stack_before_architecture(self):
        # E2e-layer guard for the v8 head reorder: the fixture's phase_progress
        # completes phase_2 (stack) BEFORE phase_3 (architecture), so the
        # reconstructed PhaseAdvanced trajectory must visit 'stack' strictly
        # before 'architecture'. A phase_2<->phase_3 swap in _PHASE_MAP would
        # flip this order (and project the wrong current_phase downstream).
        trajectory = [
            e.payload["to"] for e in self.events if e.type == "PhaseAdvanced"
        ]
        self.assertIn("stack", trajectory)
        self.assertIn("architecture", trajectory)
        self.assertLess(
            trajectory.index("stack"),
            trajectory.index("architecture"),
            msg=f"trajectory: {trajectory}",
        )

    def test_one_audit_completed_from_last_audit(self):
        audits = [e for e in self.events if e.type == "AuditCompleted"]
        self.assertEqual(len(audits), 1)
        # blocker == 0 -> clean; checks_failed == blocker+warning+info = 3.
        self.assertEqual(audits[0].payload["result"], "clean")
        self.assertEqual(audits[0].payload["checks_failed"], 3)
        self.assertEqual(audits[0].payload["checks_passed"], 0)

    def test_one_lock_set_when_locked(self):
        locks = [e for e in self.events if e.type == "LockSet"]
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0].payload["locked_at"], "2026-04-12T17:25:00Z")

    def test_no_lock_set_when_unlocked(self):
        state = _load_fixture_state()
        state["locked"] = False
        events = migration.synthesize_events(state)
        self.assertEqual([e for e in events if e.type == "LockSet"], [])

    def test_audit_blocked_when_blocker_positive(self):
        state = _load_fixture_state()
        state["last_audit"]["blocker"] = 1
        events = migration.synthesize_events(state)
        audit = next(e for e in events if e.type == "AuditCompleted")
        self.assertEqual(audit.payload["result"], "blocked")

    def test_no_audit_when_last_audit_null(self):
        state = _load_fixture_state()
        state["last_audit"] = None
        events = migration.synthesize_events(state)
        self.assertEqual([e for e in events if e.type == "AuditCompleted"], [])


class TestReplayCompareInvariant(unittest.TestCase):

    def test_replay_flat_index_equals_flatten(self):
        state = _load_fixture_state()
        events = migration.synthesize_events(state)
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "events.jsonl"
            log.write_text("".join(e.to_json() + "\n" for e in events))
            projections = replay(log)
        expected = migration.flatten_decisions(state["decisions"])
        self.assertEqual(projections["_flat_index"]["decisions"], expected)

    def test_compare_clean_on_faithful_migration(self):
        state = _load_fixture_state()
        events = migration.synthesize_events(state)
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "events.jsonl"
            log.write_text("".join(e.to_json() + "\n" for e in events))
            projections = replay(log)
        drift = migration.compare_v7_vs_v8(state, projections)
        self.assertEqual(drift, [], msg=f"unexpected drift: {drift}")

    def test_compare_reports_injected_decision_drift(self):
        state = _load_fixture_state()
        events = migration.synthesize_events(state)
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "events.jsonl"
            log.write_text("".join(e.to_json() + "\n" for e in events))
            projections = replay(log)
        # Corrupt a decision value in the projection.
        projections["_flat_index"]["decisions"]["tech_stack.language"] = "python"
        drift = migration.compare_v7_vs_v8(state, projections)
        self.assertTrue(drift)
        self.assertTrue(any("tech_stack.language" in d for d in drift))

    def test_compare_reports_missing_adr(self):
        state = _load_fixture_state()
        events = migration.synthesize_events(state)
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "events.jsonl"
            log.write_text("".join(e.to_json() + "\n" for e in events))
            projections = replay(log)
        projections["_flat_index"]["adrs"] = [
            a for a in projections["_flat_index"]["adrs"] if a["id"] != "0001"
        ]
        drift = migration.compare_v7_vs_v8(state, projections)
        self.assertTrue(any("0001" in d for d in drift))


class TestSnapshot(unittest.TestCase):

    def test_snapshot_contains_monolith_and_never_deletes(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            tarball = migration.snapshot_v7(docs)
            self.assertTrue(tarball.exists())
            self.assertTrue(tarball.name.endswith(".tar.gz"))
            # The monolith is still there (never deleted).
            self.assertTrue((docs / "_architect_state.json").exists())
            # The tarball CONTAINS the monolith.
            with tarfile.open(tarball, "r:gz") as tf:
                members = tf.getnames()
            self.assertTrue(
                any(m.endswith("_architect_state.json") for m in members),
                msg=f"members: {members}",
            )

    def test_snapshot_includes_decisions_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            tarball = migration.snapshot_v7(docs)
            with tarfile.open(tarball, "r:gz") as tf:
                members = tf.getnames()
            self.assertTrue(any("decisions" in m and m.endswith(".md") for m in members))


class TestRestampAdrs(unittest.TestCase):

    def test_restamp_adds_frontmatter_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            decisions_dir = docs / "decisions"
            count = migration.restamp_adrs(decisions_dir)
            self.assertEqual(count, 2)  # two free-form ADRs
            # Each file now begins with a frontmatter block.
            for md in decisions_dir.glob("*.md"):
                self.assertTrue(md.read_text().startswith("---"))
            # Second run is a no-op (already stamped).
            count2 = migration.restamp_adrs(decisions_dir)
            self.assertEqual(count2, 0)

    def test_restamp_frontmatter_parses_back(self):
        from architect_brain import __version__
        from architect_brain.adr import parse_frontmatter

        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            decisions_dir = docs / "decisions"
            migration.restamp_adrs(decisions_dir)
            md = decisions_dir / "0001-use-rust.md"
            fm = parse_frontmatter(md.read_text())
            self.assertEqual(fm.get("type"), "adr")
            self.assertEqual(fm.get("schema_version"), "4.0")
            self.assertEqual(fm.get("id"), "0001")
            # The migrator stamps the resolved plugin version (single source of
            # truth = plugin.json), never a hardcoded literal — see
            # test_version_single_source.
            self.assertEqual(fm.get("plugin_version"), __version__)


class TestDetectAndFloorCeiling(unittest.TestCase):

    def test_detect_legacy_finds_monolith(self):
        result = migration.detect_legacy(_FIXTURE / "docs")
        self.assertIsNotNone(result)
        self.assertEqual(result["schema_version"], "3.0")
        self.assertEqual(result["state"]["plugin_version"], "7.2.0")

    def test_detect_legacy_none_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(migration.detect_legacy(Path(tmp)))

    def test_floor_refuses_below_2(self):
        ok, reason = migration.migration_floor_ceiling_ok("1.0", "3.1.0")
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_ceiling_refuses_above_8(self):
        ok, reason = migration.migration_floor_ceiling_ok("3.0", "9.0.0")
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_in_range_ok(self):
        ok, _ = migration.migration_floor_ceiling_ok("3.0", "7.2.0")
        self.assertTrue(ok)

    def test_missing_versions_proceed(self):
        ok, _ = migration.migration_floor_ceiling_ok(None, None)
        self.assertTrue(ok)


class TestMigrateEndToEnd(unittest.TestCase):

    def test_migrate_produces_state_dir_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            result = migration.migrate(docs, run_audit=False)
            self.assertTrue(result["ok"], msg=f"drift: {result.get('drift')}")
            self.assertEqual(result["drift"], [])

            state_dir = docs / "_architect_state"
            self.assertTrue(state_dir.is_dir())
            self.assertTrue((state_dir / "events.jsonl").exists())
            self.assertTrue((state_dir / "99-flat-index.json").exists())
            self.assertTrue((state_dir / "schema_version").exists())
            # The backup tarball exists.
            self.assertTrue(result["snapshot"].exists())
            self.assertGreater(result["events"], 0)

    def test_migrate_flat_index_preserves_v7_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            migration.migrate(docs, run_audit=False)
            flat = json.loads(
                (docs / "_architect_state" / "99-flat-index.json").read_text()
            )
            self.assertEqual(flat["decisions"]["tech_stack.language"], "rust")
            self.assertNotIn("stack.language", flat["decisions"])

    def test_migrate_sets_workflow_current_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            migration.migrate(docs, run_audit=False)
            workflow = json.loads(
                (docs / "_architect_state" / "workflow.json").read_text()
            )
            self.assertEqual(workflow["current_phase"], "complete")
            self.assertTrue(workflow["locked"])

    def test_migrate_then_check_state_passes(self):
        from architect_brain.__main__ import main

        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            migration.migrate(docs, run_audit=False)
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["check-state", "--docs-dir", str(docs)])
            self.assertEqual(code, 0, msg=out.getvalue())

    def test_migrate_then_audit_only_31_passes(self):
        from architect_brain.__main__ import main

        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            migration.migrate(docs, run_audit=False)
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["audit", "--docs-dir", str(docs), "--only", "31"])
            self.assertEqual(code, 0, msg=out.getvalue())

    def test_migrate_refuses_schema_below_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            mono = docs / "_architect_state.json"
            state = json.loads(mono.read_text())
            state["schema_version"] = "1.0"
            mono.write_text(json.dumps(state))
            result = migration.migrate(docs, run_audit=False)
            self.assertFalse(result["ok"])
            # The new state dir must NOT have been created on a refusal.
            self.assertFalse((docs / "_architect_state").is_dir())

    def test_migrate_refuses_plugin_above_8(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            mono = docs / "_architect_state.json"
            state = json.loads(mono.read_text())
            state["plugin_version"] = "9.0.0"
            mono.write_text(json.dumps(state))
            result = migration.migrate(docs, run_audit=False)
            self.assertFalse(result["ok"])

    def test_migrate_aborts_and_leaves_v7_untouched_on_drift(self):
        # Safety-critical invariant: on non-empty drift, migrate() ABORTS,
        # cleans up the in-progress v8 dir, and leaves the v7 monolith
        # untouched at its original name (NOT renamed to the .migrated sidecar).
        # Patch the MODULE-QUALIFIED name (migrate resolves the bare name at
        # call time) to force drift regardless of the actual comparison.
        import unittest.mock

        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            with unittest.mock.patch(
                "architect_brain.migration.compare_v7_vs_v8",
                return_value=["forced drift"],
            ):
                result = migration.migrate(docs, run_audit=False)
            self.assertIs(result["ok"], False)
            self.assertEqual(result["drift"], ["forced drift"])
            # No v8 state dir left behind (the temp dir was cleaned up).
            self.assertFalse((docs / "_architect_state").is_dir())
            # The monolith is intact at its original name...
            self.assertTrue((docs / "_architect_state.json").is_file())
            # ...and was NOT renamed to the .migrated sidecar.
            self.assertFalse((docs / "_architect_state.json.migrated").exists())


class TestMigrateCLI(unittest.TestCase):

    def test_cli_migrate_exit_zero_and_artifacts(self):
        from architect_brain.__main__ import main

        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(["migrate", "--docs-dir", str(docs), "--no-audit"])
            self.assertEqual(code, 0, msg=out.getvalue() + err.getvalue())

            state_dir = docs / "_architect_state"
            self.assertTrue(state_dir.is_dir())
            self.assertTrue((state_dir / "events.jsonl").exists())
            # A backup tarball exists in docs/.
            tarballs = list(docs.glob("_architect_state.json.v7-backup.*.tar.gz"))
            self.assertEqual(len(tarballs), 1, msg=str(list(docs.iterdir())))

    def test_cli_migrate_refuses_old_schema_exit_one(self):
        from architect_brain.__main__ import main

        with tempfile.TemporaryDirectory() as tmp:
            docs = _copy_fixture(Path(tmp))
            mono = docs / "_architect_state.json"
            state = json.loads(mono.read_text())
            state["schema_version"] = "1.0"
            mono.write_text(json.dumps(state))
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(["migrate", "--docs-dir", str(docs), "--no-audit"])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
