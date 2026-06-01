"""Tests for the check_08_no_placeholders auditor check."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_08_no_placeholders
from architect_brain.checks.check_08_no_placeholders import CHECK_ID, NAME, SEVERITY, run


def _docs(tmp: str, files: dict[str, str]) -> Path:
    """Build a project tree with a docs/ dir + _architect_state, return state_dir."""
    docs = Path(tmp) / "docs"
    state = docs / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in files.items():
        p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck08(unittest.TestCase):

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "08")
        self.assertEqual(NAME, "no_placeholders")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertTrue(hasattr(check_08_no_placeholders, "run"))

    def test_pass_when_no_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _docs(tmp, {
                "VISION.md": "# Vision\n\nA real project with no markers.\n",
                "design/ARCHITECTURE.md": "## Architecture\n\nClean prose.\n",
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "08")
            self.assertEqual(result.findings, ())

    def test_fail_on_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _docs(tmp, {
                "VISION.md": "# Vision\n\nGreat tool.\n",
                "design/ARCHITECTURE.md": "## Arch\n\nBuilt for {{project_name}} users.\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "08")
            # one Finding for the failing file, located at the relpath
            self.assertTrue(any(f.location == "design/ARCHITECTURE.md" for f in result.findings))
            joined = " ".join(f.message for f in result.findings)
            self.assertIn("{{project_name}}", joined)
            self.assertIn("design/ARCHITECTURE.md", joined)
            # clean file produces no Finding
            self.assertFalse(any("VISION.md" in (f.location or "") for f in result.findings))

    def test_reports_first_match_per_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _docs(tmp, {
                "DOC.md": "intro {{first_key}}\nthen {{second_key}}\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            # exactly ONE finding for this single file (first match only)
            doc_findings = [f for f in result.findings if f.location == "DOC.md"]
            self.assertEqual(len(doc_findings), 1)
            msg = doc_findings[0].message
            self.assertIn("{{first_key}}", msg)
            self.assertNotIn("{{second_key}}", msg)
            # line number of the first match (line 1)
            self.assertIn("1:", msg)

    def test_one_finding_per_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _docs(tmp, {
                "A.md": "uses {{key_a}}\n",
                "B.md": "uses {{key_b}}\n",
                "C.md": "clean\n",
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 2)
            locs = {f.location for f in result.findings}
            self.assertEqual(locs, {"A.md", "B.md"})

    def test_case_sensitive_lowercase_only(self):
        # Uppercase {{TOC}} and spaced Jinja {{ project_name }} are NOT flagged.
        with tempfile.TemporaryDirectory() as tmp:
            state = _docs(tmp, {
                "DOC.md": "table {{TOC}}\nspaced {{ project_name }}\nmixed {{Project_Name}}\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    def test_skips_versions_and_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _docs(tmp, {
                "versions/v1/OLD.md": "frozen {{stale_key}}\n",
                "research/notes.md": "ref {{ignored_key}}\n",
                "VISION.md": "clean prose\n",
            })
            result = run(state)
            self.assertTrue(result.passed)

    def test_pass_when_no_docs_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            # state_dir whose parent (docs/) does not actually contain markdown
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_pass_when_only_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _docs(tmp, {})
            # markdown only under _architect_state is skipped by collect_markdown
            (state / "note.md").write_text("internal {{state_key}}\n", encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
