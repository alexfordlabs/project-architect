"""Tests for the check_06_claude_md_hierarchy auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_06_claude_md_hierarchy as mod
from architect_brain.checks.check_06_claude_md_hierarchy import CHECK_ID, NAME, SEVERITY, run


def _build(tmp: str, *, decisions=None, root_claude=False, subfolder_claudes=(), other_files=()) -> Path:
    """Build a project tree; return the state_dir (docs/_architect_state).

    ``decisions`` -> the flat dotted-key map written into 99-flat-index.json.
    ``root_claude`` -> create proj/CLAUDE.md.
    ``subfolder_claudes`` -> iterable of relative paths (from proj) to also create.
    ``other_files`` -> iterable of relative paths (from proj) to NON-CLAUDE.md files
        to create (e.g. ``src/main.py``); used to prove the filename filter matters.
    """
    proj = Path(tmp) / "myproject"
    state = proj / "docs" / "_architect_state"
    state.mkdir(parents=True)
    index = {"schema_version": "4.0", "decisions": dict(decisions or {}), "adrs": []}
    (state / "99-flat-index.json").write_text(json.dumps(index), encoding="utf-8")
    if root_claude:
        (proj / "CLAUDE.md").write_text("# root\n", encoding="utf-8")
    for rel in subfolder_claudes:
        p = proj / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# router\n", encoding="utf-8")
    for rel in other_files:
        p = proj / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# not a router\n", encoding="utf-8")
    return state


class TestCheck06(unittest.TestCase):

    # ----- module contract -----

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "06")
        self.assertEqual(NAME, "claude_md_hierarchy")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(mod.CHECK_ID, "06")

    # ----- degraded / not-required passes -----

    def test_pass_when_no_state_at_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            # state dir exists but no flat index -> decisions empty -> not required
            state = Path(tmp) / "p" / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "06")

    def test_pass_when_subfolders_not_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(tmp, decisions={"project.has_subfolders": False}, root_claude=True)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_pass_when_subfolders_key_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(tmp, decisions={"unrelated.key": "x"}, root_claude=True)
            self.assertTrue(run(state).passed)

    def test_pass_when_required_but_no_root_claude(self):
        # has_subfolders true but pre-Phase-7 (no root CLAUDE.md yet) -> decline to claim
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(tmp, decisions={"project.has_subfolders": True}, root_claude=False)
            result = run(state)
            self.assertTrue(result.passed)

    # ----- passing fixture -----

    def test_pass_when_root_plus_subfolder(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(
                tmp,
                decisions={"project.has_subfolders": True},
                root_claude=True,
                subfolder_claudes=["src/CLAUDE.md"],
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_pass_via_alt_subfolders_enabled_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(
                tmp,
                decisions={"subfolders.enabled": True},
                root_claude=True,
                subfolder_claudes=["tests/CLAUDE.md"],
            )
            self.assertTrue(run(state).passed)

    # ----- failing fixture -----

    def test_fail_when_root_only_no_subfolder(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(
                tmp,
                decisions={"project.has_subfolders": True},
                root_claude=True,
                subfolder_claudes=[],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("no subfolder CLAUDE.md", result.findings[0].message)

    def test_fail_alt_key_root_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(
                tmp,
                decisions={"subfolders.enabled": True},
                root_claude=True,
                subfolder_claudes=[],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")

    # ----- depth semantics: only EXACTLY-depth-2 CLAUDE.md counts -----

    def test_deeper_nested_claude_does_not_satisfy(self):
        # src/foo/CLAUDE.md is depth 3 from proj -> does NOT count -> still a fail
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(
                tmp,
                decisions={"project.has_subfolders": True},
                root_claude=True,
                subfolder_claudes=["src/foo/CLAUDE.md"],
            )
            result = run(state)
            self.assertFalse(result.passed)

    def test_depth2_non_claude_file_does_not_satisfy(self):
        # M5 guard: a depth-2 file that is NOT named CLAUDE.md (src/main.py)
        # must NOT count as a subfolder router. has_subfolders=true, root
        # CLAUDE.md present, but the only depth-2 file is src/main.py and there
        # is NO subfolder CLAUDE.md -> must FAIL. Dropping the names={"CLAUDE.md"}
        # filter from walk_files would make this wrongly PASS.
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(
                tmp,
                decisions={"project.has_subfolders": True},
                root_claude=True,
                subfolder_claudes=[],
                other_files=["src/main.py"],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertIn("no subfolder CLAUDE.md", result.findings[0].message)
            # the summary must NOT claim a router was found
            self.assertNotIn("found alongside root", result.summary)

    def test_skip_dir_subfolder_does_not_count(self):
        # a CLAUDE.md inside node_modules (a pruned dir) must not satisfy the check
        with tempfile.TemporaryDirectory() as tmp:
            state = _build(
                tmp,
                decisions={"project.has_subfolders": True},
                root_claude=True,
                subfolder_claudes=["node_modules/CLAUDE.md"],
            )
            result = run(state)
            self.assertFalse(result.passed)

    def test_never_raises_on_garbage_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "p" / "docs" / "_architect_state"
            state.mkdir(parents=True)
            (state / "99-flat-index.json").write_text("{not json", encoding="utf-8")
            # malformed index -> safe-empty decisions -> not required -> pass, no crash
            result = run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
