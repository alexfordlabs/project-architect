"""Tests for architect_brain.auditor.run_all_checks — the aggregator + LOCK verdict."""

import unittest

from architect_brain.auditor import run_all_checks
from architect_brain.severity import CheckResult


class _FakeCheck:
    """A stand-in check: fixed CHECK_ID + a canned CheckResult."""

    def __init__(self, check_id: str, result: CheckResult):
        self.CHECK_ID = check_id
        self._result = result

    def run(self, state_dir):  # noqa: ARG002 - state_dir unused in the fake
        return self._result


def _r(check_id, passed, severity):
    return CheckResult(check_id=check_id, passed=passed, severity=severity, summary="")


class TestRunAllChecks(unittest.TestCase):

    def test_all_pass_exit_zero(self):
        checks = [_FakeCheck("01", _r("01", True, "INFO")),
                  _FakeCheck("02", _r("02", True, "BLOCKING"))]
        report = run_all_checks("ignored", checks)
        self.assertEqual(report.exit_code, 0)
        self.assertEqual(report.blocking, ())
        self.assertIsNone(report.worst)

    def test_fatal_failure_blocks(self):
        checks = [_FakeCheck("01", _r("01", True, "INFO")),
                  _FakeCheck("29", _r("29", False, "FATAL"))]
        report = run_all_checks("ignored", checks)
        self.assertEqual(report.exit_code, 1)
        self.assertEqual(len(report.blocking), 1)
        self.assertEqual(report.worst, "FATAL")

    def test_blocking_failure_blocks_without_ack(self):
        checks = [_FakeCheck("28", _r("28", False, "BLOCKING"))]
        report = run_all_checks("ignored", checks)
        self.assertEqual(report.exit_code, 1)

    def test_ack_downgrades_blocking(self):
        checks = [_FakeCheck("28", _r("28", False, "BLOCKING"))]
        report = run_all_checks("ignored", checks, ack="known issue, shipping anyway")
        self.assertEqual(report.exit_code, 0)
        self.assertEqual(report.blocking, ())
        self.assertEqual(report.worst, "BLOCKING")  # worst still reflects the failure

    def test_ack_does_not_downgrade_fatal(self):
        checks = [_FakeCheck("29", _r("29", False, "FATAL"))]
        report = run_all_checks("ignored", checks, ack="nice try")
        self.assertEqual(report.exit_code, 1)

    def test_warning_failure_does_not_block(self):
        checks = [_FakeCheck("33", _r("33", False, "WARNING"))]
        report = run_all_checks("ignored", checks)
        self.assertEqual(report.exit_code, 0)
        self.assertEqual(report.worst, "WARNING")

    def test_only_filters_to_one_check(self):
        checks = [_FakeCheck("01", _r("01", False, "FATAL")),
                  _FakeCheck("02", _r("02", True, "INFO"))]
        report = run_all_checks("ignored", checks, only="02")
        self.assertEqual(len(report.results), 1)
        self.assertEqual(report.results[0].check_id, "02")
        self.assertEqual(report.exit_code, 0)

    # --- crash-safety: a raising check must not abort the whole audit -------

    def test_crashing_check_does_not_abort_run(self):
        class _Boom:
            CHECK_ID = "98"
            SEVERITY = "BLOCKING"

            def run(self, state_dir):  # noqa: ARG002
                raise RuntimeError("kaboom")

        checks = [_Boom(), _FakeCheck("01", _r("01", True, "INFO"))]
        report = run_all_checks("ignored", checks)
        # Both checks produced a result — the crash did not lose check 01.
        ids = {r.check_id for r in report.results}
        self.assertEqual(ids, {"98", "01"})
        crashed = next(r for r in report.results if r.check_id == "98")
        self.assertFalse(crashed.passed)
        self.assertIn("crashed", crashed.summary)
        self.assertEqual(crashed.severity, "BLOCKING")
        # A crashed BLOCKING check blocks LOCK.
        self.assertEqual(report.exit_code, 1)

    def test_crashing_check_uses_declared_severity(self):
        # A crashing INFO check fails but does NOT block (severity-faithful).
        class _BoomInfo:
            CHECK_ID = "97"
            SEVERITY = "INFO"

            def run(self, state_dir):  # noqa: ARG002
                raise ValueError("nope")

        report = run_all_checks("ignored", [_BoomInfo()])
        self.assertFalse(report.results[0].passed)
        self.assertEqual(report.results[0].severity, "INFO")
        self.assertEqual(report.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
