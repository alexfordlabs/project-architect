"""check_11 -- the state-schema version probe must equal the expected "4.0".

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Reads the one-line probe file ``state_dir/schema_version`` (written
unconditionally by ``projections.projections_to_disk`` as ``"4.0\\n"``) and
verifies it equals the expected schema version. WARNING-severity: a mismatched
or missing probe does not corrupt state, but it confuses every consumer that
branches on the schema version, so it is surfaced loudly without halting LOCK.

v8-ADAPTATION: v7's check_11 also asserted schema_version != plugin_version to
catch bug #1 (the two concepts were conflated at init). v8 projections carry NO
plugin_version field, so that conflation is structurally impossible -- the
sub-check is dropped entirely and only the probe-value comparison remains.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.severity import CheckResult, Finding

CHECK_ID = "11"
NAME = "schema_version"
SEVERITY = "WARNING"

_EXPECTED = "4.0"


def run(state_dir) -> CheckResult:
    """Verify ``state_dir/schema_version`` strips to the expected ``"4.0"``."""
    state_dir = Path(state_dir)
    probe = state_dir / "schema_version"

    try:
        raw = probe.read_text(encoding="utf-8")
    except OSError:
        finding = Finding(message="schema_version probe missing", location=str(probe))
        return CheckResult(
            check_id=CHECK_ID, passed=False, severity=SEVERITY,
            summary="schema_version probe missing", findings=(finding,),
        )

    value = raw.strip()
    if value != _EXPECTED:
        finding = Finding(
            message=f"schema_version is {value!r}, expected {_EXPECTED!r}",
            location=str(probe),
        )
        return CheckResult(
            check_id=CHECK_ID, passed=False, severity=SEVERITY,
            summary=f"schema_version is {value!r} (expected {_EXPECTED!r})",
            findings=(finding,),
        )

    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=f"schema_version={_EXPECTED}", findings=(),
    )
