"""Tests for the check_22_cross_link_integrity auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

check_22 is the v7 sibling of check_01 (both port a doc cross-link checker).
These tests focus on what 22 adds over 01: optional-link-title stripping,
absolute-vs-project-root target resolution, the ``versions``/``research``
extra-skip dirs, and the ``... (target missing)`` finding-message form.
"""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_22_cross_link_integrity


def _project(tmp: str, files: dict[str, str]) -> Path:
    """Build a project tree under tmp/ with docs/_architect_state/ as state_dir.

    ``files`` maps a path relative to the project's ``docs/`` to its content.
    Returns the state_dir (``docs/_architect_state``) the check is invoked with.
    project_root = state_dir.parent.parent = tmp.
    """
    docs = Path(tmp) / "docs"
    state = docs / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in files.items():
        p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck22Contract(unittest.TestCase):

    def test_module_contract(self):
        self.assertEqual(check_22_cross_link_integrity.CHECK_ID, "22")
        self.assertEqual(check_22_cross_link_integrity.NAME, "cross_link_integrity")
        self.assertEqual(check_22_cross_link_integrity.SEVERITY, "BLOCKING")
        self.assertTrue(callable(check_22_cross_link_integrity.run))


class TestCheck22Pass(unittest.TestCase):

    def test_pass_when_links_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "OVERVIEW.md": "See [arch](ARCHITECTURE.md) for details.",
                "ARCHITECTURE.md": "# Architecture\n",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "22")
            self.assertEqual(result.findings, ())

    def test_pass_on_subdir_relative_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "INDEX.md": "Read [adr](decisions/0001-x.md).",
                "decisions/0001-x.md": "# ADR 0001\n",
            })
            self.assertTrue(check_22_cross_link_integrity.run(state).passed)

    def test_pass_on_parent_relative_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "sub/CHILD.md": "Back to [overview](../OVERVIEW.md).",
                "OVERVIEW.md": "# Overview\n",
            })
            self.assertTrue(check_22_cross_link_integrity.run(state).passed)

    def test_skips_external_and_anchor_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "OVERVIEW.md": (
                    "[ext](https://example.com/page)\n"
                    "[ftp](ftp://host/file)\n"
                    "[rel](//cdn.example.com/x)\n"
                    "[mail](mailto:alex@example.com)\n"
                    "[phone](tel:+15555550100)\n"
                    "[anchor](#a-heading)\n"
                ),
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_anchor_stripped_from_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "Jump to [section](B.md#heading).",
                "B.md": "# B\n## heading\n",
            })
            self.assertTrue(check_22_cross_link_integrity.run(state).passed)

    # --- v8-adaptation: optional link title stripping ----------------------

    def test_link_title_stripped_then_target_resolves(self):
        # `[x](FILE.md "Some Title")` — the ` "Some Title"` portion is dropped via
        # tgt.split(" ", 1)[0] so the resolved target is just FILE.md (exists).
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": '[doc](TARGET.md "A Friendly Title").',
                "TARGET.md": "# target\n",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertTrue(result.passed, msg=f"findings: {result.findings}")
            self.assertEqual(result.findings, ())

    # --- v8-adaptation: absolute target resolves against project root ------

    def test_absolute_target_resolves_against_project_root(self):
        # `/docs/A.md` is resolved against proj (= tmp), i.e. tmp/docs/A.md which
        # exists. (check_01 would SKIP this; check_22 resolves it.)
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "sub/CHILD.md": "[root](/docs/OVERVIEW.md).",
                "OVERVIEW.md": "# Overview\n",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertTrue(result.passed, msg=f"findings: {result.findings}")
            self.assertEqual(result.findings, ())

    # --- v8-adaptation: versions/ + research/ are skipped ------------------

    def test_versions_subtree_not_scanned(self):
        # docs/versions/ holds frozen historical snapshots — a broken link there
        # must NOT be flagged (extra_skip_dirs={"versions","research"}).
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "versions/v1/OLD.md": "[gone](GHOST.md).",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertTrue(result.passed, msg=f"findings: {result.findings}")
            self.assertEqual(result.findings, ())

    def test_research_subtree_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "research/NOTES.md": "[gone](MISSING.md).",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertTrue(result.passed, msg=f"findings: {result.findings}")
            self.assertEqual(result.findings, ())


class TestCheck22Fail(unittest.TestCase):

    def test_fail_on_dangling_relative_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "OVERVIEW.md": "See [missing](DOES_NOT_EXIST.md).",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "22")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            # location is relative to project_root, so it carries the docs/ prefix.
            self.assertEqual(f.location, "docs/OVERVIEW.md")
            self.assertEqual(
                f.message, "docs/OVERVIEW.md -> DOES_NOT_EXIST.md (target missing)"
            )

    def test_fail_on_dangling_absolute_link(self):
        # An absolute `/x` target that does not exist under proj must FAIL
        # (mutation-killer: absolute targets are RESOLVED here, not skipped).
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "OVERVIEW.md": "[root](/docs/GHOST.md).",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertEqual(
                f.message, "docs/OVERVIEW.md -> /docs/GHOST.md (target missing)"
            )

    def test_fail_title_stripped_then_target_missing(self):
        # The title is dropped first; the bare path is still missing.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": '[doc](GONE.md "Some Title").',
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            # the reported target is the title-stripped (and anchor-stripped) form
            self.assertEqual(
                result.findings[0].message, "docs/A.md -> GONE.md (target missing)"
            )

    def test_fail_anchor_stripped_then_target_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "Jump to [gone](MISSING.md#heading).",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(
                result.findings[0].message, "docs/A.md -> MISSING.md (target missing)"
            )

    def test_multiple_dangling_links_each_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "[x](GONE1.md) and [y](GONE2.md).",
                "B.md": "[z](GONE3.md).",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 3)
            locations = {f.location for f in result.findings}
            self.assertEqual(locations, {"docs/A.md", "docs/B.md"})

    def test_location_relative_to_project_root_for_subdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "sub/CHILD.md": "[broken](NOPE.md).",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertFalse(result.passed)
            f = result.findings[0]
            self.assertEqual(f.location, "docs/sub/CHILD.md")
            self.assertEqual(
                f.message, "docs/sub/CHILD.md -> NOPE.md (target missing)"
            )


class TestCheck22Degraded(unittest.TestCase):

    def test_pass_when_no_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            # docs/ exists but only holds the state dir; no design *.md.
            state = _project(tmp, {})
            self.assertTrue(check_22_cross_link_integrity.run(state).passed)

    def test_pass_when_docs_root_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            # state_dir points somewhere with no docs/ parent content at all.
            state = Path(tmp) / "ghost" / "_architect_state"
            state.mkdir(parents=True)
            self.assertTrue(check_22_cross_link_integrity.run(state).passed)

    def test_state_subtree_not_scanned(self):
        # Markdown under _architect_state is machine state, never a design doc;
        # collect_markdown skips it, so a broken link there is not flagged.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {})
            (state / "note.md").write_text("[broken](GONE.md)", encoding="utf-8")
            self.assertTrue(check_22_cross_link_integrity.run(state).passed)

    def test_run_does_not_raise_on_empty_target(self):
        # `[x]()` and `[x](#)` reduce to empty path → skipped, no crash.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "[empty]() and [hash](#) and [ok](B.md).",
                "B.md": "# B\n",
            })
            result = check_22_cross_link_integrity.run(state)
            self.assertTrue(result.passed, msg=f"findings: {result.findings}")


if __name__ == "__main__":
    unittest.main()
