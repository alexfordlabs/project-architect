"""check_08 -- no design doc contains an unfilled {{placeholder}} literal.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Ports v7's check_08_no_placeholders. A literal ``{{project_name}}``-style marker
in a generated doc means the template engine never substituted it -- the artifact
is broken output, so this is BLOCKING. The pattern is case-sensitive lowercase +
underscore (``\\{\\{[a-z_]+\\}\\}``); uppercase ``{{TOC}}`` and spaced Jinja
``{{ project_name }}`` are out of scope. v8-adaptation: the v7 inline ``find``
becomes the shared :func:`collect_markdown`, which skips vendor/build dirs and the
``_architect_state`` machine-state subtree; ``versions``/``research`` are excluded
per v7 (frozen snapshots + reference notes aren't live design). One Finding per
file (first match), located at the doc's path relative to ``docs/``.
"""

from __future__ import annotations

import re

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "08"
NAME = "no_placeholders"
SEVERITY = "BLOCKING"

# Lowercase letters + underscore only, case-sensitive (matches our template-token
# convention, e.g. {{project_name}}, {{adr_id}}).
_PLACEHOLDER = re.compile(r"\{\{[a-z_]+\}\}")


def run(state_dir) -> CheckResult:
    """Scan every design ``*.md`` for the first ``{{placeholder}}`` per file."""
    docs_root = _state.docs_root(state_dir)
    md_files = collect_markdown(docs_root, extra_skip_dirs={"versions", "research"})

    findings: list[Finding] = []
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            # Unreadable file: decline to claim a defect (json/schema checks own I/O verdicts).
            continue
        try:
            relpath = str(md.relative_to(docs_root))
        except ValueError:
            relpath = str(md)
        for lineno, line in enumerate(text.splitlines(), start=1):
            match = _PLACEHOLDER.search(line)
            if match:
                findings.append(Finding(
                    message=f"{relpath}: {lineno}:{match.group(0)}",
                    location=relpath,
                ))
                break  # first match per file only

    passed = not findings
    if passed:
        summary = (
            f"all {len(md_files)} doc(s) have no unfilled placeholders"
            if md_files else "no markdown files to check"
        )
    else:
        summary = f"{len(findings)} doc(s) contain unfilled placeholders"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
