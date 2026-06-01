"""Tests for architect_brain.events — event envelope + JSON round-trip.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.events import (
    ALLOWED_EVENT_TYPES,
    EventEnvelope,
    append_event,
    read_events,
)
from architect_brain.ulid import new_ulid


class TestEventEnvelope(unittest.TestCase):

    def test_envelope_to_json_round_trip(self):
        env = EventEnvelope(
            id="01HXYZABCDEFG1234567890123",
            ts="2026-05-27T15:23:11Z",
            by="orchestrator",
            phase="stack",
            type="DecisionMade",
            payload={"key": "stack.frontend.framework", "value": "next.js"},
        )
        line = env.to_json()
        parsed = json.loads(line)
        self.assertEqual(parsed["type"], "DecisionMade")
        self.assertEqual(parsed["payload"]["key"], "stack.frontend.framework")
        round_trip = EventEnvelope.from_json(line)
        self.assertEqual(round_trip, env)

    def test_envelope_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            EventEnvelope(
                id="01HXYZABCDEFG1234567890123",
                ts="2026-05-27T15:23:11Z",
                by="orchestrator",
                phase=None,
                type="NotARealEventType",
                payload={},
            )

    def test_allowed_event_types_include_core_set(self):
        for required in [
            "DecisionMade", "ADRFiled", "ADRSuperseded",
            "DocGenerated", "PhaseAdvanced", "PhaseSkipped",
            "SubstepRecorded", "AuditCompleted", "ResearchRefAdded",
            "GoldenPathApplied", "LockSet", "Upgraded",
        ]:
            self.assertIn(required, ALLOWED_EVENT_TYPES)


class TestEventLogIO(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def _make_event(self, etype: str = "DecisionMade", payload: dict | None = None) -> EventEnvelope:
        return EventEnvelope(
            id=new_ulid(),
            ts="2026-05-27T15:23:11Z",
            by="orchestrator",
            phase="stack",
            type=etype,
            payload=payload or {"key": "stack.frontend.framework", "value": "next.js"},
        )

    def test_append_creates_file_with_one_line(self):
        event = self._make_event()
        append_event(self.log_path, event)
        lines = self.log_path.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(EventEnvelope.from_json(lines[0]), event)

    def test_multiple_appends_preserve_order(self):
        events = [self._make_event(payload={"i": i}) for i in range(5)]
        for e in events:
            append_event(self.log_path, e)
        read_back = list(read_events(self.log_path))
        self.assertEqual(len(read_back), 5)
        for i, e in enumerate(read_back):
            self.assertEqual(e.payload, {"i": i})

    def test_read_events_handles_empty_file(self):
        self.log_path.write_text("")
        self.assertEqual(list(read_events(self.log_path)), [])

    def test_read_events_handles_missing_file(self):
        self.assertEqual(list(read_events(self.log_path)), [])

    def test_read_events_skips_blank_lines(self):
        self.log_path.write_text("\n" + self._make_event().to_json() + "\n\n")
        events = list(read_events(self.log_path))
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
