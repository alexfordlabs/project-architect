"""Tests for the check_10_yaml_frontmatter auditor check."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from architect_brain.checks import check_10_yaml_frontmatter
from architect_brain.checks.check_10_yaml_frontmatter import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)

try:
    import yaml  # noqa: F401
    _HAVE_YAML = True
except ImportError:  # pragma: no cover - exercised only on a host without PyYAML
    _HAVE_YAML = False


# A well-formed frontmatter block.
_VALID_FM = """---
title: ADR-001
status: accepted
tags:
  - one
  - two
---

# Body
"""

# Malformed YAML: a value that opens a flow-mapping but never closes it, plus
# an unmatched bracket — yaml.safe_load raises yaml.YAMLError on this.
_INVALID_FM = """---
title: broken
bad: {unterminated: [1, 2
  : also-bad
---

# Body
"""

# A markdown file with no frontmatter block at all (skipped by the check).
_NO_FM = """# Just a heading

Some prose, no `---` opener.
"""

# Opens with `---` but never closes — treated as having no frontmatter.
_UNCLOSED_FM = """---
title: never closed
no terminator here
"""


def _state(tmp: str, docs: dict[str, str]) -> Path:
    """Build docs/<files> + docs/_architect_state and return the state_dir.

    ``docs`` maps a path relative to ``docs/`` to file content.
    """
    docs_root = Path(tmp) / "docs"
    state = docs_root / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in docs.items():
        p = docs_root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck10(unittest.TestCase):

    # --- module contract -------------------------------------------------

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "10")
        self.assertEqual(check_10_yaml_frontmatter.CHECK_ID, "10")
        self.assertEqual(NAME, "yaml_frontmatter")
        self.assertEqual(check_10_yaml_frontmatter.NAME, "yaml_frontmatter")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertEqual(check_10_yaml_frontmatter.SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))

    # --- passing fixtures ------------------------------------------------

    @unittest.skipUnless(_HAVE_YAML, "PyYAML not installed")
    def test_pass_when_all_frontmatter_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "decisions/ADR-001.md": _VALID_FM,
                "VISION.md": _VALID_FM,
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "10")
            self.assertEqual(result.findings, ())

    @unittest.skipUnless(_HAVE_YAML, "PyYAML not installed")
    def test_pass_when_no_frontmatter_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "README.md": _NO_FM,
                "NOTES.md": _UNCLOSED_FM,
            })
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    @unittest.skipUnless(_HAVE_YAML, "PyYAML not installed")
    def test_pass_when_no_markdown_files(self):
        # Fresh project: docs/ exists (with state) but holds no design .md.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {})
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    @unittest.skipUnless(_HAVE_YAML, "PyYAML not installed")
    def test_pass_when_docs_dir_missing(self):
        # state_dir.parent does not exist as a real docs/ tree of .md files.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            # Remove the docs/ parent's siblings; collect_markdown finds nothing.
            result = run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_YAML, "PyYAML not installed")
    def test_state_subtree_is_not_scanned(self):
        # A malformed .md INSIDE _architect_state must NOT trip the check —
        # collect_markdown skips the _architect_state subtree.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"VISION.md": _VALID_FM})
            (state / "junk.md").write_text(_INVALID_FM, encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)

    # --- failing fixture -------------------------------------------------

    @unittest.skipUnless(_HAVE_YAML, "PyYAML not installed")
    def test_fail_on_invalid_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {
                "VISION.md": _VALID_FM,
                "decisions/ADR-002.md": _INVALID_FM,
            })
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertTrue(len(result.findings) >= 1)
            # The offending file is named in a Finding's location AND message.
            self.assertTrue(
                any("ADR-002.md" in (f.location or "") for f in result.findings)
            )
            self.assertTrue(
                any("ADR-002.md" in f.message for f in result.findings)
            )
            # The valid file is NOT reported.
            self.assertFalse(
                any("VISION.md" in (f.location or "") for f in result.findings)
            )

    @unittest.skipUnless(_HAVE_YAML, "PyYAML not installed")
    def test_finding_message_is_single_line(self):
        # PyYAML errors are multi-line; the check keeps only the first line.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"decisions/ADR-003.md": _INVALID_FM})
            result = run(state)
            self.assertFalse(result.passed)
            for f in result.findings:
                self.assertNotIn("\n", f.message)

    # --- degraded branch (PyYAML absent) ---------------------------------

    def test_pass_when_pyyaml_absent(self):
        # The check imports ``yaml`` *inside* run(); a sys.modules entry of
        # None makes that ``import yaml`` raise ImportError at call time,
        # forcing the graceful-degradation branch (PASS, "nothing to verify")
        # even when an invalid-frontmatter doc is present. Pinning this branch
        # kills mutations that drop the try/except or invert its verdict.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"decisions/ADR-004.md": _INVALID_FM})
            with mock.patch.dict(sys.modules, {"yaml": None}):
                result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "10")
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.findings, ())
            self.assertIn("PyYAML not installed", result.summary)

    # --- never raises ----------------------------------------------------

    def test_run_returns_check_result_and_never_raises(self):
        # Even on a totally empty / weird path, run must produce a CheckResult.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "nonexistent_state"
            result = run(state)
            self.assertEqual(result.check_id, "10")
            self.assertIsInstance(result.passed, bool)


if __name__ == "__main__":
    unittest.main()
