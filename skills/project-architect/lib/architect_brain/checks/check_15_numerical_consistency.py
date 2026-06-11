"""check_15 -- performance targets must not silently outpace their baselines.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

v8-ADAPTATION of v7's check_15_numerical_consistency. v7 walked the nested
``state.decisions.architecture.performance_targets`` object inside the monolithic
state file. v8 stores decisions as a FLAT dotted-key map, so the same object now
lives under the single key ``architecture.performance_targets`` (a JSON dict set
via ``set-decision``). The comparison logic is ported verbatim: a ``*_max`` /
``*_target`` numeric commitment that claims more than a 30% improvement over its
matched ``baseline`` typical (ratio < 0.7) without a stretch disclaimer is a
WARNING -- it doesn't break runtime, it just lets the document quietly lie to
readers about a firm-looking number. Absent / non-dict / empty perf-targets ->
the check passes (nothing to verify).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "15"
NAME = "numerical_consistency"
SEVERITY = "WARNING"

# Targets claiming more than a 30% improvement over baseline are "aggressive".
AGGRESSIVE_RATIO = 0.7

_PERF_TARGETS_KEY = "architecture.performance_targets"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def _find_baseline(baseline_obj, target_key):
    """Find a matching numeric baseline value for ``target_key`` (or None).

    Ported verbatim from v7. Pair-matching strategies, first hit wins:

      1. target ends in ``_seconds_max``: strip it, try ``<base>_typical_seconds``,
         then ``<base>_seconds_typical``, then ``<base>_typical``.
      2. target ends in ``_max`` (not ``_seconds_max``): strip it, try
         ``<base>_typical`` then ``<base>_typical_value``.
      3. target ends in ``_target``: treat like ``_max``.

    Non-dict baseline, missing keys, and non-numeric / bool matches return None.
    """
    if not isinstance(baseline_obj, dict):
        return None

    def _lookup(candidates):
        for cand in candidates:
            val = baseline_obj.get(cand)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return val
        return None

    if target_key.endswith("_seconds_max"):
        base = target_key[: -len("_seconds_max")]
        return _lookup([
            f"{base}_typical_seconds",
            f"{base}_seconds_typical",
            f"{base}_typical",
        ])

    if target_key.endswith("_max"):
        base = target_key[: -len("_max")]
        return _lookup([f"{base}_typical", f"{base}_typical_value"])

    if target_key.endswith("_target"):
        base = target_key[: -len("_target")]
        return _lookup([f"{base}_typical", f"{base}_typical_value"])

    return None


def run(state_dir) -> CheckResult:
    """Flag aggressive perf targets lacking a stretch disclaimer."""
    state_dir = Path(state_dir)

    pt = _state.load_decisions(state_dir).get(_PERF_TARGETS_KEY)
    if not isinstance(pt, dict) or not pt:
        return _pass("no performance_targets")

    baseline = pt.get("baseline") if isinstance(pt.get("baseline"), dict) else {}
    top_level_disclaimer = pt.get("stretch_disclaimer")

    findings: list[Finding] = []
    for key, target_val in pt.items():
        # Bools are an int subclass; exclude them so "<flag>_max": true is not
        # treated as a numeric commitment.
        if not isinstance(target_val, (int, float)) or isinstance(target_val, bool):
            continue
        if not (key.endswith("_max") or key.endswith("_target")):
            continue
        # The per-key disclaimer fields themselves end in _stretch_disclaimer;
        # they aren't commitments (and aren't numeric anyway — defensive skip).
        if key.endswith("_stretch_disclaimer"):
            continue

        baseline_val = _find_baseline(baseline, key)
        if baseline_val is None or baseline_val <= 0:
            # No matching baseline OR a non-positive baseline (no meaningful
            # ratio). Skip silently.
            continue

        ratio = target_val / baseline_val
        if ratio < AGGRESSIVE_RATIO:
            per_key_disclaimer = pt.get(f"{key}_stretch_disclaimer")
            if top_level_disclaimer or per_key_disclaimer:
                continue  # author has acknowledged the stretch
            findings.append(Finding(
                message=f"{key}={target_val} (baseline={baseline_val}, ratio={ratio:.2f})",
                location=key,
            ))

    if findings:
        return CheckResult(
            check_id=CHECK_ID, passed=False, severity=SEVERITY,
            summary=f"{len(findings)} aggressive target(s) without stretch_disclaimer",
            findings=tuple(findings),
        )
    return _pass("all performance targets reasonable (or disclaimed)")
