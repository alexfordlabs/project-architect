"""Tests for the check_09_no_todos auditor check."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_09_no_todos
from architect_brain.checks.check_09_no_todos import CHECK_ID, NAME, SEVERITY, run


def _state(tmp: str, docs: dict[str, str]) -> Path:
    """Build docs/<...> + docs/_architect_state, return the state_dir."""
    project = Path(tmp)
    docs_dir = project / "docs"
    state = docs_dir / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in docs.items():
        p = docs_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck09(unittest.TestCase):

    # --- module contract ----------------------------------------------------

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "09")
        self.assertEqual(NAME, "no_todos")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_09_no_todos.CHECK_ID, "09")
        self.assertTrue(hasattr(check_09_no_todos, "run"))

    # --- passing fixtures ----------------------------------------------------

    def test_pass_when_clean_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "VISION.md": "# Vision\n\nA clean document with no markers.\n",
                "ARCHITECTURE.md": "# Architecture\n\nAll done here.\n",
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "09")
            self.assertEqual(result.findings, ())

    def test_lowercase_todo_does_not_trip(self):
        # case-sensitive: lowercase "todo" in prose is a noun, not a marker.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "NOTES.md": "the todo list is at the end; FOXXXING is fine too.\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    def test_pass_when_only_backlog_has_markers(self):
        # BACKLOG.md is the canonical place for parked TODOs; excluded by design.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "BACKLOG.md": "- TODO: finish the auth flow\n- FIXME: rate limit\n",
                "VISION.md": "# Vision\n\nNothing to fix.\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    def test_pass_when_only_backlog_in_subdir(self):
        # basename match: any subdir's BACKLOG.md is excluded.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "planning/BACKLOG.md": "TODO: deferred work lives here\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    # --- failing fixtures ----------------------------------------------------

    def test_fail_on_todo_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "VISION.md": "# Vision\n\nTODO: write the rest of this section.\n",
                "ARCHITECTURE.md": "# Architecture\n\nAll done here.\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertEqual(f.location, "VISION.md")
            self.assertIn("VISION.md", f.message)
            self.assertIn("TODO", f.message)
            self.assertIn("3", f.message)  # marker is on line 3

    def test_fail_on_fixme_and_xxx(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "A.md": "first line\nFIXME this needs work\n",
                "B.md": "XXX revisit\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 2)
            locations = {f.location for f in result.findings}
            self.assertEqual(locations, {"A.md", "B.md"})
            messages = " ".join(f.message for f in result.findings)
            self.assertIn("FIXME", messages)
            self.assertIn("XXX", messages)

    def test_first_match_per_file_only(self):
        # Multiple markers in one file -> exactly one Finding (the first).
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "M.md": "line one\nTODO first\nFIXME second\nXXX third\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertIn("TODO", result.findings[0].message)
            self.assertIn("2", result.findings[0].message)  # first marker, line 2

    def test_word_boundary_no_substring_false_positive(self):
        # "FOXXXING" should not match; "TODOs" should not match (word-boundary).
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "P.md": "FOXXXING is a word.\nTODOs are common.\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    def test_backlog_excluded_other_file_still_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "BACKLOG.md": "TODO: parked here, ignored.\n",
                "SPEC.md": "TODO: but this one counts.\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "SPEC.md")

    # --- empty / degraded ----------------------------------------------------

    def test_pass_when_no_docs_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            # state_dir whose parent (docs/) does not exist as a real tree of md
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "09")

    def test_pass_when_no_markdown_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {})
            # add a non-md file so docs/ exists but has no markdown
            (Path(tmp) / "docs" / "data.json").write_text("{}", encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)

    def test_state_subtree_md_not_scanned(self):
        # _architect_state markdown is machine state, never a design doc.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {})
            (state / "note.md").write_text("TODO machine note\n", encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)

    def test_never_raises_on_missing_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            # state_dir parent simply doesn't exist
            state = Path(tmp) / "nope" / "_architect_state"
            result = run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
