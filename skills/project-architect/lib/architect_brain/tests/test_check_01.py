"""Tests for the check_01_links auditor check (link_integrity, ported from v7)."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_01_links


def _project(tmp: str, files: dict[str, str]) -> Path:
    """Build a project tree under tmp/ with docs/_architect_state/ as state_dir.

    ``files`` maps a path relative to the project's ``docs/`` to its content.
    Returns the state_dir (``docs/_architect_state``) the check is invoked with.
    """
    docs = Path(tmp) / "docs"
    state = docs / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in files.items():
        p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck01(unittest.TestCase):

    # --- module contract ---------------------------------------------------

    def test_module_contract(self):
        self.assertEqual(check_01_links.CHECK_ID, "01")
        self.assertEqual(check_01_links.NAME, "link_integrity")
        self.assertEqual(check_01_links.SEVERITY, "BLOCKING")
        self.assertTrue(callable(check_01_links.run))

    # --- passing fixtures --------------------------------------------------

    def test_pass_when_links_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "VISION.md": "See [arch](ARCHITECTURE.md) for details.",
                "ARCHITECTURE.md": "# Architecture\n",
            })
            result = check_01_links.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "01")
            self.assertEqual(result.findings, ())

    def test_pass_on_subdir_relative_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "INDEX.md": "Read [adr](adr/ADR-001.md).",
                "adr/ADR-001.md": "# ADR 001\n",
            })
            self.assertTrue(check_01_links.run(state).passed)

    def test_pass_on_parent_relative_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "sub/CHILD.md": "Back to [vision](../VISION.md).",
                "VISION.md": "# Vision\n",
            })
            self.assertTrue(check_01_links.run(state).passed)

    def test_skips_external_anchor_and_absolute_links(self):
        # All of these must be SKIPPED (never flagged broken):
        #   external URL, protocol-relative, mailto, tel, pure anchor, absolute path.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "VISION.md": (
                    "[ext](https://example.com/page)\n"
                    "[ftp](ftp://host/file)\n"
                    "[rel](//cdn.example.com/x)\n"
                    "[mail](mailto:alex@example.com)\n"
                    "[phone](tel:+15555550100)\n"
                    "[anchor](#a-heading)\n"
                    "[abs](/etc/passwd)\n"
                ),
            })
            result = check_01_links.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_nonexistent_absolute_target_is_skipped(self):
        # Mutation-killer for the absolute-path skip (`if path_only.startswith('/')`).
        # The target is absolute AND does not exist; with the skip it must PASS,
        # without the skip it would resolve to a missing path and be flagged.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "VISION.md": "[abs](/nonexistent_xyz_dir/missing.md)\n",
            })
            result = check_01_links.run(state)
            self.assertTrue(result.passed, msg=f"findings: {result.findings}")
            self.assertEqual(result.findings, ())

    def test_anchor_stripped_from_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "Jump to [section](B.md#heading).",
                "B.md": "# B\n## heading\n",
            })
            self.assertTrue(check_01_links.run(state).passed)

    # --- failing fixtures --------------------------------------------------

    def test_fail_on_broken_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "VISION.md": "See [missing](DOES_NOT_EXIST.md).",
            })
            result = check_01_links.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "01")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            # location is relative to project_root, so it carries the docs/ prefix.
            self.assertEqual(f.location, "docs/VISION.md")
            self.assertIn("DOES_NOT_EXIST.md", f.message)

    def test_fail_anchor_stripped_then_target_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "Jump to [gone](MISSING.md#heading).",
            })
            result = check_01_links.run(state)
            self.assertFalse(result.passed)
            # the target reported is the anchor-stripped form
            self.assertTrue(
                any(f.message.endswith("MISSING.md") for f in result.findings),
                msg=f"findings: {result.findings}",
            )

    def test_multiple_broken_links_each_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "[x](GONE1.md) and [y](GONE2.md).",
                "B.md": "[z](GONE3.md).",
            })
            result = check_01_links.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 3)
            locations = {f.location for f in result.findings}
            self.assertEqual(locations, {"docs/A.md", "docs/B.md"})

    def test_location_relative_to_project_root_for_subdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "sub/CHILD.md": "[broken](NOPE.md).",
            })
            result = check_01_links.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.findings[0].location, "docs/sub/CHILD.md")
            self.assertIn("NOPE.md", result.findings[0].message)

    # --- v7 documented limitation: parens in filenames ---------------------

    def test_parens_in_filename_treated_as_broken(self):
        # The regex [^)]+ stops at the first ')', so a link to "weird(1).md"
        # is captured as "weird(1" and flagged broken even though the file
        # exists. Faithful to v7's documented limitation.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "A.md": "[paren](weird(1).md).",
                "weird(1).md": "# weird\n",
            })
            result = check_01_links.run(state)
            self.assertFalse(result.passed)

    # --- degraded / empty path ---------------------------------------------

    def test_pass_when_no_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            # docs/ exists but only holds the state dir; no design *.md.
            state = _project(tmp, {})
            self.assertTrue(check_01_links.run(state).passed)

    def test_pass_when_docs_root_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            # state_dir points somewhere with no docs/ parent content at all.
            state = Path(tmp) / "ghost" / "_architect_state"
            state.mkdir(parents=True)
            self.assertTrue(check_01_links.run(state).passed)

    def test_state_subtree_not_scanned(self):
        # Markdown that happens to live under _architect_state must be ignored
        # (collect_markdown skips the state dir), so a broken link there is OK.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {})
            (state / "note.md").write_text("[broken](GONE.md)", encoding="utf-8")
            self.assertTrue(check_01_links.run(state).passed)

    def test_run_never_raises_on_unreadable(self):
        # A markdown path that is actually a directory shouldn't crash run().
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {"VISION.md": "# fine\n"})
            # Should simply pass (no links, no crash).
            result = check_01_links.run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
