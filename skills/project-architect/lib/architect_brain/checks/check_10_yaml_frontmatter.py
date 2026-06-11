"""check_10 -- every docs/**/*.md YAML frontmatter parses via yaml.safe_load.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Ports v7's check_10 (the first Python auditor check). YAML frontmatter is the
``---``-bounded block at the top of a markdown file; malformed frontmatter
breaks downstream consumers (catalog discovery, ADR indexing, claude-md-author
template substitution), so an invalid block is BLOCKING. v8 adaptation: doc
collection now goes through the shared ``collect_markdown`` helper (which skips
vendor/build dirs and the ``_architect_state`` subtree); the v7 INFO-vs-BLOCKER
split on the *passing* paths collapses because v8 only consults severity on
failure. Graceful degradation is preserved: if PyYAML is absent the check
PASSES ("nothing to verify") rather than crashing.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _docscan, _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "10"
NAME = "yaml_frontmatter"
SEVERITY = "BLOCKING"


def extract_frontmatter(content: str):
    """Return the YAML text between leading ``---`` markers, or None.

    Copied verbatim from v7 check_10. The grammar is intentionally strict to
    match how downstream consumers (Jekyll/Hugo-style frontmatter, ADR tooling)
    parse the block:
      - The file must start with a line that is exactly "---" (after strip).
      - Some subsequent line must also be exactly "---" (after strip).
      - The text between (exclusive) is the frontmatter body.
    A file with no opening ``---`` or no closing ``---`` is treated as having no
    frontmatter (returns None -- the file is silently skipped).
    """
    if not content.startswith("---"):
        return None
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    # Find closing marker on its own line (after the opener).
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:i])
    return None


def run(state_dir) -> CheckResult:
    """Validate the YAML frontmatter of every design ``*.md`` under ``docs/``."""
    try:
        import yaml
    except ImportError:
        # Graceful degradation: PyYAML missing. Decline to claim rather than
        # crash -- there is nothing this check can verify on this host.
        return CheckResult(
            check_id=CHECK_ID, passed=True, severity=SEVERITY,
            summary="PyYAML not installed; check skipped", findings=(),
        )

    state_dir = Path(state_dir)
    docs_root = _state.docs_root(state_dir)
    md_files = _docscan.collect_markdown(docs_root)

    findings: list[Finding] = []
    for path in md_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            relpath = _relpath(path, docs_root)
            findings.append(Finding(message=f"{relpath}: read error: {exc}", location=relpath))
            continue
        fm = extract_frontmatter(content)
        if fm is None:
            # No frontmatter block -- out of scope for this check.
            continue
        try:
            yaml.safe_load(fm)
        except yaml.YAMLError as exc:
            # PyYAML messages are multi-line; keep only the first line for a
            # compact, single-line finding.
            err = str(exc).split("\n")[0]
            relpath = _relpath(path, docs_root)
            findings.append(Finding(message=f"{relpath}: {err}", location=relpath))

    passed = not findings
    if passed:
        summary = "all frontmatter blocks valid"
    else:
        summary = f"{len(findings)} file(s) have invalid frontmatter"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )


def _relpath(path: Path, docs_root: Path) -> str:
    """Path relative to ``docs/`` when possible, else the absolute string."""
    try:
        return str(path.relative_to(docs_root))
    except ValueError:
        return str(path)
