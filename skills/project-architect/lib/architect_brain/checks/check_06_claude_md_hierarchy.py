"""check_06 -- CLAUDE.md hierarchy matches the subfolders decision.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Ports v7's check_06_claude_md_hierarchy: when the project opts into a
subfolder layout, a root CLAUDE.md alone is the "root-only" anti-pattern
(bug #8 from the v2.1.5 md2pdf live test) -- there should be at least one
per-subfolder router CLAUDE.md one level down.

Key assumption: the opt-in lives under the flat decision keys
``project.has_subfolders`` (preferred) or ``subfolders.enabled``. The check
degrades to PASS when neither key is truthy (monolith project), when no root
CLAUDE.md exists yet (pre-Phase-7), and on any missing/garbage state -- v7's
decline-to-claim idiom. "Subfolder CLAUDE.md" means EXACTLY one level deep
(depth 2 from the project root: ``<subdir>/CLAUDE.md``); deeper-nested routers
do not satisfy the check on their own.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _findlib, _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "06"
NAME = "claude_md_hierarchy"
SEVERITY = "WARNING"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def run(state_dir) -> CheckResult:
    """Verify the CLAUDE.md hierarchy matches the subfolders decision."""
    state_dir = Path(state_dir)
    decisions = _state.load_decisions(state_dir)

    # Opt-in gate: subfolder hierarchy only required when one of the two keys
    # is truthy. Absent/false/None -> monolith -> nothing to verify.
    has = decisions.get("project.has_subfolders") or decisions.get("subfolders.enabled")
    if not has:
        return _pass("subfolder hierarchy not required (has_subfolders not set)")

    proj = _state.project_root(state_dir)
    if not (proj / "CLAUDE.md").exists():
        return _pass("no root CLAUDE.md -- project may be pre-Phase-7")

    # Subfolder CLAUDE.md == exactly one level deep: <subdir>/CLAUDE.md is
    # depth 2 from proj. _findlib prunes VCS/build/vendor/cache + fixtures dirs.
    candidates = [
        p for p in _findlib.walk_files(proj, names={"CLAUDE.md"}, max_depth=2)
        if len(p.relative_to(proj).parts) == 2
    ]

    if not candidates:
        finding = Finding(
            message=(
                "root CLAUDE.md exists but no subfolder CLAUDE.md "
                "(has_subfolders=true expects >=1)"
            ),
            location=str(proj / "CLAUDE.md"),
        )
        return CheckResult(
            check_id=CHECK_ID, passed=False, severity=SEVERITY,
            summary="root-only CLAUDE.md hierarchy (no subfolder routers)",
            findings=(finding,),
        )

    return _pass(f"{len(candidates)} subfolder CLAUDE.md(s) found alongside root")
