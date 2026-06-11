"""Tests for the check_28_markdownlint auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

markdownlint-cli2 need NOT be installed on the test host: detection
(``shutil.which``) and invocation (``subprocess.run``) are both mocked, so the
not-installed / clean / violations paths are all exercised deterministically.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from architect_brain.checks import check_28_markdownlint
from architect_brain.checks.check_28_markdownlint import CHECK_ID, NAME, SEVERITY, run

_MOD = "architect_brain.checks.check_28_markdownlint"


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


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    """A fake subprocess.CompletedProcess for mock(subprocess.run)."""
    return subprocess.CompletedProcess(
        args=["markdownlint-cli2"], returncode=returncode,
        stdout=stdout, stderr=stderr,
    )


class TestCheck28Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "28")
        self.assertEqual(NAME, "markdownlint")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_28_markdownlint.CHECK_ID, "28")
        self.assertTrue(callable(check_28_markdownlint.run))


class TestCheck28Degraded(unittest.TestCase):
    def test_not_installed_passes_degraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"a.md": "# A\n\nBody.\n"})
            with mock.patch(f"{_MOD}.shutil.which", return_value=None):
                # subprocess.run must NOT be invoked when the tool is absent.
                with mock.patch(f"{_MOD}.subprocess.run") as run_mock:
                    result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "28")
            self.assertEqual(result.findings, ())
            self.assertIn("not installed", result.summary)
            run_mock.assert_not_called()

    def test_no_docs_passes_without_invoking(self):
        # Tool present but there are no markdown files → nothing to lint → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(f"{_MOD}.subprocess.run") as run_mock:
                    result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())
            run_mock.assert_not_called()

    def test_docs_root_missing_passes(self):
        # Fresh/degraded project: state_dir exists, no docs content beyond it.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(f"{_MOD}.subprocess.run") as run_mock:
                    result = run(state)
            self.assertTrue(result.passed)
            run_mock.assert_not_called()

    def test_subprocess_oserror_passes_degraded(self):
        # If invoking the tool raises OSError, decline to claim a defect.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"a.md": "# A\n\nBody.\n"})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(
                    f"{_MOD}.subprocess.run", side_effect=OSError("boom")
                ):
                    result = run(state)
            self.assertTrue(result.passed)


class TestCheck28Pass(unittest.TestCase):
    def test_clean_output_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"a.md": "# A\n\nBody.\n"})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(
                    f"{_MOD}.subprocess.run", return_value=_completed("", "")
                ):
                    result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "28")
            self.assertEqual(result.findings, ())

    def test_only_untargeted_rules_passes(self):
        # markdownlint reports violations, but none are in the targeted set of
        # 5 rules → those are ignored → pass.
        stdout = (
            "docs/a.md:1 MD013/line-length Line length [Expected: 80]\n"
            "docs/a.md:3:5 MD009/no-trailing-spaces Trailing spaces\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"a.md": "# A\n\nBody.\n"})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(
                    f"{_MOD}.subprocess.run",
                    return_value=_completed("", stdout),
                ):
                    result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck28Fail(unittest.TestCase):
    def test_md025_violation_fails_blocking(self):
        # The canonical fail path: markdownlint emits an MD025 line.
        stderr = (
            "docs/architecture.md:8:1 MD025/single-title/single-h1 "
            "Multiple top-level headings in the same document\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"architecture.md": "# A\n\n# Second\n"})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(
                    f"{_MOD}.subprocess.run",
                    return_value=_completed("", stderr, returncode=1),
                ):
                    result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "28")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertIn("MD025", f.message)
            self.assertIn("docs/architecture.md:8", f.message)
            self.assertEqual(f.location, "docs/architecture.md")

    def test_violation_on_stdout_also_caught(self):
        # markdownlint-cli2 prints to stderr by default, but the check must also
        # scan stdout so it is robust to either stream.
        stdout = (
            "docs/a.md:2 MD040/fenced-code-language Fenced code blocks should "
            "have a language specified\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"a.md": "# A\n\n```\ncode\n```\n"})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(
                    f"{_MOD}.subprocess.run",
                    return_value=_completed(stdout, "", returncode=1),
                ):
                    result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("MD040", result.findings[0].message)

    def test_multiple_targeted_rules_each_a_finding(self):
        out = (
            "docs/a.md:1 MD001/heading-increment Heading levels should only "
            "increment by one level at a time\n"
            "docs/a.md:5 MD036/no-emphasis-as-heading Emphasis used instead "
            "of a heading\n"
            "docs/b.md:3:1 MD045/no-alt-text Images should have alternate text\n"
            "docs/b.md:9 MD013/line-length Line length\n"  # untargeted → ignored
        )
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"a.md": "x\n", "b.md": "y\n"})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(
                    f"{_MOD}.subprocess.run",
                    return_value=_completed(out, "", returncode=1),
                ):
                    result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            rules = sorted(
                next(tok for tok in f.message.split() if tok.startswith("MD"))
                for f in result.findings
            )
            # Exactly the three targeted rules; MD013 ignored.
            self.assertEqual(len(result.findings), 3)
            self.assertEqual(
                [r.split("/")[0] for r in rules],
                ["MD001", "MD036", "MD045"],
            )

    def test_run_receives_collected_files_as_args(self):
        # The check passes the collected markdown paths to the tool as args.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"a.md": "x\n", "sub/b.md": "y\n"})
            with mock.patch(
                f"{_MOD}.shutil.which", return_value="/usr/bin/markdownlint-cli2"
            ):
                with mock.patch(
                    f"{_MOD}.subprocess.run", return_value=_completed("", "")
                ) as run_mock:
                    result = run(state)
            self.assertTrue(result.passed)
            run_mock.assert_called_once()
            call_args = run_mock.call_args[0][0]
            # The invoked argv must include the two collected markdown files.
            joined = " ".join(call_args)
            self.assertIn("a.md", joined)
            self.assertIn("b.md", joined)


if __name__ == "__main__":
    unittest.main()
