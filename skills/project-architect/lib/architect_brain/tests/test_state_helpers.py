"""Tests for the shared _state.py auditor state-reader helpers."""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import _state


def _mk_state(tmp: str, files: dict[str, str]) -> Path:
    """Create docs/_architect_state/<rel> files; return the state dir."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in files.items():
        p = state / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestStateHelpers(unittest.TestCase):

    def test_load_json_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.json"
            p.write_text('{"a": 1}', encoding="utf-8")
            self.assertEqual(_state.load_json(p), {"a": 1})

    def test_load_json_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(_state.load_json(Path(tmp) / "nope.json"))

    def test_load_json_invalid_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text("{not json", encoding="utf-8")
            self.assertIsNone(_state.load_json(p))

    def test_load_flat_index_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {
                "99-flat-index.json": json.dumps(
                    {"schema_version": "4.0",
                     "decisions": {"stack.frontend.framework": "next.js"},
                     "adrs": [{"id": "0001"}]}
                ),
            })
            self.assertEqual(
                _state.load_decisions(state),
                {"stack.frontend.framework": "next.js"},
            )
            self.assertEqual(_state.load_adrs(state), [{"id": "0001"}])

    def test_load_flat_index_absent_safe_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {})
            self.assertEqual(_state.load_decisions(state), {})
            self.assertEqual(_state.load_adrs(state), [])
            self.assertEqual(_state.load_flat_index(state)["schema_version"], "4.0")

    def test_load_flat_index_invalid_safe_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {"99-flat-index.json": "{broken"})
            self.assertEqual(_state.load_decisions(state), {})

    def test_load_projection_and_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {
                "workflow.json": json.dumps(
                    {"concern": "workflow", "current_phase": "stack",
                     "locked": False, "audits": []}
                ),
            })
            self.assertEqual(_state.load_workflow(state)["current_phase"], "stack")
            self.assertEqual(_state.load_projection(state, "missing"), {})

    def test_load_decisions_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {
                "decisions/index.json": json.dumps(
                    {"schema_version": "4.0", "regenerated_at": "x",
                     "adrs": [{"id": "0002"}]}
                ),
            })
            self.assertEqual(_state.load_decisions_index(state)["adrs"], [{"id": "0002"}])

    def test_load_decisions_index_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {})
            self.assertEqual(_state.load_decisions_index(state)["adrs"], [])

    def test_load_docs_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {
                "docs.json": json.dumps(
                    {"concern": "docs",
                     "completed": [{"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md"}]}
                ),
            })
            got = _state.load_docs_completed(state)
            self.assertEqual(got[0]["path"], "docs/PROJECT_OVERVIEW.md")

    def test_load_docs_completed_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {})
            self.assertEqual(_state.load_docs_completed(state), [])

    def test_path_helpers(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {})
            self.assertEqual(_state.docs_root(state), Path(tmp) / "docs")
            self.assertEqual(_state.project_root(state), Path(tmp))
            self.assertEqual(
                _state.decisions_md_dir(state), state / "decisions"
            )

    def test_iter_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {})
            line = json.dumps({
                "id": "01J0", "ts": "2026-05-29T00:00:00Z", "by": "orchestrator",
                "phase": None, "type": "DecisionMade",
                "payload": {"key": "project.type", "value": "web_app"},
            })
            (state / "events.jsonl").write_text(line + "\n", encoding="utf-8")
            events = list(_state.iter_events(state))
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].type, "DecisionMade")

    def test_iter_events_no_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {})
            self.assertEqual(list(_state.iter_events(state)), [])

    def test_iter_events_skips_malformed_lines(self):
        # A degraded log (bad JSON, unknown type, missing key) must NOT raise —
        # parseable events are still yielded; broken lines are skipped (defer to
        # check_05 / check_29). This is the guarantee event-consuming checks rely on.
        good = json.dumps({
            "id": "01J0", "ts": "2026-05-29T00:00:00Z", "by": "orchestrator",
            "phase": None, "type": "DecisionMade",
            "payload": {"key": "project.type", "value": "web_app"},
        })
        good2 = json.dumps({
            "id": "01J1", "ts": "2026-05-29T01:00:00Z", "by": "orchestrator",
            "phase": None, "type": "PhaseAdvanced",
            "payload": {"from": None, "to": "kickoff"},
        })
        unknown_type = json.dumps({
            "id": "01J2", "ts": "2026-05-29T02:00:00Z", "by": "x",
            "phase": None, "type": "TotallyBogusEvent", "payload": {},
        })
        missing_key = json.dumps({"id": "01J3", "type": "DecisionMade"})  # no ts/by/payload
        with tempfile.TemporaryDirectory() as tmp:
            state = _mk_state(tmp, {})
            (state / "events.jsonl").write_text(
                "\n".join([good, "{not json at all", unknown_type, missing_key, good2]) + "\n",
                encoding="utf-8",
            )
            # Does not raise; yields ONLY the two well-formed, known-type events.
            events = list(_state.iter_events(state))
            self.assertEqual([e.type for e in events], ["DecisionMade", "PhaseAdvanced"])


if __name__ == "__main__":
    unittest.main()
