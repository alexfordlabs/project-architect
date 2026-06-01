"""Tests for the check_29_state_schema_valid auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_29_state_schema_valid
from architect_brain.checks.check_29_state_schema_valid import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)
from architect_brain.projections import empty_projections, projections_to_disk

# The LIVE shipped schemas dir, resolved the same way the check resolves it.
_SCHEMAS_DIR = (
    Path(check_29_state_schema_valid.__file__).resolve().parents[3]
    / "references"
    / "schemas"
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _materialise_valid(state: Path) -> None:
    """Write a consistent, schema-valid set of projections to ``state``."""
    projections_to_disk(state, empty_projections())


class TestCheck29(unittest.TestCase):

    # --- module contract ---------------------------------------------------

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "29")
        self.assertEqual(NAME, "state_schema_valid")
        self.assertEqual(SEVERITY, "FATAL")
        self.assertEqual(check_29_state_schema_valid.CHECK_ID, "29")
        self.assertEqual(check_29_state_schema_valid.NAME, "state_schema_valid")
        self.assertEqual(check_29_state_schema_valid.SEVERITY, "FATAL")
        self.assertTrue(callable(run))
        self.assertTrue(hasattr(check_29_state_schema_valid, "run"))

    # --- passing fixture ---------------------------------------------------

    def test_pass_when_projections_valid(self):
        # A freshly-materialised empty state validates against every shipped
        # schema (this is the byte-deterministic output of projections_to_disk).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "29")
            self.assertEqual(result.severity, "FATAL")
            self.assertEqual(result.findings, ())

    # --- failing fixture ---------------------------------------------------

    def test_fail_when_stack_projection_violates_schema(self):
        # Craft a stack.json that VIOLATES the real shipped state-v4-stack.json:
        # the schema pins concern == const "stack"; "WRONG" breaks the const.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)  # everything else stays valid
            (state / "stack.json").write_text(
                json.dumps(
                    {
                        "schema_version": "4.0",
                        "concern": "WRONG",
                        "decisions": {},
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertGreaterEqual(len(result.findings), 1)
            # The finding names the offending concern + file.
            self.assertTrue(
                any(f.location == "stack.json" for f in result.findings)
            )
            self.assertTrue(
                any("stack" in f.message for f in result.findings)
            )

    def test_fail_when_required_field_missing(self):
        # Drop the required "decisions" field -> schema "required" violation.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)
            (state / "stack.json").write_text(
                json.dumps(
                    {"schema_version": "4.0", "concern": "stack"},
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertGreaterEqual(len(result.findings), 1)

    def test_fail_when_wrong_type(self):
        # decisions must be an object; a list is a type violation.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)
            (state / "vision.json").write_text(
                json.dumps(
                    {
                        "schema_version": "4.0",
                        "concern": "vision",
                        "decisions": [],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertTrue(
                any(f.location == "vision.json" for f in result.findings)
            )

    # --- degraded / empty path --------------------------------------------

    def test_pass_when_no_projections_present(self):
        # An empty state dir (no projection files) has nothing to validate.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertEqual(result.findings, ())

    def test_pass_when_state_dir_missing(self):
        # A state_dir that does not exist must still return a passing result
        # (nothing to validate) and must NOT raise.
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does" / "not" / "exist"
            result = run(missing)
            self.assertTrue(result.passed)
            self.assertEqual(result.severity, "FATAL")

    def test_skip_unparseable_projection_defers_to_check_05(self):
        # A malformed projection JSON is NOT this check's verdict (check_05 owns
        # well-formedness); we skip it and still PASS on the rest.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)
            (state / "stack.json").write_text("{not json", encoding="utf-8")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_skip_concern_when_schema_absent(self):
        # If a concern's SCHEMA file is missing, the concern is skipped even if
        # its projection is present. Exercised by pointing the check at a temp
        # schemas dir that lacks state-v4-stack.json.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)
            # An obviously-invalid stack.json that WOULD fail if the schema were
            # found -- but the schemas dir below has no stack schema.
            (state / "stack.json").write_text(
                json.dumps({"concern": "WRONG"}), encoding="utf-8"
            )
            empty_schemas = Path(tmp) / "empty_schemas"
            empty_schemas.mkdir()
            orig = check_29_state_schema_valid._schemas_dir
            try:
                check_29_state_schema_valid._schemas_dir = lambda: empty_schemas
                result = run(state)
            finally:
                check_29_state_schema_valid._schemas_dir = orig
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_accepts_str_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)
            result = run(str(state))
            self.assertTrue(result.passed)

    def test_never_raises_on_garbage_schema(self):
        # Defensive: even a corrupt schema file must not crash the auditor; the
        # concern is skipped (schema unreadable).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _materialise_valid(state)
            bad_schemas = Path(tmp) / "bad_schemas"
            bad_schemas.mkdir()
            (bad_schemas / "state-v4-stack.json").write_text(
                "{not json", encoding="utf-8"
            )
            orig = check_29_state_schema_valid._schemas_dir
            try:
                check_29_state_schema_valid._schemas_dir = lambda: bad_schemas
                result = run(state)  # must not raise
            finally:
                check_29_state_schema_valid._schemas_dir = orig
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
