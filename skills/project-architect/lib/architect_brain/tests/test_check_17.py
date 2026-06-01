"""Tests for the check_17_adr_files_exist auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_17_adr_files_exist
from architect_brain.checks.check_17_adr_files_exist import CHECK_ID, NAME, SEVERITY, run


def _make_state(tmp: str, adrs: list[dict] | None = None) -> Path:
    """Create ``<tmp>/docs/_architect_state`` with a flat index carrying ``adrs``.

    Returns the state_dir. ``decisions_md_dir`` = state_dir/decisions.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    if adrs is not None:
        (state / "99-flat-index.json").write_text(
            json.dumps({"schema_version": "4.0", "decisions": {}, "adrs": adrs}),
            encoding="utf-8",
        )
    return state


def _write_adr_file(state_dir: Path, filename: str) -> None:
    dec = state_dir / "decisions"
    dec.mkdir(parents=True, exist_ok=True)
    (dec / filename).write_text("# adr stub\n", encoding="utf-8")


class TestCheck17Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "17")
        self.assertEqual(NAME, "adr_files_exist")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_17_adr_files_exist.CHECK_ID, "17")
        self.assertTrue(callable(check_17_adr_files_exist.run))


class TestCheck17Degraded(unittest.TestCase):
    def test_no_state_at_all_passes(self):
        # No 99-flat-index.json → load_adrs() safe-empty → nothing to verify.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, adrs=None)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "17")
            self.assertEqual(result.findings, ())

    def test_no_adrs_recorded_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, adrs=[])
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck17Pass(unittest.TestCase):
    def test_id_dash_slug_file_matches(self):
        # decisions/<id>-*.md glob match counts as present.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp, adrs=[{"id": "0001", "title": "Use Postgres", "status": "Accepted"}]
            )
            _write_adr_file(state, "0001-use-postgres.md")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_bare_id_file_matches(self):
        # decisions/<id>.md (no slug suffix) also counts as present.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp, adrs=[{"id": "0002", "title": "Bare id", "status": "Accepted"}]
            )
            _write_adr_file(state, "0002.md")
            result = run(state)
            self.assertTrue(result.passed)

    def test_all_recorded_have_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                adrs=[
                    {"id": "0001", "title": "A", "status": "Accepted"},
                    {"id": "0002", "title": "B", "status": "Proposed"},
                ],
            )
            _write_adr_file(state, "0001-a.md")
            _write_adr_file(state, "0002-b.md")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_reserved_status_skipped(self):
        # A Reserved ADR legitimately has no file yet → must NOT be flagged.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                adrs=[
                    {"id": "0001", "title": "A", "status": "Accepted"},
                    {"id": "0009", "title": "future", "status": "Reserved"},
                ],
            )
            _write_adr_file(state, "0001-a.md")
            # 0009 has NO file but is Reserved → still passes.
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck17Fail(unittest.TestCase):
    def test_fileless_adr_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp, adrs=[{"id": "0003", "title": "Missing", "status": "Accepted"}]
            )
            # No decisions/ dir / no file written.
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "17")
            self.assertEqual(len(result.findings), 1)
            finding = result.findings[0]
            self.assertEqual(
                finding.message, "ADR 0003 recorded but no file in decisions/"
            )
            self.assertEqual(finding.location, "0003")

    def test_mixed_only_fileless_flagged(self):
        # One ADR has a file, one does not → exactly one finding for the fileless.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                adrs=[
                    {"id": "0001", "title": "Has file", "status": "Accepted"},
                    {"id": "0004", "title": "No file", "status": "Proposed"},
                ],
            )
            _write_adr_file(state, "0001-has-file.md")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "0004")

    def test_reserved_not_counted_among_failures(self):
        # A Reserved fileless ADR is skipped; a non-reserved fileless ADR fails.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                adrs=[
                    {"id": "0009", "title": "future", "status": "Reserved"},
                    {"id": "0005", "title": "real missing", "status": "Accepted"},
                ],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "0005")


if __name__ == "__main__":
    unittest.main()
