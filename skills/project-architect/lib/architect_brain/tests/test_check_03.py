"""Tests for the check_03_decisions_in_docs auditor check."""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_03_decisions_in_docs as check_03


def _state(tmp: str, *, decisions: dict | None = None, docs: dict[str, str] | None = None) -> Path:
    """Build a v8 docs/_architect_state tree and any sibling docs/*.md files.

    ``decisions`` becomes the flat decision map in 99-flat-index.json (absent =>
    no index file written, exercising the degraded path). ``docs`` maps a
    relative path under docs/ to file content.
    """
    docs_dir = Path(tmp) / "docs"
    state = docs_dir / "_architect_state"
    state.mkdir(parents=True)
    if decisions is not None:
        (state / "99-flat-index.json").write_text(
            json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
            encoding="utf-8",
        )
    for rel, content in (docs or {}).items():
        p = docs_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck03(unittest.TestCase):

    # --- module contract ---

    def test_module_contract(self):
        self.assertEqual(check_03.CHECK_ID, "03")
        self.assertEqual(check_03.NAME, "decisions_in_docs")
        self.assertEqual(check_03.SEVERITY, "WARNING")
        self.assertTrue(callable(check_03.run))

    # --- passing fixtures ---

    def test_pass_when_every_decision_mentioned_by_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={"stack.language": "Rust", "stack.framework": "Axum"},
                docs={"TECH_STACK.md": "We chose Rust with the Axum web framework."},
            )
            result = check_03.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "03")
            self.assertEqual(result.findings, ())

    def test_pass_when_mentioned_by_leaf_key(self):
        # Value not in docs, but the leaf key ("language") is.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={"stack.language": "Rust"},
                docs={"VISION.md": "The chosen language is documented elsewhere."},
            )
            result = check_03.run(state)
            self.assertTrue(result.passed)

    def test_pass_skips_null_and_empty_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={"stack.db": None, "stack.cache": "", "stack.language": "Rust"},
                docs={"D.md": "Rust everywhere."},
            )
            result = check_03.run(state)
            self.assertTrue(result.passed)

    def test_pass_searches_across_all_markdown_files(self):
        # Decision documented in a DIFFERENT file than another.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={"stack.language": "Rust", "deploy.platform": "Fly.io"},
                docs={
                    "TECH_STACK.md": "Language: Rust.",
                    "DEPLOYMENT.md": "Deploy to Fly.io.",
                },
            )
            self.assertTrue(check_03.run(state).passed)

    # --- failing fixture ---

    def test_fail_on_undocumented_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={
                    "stack.language": "Rust",
                    "deploy.platform": "Fly.io",  # neither value nor leaf "platform" appears
                },
                docs={"TECH_STACK.md": "We picked Rust."},
            )
            result = check_03.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "03")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertEqual(f.location, "deploy.platform")
            self.assertIn("deploy.platform", f.message)
            self.assertIn("Fly.io", f.message)

    def test_fail_lists_one_finding_per_undocumented_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={
                    "stack.language": "Rust",      # documented
                    "deploy.platform": "Fly.io",   # undocumented
                    "deploy.region": "iad",        # undocumented
                },
                docs={"D.md": "Rust only."},
            )
            result = check_03.run(state)
            self.assertFalse(result.passed)
            locations = sorted(f.location for f in result.findings)
            self.assertEqual(locations, ["deploy.platform", "deploy.region"])

    def test_case_sensitive_substring_v7_parity(self):
        # Value "Rust" must NOT match doc text "rust" (lowercase), and the leaf
        # "language" must not match either -> undocumented.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={"stack.language": "Rust"},
                docs={"D.md": "we use rust here."},
            )
            result = check_03.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.findings[0].location, "stack.language")

    def test_non_string_value_is_stringified_for_search(self):
        # Numeric/boolean decision values are matched as their str() form.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={"cost.monthly_usd": 25, "stack.async": True},
                docs={"COST.md": "Budget is 25 dollars. Fully async (True)."},
            )
            self.assertTrue(check_03.run(state).passed)

    # --- empty / degraded paths ---

    def test_pass_when_no_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, decisions={}, docs={"D.md": "anything"})
            self.assertTrue(check_03.run(state).passed)

    def test_pass_when_no_flat_index(self):
        # Fresh project: no 99-flat-index.json at all.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, decisions=None, docs={"D.md": "anything"})
            self.assertTrue(check_03.run(state).passed)

    def test_pass_when_no_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, decisions={"stack.language": "Rust"}, docs={})
            result = check_03.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_never_raises_on_missing_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            ghost = Path(tmp) / "docs" / "_architect_state"  # not created
            result = check_03.run(ghost)
            self.assertTrue(result.passed)

    # --- operational-key precision filter (v8.0.1) ---
    # Bookkeeping/operational keys the orchestrator records for state + tooling
    # (not design choices a reader expects in prose) are exempt, so the WARNING
    # surfaces only SUBSTANTIVE undocumented decisions.

    def test_operational_keys_not_required_in_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={
                    "git.repo_init": True,
                    "git.remote_url": "git@github.com:x/y.git",
                    "scm.host": "github",
                    "scaffold.deferred": True,
                    "memory_pointer": {"path": "/x/mem.md"},
                    "carry_forward.notes": "rulebook carried verbatim",
                },
                docs={"D.md": "Entirely unrelated prose."},
            )
            result = check_03.run(state)
            self.assertTrue(result.passed, msg=f"unexpected findings: {result.findings}")
            self.assertEqual(result.findings, ())

    def test_substantive_decision_still_flagged_alongside_operational(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(
                tmp,
                decisions={
                    "git.repo_init": True,                  # operational → exempt
                    "scm.host": "github",                   # operational → exempt
                    "admin.csam_workflow": "hash_match_holds",  # substantive → must be flagged
                },
                docs={"D.md": "Unrelated prose."},
            )
            result = check_03.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "admin.csam_workflow")


if __name__ == "__main__":
    unittest.main()
