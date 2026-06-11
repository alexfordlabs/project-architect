"""check_18 -- every design doc on disk must be recorded in the docs ledger.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Ports v7's check_18_ledger_complete (WARNING). Catches the T1 drift mode where a
design doc was written to disk but never recorded in the ledger — the deliverable
exists yet the state's record of "what was generated" is incomplete. v8
adaptation: the v7 monolithic ``state.documents_generated[].path`` becomes
``docs.json``'s ``completed[].path`` (via ``_state.load_docs_completed``), and
the inline ``find docs -maxdepth 2`` is the shared ``collect_markdown`` helper
plus a depth-≤2 filter, excluding the ``decisions``/``research``/``versions``
subtrees (ADRs are check_17's job; research/version snapshots aren't
ledger-tracked design docs). Recorded paths are stored PROJECT-relative
(``docs/<NAME>.md``), so each on-disk doc is compared via its path relative to
the project root — like-for-like with v7.
"""

from __future__ import annotations

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "18"
NAME = "ledger_complete"
SEVERITY = "WARNING"

# Subtrees that are NOT ledger-tracked design docs (mirrors v7's find exclusions).
_EXCLUDED_SUBTREES = frozenset({"decisions", "research", "versions"})

# v7 scanned docs/ at -maxdepth 2: a doc directly under docs/ (1 part) or one
# subdirectory deep (2 parts). Deeper docs are out of scope.
_MAX_DEPTH = 2


def run(state_dir) -> CheckResult:
    """Flag every in-scope on-disk design doc absent from ``docs.completed``."""
    docs_root = _state.docs_root(state_dir)
    proj = _state.project_root(state_dir)

    # The ledger of recorded docs (project-relative paths, e.g. "docs/X.md").
    ledger_set = {
        c["path"]
        for c in _state.load_docs_completed(state_dir)
        if isinstance(c, dict) and "path" in c
    }

    findings: list[Finding] = []
    # collect_markdown already skips _architect_state + vendor/build dirs; the
    # extra skip-dirs prune the excluded subtrees wherever they appear.
    for md in collect_markdown(docs_root, extra_skip_dirs=_EXCLUDED_SUBTREES):
        # Restrict to depth ≤ 2 under docs_root (v7's -maxdepth 2).
        if len(md.relative_to(docs_root).parts) > _MAX_DEPTH:
            continue
        rel = md.relative_to(proj).as_posix()
        if rel not in ledger_set:
            findings.append(
                Finding(
                    message=f"{rel} on disk but absent from docs.completed",
                    location=rel,
                )
            )

    passed = not findings
    if passed:
        summary = "docs.completed covers all on-disk design docs"
    else:
        summary = f"{len(findings)} on-disk doc(s) absent from docs.completed"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
