"""Tests for the check_14_adr_coverage auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_14_adr_coverage
from architect_brain.checks.check_14_adr_coverage import CHECK_ID, NAME, SEVERITY, run


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` (with ``decisions/``) and return it."""
    state = Path(tmp) / "docs" / "_architect_state"
    (state / "decisions").mkdir(parents=True)
    return state


def _write_flat_index(state_dir: Path, decisions: dict) -> None:
    (state_dir / "99-flat-index.json").write_text(
        json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
        encoding="utf-8",
    )


def _write_adr(state_dir: Path, name: str, fm: dict, body: str = "Body.") -> None:
    """Write an ADR markdown file with the given frontmatter dict."""
    from architect_brain.adr import emit_frontmatter

    text = emit_frontmatter(fm) + "\n" + body + "\n"
    (state_dir / "decisions" / name).write_text(text, encoding="utf-8")


class TestCheck14Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "14")
        self.assertEqual(NAME, "adr_coverage")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_14_adr_coverage.CHECK_ID, "14")
        self.assertTrue(callable(check_14_adr_coverage.run))


class TestCheck14Degraded(unittest.TestCase):
    def test_no_state_at_all_passes(self):
        # Fresh project: no flat index, no decisions/ dir.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "14")
            self.assertEqual(result.findings, ())

    def test_no_adrs_passes(self):
        # Decisions recorded but no ADR markdown declares decision_keys.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_adr_without_decision_keys_passes(self):
        # An ADR exists but omits the optional decision_keys list → nothing cited.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            _write_adr(state, "0001-pick-rust.md",
                       {"id": "ADR-0001", "title": "Pick Rust", "status": "accepted"})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertIn("no decision_keys", result.summary)

    def test_scalar_decision_keys_passes_without_char_findings(self):
        # A present-but-non-list decision_keys (a scalar string) must be guarded
        # by ``isinstance(keys, list)`` — NOT merely a ``keys is None`` check.
        # Without the list-type guard the code would iterate the string
        # character-by-character, fabricating one dangling-citation finding per
        # character. Assert the check passes cleanly with zero findings.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            _write_adr(state, "0001-scalar.md", {
                "id": "ADR-0001", "title": "Scalar", "status": "accepted",
                "decision_keys": "stack.language",  # scalar string, not a list
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_malformed_adr_frontmatter_does_not_raise(self):
        # An ADR with no/garbled frontmatter contributes no keys; must not crash.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            (state / "decisions" / "0001-broken.md").write_text(
                "no frontmatter here at all\njust prose\n", encoding="utf-8"
            )
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck14Pass(unittest.TestCase):
    def test_all_cited_keys_exist_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {
                "stack.language": "rust",
                "stack.framework": "axum",
            })
            _write_adr(state, "0001-stack.md", {
                "id": "ADR-0001", "title": "Stack", "status": "accepted",
                "decision_keys": ["stack.language", "stack.framework"],
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_multiple_adrs_all_covered_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {
                "stack.language": "rust",
                "architecture.style": "hexagonal",
            })
            _write_adr(state, "0001-lang.md", {
                "id": "ADR-0001", "title": "Lang", "status": "accepted",
                "decision_keys": ["stack.language"],
            })
            _write_adr(state, "0002-arch.md", {
                "id": "ADR-0002", "title": "Arch", "status": "accepted",
                "decision_keys": ["architecture.style"],
            })
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck14Fail(unittest.TestCase):
    def test_dangling_citation_fails_warning(self):
        # ADR cites a decision_key that is NOT in the flat decisions map.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            _write_adr(state, "0001-stale.md", {
                "id": "ADR-0001", "title": "Stale", "status": "accepted",
                "decision_keys": ["stack.database"],  # not recorded
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "14")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertIn("ADR-0001", f.message)
            self.assertIn("stack.database", f.message)
            self.assertEqual(f.location, "stack.database")

    def test_one_dangling_among_several_cited(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            _write_adr(state, "0001.md", {
                "id": "ADR-0001", "title": "Mixed", "status": "accepted",
                "decision_keys": ["stack.language", "stack.ghost"],
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "stack.ghost")

    def test_dangling_across_two_adrs(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            _write_adr(state, "0001.md", {
                "id": "ADR-0001", "title": "A", "status": "accepted",
                "decision_keys": ["stack.gone1"],
            })
            _write_adr(state, "0002.md", {
                "id": "ADR-0002", "title": "B", "status": "accepted",
                "decision_keys": ["stack.gone2"],
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 2)
            locations = {f.location for f in result.findings}
            self.assertEqual(locations, {"stack.gone1", "stack.gone2"})

    def test_adr_missing_id_uses_question_mark(self):
        # v8-adaptation: an ADR with a dangling citation but no id field still
        # produces a finding, with "?" standing in for the missing id.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"stack.language": "rust"})
            _write_adr(state, "0001.md", {
                "title": "No Id", "status": "accepted",
                "decision_keys": ["stack.ghost"],
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertIn("ADR ?", result.findings[0].message)
            self.assertEqual(result.findings[0].location, "stack.ghost")


if __name__ == "__main__":
    unittest.main()
