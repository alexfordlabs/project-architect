"""Tests for the check_18_ledger_complete auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_18_ledger_complete
from architect_brain.checks.check_18_ledger_complete import CHECK_ID, NAME, SEVERITY, run


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    docs_root      = state_dir.parent        = ``<tmp>/docs``
    project_root   = state_dir.parent.parent = ``<tmp>``
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_doc(tmp: str, rel: str, body: str = "# doc\n") -> Path:
    """Write a markdown doc at ``<tmp>/<rel>`` (rel is project-relative)."""
    path = Path(tmp) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_docs_json(state_dir: Path, completed: list[dict]) -> None:
    (state_dir / "docs.json").write_text(
        json.dumps({"schema_version": "4.0", "completed": completed}),
        encoding="utf-8",
    )


class TestCheck18Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "18")
        self.assertEqual(NAME, "ledger_complete")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_18_ledger_complete.CHECK_ID, "18")
        self.assertTrue(callable(check_18_ledger_complete.run))


class TestCheck18Degraded(unittest.TestCase):
    def test_no_docs_at_all_passes(self):
        # Fresh project: only the state dir exists, no design docs on disk.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "18")
            self.assertEqual(result.findings, ())

    def test_docs_present_no_docs_json_fails(self):
        # On-disk doc exists but docs.json is absent → ledger empty → unrecorded.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/PROJECT_OVERVIEW.md")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "docs/PROJECT_OVERVIEW.md")

    def test_empty_completed_with_no_docs_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_docs_json(state, [])
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck18Pass(unittest.TestCase):
    def test_every_doc_recorded_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/PROJECT_OVERVIEW.md")
            _write_doc(tmp, "docs/ARCHITECTURE.md")
            _write_docs_json(
                state,
                [
                    {"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md",
                     "content_hash": "a"},
                    {"name": "ARCHITECTURE", "path": "docs/ARCHITECTURE.md",
                     "content_hash": "b"},
                ],
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_one_level_subdir_doc_recorded_passes(self):
        # A doc one directory deep (depth == 2) is still in scope and recorded.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/design/COMPONENT.md")
            _write_docs_json(
                state,
                [{"name": "COMPONENT", "path": "docs/design/COMPONENT.md",
                  "content_hash": "c"}],
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_excluded_subtrees_not_required(self):
        # ADRs (decisions/), research/, and frozen versions/ snapshots are NOT
        # ledger-tracked design docs — present on disk but absent from the ledger
        # must NOT fail the check.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/decisions/ADR-0001-foo.md")
            _write_doc(tmp, "docs/research/notes.md")
            _write_doc(tmp, "docs/versions/v1/SNAPSHOT.md")
            _write_docs_json(state, [])  # nothing recorded
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_deep_doc_beyond_depth_two_ignored(self):
        # A doc THREE levels deep (depth 3 > 2) is outside scope and not required.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/a/b/DEEP.md")
            _write_docs_json(state, [])  # nothing recorded
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck18Fail(unittest.TestCase):
    def test_unrecorded_doc_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/PROJECT_OVERVIEW.md")
            _write_doc(tmp, "docs/ARCHITECTURE.md")
            # Only one of the two recorded.
            _write_docs_json(
                state,
                [{"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md",
                  "content_hash": "a"}],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "18")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertEqual(f.location, "docs/ARCHITECTURE.md")
            self.assertIn("docs/ARCHITECTURE.md", f.message)
            self.assertIn("absent from docs.completed", f.message)

    def test_multiple_unrecorded_each_get_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/A.md")
            _write_doc(tmp, "docs/B.md")
            _write_docs_json(state, [])
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 2)
            locations = sorted(f.location for f in result.findings)
            self.assertEqual(locations, ["docs/A.md", "docs/B.md"])

    def test_v8_adaptation_compares_project_relative_path(self):
        # v8-adaptation: completed[].path is PROJECT-relative ("docs/<NAME>.md").
        # If the ledger stored only the DOCS-relative form ("<NAME>.md"), the
        # like-for-like comparison must NOT match — the check compares against the
        # project_root-relative posix path.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/PROJECT_OVERVIEW.md")
            # Ledger holds the DOCS-relative (wrong-form) path.
            _write_docs_json(
                state,
                [{"name": "PROJECT_OVERVIEW", "path": "PROJECT_OVERVIEW.md",
                  "content_hash": "a"}],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "docs/PROJECT_OVERVIEW.md")

    def test_unrecorded_depth_two_subdir_doc_fails(self):
        # Depth-2 boundary: a doc ONE subdirectory deep (docs/design/COMPONENT.md
        # → relative-to-docs_root parts == 2) is IN scope. Left unrecorded it must
        # produce a finding. This kills the boundary mutation `> _MAX_DEPTH` →
        # `>= _MAX_DEPTH`, which would silently drop the depth-2 doc (0 findings).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/design/COMPONENT.md")
            _write_docs_json(state, [])  # nothing recorded
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "docs/design/COMPONENT.md")

    def test_completed_entry_without_path_ignored(self):
        # A completed entry missing "path" must not crash and must not satisfy any
        # on-disk doc.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(tmp, "docs/PROJECT_OVERVIEW.md")
            _write_docs_json(
                state,
                [{"name": "PROJECT_OVERVIEW", "content_hash": "a"}],  # no "path"
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "docs/PROJECT_OVERVIEW.md")


if __name__ == "__main__":
    unittest.main()
