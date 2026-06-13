"""Golden Paths — curated decision bundles for one-click project pre-fill.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

A Golden Path (spec §5.1) pre-fills 10–14 decisions via a GoldenPathApplied
event + per-key DecisionMade events. Data lives in references/golden-paths.json;
this module loads + validates it and exposes the per-path decision bundle. The
``golden-path`` CLI (later task) applies a path by emitting the events.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from architect_brain.validator import validate_schema


class GoldenPathError(Exception):
    """A golden-paths file failed to load/validate, or an id was not found."""


def _schema_path() -> Path:
    """Resolve references/schemas/golden-paths-v4.json relative to this module."""
    return (
        Path(__file__).resolve().parents[2]
        / "references" / "schemas" / "golden-paths-v4.json"
    )


_PATH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "label", "description", "decisions"],
    "properties": {
        "id": {"type": "string"},
        "label": {"type": "string"},
        "description": {"type": "string"},
        "decisions": {"type": "object"},
        "valid_through": {"type": "string"},
    },
}


def load_golden_paths(path: Path) -> dict[str, Any]:
    """Load + validate a golden-paths.json file. Raise GoldenPathError on any problem.

    Validates the envelope against golden-paths-v4.json, each path against
    ``_PATH_SCHEMA``, and that path ids are unique. Errors are collected and
    reported together.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GoldenPathError(f"cannot load golden paths {path}: {exc}") from exc

    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    errors = list(validate_schema(data, schema))

    paths = data.get("paths", [])
    if isinstance(paths, list):
        seen: set[str] = set()
        for i, entry in enumerate(paths):
            for err in validate_schema(entry, _PATH_SCHEMA):
                errors.append(f"paths[{i}].{err}")
            if isinstance(entry, dict) and "id" in entry:
                if entry["id"] in seen:
                    errors.append(f"paths[{i}]: duplicate id {entry['id']!r}")
                seen.add(entry["id"])

    if errors:
        raise GoldenPathError(
            f"golden paths {path} are invalid:\n  " + "\n  ".join(errors)
        )
    return data


def list_paths(
    golden_paths: dict[str, Any], today: datetime.date | None = None
) -> list[dict[str, Any]]:
    """Return [{id, label, description, valid_through, expired}, ...] in catalog order.

    v9.1: ``valid_through`` is honored, not dead metadata — a path whose
    declared shelf life has passed is marked ``expired`` so the menu warns that
    its pre-filled stack reflects a stale snapshot and versions must be
    re-resolved (research-scout § 1a), not trusted. A path with no
    ``valid_through`` never expires.
    """
    if today is None:
        today = datetime.date.today()
    rows: list[dict[str, Any]] = []
    for p in golden_paths.get("paths", []):
        valid_through = p.get("valid_through")
        expired = False
        if isinstance(valid_through, str) and valid_through:
            try:
                expired = datetime.date.fromisoformat(valid_through) < today
            except ValueError:
                expired = False  # malformed date: schema validation's verdict
        rows.append({
            "id": p["id"],
            "label": p["label"],
            "description": p["description"],
            "valid_through": valid_through,
            "expired": expired,
        })
    return rows


def decisions_for(path_id: str, golden_paths: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the decision bundle for ``path_id``. Raise if not found."""
    for p in golden_paths.get("paths", []):
        if p.get("id") == path_id:
            return dict(p["decisions"])
    raise GoldenPathError(f"unknown golden path: {path_id!r}")
