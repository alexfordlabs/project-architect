"""Tests for the check_32_catalog_topo_acyclic auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from architect_brain.catalog import CatalogError
from architect_brain.checks import check_32_catalog_topo_acyclic
from architect_brain.checks.check_32_catalog_topo_acyclic import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


class TestCheck32Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "32")
        self.assertEqual(NAME, "catalog_topo_acyclic")
        self.assertEqual(SEVERITY, "FATAL")
        self.assertTrue(callable(run))
        self.assertEqual(check_32_catalog_topo_acyclic.CHECK_ID, "32")
        self.assertEqual(check_32_catalog_topo_acyclic.NAME, "catalog_topo_acyclic")
        self.assertEqual(check_32_catalog_topo_acyclic.SEVERITY, "FATAL")
        self.assertTrue(hasattr(check_32_catalog_topo_acyclic, "run"))


class TestCheck32Pass(unittest.TestCase):
    """The SHIPPED catalog IS acyclic, so the real run passes regardless of state."""

    def test_pass_with_real_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "32")
            self.assertEqual(result.severity, "FATAL")
            self.assertEqual(result.findings, ())

    def test_pass_ignores_state_dir_contents(self):
        # state_dir is ignored entirely; even a nonexistent path passes.
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does" / "not" / "exist"
            result = run(missing)
            self.assertTrue(result.passed)

    def test_pass_accepts_str_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "_architect_state"
            state.mkdir(parents=True)
            result = run(str(state))
            self.assertTrue(result.passed)

    def test_pass_with_none_state_dir(self):
        # The check does not depend on state_dir; None must not raise.
        result = run(None)
        self.assertTrue(result.passed)


class TestCheck32Fail(unittest.TestCase):
    """Reach the FAIL paths by patching the engine functions as bound in the module."""

    def test_fail_on_cycle(self):
        with mock.patch.object(
            check_32_catalog_topo_acyclic,
            "detect_cycles",
            return_value=["A", "B", "A"],
        ):
            result = run("ignored")
        self.assertFalse(result.passed)
        self.assertEqual(result.check_id, "32")
        self.assertEqual(result.severity, "FATAL")
        self.assertEqual(len(result.findings), 1)
        self.assertIn("cycle", result.findings[0].message.lower())
        self.assertIn("A -> B -> A", result.findings[0].message)

    def test_fail_on_unloadable_catalog(self):
        with mock.patch.object(
            check_32_catalog_topo_acyclic,
            "load_catalog",
            side_effect=CatalogError("boom: schema invalid"),
        ):
            result = run("ignored")
        self.assertFalse(result.passed)
        self.assertEqual(result.severity, "FATAL")
        self.assertEqual(len(result.findings), 1)
        self.assertIn("unloadable", result.findings[0].message.lower())
        self.assertIn("boom", result.findings[0].message)

    def test_fail_does_not_call_detect_cycles_when_unloadable(self):
        # If the catalog can't load, we must short-circuit (not pass the failed
        # load result into detect_cycles).
        with mock.patch.object(
            check_32_catalog_topo_acyclic,
            "load_catalog",
            side_effect=CatalogError("nope"),
        ), mock.patch.object(
            check_32_catalog_topo_acyclic, "detect_cycles"
        ) as mock_detect:
            result = run("ignored")
        self.assertFalse(result.passed)
        mock_detect.assert_not_called()

    def test_does_not_raise_on_arbitrary_engine_error(self):
        # Defensive: even a non-CatalogError must not propagate out of run().
        with mock.patch.object(
            check_32_catalog_topo_acyclic,
            "load_catalog",
            side_effect=RuntimeError("unexpected"),
        ):
            try:
                result = run("ignored")
            except Exception as exc:  # pragma: no cover - this is the assertion
                self.fail(f"run() raised {exc!r}; it must never raise")
        self.assertFalse(result.passed)
        self.assertEqual(result.severity, "FATAL")


if __name__ == "__main__":
    unittest.main()
