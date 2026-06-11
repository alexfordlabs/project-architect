"""Tests for the check_27_required_docs_generated auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_27_required_docs_generated
from architect_brain.checks.check_27_required_docs_generated import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)

# The LIVE plugin template dir, resolved the same way the check resolves it.
_TEMPLATE_DIR = (
    Path(check_27_required_docs_generated.__file__).resolve().parents[3]
    / "references"
    / "templates"
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    project_root = state_dir.parent.parent = ``<tmp>`` ; docs_root = ``<tmp>/docs``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _live_required_names() -> list[str]:
    """The doc-class generate_when:always NAMEs from the LIVE template dir.

    Mirrors the check's own derivation so the fixtures stay in sync with the
    plugin's actual templates (v7 used the live frontmatter as source of truth).
    Reads the FIRST ``---`` frontmatter block even past a leading HTML-comment
    header (3 of the 5 always-doc templates begin with an attribution comment).
    """
    from architect_brain.adr import parse_frontmatter

    names: list[str] = []
    for tmpl in sorted(_TEMPLATE_DIR.glob("*.md")):
        name = tmpl.stem
        if name == "CLAUDE_MD_ROOT" or name.startswith("SLASH_"):
            continue
        text = tmpl.read_text(encoding="utf-8")
        # Strip any leading HTML-comment header + blank lines so the text
        # begins at the first ``---`` (parse_frontmatter requires that).
        idx = text.find("\n---")
        head = text.lstrip()
        if head.startswith("---"):
            fm = parse_frontmatter(head)
        elif idx != -1:
            fm = parse_frontmatter(text[idx + 1 :])
        else:
            fm = {}
        if fm.get("generate_when") == "always":
            names.append(name)
    return names


class TestCheck27Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "27")
        self.assertEqual(NAME, "required_docs_generated")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_27_required_docs_generated.CHECK_ID, "27")
        self.assertTrue(callable(check_27_required_docs_generated.run))


class TestCheck27Discovery(unittest.TestCase):
    def test_live_templates_yield_the_v7_doc_class_set(self):
        # The v8-adaptation hinge: 3 of the 5 always-doc-class templates begin
        # with a leading HTML-comment header, so a naive parse_frontmatter on the
        # raw bytes would drop them. We require the full v7 set.
        names = set(_live_required_names())
        self.assertEqual(
            names,
            {
                "PROJECT_OVERVIEW",
                "PROJECT_REQUIREMENTS",
                "CLAUDE_MD_PLAN",
                "CLAUDE_TOOLING_PLAN",
                "NEXT_STEP_PLAN",
            },
        )
        # CLAUDE_MD_ROOT (always, but Phase 6/7) and SLASH_* must be excluded.
        self.assertNotIn("CLAUDE_MD_ROOT", names)
        self.assertFalse(any(n.startswith("SLASH_") for n in names))


class TestCheck27Pass(unittest.TestCase):
    def test_all_required_docs_present_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            docs = state.parent  # <tmp>/docs
            for name in _live_required_names():
                (docs / f"{name}.md").write_text("# doc\n", encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "27")
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.findings, ())

    def test_excluded_templates_not_required(self):
        # CLAUDE_MD_ROOT.md and SLASH_*.md are NOT required at the Phase-4 gate;
        # leaving them off disk must not fail the check when the doc-class set
        # is all present.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            docs = state.parent
            for name in _live_required_names():
                (docs / f"{name}.md").write_text("# doc\n", encoding="utf-8")
            # Intentionally do NOT create CLAUDE_MD_ROOT.md or any SLASH_*.md.
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck27Fail(unittest.TestCase):
    def test_one_missing_doc_fails_blocking(self):
        required = _live_required_names()
        self.assertIn("PROJECT_REQUIREMENTS", required)  # guard the fixture
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            docs = state.parent
            for name in required:
                if name == "PROJECT_REQUIREMENTS":
                    continue  # the one that was silently skipped (the v7 bug)
                (docs / f"{name}.md").write_text("# doc\n", encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "27")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].message, "docs/PROJECT_REQUIREMENTS.md")
            self.assertEqual(
                result.findings[0].location, "docs/PROJECT_REQUIREMENTS.md"
            )

    def test_no_docs_at_all_fails_with_finding_per_required(self):
        required = _live_required_names()
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            # docs/ exists (the state dir's parent) but holds no generated docs.
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), len(required))
            messages = {f.message for f in result.findings}
            self.assertIn("docs/PROJECT_OVERVIEW.md", messages)
            self.assertIn("docs/PROJECT_REQUIREMENTS.md", messages)


class TestCheck27Degraded(unittest.TestCase):
    def test_template_dir_not_locatable_passes(self):
        # If the template dir cannot be located (off-plugin layout), the check
        # must NOT false-block. We simulate this by monkeypatching the resolved
        # template dir to a path that does not exist.
        original = check_27_required_docs_generated._template_dir
        try:
            check_27_required_docs_generated._template_dir = (
                lambda: Path("/nonexistent/templates/dir/__nope__")
            )
            with tempfile.TemporaryDirectory() as tmp:
                state = _make_state(tmp)
                result = run(state)
                self.assertTrue(result.passed)
                self.assertEqual(result.findings, ())
        finally:
            check_27_required_docs_generated._template_dir = original

    def test_no_always_doc_templates_discovered_passes(self):
        # An empty template dir → no always-doc NAMEs discovered → decline to
        # make a claim (pass), exactly like the v7 INFO-pass branch.
        original = check_27_required_docs_generated._template_dir
        try:
            with tempfile.TemporaryDirectory() as tmpl_tmp:
                empty = Path(tmpl_tmp) / "templates"
                empty.mkdir()
                check_27_required_docs_generated._template_dir = lambda: empty
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp)
                    result = run(state)
                    self.assertTrue(result.passed)
                    self.assertEqual(result.findings, ())
        finally:
            check_27_required_docs_generated._template_dir = original

    def test_only_excluded_templates_discovered_passes(self):
        # A template dir containing ONLY excluded always-templates
        # (CLAUDE_MD_ROOT + SLASH_*) → no doc-class NAMEs → pass.
        original = check_27_required_docs_generated._template_dir
        try:
            with tempfile.TemporaryDirectory() as tmpl_tmp:
                tdir = Path(tmpl_tmp) / "templates"
                tdir.mkdir()
                fm = "---\ngenerate_when: always\n---\n# x\n"
                (tdir / "CLAUDE_MD_ROOT.md").write_text(fm, encoding="utf-8")
                (tdir / "SLASH_IMPLEMENT.md").write_text(fm, encoding="utf-8")
                check_27_required_docs_generated._template_dir = lambda: tdir
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp)
                    result = run(state)
                    self.assertTrue(result.passed)
        finally:
            check_27_required_docs_generated._template_dir = original

    def test_leading_comment_template_is_required(self):
        # The v8-adaptation, isolated: a template that begins with an HTML
        # comment header BEFORE its --- frontmatter must still be discovered as
        # an always-doc and required on disk. parse_frontmatter on the raw bytes
        # would return {} (text must start with ---); the check strips the
        # leading comment first.
        original = check_27_required_docs_generated._template_dir
        try:
            with tempfile.TemporaryDirectory() as tmpl_tmp:
                tdir = Path(tmpl_tmp) / "templates"
                tdir.mkdir()
                (tdir / "WIDGET.md").write_text(
                    "<!-- Author: Someone -->\n"
                    "<!-- License: MIT -->\n"
                    "\n"
                    "---\n"
                    "template_name: WIDGET\n"
                    "generate_when: always\n"
                    "---\n\n# Widget\n",
                    encoding="utf-8",
                )
                check_27_required_docs_generated._template_dir = lambda: tdir
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp)
                    # docs/WIDGET.md missing → must FAIL (the leading-comment
                    # template was correctly discovered as required).
                    result = run(state)
                    self.assertFalse(result.passed)
                    self.assertEqual(result.severity, "BLOCKING")
                    self.assertEqual(len(result.findings), 1)
                    self.assertEqual(result.findings[0].message, "docs/WIDGET.md")
                    # And present → passes.
                    (state.parent / "WIDGET.md").write_text("# w\n", encoding="utf-8")
                    self.assertTrue(run(state).passed)
        finally:
            check_27_required_docs_generated._template_dir = original

    def test_quoted_generate_when_value_recognised(self):
        # PROJECT_OVERVIEW uses `generate_when: "always"` (quoted). parse_frontmatter
        # strips the quotes, so the comparison against the bare string holds.
        original = check_27_required_docs_generated._template_dir
        try:
            with tempfile.TemporaryDirectory() as tmpl_tmp:
                tdir = Path(tmpl_tmp) / "templates"
                tdir.mkdir()
                (tdir / "QUOTED.md").write_text(
                    '---\ngenerate_when: "always"\n---\n# q\n', encoding="utf-8"
                )
                check_27_required_docs_generated._template_dir = lambda: tdir
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp)
                    result = run(state)
                    self.assertFalse(result.passed)
                    self.assertEqual(result.findings[0].message, "docs/QUOTED.md")
        finally:
            check_27_required_docs_generated._template_dir = original

    def test_does_not_raise_on_missing_state_tree(self):
        # Even with a bare state_dir whose project docs/ has nothing, the check
        # must not raise.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            try:
                run(state)
            except Exception as exc:  # pragma: no cover - guard
                self.fail(f"run() raised: {exc!r}")


if __name__ == "__main__":
    unittest.main()
