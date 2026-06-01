"""Tests for the check_07_attribution_footer auditor check."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_07_attribution_footer
from architect_brain.checks.check_07_attribution_footer import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)

_FOOTER = (
    "*★ Skillfully made with "
    "[project-architect](https://github.com/alexfordlabs/project-architect).*"
)


def _state(tmp: str, docs: dict[str, str]) -> Path:
    """Build a project tree with ``docs/<rel> = content`` and a state dir.

    Returns the ``state_dir`` (``docs/_architect_state``); ``docs_root`` is its
    parent, which is where the check scans for markdown.
    """
    docs_root = Path(tmp) / "docs"
    state = docs_root / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in docs.items():
        p = docs_root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck07(unittest.TestCase):

    # --- module contract -------------------------------------------------

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "07")
        self.assertEqual(NAME, "attribution_footer")
        self.assertEqual(SEVERITY, "INFO")
        self.assertTrue(callable(run))
        self.assertTrue(hasattr(check_07_attribution_footer, "run"))

    # --- passing fixture -------------------------------------------------

    def test_pass_when_all_docs_have_footer(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "architecture.md": f"# Architecture\n\nBody.\n\n---\n\n{_FOOTER}\n",
                "vision.md": f"# Vision\n\nBody text.\n\n{_FOOTER}\n",
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "07")
            self.assertEqual(result.findings, ())

    def test_pass_footer_in_last_three_lines_with_trailing_blank(self):
        # Footer is the 3rd-from-last line; a trailing blank line + EOF newline
        # must still count (splitlines()[-3:] includes it).
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "doc.md": f"# Doc\n\nBody.\n\n{_FOOTER}\n\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    def test_pass_footer_exactly_third_from_last_with_two_content_lines(self):
        # Footer is the EXACT 3rd-from-last line, followed by two trailing
        # CONTENT lines (not blanks). The window must reach back 3 lines for
        # the footer to count. This pins splitlines()[-3:]: with [-3:] the
        # footer is in-window (PASS); with [-2:] it would be missed (mutation
        # kill).
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "doc.md": f"# Doc\n\nBody.\n\n{_FOOTER}\nline2\nline3\n",
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    # --- failing fixture (INFO) -----------------------------------------

    def test_fail_when_a_doc_missing_footer(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "architecture.md": f"# Architecture\n\nBody.\n\n{_FOOTER}\n",
                "naked.md": "# Naked\n\nNo footer here.\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "INFO")
            self.assertEqual(result.check_id, "07")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertEqual(f.location, "naked.md")
            self.assertEqual(f.message, "naked.md")

    def test_fail_when_footer_pushed_out_of_last_three_lines(self):
        # Footer present but followed by >2 trailing content lines -> not in
        # the last 3 lines -> missing.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "doc.md": f"# Doc\n\n{_FOOTER}\n\nextra1\nextra2\nextra3\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertTrue(any(f.location == "doc.md" for f in result.findings))

    def test_fail_lists_every_missing_doc(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "a.md": "# A\n\nno footer\n",
                "b.md": "# B\n\nno footer\n",
                "c.md": f"# C\n\n{_FOOTER}\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            locs = {f.location for f in result.findings}
            self.assertEqual(locs, {"a.md", "b.md"})

    # --- skip dirs (versions/research) ----------------------------------

    def test_versions_and_research_dirs_are_skipped(self):
        # Footer-less docs under docs/versions/ and docs/research/ must NOT
        # cause a failure (extra_skip_dirs excludes them).
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "architecture.md": f"# Architecture\n\nBody.\n\n{_FOOTER}\n",
                "versions/v1/old.md": "# Old snapshot\n\nno footer\n",
                "research/notes.md": "# Reference notes\n\nno footer\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    # --- empty / degraded path ------------------------------------------

    def test_pass_when_no_docs(self):
        # No markdown files at all under docs/ -> nothing to verify -> pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_pass_when_docs_root_missing(self):
        # Fresh/degraded project: state_dir has no parent docs content beyond
        # itself; collect_markdown returns [] -> pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(state)
            self.assertTrue(result.passed)

    def test_never_raises_on_str_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"x.md": f"hi\n\n{_FOOTER}\n"})
            # pass a str, not a Path
            result = run(str(state))
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
