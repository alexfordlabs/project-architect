"""check_29 -- every present projection validates against its shipped schema.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

FATAL. This is the engine behind the ``check-state`` CLI: it reuses
``validator.validate_schema`` to validate each per-concern projection
(``<concern>.json``) against its shipped JSON Schema fragment
(``references/schemas/state-v4-<concern>.json``). A schema violation means the
state on disk is structurally wrong for every consumer that trusts the schema,
so it blocks LOCK unconditionally. Concerns whose projection OR schema file is
absent are skipped (nothing to verify); a malformed projection JSON defers to
check_05 (json_valid) rather than counting as a schema error here.
"""

from __future__ import annotations

import json
from pathlib import Path

from architect_brain.projections import CONCERN_NAMES
from architect_brain.severity import CheckResult, Finding
from architect_brain.validator import validate_schema

CHECK_ID = "29"
NAME = "state_schema_valid"
SEVERITY = "FATAL"


def _schemas_dir() -> Path:
    """The plugin's live state-schema fragment dir.

    Resolved relative to this module: ``checks/check_29_*.py`` →
    ``parents[3]`` == ``skills/project-architect/``. Exposed as a module-level
    function so tests can substitute it without touching the filesystem layout.
    """
    return Path(__file__).resolve().parents[3] / "references" / "schemas"


def _load_json(path: Path):
    """Parse a JSON file; return None on missing/unreadable/invalid."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def run(state_dir) -> CheckResult:
    """Validate each present projection against its shipped per-concern schema."""
    state_dir = Path(state_dir)
    schemas_dir = _schemas_dir()
    findings: list[Finding] = []

    for concern in CONCERN_NAMES:
        proj_path = state_dir / f"{concern}.json"
        schema_path = schemas_dir / f"state-v4-{concern.replace('_', '-')}.json"

        # Skip concerns whose projection OR schema file is absent.
        if not proj_path.exists() or not schema_path.exists():
            continue

        projection = _load_json(proj_path)
        if projection is None:
            # Malformed projection JSON -> defer to check_05 (json_valid).
            continue
        schema = _load_json(schema_path)
        if not isinstance(schema, dict):
            # Unreadable/corrupt schema fragment -> nothing we can assert.
            continue

        for err in validate_schema(projection, schema):
            findings.append(
                Finding(message=f"{concern}: {err}", location=f"{concern}.json")
            )

    passed = not findings
    if passed:
        summary = "all present projections validate"
    else:
        summary = f"{len(findings)} schema violation(s)"
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
