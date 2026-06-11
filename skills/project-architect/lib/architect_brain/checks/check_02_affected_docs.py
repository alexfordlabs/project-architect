"""check_02 -- ADR-declared affected_docs are all generated.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Adapts v7's check_02_affected_docs (a BLOCKER guarding against ADR-promised
docs being silently dropped). v8-ADAPTATION: v8 ADR events carry NO
``affected_docs`` and there is no ``deferred_docs`` concept, so this check
reads an OPTIONAL ``affected_docs`` list from each ADR markdown's frontmatter.
v8 ADRs do not normally carry ``affected_docs`` -- this check only fires when a
project's ADR frontmatter opts in. Membership is by basename (path prefixes
like ``docs/`` are ignored), with ``.md`` normalised on both sides.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.adr import parse_frontmatter
from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "02"
NAME = "adr_affected_docs"
SEVERITY = "BLOCKING"


def _as_md_basename(value: str) -> str:
    """Basename of ``value`` with a single trailing ``.md`` guaranteed."""
    base = Path(str(value)).name
    return base if base.endswith(".md") else base + ".md"


def run(state_dir) -> CheckResult:
    """Verify every ADR-declared ``affected_docs`` entry was generated."""
    state_dir = Path(state_dir)

    # Build the set of generated-doc basenames from the docs.completed ledger.
    # For each completed item, register BOTH the basename of its "name"
    # (with ".md" ensured) and the basename of its "path".
    generated_set: set[str] = set()
    for item in _state.load_docs_completed(state_dir):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and name:
            generated_set.add(_as_md_basename(name))
        path = item.get("path")
        if isinstance(path, str) and path:
            generated_set.add(Path(path).name)

    # For each ADR markdown, read the optional affected_docs frontmatter list
    # and verify each entry is in the generated set.
    findings: list[Finding] = []
    any_declared = False
    decisions_dir = _state.decisions_md_dir(state_dir)
    for adr_path in sorted(decisions_dir.glob("*.md")):
        try:
            text = adr_path.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = parse_frontmatter(text)
        affected = fm.get("affected_docs")
        if not isinstance(affected, list):
            continue
        any_declared = True
        adr_id = fm.get("id", "?")
        for entry in affected:
            if not isinstance(entry, str) or not entry:
                continue
            basename = _as_md_basename(entry)
            if basename not in generated_set:
                findings.append(
                    Finding(
                        message=f"ADR {adr_id} promised {basename} but not generated",
                        location=basename,
                    )
                )

    passed = not findings
    if not passed:
        summary = f"{len(findings)} ADR-promised doc(s) not generated"
    elif any_declared:
        summary = "all ADR affected_docs are generated"
    else:
        summary = "no ADR affected_docs to verify"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
