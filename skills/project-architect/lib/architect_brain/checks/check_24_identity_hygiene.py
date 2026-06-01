"""check_24 -- docs/ must not leak forbidden identity terms.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Port of v7's check_24_identity_hygiene. The forbidden terms come from an
OPTIONAL project file ``.architect/identity-deny.txt`` (one term per line; blank
lines and ``#`` comments ignored); each is matched as a FIXED string (never a
regex) against every file under the project's ``docs/``. This is the T5
identity/security guard for non-secret PII (a real name, a personal email) that
must not appear in a pseudonymous project's public docs.

v8-ADAPTATION: v7 gated on ``schema_version == "3.0"`` before running; v8 drops
that gate (check_05/29 own state-validity, and the deny-file-absent case is
already the graceful no-op). The scan covers ALL file types under ``docs/`` (v7
parity -- not just ``*.md``) but skips the ``_architect_state`` machine-state
subtree, which lives under ``docs/`` in v8 and holds events/projections, not
author-written design docs.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "24"
NAME = "identity_hygiene"
SEVERITY = "BLOCKING"

# Machine-state subtree under docs/ — never scanned for identity leaks.
_STATE_DIR_NAME = "_architect_state"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def _load_terms(deny_path: Path) -> list[str]:
    """Parse the deny file: one term per line; strip; drop blanks + ``#`` lines."""
    try:
        raw = deny_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    terms: list[str] = []
    for line in raw.splitlines():
        term = line.strip()
        if not term or term.startswith("#"):
            continue
        terms.append(term)
    return terms


def run(state_dir) -> CheckResult:
    """Flag any forbidden identity term that leaks into a file under ``docs/``."""
    state_dir = Path(state_dir)
    proj = _state.project_root(state_dir)
    deny_path = proj / ".architect" / "identity-deny.txt"

    if not deny_path.is_file():
        return _pass("no .architect/identity-deny.txt configured")

    terms = _load_terms(deny_path)
    if not terms:
        return _pass("no forbidden terms configured")

    docs_root = _state.docs_root(state_dir)
    if not docs_root.is_dir():
        return _pass("no docs/ directory to scan")

    findings: list[Finding] = []
    for path in sorted(docs_root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(docs_root).parts
        # Skip the machine-state subtree (events/projections, not design docs).
        if _STATE_DIR_NAME in rel_parts[:-1] or rel_parts[0] == _STATE_DIR_NAME:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue  # unreadable file → skip
        rel = path.relative_to(docs_root).as_posix()
        for term in terms:
            if term in content:  # FIXED-string match (no regex)
                findings.append(
                    Finding(
                        message=f"{rel} contains forbidden term: '{term}'",
                        location=rel,
                    )
                )

    if not findings:
        return _pass("no forbidden identity terms found in docs/")

    plural = "term" if len(findings) == 1 else "terms"
    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=f"{len(findings)} leaked identity {plural} in docs/",
        findings=tuple(findings),
    )
