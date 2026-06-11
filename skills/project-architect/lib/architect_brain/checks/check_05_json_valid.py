"""check_05 — every JSON file under the state dir parses as valid JSON.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Adapts v7's check_05_json_valid to v8's multi-file state. A malformed state
projection or decisions file is a BLOCKING defect (the orchestrator can re-emit
it; it isn't the unconditional-fatal case that a schema violation is).
"""

from __future__ import annotations

import json
from pathlib import Path

from architect_brain.severity import CheckResult, Finding

CHECK_ID = "05"
NAME = "json_valid"
SEVERITY = "BLOCKING"


def run(state_dir) -> CheckResult:
    """Validate that every ``*.json`` under ``state_dir`` parses."""
    state_dir = Path(state_dir)
    findings: list[Finding] = []
    for json_file in sorted(state_dir.rglob("*.json")):
        try:
            json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            findings.append(Finding(message=f"invalid JSON: {exc}", location=str(json_file)))
    passed = not findings
    summary = "all JSON files valid" if passed else f"{len(findings)} invalid JSON file(s)"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
