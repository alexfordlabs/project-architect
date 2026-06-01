"""Tests for the check_04_shellcheck auditor check."""

import re
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from architect_brain.checks import check_04_shellcheck

_HAVE_SHELLCHECK = shutil.which("shellcheck") is not None

# A trivially clean script: well-quoted, no shellcheck warnings at -S warning.
_CLEAN_SH = '#!/usr/bin/env bash\nset -euo pipefail\nname="world"\necho "hello ${name}"\n'

# A script with an obvious SC2086 (unquoted variable) + SC2154/SC2034-class issue.
_DIRTY_SH = '#!/usr/bin/env bash\nfoo=$1\nrm $foo\necho $undefined_var_xyz\n'


def _project(tmp: str, sh_files: dict[str, str]) -> Path:
    """Build a project tree (docs/_architect_state under it) with .sh files.

    Returns the state_dir; project_root = state_dir.parent.parent (= tmp).
    """
    proj = Path(tmp)
    state = proj / "docs" / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in sh_files.items():
        p = proj / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck04(unittest.TestCase):

    def test_module_contract(self):
        self.assertEqual(check_04_shellcheck.CHECK_ID, "04")
        self.assertEqual(check_04_shellcheck.NAME, "shellcheck")
        self.assertEqual(check_04_shellcheck.SEVERITY, "BLOCKING")
        self.assertTrue(callable(check_04_shellcheck.run))

    def test_pass_when_no_sh_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {})
            result = check_04_shellcheck.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "04")
            self.assertEqual(result.findings, ())

    def test_pass_when_only_non_sh_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {"README.md": "# hi\n", "main.py": "print(1)\n"})
            result = check_04_shellcheck.run(state)
            self.assertTrue(result.passed)

    def test_skips_vendor_and_fixtures(self):
        # A dirty script under a pruned dir must NOT cause a failure.
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "node_modules/pkg/bad.sh": _DIRTY_SH,
                "tests/fixtures/bad.sh": _DIRTY_SH,
            })
            result = check_04_shellcheck.run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_SHELLCHECK, "shellcheck not installed on host")
    def test_pass_when_clean_sh(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {"bin/run.sh": _CLEAN_SH})
            result = check_04_shellcheck.run(state)
            self.assertTrue(result.passed, msg=result.summary)
            self.assertEqual(result.check_id, "04")
            self.assertEqual(result.findings, ())

    @unittest.skipUnless(_HAVE_SHELLCHECK, "shellcheck not installed on host")
    def test_fail_on_dirty_sh(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {"bin/bad.sh": _DIRTY_SH})
            result = check_04_shellcheck.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "04")
            # one Finding per failing file
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            # relpath relative to project root
            self.assertEqual(f.location, "bin/bad.sh")
            self.assertIn("bin/bad.sh", f.message)
            # at least one SC code present in the message bracket
            self.assertIn("SC", f.message)

    @unittest.skipUnless(_HAVE_SHELLCHECK, "shellcheck not installed on host")
    def test_fail_lists_each_failing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {
                "a.sh": _DIRTY_SH,
                "sub/b.sh": _DIRTY_SH,
                "ok.sh": _CLEAN_SH,
            })
            result = check_04_shellcheck.run(state)
            self.assertFalse(result.passed)
            locs = {f.location for f in result.findings}
            self.assertEqual(locs, {"a.sh", "sub/b.sh"})

    @unittest.skipUnless(_HAVE_SHELLCHECK, "shellcheck not installed on host")
    def test_codes_capped_at_three(self):
        # A script emitting >=4 distinct WARNING-level SC codes. The module caps
        # the bracketed list at 3 (first-seen order), so we assert EXACTLY 3 —
        # proving truncation actually happens (a cap of 4+ would surface 4 codes
        # here and fail this test). Verified against shellcheck 0.11.0:
        #   SC2168 ('local' outside a function), SC2034 (unused var),
        #   SC2164 (cd without || exit), SC2050/SC2166 ([ ] -a expr),
        #   SC2154 (referenced-but-unassigned) — 6 distinct codes at -S warning.
        many = (
            "#!/usr/bin/env bash\n"
            "local foo=1\n"      # SC2168 + SC2034
            "unused_var=99\n"    # SC2034
            "cd /tmp\n"          # SC2164
            "[ a = b -a c = d ]\n"  # SC2050 + SC2166
            'echo "$undefined"\n'   # SC2154
        )
        with tempfile.TemporaryDirectory() as tmp:
            state = _project(tmp, {"messy.sh": many})
            result = check_04_shellcheck.run(state)
            self.assertFalse(result.passed)
            msg = result.findings[0].message
            # extract the bracketed codes list
            m = re.search(r"\[([^\]]*)\]", msg)
            self.assertIsNotNone(m)
            assert m is not None  # narrow Optional for the type checker
            codes = [c for c in m.group(1).split(",") if c.startswith("SC")]
            # The fixture yields >=4 distinct codes; the cap MUST truncate to 3.
            self.assertEqual(len(codes), 3)

    def test_pass_when_shellcheck_not_installed(self):
        # Degraded branch: which() returns None -> the check PASSES with the
        # documented "skipped" summary, never blocking a host that lacks the tool.
        with tempfile.TemporaryDirectory() as tmp:
            # A dirty .sh that WOULD fail if shellcheck ran — ensures the pass is
            # due to the not-installed short-circuit, not an empty tree.
            state = _project(tmp, {"bin/bad.sh": _DIRTY_SH})
            with mock.patch.object(
                check_04_shellcheck.shutil, "which", return_value=None
            ):
                result = check_04_shellcheck.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "04")
            self.assertEqual(result.findings, ())
            self.assertEqual(result.summary, "shellcheck not installed; skipped")

    def test_run_never_raises_on_missing_tree(self):
        # state_dir pointing at a project root with no files at all.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = check_04_shellcheck.run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
