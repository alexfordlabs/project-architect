"""Tests for the check_02_affected_docs auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Covers the module contract, a passing fixture (every ADR-declared
``affected_docs`` entry is generated), a failing fixture (a declared doc is
missing -> BLOCKING), and the empty/degraded path (no ADRs / no opt-in
frontmatter -> PASS, decline-to-claim).
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_02_affected_docs
from architect_brain.checks.check_02_affected_docs import CHECK_ID, NAME, SEVERITY, run


def _state(tmp: str, *, docs_json=None, adrs: dict[str, str] | None = None) -> Path:
    """Build a tempdir v8 state dir.

    ``docs_json`` is the parsed object written to ``docs.json`` (default: a
    docs.json with an empty ``completed`` list). ``adrs`` maps a filename
    (e.g. ``"0001-foo.md"``) to its full markdown content; each lands under
    ``state_dir/decisions/``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    if docs_json is None:
        docs_json = {"schema_version": "4.0", "concern": "docs", "completed": []}
    (state / "docs.json").write_text(json.dumps(docs_json), encoding="utf-8")
    decisions = state / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    for name, content in (adrs or {}).items():
        (decisions / name).write_text(content, encoding="utf-8")
    return state


def _adr_md(adr_id: str, affected_docs=None) -> str:
    """Build a minimal ADR markdown body with optional ``affected_docs``."""
    lines = ["---", "type: adr", f"id: {adr_id}", "status: accepted"]
    if affected_docs is not None:
        lines.append("affected_docs:")
        for d in affected_docs:
            lines.append(f"  - {d}")
    lines += ["---", "", f"# {adr_id}", "", "Body text.", ""]
    return "\n".join(lines)


class TestCheck02(unittest.TestCase):

    # ---- module contract --------------------------------------------------

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "02")
        self.assertEqual(NAME, "adr_affected_docs")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_02_affected_docs.CHECK_ID, "02")
        self.assertEqual(check_02_affected_docs.NAME, "adr_affected_docs")
        self.assertEqual(check_02_affected_docs.SEVERITY, "BLOCKING")
        self.assertTrue(hasattr(check_02_affected_docs, "run"))

    # ---- passing fixtures -------------------------------------------------

    def test_pass_when_all_affected_docs_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_json = {
                "completed": [
                    {"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md", "content_hash": "x"},
                    {"name": "ARCHITECTURE.md", "path": "docs/ARCHITECTURE.md", "content_hash": "y"},
                ]
            }
            adrs = {
                "0001-overview.md": _adr_md("ADR-0001", ["PROJECT_OVERVIEW.md"]),
                "0002-arch.md": _adr_md("ADR-0002", ["docs/ARCHITECTURE.md"]),
            }
            state = _state(tmp, docs_json=docs_json, adrs=adrs)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "02")
            self.assertEqual(result.findings, ())

    def test_pass_when_affected_doc_declared_without_md_suffix(self):
        # ADR declares "PROJECT_OVERVIEW" (no .md); ".md" is appended before
        # comparison. The generated set contains "PROJECT_OVERVIEW.md".
        with tempfile.TemporaryDirectory() as tmp:
            docs_json = {"completed": [{"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md"}]}
            adrs = {"0001.md": _adr_md("ADR-0001", ["PROJECT_OVERVIEW"])}
            state = _state(tmp, docs_json=docs_json, adrs=adrs)
            result = run(state)
            self.assertTrue(result.passed)

    def test_pass_when_match_only_via_path_basename(self):
        # The "name" is a human title whose basename DIVERGES from the
        # filename; only the PATH basename matches the ADR-declared doc. This
        # proves the path-registration branch is load-bearing: deleting it
        # leaves the set with only "Architecture Overview.md" and the check
        # would (wrongly) fail.
        with tempfile.TemporaryDirectory() as tmp:
            docs_json = {
                "completed": [
                    {"name": "Architecture Overview", "path": "docs/ARCHITECTURE.md", "content_hash": "z"},
                ]
            }
            adrs = {"0001-arch.md": _adr_md("ADR-0001", ["ARCHITECTURE.md"])}
            state = _state(tmp, docs_json=docs_json, adrs=adrs)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_pass_when_match_only_via_name_basename(self):
        # The completed item has NO usable path (key absent); only the NAME
        # basename (".md" ensured) matches the ADR-declared doc. This proves
        # the name-registration branch is load-bearing: deleting it leaves the
        # set empty and the check would (wrongly) fail.
        with tempfile.TemporaryDirectory() as tmp:
            docs_json = {
                "completed": [
                    {"name": "ARCHITECTURE", "content_hash": "z"},
                ]
            }
            adrs = {"0001-arch.md": _adr_md("ADR-0001", ["ARCHITECTURE.md"])}
            state = _state(tmp, docs_json=docs_json, adrs=adrs)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_pass_when_no_adr_declares_affected_docs(self):
        # ADRs exist but none opt into affected_docs frontmatter -> nothing to
        # verify -> PASS (v8 ADRs normally carry no affected_docs).
        with tempfile.TemporaryDirectory() as tmp:
            adrs = {
                "0001.md": _adr_md("ADR-0001"),
                "0002.md": _adr_md("ADR-0002"),
            }
            state = _state(tmp, adrs=adrs)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())
            self.assertIn("no ADR affected_docs to verify", result.summary)

    def test_pass_when_affected_docs_not_a_list(self):
        # Malformed frontmatter: affected_docs is a scalar, not a list. The
        # spec says read it only "if it is a list" -> ignored -> PASS.
        with tempfile.TemporaryDirectory() as tmp:
            adr = "\n".join(
                ["---", "type: adr", "id: ADR-0001", "affected_docs: PROJECT_OVERVIEW.md",
                 "---", "", "# ADR-0001", ""]
            )
            state = _state(tmp, adrs={"0001.md": adr})
            result = run(state)
            self.assertTrue(result.passed)

    # ---- failing fixtures -------------------------------------------------

    def test_fail_when_affected_doc_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_json = {"completed": [{"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md"}]}
            adrs = {"0007.md": _adr_md("ADR-0007", ["DATA_MODEL.md"])}
            state = _state(tmp, docs_json=docs_json, adrs=adrs)
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertIn("ADR-0007", f.message)
            self.assertIn("DATA_MODEL.md", f.message)
            self.assertEqual(f.location, "DATA_MODEL.md")

    def test_fail_location_is_basename_not_path(self):
        # ADR declares "docs/DATA_MODEL.md"; the Finding.location is the
        # basename "DATA_MODEL.md".
        with tempfile.TemporaryDirectory() as tmp:
            adrs = {"0007.md": _adr_md("ADR-0007", ["docs/DATA_MODEL.md"])}
            state = _state(tmp, adrs=adrs)
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.findings[0].location, "DATA_MODEL.md")
            self.assertIn("DATA_MODEL.md", result.findings[0].message)

    def test_fail_multiple_missing_one_finding_each(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_json = {"completed": [{"name": "PROJECT_OVERVIEW", "path": "docs/PROJECT_OVERVIEW.md"}]}
            adrs = {
                "0001.md": _adr_md("ADR-0001", ["PROJECT_OVERVIEW.md", "MISSING_ONE.md"]),
                "0002.md": _adr_md("ADR-0002", ["MISSING_TWO"]),
            }
            state = _state(tmp, docs_json=docs_json, adrs=adrs)
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 2)
            locations = {f.location for f in result.findings}
            self.assertEqual(locations, {"MISSING_ONE.md", "MISSING_TWO.md"})

    def test_id_falls_back_to_question_mark_when_absent(self):
        # ADR with no id in frontmatter -> message uses '?'.
        with tempfile.TemporaryDirectory() as tmp:
            adr = "\n".join(
                ["---", "type: adr", "affected_docs:", "  - GHOST.md", "---", "", "# x", ""]
            )
            state = _state(tmp, adrs={"0001.md": adr})
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertIn("?", result.findings[0].message)
            self.assertEqual(result.findings[0].location, "GHOST.md")

    # ---- empty / degraded paths ------------------------------------------

    def test_pass_when_no_decisions_dir(self):
        # docs.json present, but no decisions/ ADR dir at all -> nothing to
        # verify -> PASS.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            (state / "docs.json").write_text(json.dumps({"completed": []}), encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)

    def test_pass_on_completely_fresh_state(self):
        # Empty state dir (no docs.json, no decisions/) -> PASS.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_never_raises_on_malformed_adr(self):
        # An ADR file with no frontmatter / garbage must not crash; it has no
        # affected_docs so it contributes nothing.
        with tempfile.TemporaryDirectory() as tmp:
            adrs = {
                "0001.md": "no frontmatter here, just prose\n",
                "0002.md": "---\nnot: closed properly\n# heading\n",
            }
            state = _state(tmp, adrs=adrs)
            result = run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
