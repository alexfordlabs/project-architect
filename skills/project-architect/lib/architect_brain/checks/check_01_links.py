"""check_01 — every relative markdown link target in docs/*.md resolves.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Ports v7's check_01_links.sh. For every design markdown file under the
project's ``docs/`` (via :func:`collect_markdown`, which already prunes vendor /
build dirs and the ``_architect_state`` machine-state subtree), find each
inline link target, strip its ``#anchor``, skip external / protocol-relative /
mailto / tel / absolute-filesystem targets, and verify the remaining relative
target resolves against the LINKING file's own directory. A broken link is a
BLOCKING defect (the orchestrator can repair docs; it is not unconditional).

Known limitation (faithful to v7): the link regex ``[^)]+`` stops at the first
``)``, so filenames containing parentheses are captured truncated and reported
broken. Avoid parens in linked filenames.
"""

from __future__ import annotations

import re
from pathlib import Path

from architect_brain.checks._docscan import collect_markdown
from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "01"
NAME = "link_integrity"
SEVERITY = "BLOCKING"

# Inline-link target: the substring between "](" and the first ")".
# Mirrors v7's `grep -oE '\]\([^)]+\)'` + sed extraction.
_LINK_RE = re.compile(r"\]\(([^)]+)\)")


def _is_external(target: str) -> bool:
    """True for targets the check must NOT resolve on the local filesystem.

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
    """Verify every relative markdown link in the project's docs resolves."""
    state_dir = Path(state_dir)
    root = _state.project_root(state_dir)
    docs = _state.docs_root(state_dir)

    findings: list[Finding] = []
    for md_file in collect_markdown(docs):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            # Unreadable file: nothing to verify here (decline to claim).
            continue
        try:
            relpath = str(md_file.relative_to(root))
        except ValueError:
            relpath = str(md_file)
        base_dir = md_file.parent
        for raw_target in _LINK_RE.findall(text):
            # Strip the #anchor suffix; keep the path portion only.
            path_only = raw_target.split("#", 1)[0]
            # Skip pure anchors (e.g. [section](#heading)).
            if not path_only:
                continue
            # Skip external / protocol-relative / mailto / tel targets.
            if _is_external(path_only):
                continue
            # Skip absolute filesystem paths (can't reason about /etc/...).
            if path_only.startswith("/"):
                continue
            resolved = base_dir / path_only
            if not resolved.exists():
                findings.append(
                    Finding(message=f"{relpath} -> {path_only}", location=relpath)
                )

    passed = not findings
    summary = "all links resolve" if passed else f"{len(findings)} broken link(s)"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
