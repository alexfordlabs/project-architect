"""Central registry guard for the auditor check suite.

Auto-discovers every ``check_NN_*`` module physically present under
architect_brain/checks/ (by NAME — no dynamic import; the modules are already
imported by ``checks/__init__.py``) and asserts the registry (``ALL_CHECKS``) +
the module contract stay consistent: every check module is registered, ids are
unique + 2-digit, the list is in CHECK_ID order, and each check declares a valid
NAME / SEVERITY / run(). A check added without registering it (the one shared
file the per-check implementers do NOT touch) fails here — the consolidation
safety net.
"""

import pkgutil
import re
import unittest

import architect_brain.checks as checks_pkg
from architect_brain.checks import ALL_CHECKS
from architect_brain.severity import SEVERITY_LEVELS

_CHECK_MODULE_RE = re.compile(r"^check_\d{2}_")


def _discovered_check_module_names() -> set[str]:
    """Fully-qualified names of every check_NN_* module on disk (no import)."""
    return {
        f"architect_brain.checks.{info.name}"
        for info in pkgutil.iter_modules(checks_pkg.__path__)
        if _CHECK_MODULE_RE.match(info.name)
    }


def _registered_module_names() -> set[str]:
    return {c.__name__ for c in ALL_CHECKS}


class TestAllChecksRegistered(unittest.TestCase):

    def test_on_disk_and_registry_match_exactly(self):
        discovered = _discovered_check_module_names()
        self.assertTrue(discovered, "no check_NN_* modules discovered on disk")
        registered = _registered_module_names()
        missing = discovered - registered      # on disk but not registered
        extra = registered - discovered        # registered but not on disk
        self.assertEqual(missing, set(), f"check modules not in ALL_CHECKS: {sorted(missing)}")
        self.assertEqual(extra, set(), f"ALL_CHECKS entries with no module: {sorted(extra)}")

    def test_no_duplicate_registry_entries(self):
        self.assertEqual(len(ALL_CHECKS), len({id(c) for c in ALL_CHECKS}),
                         "ALL_CHECKS contains a duplicate module")

    def test_check_ids_unique_and_two_digit(self):
        ids = [c.CHECK_ID for c in ALL_CHECKS]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate CHECK_IDs: {ids}")
        for cid in ids:
            self.assertRegex(cid, r"^\d{2}$", f"CHECK_ID not 2-digit: {cid!r}")

    def test_registry_sorted_by_check_id(self):
        ids = [c.CHECK_ID for c in ALL_CHECKS]
        self.assertEqual(ids, sorted(ids), "ALL_CHECKS must be in CHECK_ID order")

    def test_each_check_has_valid_contract(self):
        for c in ALL_CHECKS:
            self.assertIsInstance(c.CHECK_ID, str, f"{c.__name__}.CHECK_ID")
            self.assertIsInstance(getattr(c, "NAME", None), str, f"{c.__name__}.NAME")
            self.assertTrue(c.NAME, f"{c.__name__}.NAME is empty")
            self.assertIn(c.SEVERITY, SEVERITY_LEVELS, f"{c.__name__}.SEVERITY")
            self.assertTrue(callable(getattr(c, "run", None)), f"{c.__name__}.run")


if __name__ == "__main__":
    unittest.main()
