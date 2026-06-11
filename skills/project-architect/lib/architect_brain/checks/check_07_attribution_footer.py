"""check_07 -- every design doc carries the project-architect attribution footer.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Ports v7's check_07_attribution_footer (INFO; cosmetic, never blocks LOCK).
Scans every design ``*.md`` under the project's ``docs/`` root and checks that
the canonical footer substring appears in the file's last 3 lines (tolerating a
trailing blank line / EOF newline). Frozen snapshots (``docs/versions/``) and
reference notes (``docs/research/``) are exempt. v8 adaptation: the v7 inline
``find`` is replaced by the shared ``collect_markdown`` helper, which already
applies the standard vendor/build exclusions plus the ``_architect_state`` skip.
"""

from __future__ import annotations

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "07"
NAME = "attribution_footer"
SEVERITY = "INFO"

# Distinct enough to be unique to the canonical footer, yet tolerant of trailing
# whitespace/punctuation. Mirrors v7's FOOTER_SUBSTR exactly.
_FOOTER_SUBSTR = "Skillfully made with [project-architect]"


def run(state_dir) -> CheckResult:
    """Verify every design doc ends with the attribution footer (last 3 lines)."""
    docs_root = _state.docs_root(state_dir)
    findings: list[Finding] = []

    for md in collect_markdown(docs_root, extra_skip_dirs={"versions", "research"}):
        try:
            content = md.read_text(encoding="utf-8")
        except OSError:
            # Unreadable file: decline to claim a missing footer; skip it.
            continue
        last_three = "\n".join(content.splitlines()[-3:])
        if _FOOTER_SUBSTR not in last_three:
            rel = str(md.relative_to(docs_root))
            findings.append(Finding(message=rel, location=rel))

    passed = not findings
    if passed:
        summary = "all docs carry the attribution footer"
    else:
        summary = f"{len(findings)} doc(s) missing attribution footer"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
