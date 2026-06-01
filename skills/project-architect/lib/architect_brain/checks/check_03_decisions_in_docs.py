"""check_03 -- every recorded decision is mentioned somewhere in docs/.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Ports v7's check_03_decisions_in_docs to v8's FLAT decision keyspace. A decision
that lives in state but is never named (by its value OR its leaf key) in any
design doc is a silent omission a reader would never spot, so this is a WARNING.
v7 walked a nested decision tree and skipped ADR-bookkeeping leaves (adr, status,
date, ...); v8 flat keys are pure decisions, but a small set of OPERATIONAL keys
(git.* / scm.* / scaffold.* / carry_forward.* / memory_pointer — state + tooling
bookkeeping, never design prose) is exempt via ``_is_operational`` (v8.0.1) so the
WARNING surfaces only substantive omissions. The corpus search is case-sensitive
(v7 parity). Missing decisions or missing docs => PASS (the decline-to-claim
idiom: nothing to verify).
"""

from __future__ import annotations

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "03"
NAME = "decisions_in_docs"
SEVERITY = "WARNING"

# Operational/bookkeeping keys the orchestrator records for STATE + TOOLING, not
# design choices a reader expects in prose. Exempt from the documented-in-docs
# requirement so the WARNING surfaces only SUBSTANTIVE undocumented decisions
# (e.g. admin.csam_workflow), not git.repo_init / memory_pointer noise. (v8.0.1)
_OPERATIONAL_PREFIXES = ("git.", "scm.", "scaffold.", "carry_forward.")
_OPERATIONAL_EXACT = frozenset({"memory_pointer"})


def _is_operational(key: str) -> bool:
    """A bookkeeping/tooling key that legitimately never appears in a design doc."""
    return key in _OPERATIONAL_EXACT or key.startswith(_OPERATIONAL_PREFIXES)


def run(state_dir) -> CheckResult:
    """Flag any SUBSTANTIVE flat decision whose value and leaf key are both absent
    from docs/ (operational/bookkeeping keys are exempt — see _is_operational)."""
    decisions = _state.load_decisions(state_dir)
    if not decisions:
        return CheckResult(
            check_id=CHECK_ID, passed=True, severity=SEVERITY,
            summary="no decisions to verify", findings=(),
        )

    md_files = collect_markdown(_state.docs_root(state_dir))
    if not md_files:
        return CheckResult(
            check_id=CHECK_ID, passed=True, severity=SEVERITY,
            summary="no docs/ markdown to search", findings=(),
        )

    # One concatenated corpus; case-sensitive substring search (v7 parity).
    parts: list[str] = []
    for md in md_files:
        try:
            parts.append(md.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    corpus = "\n".join(parts)

    findings: list[Finding] = []
    for key, value in decisions.items():
        if value is None or value == "":
            continue
        if _is_operational(key):
            continue
        leaf = key.rsplit(".", 1)[-1]
        if str(value) not in corpus and leaf not in corpus:
            findings.append(Finding(message=f"{key}={value}", location=key))

    passed = not findings
    summary = (
        "all decisions are mentioned in docs"
        if passed
        else f"{len(findings)} undocumented decision(s)"
    )
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
