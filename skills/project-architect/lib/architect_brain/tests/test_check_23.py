"""Tests for the check_23_dependency_freshness auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_23_dependency_freshness
from architect_brain.checks.check_23_dependency_freshness import (
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


def _write_manifest(state_dir: Path, name: str, content: str) -> None:
    """Write a top-level project manifest (``<project_root>/<name>``)."""
    proj = state_dir.parent.parent
    (proj / name).write_text(content, encoding="utf-8")


class TestCheck23Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "23")
        self.assertEqual(NAME, "dependency_freshness")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_23_dependency_freshness.CHECK_ID, "23")
        self.assertTrue(callable(check_23_dependency_freshness.run))


class TestCheck23Degraded(unittest.TestCase):
    def test_no_manifests_passes(self):
        # Fresh project, no manifests at all → nothing to verify → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "23")
            self.assertEqual(result.findings, ())

    def test_invalid_package_json_does_not_raise(self):
        # A malformed package.json defers to json_valid; this check must not
        # crash and must not flag (nothing parseable to verify).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(state, "package.json", "{not json")
            result = run(state)
            self.assertTrue(result.passed)

    def test_nested_manifest_is_ignored(self):
        # Only top-level proj/<manifest> is scanned, not nested ones.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            proj = state.parent.parent
            nested = proj / "vendor" / "subpkg"
            nested.mkdir(parents=True)
            # The pin carries a real prerelease tag the regex DOES match
            # (leading hyphen + rc). If the scan ever recurses into nested
            # dirs, this finding would surface and the assertion below fails.
            (nested / "requirements.txt").write_text(
                "django==5.0.0-rc.1\n", encoding="utf-8"
            )
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck23Pass(unittest.TestCase):
    def test_stable_package_json_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state,
                "package.json",
                '{"dependencies": {"react": "19.0.0"}, '
                '"devDependencies": {"typescript": "5.4.0"}}',
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_preact_not_false_positive(self):
        # `pre` has no leading hyphen → must NOT flag.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state, "package.json", '{"dependencies": {"preact": "10.0.0"}}'
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_own_version_in_toml_not_flagged(self):
        # The project's OWN bare top-level `version = "x"` is dropped before
        # matching, so a project's own pre-release does NOT flag (Cargo.toml).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state,
                "Cargo.toml",
                "[package]\n"
                'name = "mycrate"\n'
                'version = "0.1.0-alpha.0"\n'
                "\n"
                "[dependencies]\n"
                'serde = "1.0.0"\n',
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_own_version_in_pyproject_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state,
                "pyproject.toml",
                "[project]\n"
                'name = "myproj"\n'
                'version = "0.1.0-beta.1"\n',
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_stable_requirements_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state, "requirements.txt", "django==5.0.0\nrequests==2.31.0\n"
            )
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck23Fail(unittest.TestCase):
    def test_prerelease_package_json_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state,
                "package.json",
                '{"dependencies": {"next": "15.0.0-rc.1", "react": "19.0.0"}}',
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "23")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(
                result.findings[0].message, "package.json: next@15.0.0-rc.1"
            )

    def test_prerelease_devdependency_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state,
                "package.json",
                '{"devDependencies": {"vite": "6.0.0-beta.2"}}',
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(
                result.findings[0].message, "package.json: vite@6.0.0-beta.2"
            )

    def test_prerelease_requirements_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state, "requirements.txt", "django==5.0.0b1-alpha.1\nrequests==2.31.0\n"
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertTrue(
                any(
                    f.message == "requirements.txt: django==5.0.0b1-alpha.1"
                    for f in result.findings
                )
            )

    def test_prerelease_dependency_in_toml_flagged(self):
        # A real dependency (carries a name) with a pre-release pin IS flagged,
        # while the own-version line is dropped.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state,
                "Cargo.toml",
                "[package]\n"
                'name = "mycrate"\n'
                'version = "0.1.0"\n'
                "\n"
                "[dependencies]\n"
                'tokio = "1.0.0-rc.1"\n',
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(
                result.findings[0].message, 'Cargo.toml: tokio = "1.0.0-rc.1"'
            )

    def test_prerelease_go_mod_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state,
                "go.mod",
                "module example.com/m\n"
                "go 1.22\n"
                "require github.com/foo/bar v2.0.0-beta.1\n",
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertTrue(
                any(
                    "v2.0.0-beta.1" in f.message and f.message.startswith("go.mod:")
                    for f in result.findings
                )
            )

    def test_multiple_manifests_aggregate(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_manifest(
                state, "package.json", '{"dependencies": {"next": "15.0.0-rc.1"}}'
            )
            _write_manifest(state, "Gemfile", 'gem "rails", "8.0.0-beta1"\n')
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 2)
            locs = {f.location for f in result.findings}
            self.assertIn(str(state.parent.parent / "package.json"), locs)
            self.assertIn(str(state.parent.parent / "Gemfile"), locs)


if __name__ == "__main__":
    unittest.main()
