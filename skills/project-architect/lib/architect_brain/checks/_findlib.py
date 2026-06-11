"""Shared project-tree file walker for auditor checks that scan beyond docs/.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

v7's ``_lib.sh::find_project_files`` walked the project root for files matching
a pattern while pruning VCS / build / vendor / cache directories AND
``tests/fixtures``. checks 04 (shellcheck), 06 (CLAUDE.md hierarchy), 21
(settings), 23 (dependency freshness), 24/25 (manifest scans), 26 (scaffold)
all need this. ``_docscan`` covers the docs-only markdown case; this covers the
whole-project case (and the depth-bounded variant check_06 needs).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Directory names never descended into. Superset of _docscan's set + the
# fixtures / Pods / gradle / bower entries v7's find_project_files excluded.
_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "vendor", "Pods", "target", "dist", "build",
    ".venv", ".tox", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".ipynb_checkpoints", ".next", ".terraform", "coverage",
    ".cache", ".claude", ".serena", ".idea", ".vscode", ".gradle",
    "bower_components", "fixtures",
})


def walk_files(
    root,
    *,
    names: Iterable[str] | None = None,
    suffixes: Iterable[str] | None = None,
    max_depth: int | None = None,
) -> list[Path]:
    """Return matching files under ``root``, sorted, vendor/build dirs skipped.

    ``names`` filters to exact basenames (e.g. ``{"CLAUDE.md"}``); ``suffixes``
    filters by extension (e.g. ``{".sh"}``). When both are None, every file is
    returned. ``max_depth`` (≥1, relative to ``root``: a direct child is depth 1)
    bounds the descent — ``max_depth=2`` matches v7 check_06's ``-mindepth 2
    -maxdepth 2`` use after callers filter by their own depth needs.

    A path is skipped if ANY component between ``root`` and the file is in the
    skip set (so ``tests/fixtures/...`` and ``node_modules/...`` are pruned).
    Returns ``[]`` if ``root`` is missing.
    """
    root = Path(root)
    if not root.is_dir():
        return []
    name_set = frozenset(names) if names is not None else None
    suffix_set = frozenset(suffixes) if suffixes is not None else None

    out: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        # rel_parts[:-1] are the intermediate directory names.
        if any(part in _SKIP_DIRS for part in rel_parts[:-1]):
            continue
        if max_depth is not None and len(rel_parts) > max_depth:
            continue
        if name_set is not None and path.name not in name_set:
            continue
        if suffix_set is not None and path.suffix not in suffix_set:
            continue
        out.append(path)
    return out
