"""Shared v8 state-reader helpers for auditor checks.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

v7's bash checks each read the monolithic ``docs/_architect_state.json`` via jq
and bailed (INFO-pass) when it was missing/unparseable. v8's state is a
directory of per-concern projection files + an append-only event log; this
module centralises reading them.

Every reader returns a SAFE-EMPTY default on a missing/unreadable/invalid file
rather than raising — check_05 (json_valid) and check_29 (state_schema_valid)
own the "is the state itself well-formed" verdict, so individual checks read
defensively and simply have "nothing to verify" when a file is absent (exactly
v7's decline-to-claim idiom). A check NEVER crashes the auditor on bad state.

Path contract: ``state_dir`` is always ``docs/_architect_state`` (``__main__``
sets ``state_dir = docs_dir / "_architect_state"``), so ``state_dir.parent`` is
the project's ``docs/`` and ``state_dir.parent.parent`` is the project root.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from architect_brain.events import EventEnvelope


def load_json(path) -> Any | None:
    """Parse a JSON file; return None on missing/unreadable/invalid."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_flat_index(state_dir) -> dict[str, Any]:
    """Read ``99-flat-index.json``; safe-empty default if absent/invalid."""
    data = load_json(Path(state_dir) / "99-flat-index.json")
    if not isinstance(data, dict):
        return {"schema_version": "4.0", "decisions": {}, "adrs": []}
    data.setdefault("decisions", {})
    data.setdefault("adrs", [])
    return data


def load_decisions(state_dir) -> dict[str, Any]:
    """Return the flat decision map (dotted-key → value)."""
    decisions = load_flat_index(state_dir).get("decisions", {})
    return decisions if isinstance(decisions, dict) else {}


def load_adrs(state_dir) -> list[dict[str, Any]]:
    """Return the ADR ledger entries from the flat index."""
    adrs = load_flat_index(state_dir).get("adrs", [])
    return adrs if isinstance(adrs, list) else []


def load_projection(state_dir, concern: str) -> dict[str, Any]:
    """Read a single ``<concern>.json`` projection; ``{}`` if absent/invalid."""
    data = load_json(Path(state_dir) / f"{concern}.json")
    return data if isinstance(data, dict) else {}


def load_workflow(state_dir) -> dict[str, Any]:
    """Read the ``workflow.json`` projection; ``{}`` if absent/invalid."""
    return load_projection(state_dir, "workflow")


def load_decisions_index(state_dir) -> dict[str, Any]:
    """Read ``decisions/index.json``; safe-empty default if absent/invalid."""
    data = load_json(Path(state_dir) / "decisions" / "index.json")
    if not isinstance(data, dict):
        return {"schema_version": "4.0", "adrs": []}
    data.setdefault("adrs", [])
    return data


def load_docs_completed(state_dir) -> list[dict[str, Any]]:
    """Return ``docs.json``'s ``completed`` list (generated-doc ledger)."""
    completed = load_projection(state_dir, "docs").get("completed", [])
    return completed if isinstance(completed, list) else []


def docs_root(state_dir) -> Path:
    """The project's ``docs/`` directory (= ``state_dir.parent``)."""
    return Path(state_dir).parent


def project_root(state_dir) -> Path:
    """The project root (= the directory containing ``docs/``)."""
    return Path(state_dir).parent.parent


def decisions_md_dir(state_dir) -> Path:
    """Where ADR markdown files live (``state_dir/decisions``)."""
    return Path(state_dir) / "decisions"


def iter_events(state_dir) -> Iterator[EventEnvelope]:
    """Yield every PARSEABLE event from ``events.jsonl``; SKIP malformed lines.

    Unlike ``events.read_events`` (the strict reader used by ``replay``), this
    check-facing reader never raises on a degraded log: an unparseable JSONL
    line, an unknown event ``type``, or an event missing a required key is
    silently skipped. Log well-formedness is check_05 (json_valid) and check_29
    (state_schema_valid)'s verdict — an event-consuming check (12/13/16/20) must
    not crash the whole audit on one bad line. Structurally valid events with a
    bad *field value* (e.g. a date-only ``ts``) ARE yielded, so the timestamp
    check can still flag them.
    """
    log_path = Path(state_dir) / "events.jsonl"
    if not log_path.exists():
        return
    try:
        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield EventEnvelope.from_json(stripped)
                except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                    continue  # defer log-validity to check_05 / check_29
    except OSError:
        return
