"""Tests for the check_24_identity_hygiene auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_24_identity_hygiene
from architect_brain.checks.check_24_identity_hygiene import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    project_root = state_dir.parent.parent = ``<tmp>``;
    docs_root    = state_dir.parent        = ``<tmp>/docs``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_deny(state_dir: Path, content: str) -> None:
    """Write the optional ``.architect/identity-deny.txt`` under the project root."""
    proj = state_dir.parent.parent
    archdir = proj / ".architect"
    archdir.mkdir(parents=True, exist_ok=True)
    (archdir / "identity-deny.txt").write_text(content, encoding="utf-8")


def _write_doc(state_dir: Path, rel: str, content: str) -> None:
    """Write a doc file under ``docs/`` (docs_root = state_dir.parent)."""
    docs = state_dir.parent
    p = docs / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


class TestCheck24Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "24")
        self.assertEqual(NAME, "identity_hygiene")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_24_identity_hygiene.CHECK_ID, "24")
        self.assertTrue(callable(check_24_identity_hygiene.run))


class TestCheck24Degraded(unittest.TestCase):
    def test_no_deny_file_passes(self):
        # Fresh project: no .architect/identity-deny.txt → nothing to enforce.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(state, "VISION.md", "Jane Q. Operator wrote this.")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "24")
            self.assertEqual(result.findings, ())

    def test_deny_file_but_no_docs_passes(self):
        # Deny file present but docs/ has no other files → nothing leaks.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "Jane Q. Operator\n")
            result = run(state)
            self.assertTrue(result.passed)

    def test_blank_and_comment_lines_ignored(self):
        # Blank lines + #-comments must not be treated as forbidden terms;
        # an empty/comment-only deny file leaks nothing.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "# this is a comment\n\n   \n")
            _write_doc(state, "VISION.md", "wholly innocuous content")
            result = run(state)
            self.assertTrue(result.passed)

    def test_comment_text_present_in_doc_still_passes(self):
        # A ``#``-prefixed deny line is a COMMENT, not a forbidden term — even
        # when that exact comment text appears verbatim in a doc. This guards
        # the ``term.startswith("#")`` skip: drop it and the comment becomes a
        # live term, producing a false BLOCKING finding against the doc.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "# Jane Q. Operator\n")
            _write_doc(state, "VISION.md", "# Jane Q. Operator")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck24Pass(unittest.TestCase):
    def test_terms_absent_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "Jane Q. Operator\nsecret@personal.example\n")
            _write_doc(state, "VISION.md", "All authored by the pseudonym.")
            _write_doc(state, "decisions/ADR-0001.md", "no PII here either")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_state_subtree_not_scanned(self):
        # A forbidden term living ONLY inside docs/_architect_state (machine
        # state, e.g. recorded in an event) must NOT trip the check — that
        # subtree is not "docs the author writes".
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "Jane Q. Operator\n")
            (state / "events.jsonl").write_text(
                '{"who":"Jane Q. Operator"}\n', encoding="utf-8"
            )
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck24Fail(unittest.TestCase):
    def test_leaked_term_fails_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "Jane Q. Operator\n")
            _write_doc(state, "VISION.md", "Authored by Jane Q. Operator in 2026.")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "24")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertIn("VISION.md", f.message)
            self.assertIn("forbidden term: 'Jane Q. Operator'", f.message)
            self.assertEqual(f.location, "VISION.md")

    def test_fixed_string_not_regex(self):
        # The dot in "Jane Q. Operator" is literal, NOT a wildcard: a doc that
        # would only match under regex semantics ("Jane QX Operator") must NOT
        # match; the verbatim term must.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "Jane Q. Operator\n")
            _write_doc(state, "regex-bait.md", "Here lurks Jane QX Operator.")
            result = run(state)
            self.assertTrue(result.passed)

            _write_doc(state, "real.md", "And also Jane Q. Operator verbatim.")
            result2 = run(state)
            self.assertFalse(result2.passed)
            self.assertTrue(
                any("real.md" in f.message for f in result2.findings)
            )

    def test_multiple_terms_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "Jane Q. Operator\nsecret@personal.example\n")
            _write_doc(state, "VISION.md", "by Jane Q. Operator")
            _write_doc(state, "CONTACT.md", "reach secret@personal.example")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 2)
            joined = " ".join(f.message for f in result.findings)
            self.assertIn("Jane Q. Operator", joined)
            self.assertIn("secret@personal.example", joined)
            locs = {f.location for f in result.findings}
            self.assertEqual(locs, {"VISION.md", "CONTACT.md"})

    def test_non_markdown_files_scanned(self):
        # v7 scanned ALL files under docs/, not just .md — a leak in a .txt
        # or .json design artifact must still be caught.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_deny(state, "Jane Q. Operator\n")
            _write_doc(state, "notes.txt", "drafted by Jane Q. Operator")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertTrue(
                any("notes.txt" in f.message for f in result.findings)
            )


if __name__ == "__main__":
    unittest.main()
