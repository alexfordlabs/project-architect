"""check_17 -- every recorded ADR must have a reviewable file on disk.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Catches the T1/T7 failure mode where the ledger records an ADR (id, title,
status) but no stub was ever written to decisions/ -- the decision exists in
state but not as a reviewable document. WARNING: the orchestrator can
mechanically close the gap (id/title/status are already in state).

v8-ADAPTATION of v7's check_17. v7 read ``state.adrs_filed[]`` from the
monolithic state.json and ``state.decisions_dir``; v8's ADR ledger is the flat
index's ``adrs[]`` (``_state.load_adrs``) and the decisions dir is always
``state_dir/decisions`` (``_state.decisions_md_dir``). A status of "Reserved"
(an id set aside for a future decision) legitimately has no file yet and is
skipped. A file is present iff ``decisions/<id>-*.md`` matches OR
``decisions/<id>.md`` exists.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "17"
NAME = "adr_files_exist"
SEVERITY = "WARNING"


def _has_file(dec_dir: Path, adr_id: str) -> bool:
    """True iff decisions/<id>-*.md matches OR decisions/<id>.md exists."""
    if (dec_dir / f"{adr_id}.md").is_file():
        return True
    return any(dec_dir.glob(f"{adr_id}-*.md"))


def run(state_dir) -> CheckResult:
    """Flag every non-Reserved recorded ADR that has no file in decisions/."""
    state_dir = Path(state_dir)
    adrs = _state.load_adrs(state_dir)
    dec_dir = _state.decisions_md_dir(state_dir)

    findings: list[Finding] = []
    checked = 0
    for entry in adrs:
        if not isinstance(entry, dict):
            continue
        adr_id = entry.get("id")
        if not adr_id:
            continue
        if entry.get("status") == "Reserved":
            continue
        checked += 1
        if not _has_file(dec_dir, str(adr_id)):
            findings.append(
                Finding(
                    message=f"ADR {adr_id} recorded but no file in decisions/",
                    location=str(adr_id),
                )
            )

    passed = not findings
    if passed:
        summary = (
            "no ADRs to verify"
            if checked == 0
            else f"all {checked} recorded ADR(s) have a file in decisions/"
        )
    else:
        summary = f"{len(findings)} recorded ADR(s) have no file in decisions/"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
