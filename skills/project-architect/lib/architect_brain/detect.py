"""Situation-router query — fast, cheap reads only.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

detect_situation(docs_dir) reports what kind of project-architect history
lives at docs_dir, which drives Preflight's routing:

  greenfield      — no architect state; could be foreign or empty
  v8_project      — multi-file state layout (schema 4.0)
  pre_v8_project  — legacy monolith (schema < 4.0)

The "foreign vs greenfield" refinement (project material present but no
architect history) is SKILL.md prose territory, not this function — it
needs to scan the broader project, which is more expensive than this
fast-path query is meant to be.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def detect_situation(docs_dir: Path) -> dict[str, Any]:
    """Classify the state of project-architect history in docs_dir.

    Returns a dict with at least:
      situation: 'greenfield' | 'v8_project' | 'pre_v8_project'
      schema_version: str | None
      state_layout: 'v8_multi_file' | 'v7_monolith' | 'v7_monolith_unreadable' | None
    """
    state_dir = docs_dir / "_architect_state"
    legacy_monolith = docs_dir / "_architect_state.json"

    # v8 layout: docs/_architect_state/schema_version file exists.
    version_probe = state_dir / "schema_version"
    if version_probe.exists():
        version = version_probe.read_text().strip()
        return {
            "situation": "v8_project",
            "schema_version": version,
            "state_layout": "v8_multi_file",
        }

    # Legacy v7 layout: docs/_architect_state.json (monolith).
    if legacy_monolith.exists():
        try:
            data = json.loads(legacy_monolith.read_text())
            return {
                "situation": "pre_v8_project",
                "schema_version": data.get("schema_version"),
                "state_layout": "v7_monolith",
            }
        except (json.JSONDecodeError, OSError):
            return {
                "situation": "pre_v8_project",
                "schema_version": None,
                "state_layout": "v7_monolith_unreadable",
            }

    # No architect state — could be greenfield OR a foreign project.
    # SKILL.md's Preflight refines this with broader scan.
    return {
        "situation": "greenfield",
        "schema_version": None,
        "state_layout": None,
    }
