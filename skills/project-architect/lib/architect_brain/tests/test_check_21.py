"""Tests for the check_21_settings_permissions_valid auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_21_settings_permissions_valid
from architect_brain.checks.check_21_settings_permissions_valid import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    project_root = state_dir.parent.parent = ``<tmp>``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_settings(state_dir: Path, content: str) -> None:
    """Write raw ``.claude/settings.json`` text at the project root."""
    proj = state_dir.parent.parent
    claude = proj / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    (claude / "settings.json").write_text(content, encoding="utf-8")


def _settings_with_rules(deny=None, allow=None, ask=None) -> str:
    perms: dict = {}
    if deny is not None:
        perms["deny"] = deny
    if allow is not None:
        perms["allow"] = allow
    if ask is not None:
        perms["ask"] = ask
    return json.dumps({"permissions": perms})


class TestCheck21Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "21")
        self.assertEqual(NAME, "settings_permissions_valid")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_21_settings_permissions_valid.CHECK_ID, "21")
        self.assertTrue(callable(check_21_settings_permissions_valid.run))


class TestCheck21Degraded(unittest.TestCase):
    def test_no_settings_file_passes(self):
        # Fresh project: no .claude/settings.json at all → nothing to verify.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "21")
            self.assertEqual(result.findings, ())

    def test_unparseable_settings_passes(self):
        # Defers to json_valid; never raises.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(state, "{not json at all")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_no_permissions_key_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(state, json.dumps({"model": "opus"}))
            result = run(state)
            self.assertTrue(result.passed)

    def test_empty_rules_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(state, _settings_with_rules(deny=[], allow=[], ask=[]))
            result = run(state)
            self.assertTrue(result.passed)

    def test_permissions_not_a_dict_passes(self):
        # permissions present but null → perms coerces to {} → no rules.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(state, json.dumps({"permissions": None}))
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck21Pass(unittest.TestCase):
    def test_trailing_glob_passes(self):
        # Trailing ":*" is the valid, intended form.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(
                state,
                _settings_with_rules(
                    deny=["Bash(rm:*)"],
                    allow=["Read(./.env)", "Bash(git:*)"],
                ),
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_no_colon_glob_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(
                state, _settings_with_rules(deny=["Read(./.env)", "Edit(./secrets/*)"])
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_inner_uses_last_paren_for_trailing(self):
        # inner is between FIRST "(" and LAST ")"; a trailing ":*" before the
        # final ")" is valid.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(state, _settings_with_rules(ask=["Bash(echo (hi):*)"]))
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck21Fail(unittest.TestCase):
    def test_mid_pattern_glob_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(
                state, _settings_with_rules(deny=["Bash(curl:* | sh)"])
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "21")
            self.assertEqual(len(result.findings), 1)
            finding = result.findings[0]
            self.assertIn("Bash(curl:* | sh)", finding.message)
            self.assertIn(":*", finding.message)
            self.assertIn("fails open", finding.message)
            self.assertEqual(finding.location, "Bash(curl:* | sh)")

    def test_mid_pattern_in_allow_and_ask_fails(self):
        # Rules drawn from all three lists; two mid-pattern offenders.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(
                state,
                _settings_with_rules(
                    deny=["Bash(rm:*)"],
                    allow=["Bash(curl:* | sh)"],
                    ask=["WebFetch(domain:* /path)"],
                ),
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 2)
            locations = {f.location for f in result.findings}
            self.assertEqual(
                locations, {"Bash(curl:* | sh)", "WebFetch(domain:* /path)"}
            )

    def test_embedded_paren_then_mid_pattern_glob_fails(self):
        # rfind(")") boundary: a rule with an EMBEDDED ")" before a later
        # mid-pattern ":*" must still be flagged. inner spans the FIRST "(" to the
        # LAST ")", so it includes ":* | sh" (mid-pattern → fails open). This kills
        # the mutation `rule.rfind(')')` → `rule.find(')')`: under `find`, inner
        # would stop at the embedded ")" ("echo (a") and miss the ":*", passing.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_settings(state, _settings_with_rules(deny=["Bash(echo (a):* | sh)"]))
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "21")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].location, "Bash(echo (a):* | sh)")

    def test_v8_adaptation_no_schema_gate(self):
        # v7 only ran on schema_version == "3.0" state; v8 reads
        # .claude/settings.json directly with NO state/schema gate. A bad rule
        # is flagged even when there is no flat-index / schema at all.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            # Deliberately NO 99-flat-index.json, NO schema marker anywhere.
            self.assertFalse((state / "99-flat-index.json").exists())
            _write_settings(state, _settings_with_rules(deny=["Bash(curl:* | sh)"]))
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.findings[0].location, "Bash(curl:* | sh)")


if __name__ == "__main__":
    unittest.main()
