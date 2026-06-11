"""check_33 -- optional Vale prose-lint of the project's design docs (INFO).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Vale (https://vale.sh) is an opt-in prose linter. This check is purely advisory:
it degrades to a clean pass whenever Vale is not installed or there are no design
docs to lint, and even when Vale DOES report issues the severity is INFO, so it
never blocks LOCK. It surfaces each reported issue line as a Finding so the
operator can read them, but the verdict is never load-bearing.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "33"
NAME = "vale_prose"
SEVERITY = "INFO"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def run(state_dir) -> CheckResult:
    """Run Vale over the project's design docs; INFO-only, never blocks LOCK."""
    state_dir = Path(state_dir)

    if shutil.which("vale") is None:
        return _pass("vale not installed; skipped")

    docs = collect_markdown(_state.docs_root(state_dir))
    if not docs:
        return _pass("no design docs to lint")

    try:
        result = subprocess.run(
            ["vale", *[str(p) for p in docs]],
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        # Could not invoke vale (missing binary mid-run, exec failure, …).
        # Advisory check — decline rather than crash the audit.
        return _pass("vale could not be run; skipped")

    issues = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    if not issues:
        return _pass(f"vale reported no issues across {len(docs)} doc(s)")

    findings = tuple(Finding(message=issue) for issue in issues)
    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=f"vale reported {len(findings)} issue line(s)",
        findings=findings,
    )
