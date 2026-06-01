"""check_04 -- every shell script under the project passes shellcheck.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Ports v7's check_04_shellcheck. Runs ``shellcheck -s bash -S warning`` over every
``*.sh`` under the project root (vendor/build/fixtures dirs pruned by _findlib),
emitting one BLOCKING Finding per failing script with up to three distinct SC
codes. v8 adaptation: when the binary is absent the check PASSES (graceful
degradation, summarised "shellcheck not installed; skipped") so a CI host that
lacks the tool isn't blocked -- v7's INFO-pass collapses into v8's plain pass.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from architect_brain.checks import _findlib
from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "04"
NAME = "shellcheck"
SEVERITY = "BLOCKING"

_SC_CODE = re.compile(r"SC\d+")


def _result(passed: bool, summary: str, findings: tuple[Finding, ...] = ()) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=findings,
    )


def _distinct_codes(text: str, limit: int = 3) -> list[str]:
    """Return up to ``limit`` distinct ``SC####`` codes in first-seen order."""
    seen: list[str] = []
    for code in _SC_CODE.findall(text):
        if code not in seen:
            seen.append(code)
        if len(seen) >= limit:
            break
    return seen


def run(state_dir) -> CheckResult:
    """Validate that every ``*.sh`` under the project root passes shellcheck."""
    if shutil.which("shellcheck") is None:
        return _result(True, "shellcheck not installed; skipped")

    proj = _state.project_root(state_dir)
    sh_files = _findlib.walk_files(proj, suffixes={".sh"})
    if not sh_files:
        return _result(True, "no shell scripts to check")

    findings: list[Finding] = []
    for f in sh_files:
        try:
            proc = subprocess.run(
                ["shellcheck", "-s", "bash", "-S", "warning", str(f)],
                capture_output=True, text=True,
            )
        except OSError:
            # The binary vanished between which() and run(); decline to claim.
            return _result(True, "shellcheck not runnable; skipped")
        if proc.returncode != 0:
            try:
                relpath = str(Path(f).relative_to(proj))
            except ValueError:
                relpath = str(f)
            codes = _distinct_codes((proc.stdout or "") + (proc.stderr or ""))
            label = ",".join(codes) if codes else "unknown"
            findings.append(Finding(message=f"{relpath} [{label}]", location=relpath))

    if not findings:
        summary = f"all {len(sh_files)} shell script(s) pass shellcheck"
        return _result(True, summary)

    summary = f"{len(findings)} failing shell script(s)"
    return _result(False, summary, tuple(findings))
