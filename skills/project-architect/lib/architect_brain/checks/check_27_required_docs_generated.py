"""check_27 -- every doc-class generate_when:always template produced its doc.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

v8-ADAPTATION of v7's check_27_required_docs_generated. The rule is unchanged:
the LIVE plugin template frontmatter is the source of truth -- a template whose
``generate_when`` is ``always`` and whose NAME is neither ``CLAUDE_MD_ROOT`` nor
a ``SLASH_*`` (those are generated in later phases) must have produced its
``docs/<NAME>.md`` output. A never-generated required doc is BLOCKING (the fix
is to dispatch document-author, not a mechanical string edit).

Two v8-specific notes:
- v7 read each template's first ``---`` frontmatter block via awk, ignoring any
  preceding HTML-comment header. ``architect_brain.adr.parse_frontmatter``
  requires the text to START at ``---``, so we strip a leading HTML-comment /
  blank-line header before parsing -- 3 of the 5 always-doc-class templates
  begin with an attribution comment, and dropping them would silently shrink
  the required set and break v7 parity.
- The template dir is located relative to THIS module
  (``parents[3]`` == ``skills/project-architect/``); the project's ``docs/`` is
  ``_state.project_root(state_dir) / "docs"`` (== ``_state.docs_root``).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.adr import parse_frontmatter
from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "27"
NAME = "required_docs_generated"
SEVERITY = "BLOCKING"


def _template_dir() -> Path:
    """The plugin's live template dir (``skills/project-architect/references/templates``).

    Resolved relative to this module: ``checks/check_27_*.py`` →
    ``parents[3]`` == ``skills/project-architect/``. Exposed as a module-level
    function so tests can substitute it without touching the filesystem layout.
    """
    return Path(__file__).resolve().parents[3] / "references" / "templates"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def _first_frontmatter(text: str) -> dict:
    """Parse the FIRST ``---`` frontmatter block, tolerating a leading comment.

    ``parse_frontmatter`` requires the text to begin at ``---`` (after an
    optional BOM). Several templates begin with an HTML-comment attribution
    header before their frontmatter; we advance to the first ``---`` line so
    those templates are not silently dropped (v7 awk parity). Returns ``{}`` if
    no frontmatter block is found.
    """
    head = text.lstrip()
    if head.startswith("---"):
        return parse_frontmatter(head)
    # Find the first line that is exactly ``---`` (start of a frontmatter block)
    # past the leading comment/blank header.
    idx = text.find("\n---")
    if idx == -1:
        return {}
    return parse_frontmatter(text[idx + 1 :])


def run(state_dir) -> CheckResult:
    """Require every doc-class generate_when:always doc to exist under docs/."""
    state_dir = Path(state_dir)

    template_dir = _template_dir()
    if not template_dir.is_dir():
        # Off-plugin layout: can't enumerate required docs -> don't false-block.
        return _pass("template dir not locatable; cannot enumerate required docs")

    required: list[str] = []
    for tmpl in sorted(template_dir.glob("*.md")):
        name = tmpl.stem
        # CLAUDE_MD_ROOT (-> root CLAUDE.md) and SLASH_* (-> .claude/commands/*)
        # are produced in Phase 6/7, not at the Phase-4 doc-gen exit gate.
        if name == "CLAUDE_MD_ROOT" or name.startswith("SLASH_"):
            continue
        try:
            text = tmpl.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = _first_frontmatter(text)
        if fm.get("generate_when") == "always":
            required.append(name)

    if not required:
        # Unexpected catalog shape -> decline to make a claim (v7 INFO-pass).
        return _pass("no doc-class generate_when:always templates discovered")

    docs_root = _state.project_root(state_dir) / "docs"
    findings: list[Finding] = []
    for name in required:
        if not (docs_root / f"{name}.md").exists():
            rel = f"docs/{name}.md"
            findings.append(Finding(message=rel, location=rel))

    if not findings:
        return _pass(f"all {len(required)} generate_when:always doc-class doc(s) generated")

    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=f"{len(findings)} required doc(s) not generated",
        findings=tuple(findings),
    )
