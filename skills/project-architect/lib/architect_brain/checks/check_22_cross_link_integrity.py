"""check_22 -- documentation cross-links must resolve (BLOCKING).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Ports v7's check_22_cross_link_integrity.sh. It is the deliberate sibling of
check_01 (v7 ships both): same ``\\]\\(([^)]+)\\)`` link scan, but check_22 adds
two behaviours check_01 lacks -- it strips an optional Markdown link *title*
(``[x](FILE.md "Title")`` -> ``FILE.md``) before resolving, and it RESOLVES an
absolute ``/x`` target against the PROJECT ROOT (check_01 simply skips absolute
targets). A dangling cross-link breaks navigation between generated docs and is
not mechanically fixable, so it is BLOCKING.

v8-ADAPTATION: v7 found docs via ``find docs -name '*.md' -not -path
'*/docs/versions/*' -not -path '*/docs/research/*'``. v8 uses the shared
``collect_markdown`` with ``extra_skip_dirs={"versions","research"}`` (frozen
snapshots + reference notes are not live design subject to link integrity) plus
the standard vendor / ``_architect_state`` pruning. Absent docs => pass.
"""

from __future__ import annotations

import re
from pathlib import Path

from architect_brain.checks._docscan import collect_markdown
from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "22"
NAME = "cross_link_integrity"
SEVERITY = "BLOCKING"

# Inline-link target: the substring between "](" and the first ")".
# Mirrors v7's `grep -oE '\]\([^)]+\)'` + sed extraction.
_LINK_RE = re.compile(r"\]\(([^)]+)\)")


def _is_external(target: str) -> bool:
    """True for targets that must NOT be resolved on the local filesystem.

    Mirrors v7's ``is_external_url``: any ``scheme://...`` form, protocol-relative
    ``//host/...``, ``mailto:``, and ``tel:``.
    """
    if "://" in target:
        return True
    if target.startswith("//"):
        return True
    if target.startswith("mailto:") or target.startswith("tel:"):
        return True
    return False


def run(state_dir) -> CheckResult:
    """Verify every relative + absolute cross-link in the project's docs resolves."""
    state_dir = Path(state_dir)
    proj = _state.project_root(state_dir)
    docs = _state.docs_root(state_dir)

    findings: list[Finding] = []
    for md_file in collect_markdown(docs, extra_skip_dirs={"versions", "research"}):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            # Unreadable file: nothing to verify here (decline to claim).
            continue
        try:
            relpath = str(md_file.relative_to(proj))
        except ValueError:
            relpath = str(md_file)
        base_dir = md_file.parent
        for raw_target in _LINK_RE.findall(text):
            tgt = raw_target
            # Skip external / protocol-relative / mailto / tel targets.
            if _is_external(tgt):
                continue
            # Skip pure in-page anchors (e.g. [section](#heading)).
            if tgt.startswith("#"):
                continue
            # Drop an optional link title: `](path "Title")` -> `path`.
            tgt = tgt.split(" ", 1)[0]
            # Strip a trailing #anchor; keep the path portion only.
            tgt = tgt.split("#", 1)[0]
            if not tgt:
                continue
            if tgt.startswith("/"):
                resolved = proj / tgt.lstrip("/")
            else:
                resolved = base_dir / tgt
            if not resolved.exists():
                findings.append(
                    Finding(
                        message=f"{relpath} -> {tgt} (target missing)",
                        location=relpath,
                    )
                )

    passed = not findings
    summary = (
        "all relative doc links resolve"
        if passed
        else f"{len(findings)} dangling cross-link(s)"
    )
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
