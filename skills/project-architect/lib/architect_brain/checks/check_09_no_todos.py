"""check_09 -- no design doc carries a TODO/FIXME/XXX marker.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Ports v7's check_09_no_todos (WARNING). Scans every design ``*.md`` under the
project's ``docs/`` (via the shared :func:`collect_markdown`, which already
prunes vendor/build dirs + the ``_architect_state`` subtree) EXCEPT files named
``BACKLOG.md`` -- the canonical place for parked work. The first
``\\b(TODO|FIXME|XXX)\\b`` match per file (case-sensitive, word-boundary) yields
one Finding; lowercase ``todo`` and substrings like ``FOXXXING``/``TODOs`` are
deliberately ignored. A TODO in a delivered doc is a workflow hint, not a broken
build -- WARNING, never blocks LOCK. Fresh project (no docs/, no markdown, or
only BACKLOG.md) passes: nothing to verify.
"""

from __future__ import annotations

import re

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "09"
NAME = "no_todos"
SEVERITY = "WARNING"

# Case-sensitive, word-boundary alternation: a standalone TODO/FIXME/XXX token.
_MARKER = re.compile(r"\b(TODO|FIXME|XXX)\b")


def run(state_dir) -> CheckResult:
    """Flag the first TODO/FIXME/XXX marker in each design doc (BACKLOG.md excluded)."""
    docs_root = _state.docs_root(state_dir)
    # collect_markdown is safe-empty on a missing docs/ and prunes _architect_state.
    md_files = [p for p in collect_markdown(docs_root) if p.name != "BACKLOG.md"]

    findings: list[Finding] = []
    for path in md_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            # Unreadable file: decline to claim a finding (json/schema checks own
            # state integrity; a TODO check never crashes on an I/O hiccup).
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            match = _MARKER.search(line)
            if match:
                try:
                    relpath = str(path.relative_to(docs_root))
                except ValueError:
                    relpath = str(path)
                findings.append(
                    Finding(
                        message=f"{relpath}: {lineno}:{match.group(0)}",
                        location=relpath,
                    )
                )
                break  # first match per file only

    passed = not findings
    if passed:
        summary = f"all {len(md_files)} doc(s) free of TODO/FIXME/XXX markers"
    else:
        summary = f"{len(findings)} doc(s) contain TODO/FIXME/XXX markers"
    return CheckResult(
        check_id=CHECK_ID,
        passed=passed,
        severity=SEVERITY,
        summary=summary,
        findings=tuple(findings),
    )
