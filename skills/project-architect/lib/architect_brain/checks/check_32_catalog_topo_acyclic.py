"""check_32 -- FATAL: the SHIPPED plugin catalog must be acyclic.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Validates the plugin's own ``references/catalog.json`` document-dependency
graph: it must load cleanly and contain no dependency cycle. This guards the
artifact that drives topological doc generation (a cycle would deadlock
``topo_sort``). It does NOT depend on the user's state -- ``run(state_dir)``
ignores ``state_dir`` and inspects the shipped catalog directly.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.catalog import CatalogError, detect_cycles, load_catalog
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "32"
NAME = "catalog_topo_acyclic"
SEVERITY = "FATAL"


def _catalog_path() -> Path:
    """Resolve the shipped references/catalog.json relative to this module.

    A check module lives at .../lib/architect_brain/checks/check_NN_*.py, so
    parents[3] is skills/project-architect/ (see the parents[3] trap note).
    """
    return Path(__file__).resolve().parents[3] / "references" / "catalog.json"


def _fail(message: str, location: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=message, findings=(Finding(message=message, location=location),),
    )


def run(state_dir) -> CheckResult:
    """Verify the shipped catalog loads and is acyclic. ``state_dir`` is ignored."""
    catalog_path = _catalog_path()

    try:
        catalog = load_catalog(catalog_path)
    except CatalogError as exc:
        return _fail(f"catalog unloadable: {exc}", str(catalog_path))
    except Exception as exc:  # pragma: no cover - defensive belt-and-braces
        # The auditor also wraps run() defensively, but the contract is that a
        # check never raises. Treat any unexpected load failure as unloadable.
        return _fail(f"catalog unloadable: {exc}", str(catalog_path))

    cycle = detect_cycles(catalog.get("documents", {}))
    if cycle:
        return _fail("cycle: " + " -> ".join(cycle), str(catalog_path))

    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary="catalog dependency graph is acyclic", findings=(),
    )
