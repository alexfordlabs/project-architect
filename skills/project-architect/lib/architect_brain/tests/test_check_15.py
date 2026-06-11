"""Tests for the check_15_numerical_consistency auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Covers the v8 adaptation: the performance_targets dict is read from a single
FLAT decision key (``architecture.performance_targets``) in
``99-flat-index.json``, not from the nested
``state.decisions.architecture.performance_targets`` path v7 walked.
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_15_numerical_consistency
from architect_brain.checks.check_15_numerical_consistency import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str, perf_targets) -> Path:
    """Create ``<tmp>/docs/_architect_state`` with a flat index.

    If ``perf_targets`` is the sentinel ``_ABSENT`` the
    ``architecture.performance_targets`` key is omitted entirely; otherwise the
    given value is stored verbatim under that flat dotted key.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    decisions = {}
    if perf_targets is not _ABSENT:
        decisions["architecture.performance_targets"] = perf_targets
    index = {"schema_version": "4.0", "decisions": decisions, "adrs": []}
    (state / "99-flat-index.json").write_text(json.dumps(index), encoding="utf-8")
    return state


_ABSENT = object()


class TestCheck15Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "15")
        self.assertEqual(NAME, "numerical_consistency")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_15_numerical_consistency.CHECK_ID, "15")
        self.assertTrue(callable(check_15_numerical_consistency.run))


class TestCheck15Degraded(unittest.TestCase):
    def test_no_state_dir_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            # state dir doesn't exist → load_decisions safe-empty → pass
            state = Path(tmp) / "docs" / "_architect_state"
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "15")
            self.assertEqual(result.findings, ())

    def test_empty_flat_index_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, _ABSENT)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_perf_targets_not_a_dict_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, "fast")  # string, not dict
            self.assertTrue(run(state).passed)

    def test_perf_targets_empty_dict_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, {})
            self.assertTrue(run(state).passed)

    def test_no_pairs_detectable_passes(self):
        # performance_targets present but no key resolves to a baseline
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "throughput_target": 1000,  # base 'throughput' has no baseline
                    "baseline": {"latency_typical": 50},  # unrelated base
                },
            )
            self.assertTrue(run(state).passed)

    def test_zero_baseline_skipped_passes(self):
        # baseline <= 0 can't yield a meaningful ratio → skipped → pass
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "cold_start_seconds_max": 0.5,
                    "baseline": {"cold_start_typical_seconds": 0},
                },
            )
            self.assertTrue(run(state).passed)


class TestCheck15Pass(unittest.TestCase):
    def test_reasonable_pair_passes(self):
        # ratio = 0.8 >= 0.7 → reasonable → pass
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "cold_start_seconds_max": 0.8,
                    "baseline": {"cold_start_typical_seconds": 1.0},
                },
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_aggressive_with_top_level_disclaimer_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "cold_start_seconds_max": 0.2,  # ratio 0.2 — aggressive
                    "baseline": {"cold_start_typical_seconds": 1.0},
                    "stretch_disclaimer": "aspirational; not a commitment",
                },
            )
            self.assertTrue(run(state).passed)

    def test_aggressive_with_per_key_disclaimer_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "cold_start_seconds_max": 0.2,
                    "baseline": {"cold_start_typical_seconds": 1.0},
                    "cold_start_seconds_max_stretch_disclaimer": "stretch goal",
                },
            )
            self.assertTrue(run(state).passed)

    def test_bool_target_ignored_passes(self):
        # a bool-valued *_max key must not be treated as a numeric commitment.
        # The baseline is chosen so that IF the bool leaked through (True is an
        # int subclass == 1) the pair would be flagged as aggressive: 1/2 = 0.5
        # < 0.7. The check passes ONLY because the bool-exclusion gate drops the
        # target before any ratio is computed.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "foo_max": True,
                    "baseline": {"foo_typical": 2},
                },
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_target_suffix_pair_passes(self):
        # '_target' suffix uses the '_max'-style baseline lookups; reasonable
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "p95_latency_target": 90,
                    "baseline": {"p95_latency_typical": 100},
                },
            )
            self.assertTrue(run(state).passed)


class TestCheck15Fail(unittest.TestCase):
    def test_aggressive_without_disclaimer_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "cold_start_seconds_max": 0.5,  # ratio 0.5 < 0.7 → aggressive
                    "baseline": {"cold_start_typical_seconds": 1.0},
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "15")
            self.assertEqual(len(result.findings), 1)
            f = result.findings[0]
            self.assertEqual(f.location, "cold_start_seconds_max")
            self.assertIn("cold_start_seconds_max=0.5", f.message)
            self.assertIn("baseline=1.0", f.message)
            self.assertIn("ratio=0.50", f.message)

    def test_target_suffix_aggressive_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "p95_latency_target": 50,  # ratio 0.5 < 0.7
                    "baseline": {"p95_latency_typical": 100},
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.findings[0].location, "p95_latency_target")

    def test_multiple_aggressive_yield_multiple_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "cold_start_seconds_max": 0.2,
                    "warm_start_seconds_max": 0.1,
                    "baseline": {
                        "cold_start_typical_seconds": 1.0,
                        "warm_start_typical_seconds": 0.8,
                    },
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 2)
            locs = {f.location for f in result.findings}
            self.assertEqual(
                locs, {"cold_start_seconds_max", "warm_start_seconds_max"}
            )

    def test_mixed_one_disclaimed_one_not(self):
        # top-level disclaimer absent; per-key disclaimer only neutralizes its
        # own key, leaving the other one flagged.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(
                tmp,
                {
                    "cold_start_seconds_max": 0.2,
                    "warm_start_seconds_max": 0.1,
                    "cold_start_seconds_max_stretch_disclaimer": "ok",
                    "baseline": {
                        "cold_start_typical_seconds": 1.0,
                        "warm_start_typical_seconds": 0.8,
                    },
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(
                result.findings[0].location, "warm_start_seconds_max"
            )


if __name__ == "__main__":
    unittest.main()
