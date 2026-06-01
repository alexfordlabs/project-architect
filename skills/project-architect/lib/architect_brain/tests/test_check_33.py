"""Tests for the check_33_vale_optional auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from architect_brain.checks import check_33_vale_optional
from architect_brain.checks.check_33_vale_optional import CHECK_ID, NAME, SEVERITY, run

_MOD = "architect_brain.checks.check_33_vale_optional"


def _make_state(tmp: str, docs: dict[str, str] | None = None) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and optional design ``.md`` files.

    ``docs`` keys are paths relative to the project's ``docs/`` directory
    (= ``state_dir.parent``).
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    if docs:
        docs_root = state.parent
        for rel, content in docs.items():
            p = docs_root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
    return state


def _completed(stdout: str = "", returncode: int = 0, stderr: str = ""):
    """A fake completed subprocess result for monkeypatching ``subprocess.run``."""
    return subprocess.CompletedProcess(
        args=["vale"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class TestCheck33Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "33")
        self.assertEqual(NAME, "vale_prose")
        self.assertEqual(SEVERITY, "INFO")
        self.assertTrue(callable(run))
        self.assertEqual(check_33_vale_optional.CHECK_ID, "33")
        self.assertTrue(callable(check_33_vale_optional.run))


class TestCheck33Degraded(unittest.TestCase):
    def test_vale_not_installed_passes(self):
        with mock.patch(f"{_MOD}.shutil.which", return_value=None):
            with tempfile.TemporaryDirectory() as tmp:
                state = _make_state(tmp, {"design/a.md": "# A\n"})
                result = run(state)
                self.assertTrue(result.passed)
                self.assertEqual(result.severity, "INFO")
                self.assertEqual(result.findings, ())
                self.assertIn("not installed", result.summary)

    def test_no_docs_passes_even_with_vale(self):
        # vale present, but there are no markdown docs to lint → clean pass,
        # and subprocess.run must never be invoked.
        with mock.patch(f"{_MOD}.shutil.which", return_value="/usr/bin/vale"):
            with mock.patch(f"{_MOD}.subprocess.run") as run_mock:
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp)  # no design docs
                    result = run(state)
                    self.assertTrue(result.passed)
                    self.assertEqual(result.findings, ())
                    run_mock.assert_not_called()

    def test_missing_docs_root_passes(self):
        # state_dir.parent does not exist on disk at all.
        with mock.patch(f"{_MOD}.shutil.which", return_value="/usr/bin/vale"):
            with mock.patch(f"{_MOD}.subprocess.run") as run_mock:
                with tempfile.TemporaryDirectory() as tmp:
                    state = Path(tmp) / "nope" / "_architect_state"
                    result = run(state)
                    self.assertTrue(result.passed)
                    run_mock.assert_not_called()

    def test_subprocess_failure_does_not_raise(self):
        # If invoking vale itself blows up (OSError), the check must still
        # return a (degraded) pass, never propagate the exception.
        with mock.patch(f"{_MOD}.shutil.which", return_value="/usr/bin/vale"):
            with mock.patch(
                f"{_MOD}.subprocess.run", side_effect=OSError("boom")
            ):
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp, {"design/a.md": "# A\n"})
                    result = run(state)
                    self.assertTrue(result.passed)
                    self.assertEqual(result.findings, ())


class TestCheck33Pass(unittest.TestCase):
    def test_clean_vale_output_passes(self):
        # vale present, docs present, vale reports nothing → pass.
        with mock.patch(f"{_MOD}.shutil.which", return_value="/usr/bin/vale"):
            with mock.patch(
                f"{_MOD}.subprocess.run", return_value=_completed(stdout="")
            ):
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp, {"design/a.md": "# A\n"})
                    result = run(state)
                    self.assertTrue(result.passed)
                    self.assertEqual(result.severity, "INFO")
                    self.assertEqual(result.findings, ())


class TestCheck33Fail(unittest.TestCase):
    def test_vale_issues_fail_info_only(self):
        # vale reports issues → passed False, but severity stays INFO (never
        # blocks LOCK). One Finding per reported issue line.
        fake_stdout = (
            "docs/design/a.md\n"
            " 3:1  warning  Avoid 'very'.            Vale.Spelling\n"
            " 7:9  error    Did you mean 'their'?    Vale.Grammar\n"
        )
        with mock.patch(f"{_MOD}.shutil.which", return_value="/usr/bin/vale"):
            with mock.patch(
                f"{_MOD}.subprocess.run",
                return_value=_completed(stdout=fake_stdout, returncode=1),
            ):
                with tempfile.TemporaryDirectory() as tmp:
                    state = _make_state(tmp, {"design/a.md": "# A\n"})
                    result = run(state)
                    self.assertFalse(result.passed)
                    self.assertEqual(result.severity, "INFO")
                    self.assertEqual(result.check_id, "33")
                    self.assertGreaterEqual(len(result.findings), 1)
                    joined = " ".join(f.message for f in result.findings)
                    self.assertIn("warning", joined)


if __name__ == "__main__":
    unittest.main()
