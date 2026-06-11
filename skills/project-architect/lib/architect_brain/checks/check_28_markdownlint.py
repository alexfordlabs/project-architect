"""check_28_markdownlint -- design docs lint clean on five structural rules.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

A NEW v8 check (spec §5.4). Runs ``markdownlint-cli2`` over the project's design
``*.md`` files and surfaces only five high-signal structural rules
(MD001/MD025/MD036/MD040/MD045) as BLOCKING findings; all other rule codes are
ignored as stylistic noise. INFO-degrades to a pass when the tool is absent,
there are no docs, or the invocation cannot run — the auditor never blocks LOCK
on missing host tooling.
"""

from __future__ import annotations

import re
import shutil
import subprocess

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "28"
NAME = "markdownlint"
SEVERITY = "BLOCKING"

_TOOL = "markdownlint-cli2"

# The five high-signal structural rules we surface; everything else is noise.
_TARGET_RULES: frozenset[str] = frozenset(
    {"MD001", "MD025", "MD036", "MD040", "MD045"}
)

# markdownlint-cli2 violation lines look like:
#   path:line ruleId/alias description
#   path:line:col ruleId/alias description
# Capture the path (everything up to the first ``:line``), the line number, and
# the rule code (the leading MDNNN before any ``/alias``).
_VIOLATION_RE = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+)(?::\d+)?\s+(?P<rule>MD\d{3})\b"
)


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def run(state_dir) -> CheckResult:
    """Lint design docs; flag any of the five targeted rules as BLOCKING."""
    if shutil.which(_TOOL) is None:
        return _pass(f"{_TOOL} not installed; skipped")

    docs_root = _state.docs_root(state_dir)
    files = collect_markdown(docs_root)
    if not files:
        return _pass("no design docs to lint")

    try:
        proc = subprocess.run(
            [_TOOL, *[str(f) for f in files]],
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        # Cannot run the tool: decline to claim a defect (degraded pass).
        return _pass(f"{_TOOL} could not be invoked; skipped")

    findings: list[Finding] = []
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    for raw in output.splitlines():
        match = _VIOLATION_RE.match(raw.strip())
        if match is None:
            continue
        if match.group("rule") not in _TARGET_RULES:
            continue
        path = match.group("path")
        findings.append(
            Finding(
                message=f"{path}:{match.group('line')} {match.group('rule')}",
                location=path,
            )
        )

    passed = not findings
    if passed:
        summary = "markdownlint clean (targeted rules)"
    else:
        summary = f"{len(findings)} markdownlint violation(s) of targeted rules"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
