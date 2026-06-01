"""Auditor aggregator — runs checks + computes the LOCK verdict.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Runs a set of checks (each an object with ``CHECK_ID: str`` + ``run(state_dir)
-> CheckResult``), aggregates the results, and decides whether the run blocks
LOCK. Waves 5b–5d register the 34 real checks; the ``audit`` CLI (Wave 5e)
wires them. ``--only`` runs one check; ``--ack=<reason>`` downgrades BLOCKING
failures (but never FATAL).
"""

from __future__ import annotations

from dataclasses import dataclass

from architect_brain.severity import CheckResult, Finding, blocks_lock, worst_severity


@dataclass(frozen=True)
class AuditReport:
    """The aggregate outcome of an audit run."""

    results: tuple[CheckResult, ...]
    blocking: tuple[CheckResult, ...]
    worst: str | None
    exit_code: int


def _run_one(check, state_dir) -> CheckResult:
    """Run a single check, converting any exception into a failing CheckResult.

    A check that raises must NOT abort the whole audit (that would lose every
    other check's verdict). A crash is itself a failure: it surfaces as a
    non-passing result at the check's declared severity (so a crashing FATAL
    check still blocks LOCK, a crashing INFO check still doesn't). This is the
    framework-level guarantee behind every check's "never raises" contract.
    """
    try:
        return check.run(state_dir)
    except Exception as exc:  # noqa: BLE001 — deliberately broad: no check may abort the audit
        check_id = getattr(check, "CHECK_ID", "??")
        severity = getattr(check, "SEVERITY", "BLOCKING")
        return CheckResult(
            check_id=check_id, passed=False, severity=severity,
            summary=f"check crashed: {type(exc).__name__}: {exc}",
            findings=(Finding(message=f"{type(exc).__name__}: {exc}"),),
        )


def run_all_checks(state_dir, checks, *, only: str | None = None, ack: str | None = None) -> AuditReport:
    """Run ``checks`` against ``state_dir`` and compute the LOCK verdict.

    ``only`` runs just the check whose ``CHECK_ID == only``. ``ack`` (a non-empty
    reason) downgrades BLOCKING failures so they don't block LOCK (FATAL still does).
    Each check runs through ``_run_one`` so a single crashing check can't abort
    the run.
    """
    selected = [c for c in checks if only is None or getattr(c, "CHECK_ID", None) == only]
    results = tuple(_run_one(c, state_dir) for c in selected)

    acked = bool(ack)
    blocking = tuple(
        r for r in results
        if not r.passed and blocks_lock(r.severity, acked=acked)
    )
    worst = worst_severity([r.severity for r in results if not r.passed])
    exit_code = 1 if blocking else 0
    return AuditReport(results=results, blocking=blocking, worst=worst, exit_code=exit_code)
