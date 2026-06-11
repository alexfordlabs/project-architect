"""check_14 -- ADR decision_keys must cite recorded decisions (citation integrity).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

v8-ADAPTATION of v7's check_14_adr_coverage. v7 detected "high-stakes"
decisions via a ``<leaf>_alternatives_considered`` SIBLING convention inside the
monolithic nested ``state.decisions`` object and required an ADR to cover each.
v8's decisions are a FLAT dotted-key map with no per-decision alternatives
sibling, so v7's "tradeoffs need ADRs" detector has no input. We invert the
relationship to the v8-available signal: ADR ``decision_keys`` CITATION
INTEGRITY -- every key an ADR's frontmatter cites must resolve to a recorded
decision. This is the analog that catches a stale ADR citation after
``/upgrade-project`` or ``/re-architect`` re-derives the keyspace and a decision
key is renamed or dropped out from under an ADR that still references it.

WARNING (not blocking): a dangling citation corrodes decision archeology but
breaks nothing at runtime. Passes (declines to claim) whenever no ADR declares
``decision_keys`` -- there is nothing to verify -- which is also the fresh-
project / no-state case (helpers return safe-empty).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.adr import parse_frontmatter
from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "14"
NAME = "adr_coverage"
SEVERITY = "WARNING"


def _collect_citations(adr_dir: Path) -> list[tuple[str, str]]:
    """Return ``(adr_id, decision_key)`` pairs for every cited key, in file order.

    Iterates ``*.md`` under ``adr_dir``, parses each file's frontmatter, and
    reads the OPTIONAL ``decision_keys`` list. Unreadable files, files with no
    (or malformed) frontmatter, and frontmatter without a list-valued
    ``decision_keys`` all contribute nothing -- ``parse_frontmatter`` already
    returns ``{}`` for the malformed case, so this never raises on bad input.
    """
    citations: list[tuple[str, str]] = []
    if not adr_dir.is_dir():
        return citations
    for md in sorted(adr_dir.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fm = parse_frontmatter(text)
        if not isinstance(fm, dict):
            continue
        keys = fm.get("decision_keys")
        if not isinstance(keys, list):
            continue
        adr_id = fm.get("id")
        adr_id = adr_id if isinstance(adr_id, str) and adr_id else "?"
        for key in keys:
            if isinstance(key, str):
                citations.append((adr_id, key))
    return citations


def run(state_dir) -> CheckResult:
    """Flag any ADR ``decision_keys`` entry that is not a recorded decision."""
    state_dir = Path(state_dir)

    citations = _collect_citations(_state.decisions_md_dir(state_dir))
    if not citations:
        return CheckResult(
            check_id=CHECK_ID, passed=True, severity=SEVERITY,
            summary="no decision_keys declared by any ADR", findings=(),
        )

    decisions = _state.load_decisions(state_dir)

    findings: list[Finding] = []
    for adr_id, key in citations:
        if key not in decisions:
            findings.append(Finding(
                message=(
                    f"ADR {adr_id} cites decision_keys['{key}'] which is not a "
                    "recorded decision"
                ),
                location=key,
            ))

    passed = not findings
    summary = (
        f"all {len(citations)} cited decision_key(s) recorded"
        if passed
        else f"{len(findings)} dangling ADR decision_key citation(s)"
    )
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
