"""Tests for the check_12_iso8601_timestamps auditor check."""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_12_iso8601_timestamps as check_12


def _state(tmp: str) -> Path:
    """Create an empty docs/_architect_state dir and return its path."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_events(state: Path, events: list[dict]) -> None:
    """Write the given event dicts (each must have at least a ts) to events.jsonl.

    Each dict is completed to a valid EventEnvelope-shaped line; only ``ts`` is
    varied across tests.
    """
    lines = []
    for i, ev in enumerate(events):
        line = {
            "id": ev.get("id", f"E{i:026d}"),
            "ts": ev["ts"],
            "by": ev.get("by", "orchestrator"),
            "phase": ev.get("phase"),
            "type": ev.get("type", "DecisionMade"),
            "payload": ev.get("payload", {}),
        }
        lines.append(json.dumps(line))
    (state / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_workflow(state: Path, workflow: dict) -> None:
    (state / "workflow.json").write_text(json.dumps(workflow), encoding="utf-8")


def _write_decisions_index(state: Path, index: dict) -> None:
    dec = state / "decisions"
    dec.mkdir(parents=True, exist_ok=True)
    (dec / "index.json").write_text(json.dumps(index), encoding="utf-8")


class TestCheck12(unittest.TestCase):

    # ---- module contract -------------------------------------------------

    def test_module_contract(self):
        self.assertEqual(check_12.CHECK_ID, "12")
        self.assertEqual(check_12.NAME, "iso8601_timestamps")
        self.assertEqual(check_12.SEVERITY, "WARNING")
        self.assertTrue(callable(check_12.run))

    # ---- passing fixtures ------------------------------------------------

    def test_pass_when_all_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_events(state, [
                {"ts": "2026-05-29T01:23:45Z"},
                {"ts": "2026-05-29T02:00:00+00:00"},
                {"ts": "2026-05-29T03:00:00.123Z"},
            ])
            _write_workflow(state, {
                "locked_at": "2026-05-29T10:00:00Z",
                "audits": [
                    {"ts": "2026-05-29T09:00:00Z", "result": "PASS"},
                    {"ts": "2026-05-29 09:30:00", "result": "PASS"},
                ],
            })
            _write_decisions_index(state, {
                "schema_version": "4.0",
                "regenerated_at": "2026-05-29T10:05:00Z",
                "adrs": [],
            })
            result = check_12.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "12")
            self.assertEqual(result.findings, ())

    def test_locked_at_null_is_skipped(self):
        # locked_at is null until lock — must not be flagged.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_workflow(state, {"locked_at": None, "audits": []})
            result = check_12.run(state)
            self.assertTrue(result.passed)

    def test_empty_state_passes(self):
        # Fresh project: no events, no workflow, no decisions index.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            result = check_12.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_adr_date_fields_not_flagged(self):
        # ADR date-only fields are by-design date-only and must NOT be flagged.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_decisions_index(state, {
                "schema_version": "4.0",
                "regenerated_at": "2026-05-29T10:05:00Z",
                "adrs": [{"id": "ADR-0001", "date": "2026-05-29"}],
            })
            result = check_12.run(state)
            self.assertTrue(result.passed)

    # ---- failing fixtures ------------------------------------------------

    def test_fail_on_date_only_event_ts(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_events(state, [
                {"ts": "2026-05-29T01:23:45Z"},
                {"ts": "2026-05-29"},  # date-only — malformed
            ])
            result = check_12.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            locations = [f.location for f in result.findings]
            self.assertIn("events[1].ts", locations)

    def test_fail_on_bad_workflow_locked_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_workflow(state, {
                "locked_at": "not a date",
                "audits": [],
            })
            result = check_12.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertTrue(
                any(f.location == "workflow.locked_at" for f in result.findings)
            )

    def test_fail_on_bad_audit_ts(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_workflow(state, {
                "audits": [
                    {"ts": "2026-05-29T09:00:00Z", "result": "PASS"},
                    {"ts": "2026-05-29", "result": "PASS"},  # date-only
                ],
            })
            result = check_12.run(state)
            self.assertFalse(result.passed)
            self.assertTrue(
                any(f.location == "workflow.audits[1].ts" for f in result.findings)
            )

    def test_fail_on_bad_decisions_index_regenerated_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_decisions_index(state, {
                "schema_version": "4.0",
                "regenerated_at": 12345,  # non-string
                "adrs": [],
            })
            result = check_12.run(state)
            self.assertFalse(result.passed)
            self.assertTrue(
                any(
                    f.location == "decisions_index.regenerated_at"
                    for f in result.findings
                )
            )

    def test_finding_message_includes_source_and_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_workflow(state, {"locked_at": "2026-05-29", "audits": []})
            result = check_12.run(state)
            self.assertFalse(result.passed)
            msgs = [f.message for f in result.findings]
            # message format: "<source>=<value!r>: <err>"
            self.assertTrue(
                any(m.startswith("workflow.locked_at=") and "'2026-05-29'" in m
                    for m in msgs),
                msgs,
            )

    def test_degraded_event_log_does_not_raise(self):
        # Mutation/contract guard: a malformed events.jsonl (bad JSON line,
        # unknown event type, event missing required keys) must NOT crash run()
        # — _state.iter_events skips unparseable lines (deferring to check_05).
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            (state / "events.jsonl").write_text(
                '\n'.join([
                    '{"id":"01J0","ts":"2026-05-29T00:00:00Z","by":"x","phase":null,'
                    '"type":"DecisionMade","payload":{}}',
                    '{not valid json',
                    '{"id":"01J2","ts":"2026-05-29T01:00:00Z","by":"x","phase":null,'
                    '"type":"NopeBogusType","payload":{}}',
                    '{"id":"01J3","type":"DecisionMade"}',
                ]) + '\n',
                encoding="utf-8",
            )
            # The one well-formed event has a valid ts → overall pass, no crash.
            result = check_12.run(state)
            self.assertTrue(result.passed, msg=f"findings: {result.findings}")

    def test_multiple_malformed_all_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp)
            _write_events(state, [{"ts": "2026-05-29"}])
            _write_workflow(state, {
                "locked_at": "bogus",
                "audits": [{"ts": "also-bad", "result": "PASS"}],
            })
            _write_decisions_index(state, {"regenerated_at": "nope", "adrs": []})
            result = check_12.run(state)
            self.assertFalse(result.passed)
            locations = {f.location for f in result.findings}
            self.assertEqual(
                locations,
                {
                    "events[0].ts",
                    "workflow.locked_at",
                    "workflow.audits[0].ts",
                    "decisions_index.regenerated_at",
                },
            )


if __name__ == "__main__":
    unittest.main()
