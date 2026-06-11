"""Tests for the check_25_anonymity_threat_preflight auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_25_anonymity_threat_preflight
from architect_brain.checks.check_25_anonymity_threat_preflight import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    project_root = state_dir.parent.parent = ``<tmp>``; docs_root = ``<tmp>/docs``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_flat_index(state_dir: Path, decisions: dict) -> None:
    (state_dir / "99-flat-index.json").write_text(
        json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
        encoding="utf-8",
    )


def _write_doc(state_dir: Path, name: str, text: str) -> None:
    """Write a markdown doc into the project's ``docs/`` (NOT _architect_state)."""
    docs = state_dir.parent
    (docs / name).write_text(text, encoding="utf-8")


def _write_manifest(state_dir: Path, name: str, text: str) -> None:
    """Write a dependency manifest at the project root."""
    proj = state_dir.parent.parent
    (proj / name).write_text(text, encoding="utf-8")


class TestCheck25Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "25")
        self.assertEqual(NAME, "anonymity_threat_preflight")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_25_anonymity_threat_preflight.CHECK_ID, "25")
        self.assertTrue(callable(check_25_anonymity_threat_preflight.run))


class TestCheck25Degraded(unittest.TestCase):
    def test_empty_project_passes(self):
        # Fresh project: no flat-index, no docs, no manifests → not triggered → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "25")
            self.assertEqual(result.findings, ())

    def test_not_privacy_sensitive_with_manifests_passes(self):
        # Manifests contain blocklisted services, but project is NOT triggered →
        # the scan never runs → pass (preflight not applicable).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": False})
            _write_doc(state, "VISION.md", "A normal CRUD web app for managing recipes.")
            _write_manifest(state, "package.json", json.dumps({"dependencies": {"firebase": "^10.0.0"}}))
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck25Pass(unittest.TestCase):
    def test_triggered_by_flag_clean_manifests_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": True})
            _write_manifest(
                state, "package.json",
                json.dumps({"dependencies": {"libsodium-wrappers": "^0.7", "openpgp": "^5"}}),
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_triggered_by_flag_string_true_clean_passes(self):
        # privacy_sensitive can be the string "true" (legacy v7 form).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": "true"})
            _write_manifest(state, "requirements.txt", "age==1.0\ncryptography==42.0\n")
            result = run(state)
            self.assertTrue(result.passed)

    def test_triggered_by_keyword_clean_passes(self):
        # No flag, but docs mention anonymity → triggered; manifests clean → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(
                state, "VISION.md",
                "We are building a metadata-resistant messenger with a strong threat model.",
            )
            _write_manifest(state, "Cargo.toml", '[dependencies]\ntokio = "1"\n')
            result = run(state)
            self.assertTrue(result.passed)

    def test_no_manifests_when_triggered_passes(self):
        # Triggered, but no manifests present at all → nothing to scan → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": True})
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck25Fail(unittest.TestCase):
    def test_triggered_by_flag_with_blocklisted_service_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": True})
            _write_manifest(
                state, "package.json",
                json.dumps({"dependencies": {"firebase": "^10.0.0", "react": "^18"}}),
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "25")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("package.json references 'firebase'", result.findings[0].message)
            self.assertTrue((result.findings[0].location or "").endswith("package.json"))

    def test_triggered_by_keyword_with_blocklisted_service_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(
                state, "ARCHITECTURE.md",
                "The product is an onion service relying on Tor for anonymity.",
            )
            _write_manifest(
                state, "package.json",
                json.dumps({"dependencies": {"@vercel/analytics": "^1.0.0"}}),
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertIn("package.json references '@vercel/analytics'", result.findings[0].message)

    def test_distinct_hits_per_manifest(self):
        # A manifest mentioning firebase twice + sentry once → 2 distinct findings.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": True})
            _write_manifest(
                state, "package.json",
                json.dumps({
                    "dependencies": {"firebase": "^10", "firebase-admin": "^12"},
                    "devDependencies": {"@sentry/node": "^7"},
                }),
            )
            result = run(state)
            self.assertFalse(result.passed)
            msgs = sorted(f.message for f in result.findings)
            # firebase + firebase-admin both hit; @sentry hits; distinct per service.
            self.assertTrue(any("'firebase'" in m for m in msgs))
            self.assertTrue(any("'firebase-admin'" in m for m in msgs))
            self.assertTrue(any("'@sentry'" in m for m in msgs))
            # Each distinct service reported once (no duplicate firebase).
            firebase_exact = [m for m in msgs if m.endswith("references 'firebase'")]
            self.assertEqual(len(firebase_exact), 1)

    def test_same_service_referenced_twice_dedupes_to_one_finding(self):
        # ONE manifest mentions the SAME blocklisted service twice (in two
        # JSON sections). The per-manifest dedup gate must collapse them to a
        # single finding. Deleting the `if svc in seen: continue` gate yields 2.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": True})
            _write_manifest(
                state, "package.json",
                json.dumps({
                    "dependencies": {"firebase": "^10"},
                    "resolutions": {"firebase": "10.1.0"},
                }),
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertTrue(
                result.findings[0].message.endswith("references 'firebase'")
            )

    def test_string_true_flag_triggers_scan_and_fails(self):
        # The privacy flag is the STRING "true" (legacy v7 form). Changing the
        # flag check from `value is True or value == 'true'` to `value is True`
        # would leave the project untriggered → this scan would not run → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": "true"})
            _write_manifest(state, "requirements.txt", "sentry-sdk==1.40\nflask==3.0\n")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            msgs = " ".join(f.message for f in result.findings)
            self.assertIn("sentry-sdk", msgs)

    def test_findings_across_multiple_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_flat_index(state, {"project.privacy_sensitive": True})
            _write_manifest(
                state, "package.json",
                json.dumps({"dependencies": {"mixpanel": "^0.18"}}),
            )
            _write_manifest(state, "requirements.txt", "sentry-sdk==1.40\nflask==3.0\n")
            result = run(state)
            self.assertFalse(result.passed)
            locs = {(f.location or "") for f in result.findings}
            self.assertTrue(any(l.endswith("package.json") for l in locs))
            self.assertTrue(any(l.endswith("requirements.txt") for l in locs))
            msgs = " ".join(f.message for f in result.findings)
            self.assertIn("mixpanel", msgs)
            self.assertIn("sentry-sdk", msgs)


class TestCheck25V8Adaptation(unittest.TestCase):
    """v8-specific: reads the flat decision index + collect_markdown corpus,
    not v7's monolithic state.json + read_md_corpus.
    """

    def test_keyword_matches_case_insensitively_across_docs_corpus(self):
        # Keyword in an uppercase variant + a nested docs/ subdir doc.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            sub = state.parent / "design"
            sub.mkdir()
            (sub / "notes.md").write_text(
                "This system must be ZERO-KNOWLEDGE end to end.", encoding="utf-8"
            )
            _write_manifest(state, "go.mod", "module x\nrequire cloud.google.com/go/datadog v1\n")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertIn("go.mod references 'datadog'", result.findings[0].message)

    def test_state_machine_dir_not_scanned_as_doc(self):
        # A blocklist-keyword living only inside _architect_state must NOT trigger
        # (collect_markdown skips the machine-state subtree).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            (state / "stray.md").write_text("anonymity threat model", encoding="utf-8")
            _write_manifest(
                state, "package.json",
                json.dumps({"dependencies": {"segment": "^1"}}),
            )
            result = run(state)
            # Not triggered (the only "anonymity" mention is inside _architect_state).
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_word_boundary_tor_not_matched_in_factory(self):
        # \bTor\b must not match "factory" / "vendor"; no other trigger present.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_doc(
                state, "VISION.md",
                "A factory automation vendor dashboard. Nothing private here.",
            )
            _write_manifest(
                state, "package.json",
                json.dumps({"dependencies": {"firebase": "^10"}}),
            )
            result = run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
