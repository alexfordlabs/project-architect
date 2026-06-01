"""Shared markdown collector for doc-scanning auditor checks.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

v7's check_06/07/08/09 each inlined the same ``find docs -name '*.md'`` with a
vendor-exclusion list (the helper was deliberately NOT shared in bash because
``find_project_files`` stripped ``tests/fixtures/`` paths). In v8 we extract it
once: every doc-scanning check derives the project's ``docs/`` root as
``state_dir.parent`` and calls :func:`collect_markdown`. The ``_architect_state``
subtree is skipped here (it holds machine state — events/projections — never
design ``.md`` files), so a check never mistakes state for a design doc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Directories never treated as design docs. Mirrors v7's standard exclusion list
# plus ``_architect_state`` (v8's machine-state directory).
_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "vendor", "target", "dist", "build",
    ".venv", ".tox", "__pycache__", ".next", ".terraform", "coverage",
    ".cache", ".claude", ".serena", ".idea", ".vscode",
    "_architect_state",
})


def collect_markdown(docs_root, *, extra_skip_dirs: Iterable[str] = ()) -> list[Path]:
    """Return every design ``*.md`` under ``docs_root``, sorted, vendor dirs skipped.

    ``extra_skip_dirs`` adds per-check exclusions (e.g. ``versions``/``research``
    for the footer + placeholder checks, which don't apply to frozen snapshots).
    Returns ``[]`` when ``docs_root`` is missing or contains no markdown.
    """
    docs_root = Path(docs_root)
    if not docs_root.is_dir():
        return []
    skip = _SKIP_DIRS | frozenset(extra_skip_dirs)
    out: list[Path] = []
    for path in sorted(docs_root.rglob("*.md")):
        rel_dir_parts = path.parent.relative_to(docs_root).parts
        if any(part in skip for part in rel_dir_parts):
            continue
        out.append(path)
    return out
