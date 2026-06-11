"""Per-concern materialised projections + apply_event routing.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

The event log (events.jsonl) is authoritative state in v8. Projections are
derived data: each concern has its own JSON file in docs/_architect_state/
<concern>.json, plus a 99-flat-index.json that aggregates all decisions and
ADRs for fast querying.

Wave 1.6 will add `replay(log_path)` that folds the event log into projections
from empty. The replay invariant is:
    replay(events) == fold(apply_event, events, empty_projections())
Wave 1.8 will add `projections_to_disk(state_dir, projections)`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from architect_brain.events import EventEnvelope


CONCERN_NAMES: tuple[str, ...] = (
    "identity",
    "vision",
    "architecture",
    "stack",
    "cost",
    "ai_agent",
    "api_contract",
    "docs",
    "workflow",
    "tooling",
    "handoff",
)


# Decision-key prefix → concern routing table.
# A decision with key "stack.foo.bar" lands in the "stack" concern projection.
_PREFIX_TO_CONCERN: dict[str, str] = {
    "identity": "identity",
    "project": "identity",
    "team": "identity",
    "scm": "identity",
    "vision": "vision",
    "requirements": "vision",
    "constraints": "vision",
    "scale": "vision",
    "architecture": "architecture",
    "stack": "stack",
    "frontend": "stack",
    "backend": "stack",
    "database": "stack",
    "hosting": "stack",
    "cost": "cost",
    "monetization": "cost",
    "ai": "ai_agent",
    "agent": "ai_agent",
    "api": "api_contract",
    "webhooks": "api_contract",
    "docs": "docs",
    "workflow": "workflow",
    "deployment": "tooling",
    "tooling": "tooling",
    "ci_cd": "tooling",
    "handoff": "handoff",
}


def empty_projections() -> dict[str, Any]:
    """Return a fresh set of empty projections (one per concern + flat-index)."""
    p: dict[str, Any] = {}
    for name in CONCERN_NAMES:
        p[name] = {
            "schema_version": "4.0",
            "concern": name,
            "decisions": {},
        }
    # Flat-index projection: a denormalised view of all decisions in one map.
    p["_flat_index"] = {
        "schema_version": "4.0",
        "decisions": {},
        "adrs": [],
    }
    # Decisions-index projection (Wave 2.11): elevates the ADR ledger to its
    # own dedicated file under docs/_architect_state/decisions/index.json.
    # _flat_index.adrs[] is still populated alongside this projection during
    # Wave 2 for backwards compatibility; this projection is the canonical
    # location going forward.
    p["_decisions_index"] = {
        "schema_version": "4.0",
        "adrs": [],
    }
    # Workflow projection carries the situation-router-relevant state.
    p["workflow"].update({
        "current_phase": None,
        "substep": None,
        "locked": False,
        "version": None,
        "audits": [],
    })
    return p


def _route_decision(key: str) -> str:
    """Map a dotted-path decision key to its owning concern."""
    head = key.split(".", 1)[0]
    return _PREFIX_TO_CONCERN.get(head, "vision")  # default: vision (catch-all)


def apply_event(event: EventEnvelope, projections: dict[str, Any]) -> None:
    """Mutate projections in-place to reflect a single event.

    Idempotent ONLY in the sense that re-applying the same event sequence from
    empty produces the same result (the replay invariant). Don't apply the same
    event twice to live state.
    """
    if event.type == "DecisionMade":
        key = event.payload["key"]
        value = event.payload["value"]
        concern = _route_decision(key)
        projections[concern]["decisions"][key] = value
        projections["_flat_index"]["decisions"][key] = value

    elif event.type == "ADRFiled":
        adr = {
            "id": event.payload["id"],
            "title": event.payload["title"],
            "status": event.payload["status"],
            "date": event.ts[:10],
            "phase": event.phase,
            "supersedes": event.payload.get("supersedes", []),
            "superseded_by": [],
        }
        # Append a fully independent copy to each projection so subsequent
        # mutations (e.g. ADRSuperseded) don't couple the two stores. Both
        # the outer dict AND its mutable list children are deep-copied here.
        def _decouple(a: dict[str, Any]) -> dict[str, Any]:
            return {
                **a,
                "supersedes": list(a["supersedes"]),
                "superseded_by": list(a["superseded_by"]),
            }
        projections["_flat_index"]["adrs"].append(_decouple(adr))
        projections["_decisions_index"]["adrs"].append(_decouple(adr))

    elif event.type == "ADRSuperseded":
        # Mutate the matching entry in BOTH projections independently.
        for projection_key in ("_flat_index", "_decisions_index"):
            for adr in projections[projection_key]["adrs"]:
                if adr["id"] == event.payload["id"]:
                    adr["status"] = "Superseded"
                    adr["superseded_by"].append(event.payload["by"])

    elif event.type == "PhaseAdvanced":
        projections["workflow"]["current_phase"] = event.payload["to"]
        projections["workflow"]["substep"] = None

    elif event.type == "SubstepRecorded":
        projections["workflow"]["substep"] = {
            "phase": event.payload["phase"],
            "substep": event.payload["substep"],
            "status": event.payload["status"],
        }

    elif event.type == "DocGenerated":
        doc = {
            "name": event.payload["name"],
            "path": event.payload["path"],
            "content_hash": event.payload["content_hash"],
        }
        projections["docs"].setdefault("completed", []).append(doc)

    elif event.type == "AuditCompleted":
        entry = {
            "ts": event.ts,
            "result": event.payload["result"],
            "checks_passed": event.payload["checks_passed"],
            "checks_failed": event.payload["checks_failed"],
        }
        # Carry the worst FAILED severity (disambiguates same-count clean vs
        # blocked) and the --ack override reason (so an acked-clean records WHY a
        # blocking finding was waived) into the ledger when present.
        if "worst_severity" in event.payload:
            entry["worst_severity"] = event.payload["worst_severity"]
        if "ack" in event.payload:
            entry["ack"] = event.payload["ack"]
        projections["workflow"]["audits"].append(entry)

    elif event.type == "LockSet":
        # `locked` defaults True (a bare LockSet locks); the /iterate-design flow
        # passes locked=False to unlock. `version` (the locked design version, e.g.
        # "v1.0" → "v1.1-draft" → "v1.1") is stored when present. locked_at is
        # stamped from the binary's own clock (the event ts) on a lock — never a
        # model-typed literal — unless the payload carries one explicitly; an
        # unlock clears it to null.
        locked = bool(event.payload.get("locked", True))
        projections["workflow"]["locked"] = locked
        if "version" in event.payload:
            projections["workflow"]["version"] = event.payload["version"]
        if "locked_at" in event.payload:
            projections["workflow"]["locked_at"] = event.payload["locked_at"]
        else:
            projections["workflow"]["locked_at"] = event.ts if locked else None

    # GoldenPathApplied / Upgraded / ResearchRefAdded / PhaseSkipped are
    # informational — they're preserved in events.jsonl but don't mutate
    # projection state directly (downstream events do the actual work).


from pathlib import Path

from architect_brain.events import read_events


def replay(log_path: Path) -> dict[str, Any]:
    """Reconstruct projections from the event log via fold.

    This is the canonical state-from-events function. The replay invariant says:
        replay(E) == fold(apply_event, E, empty_projections())
    Live-system incremental updates must produce byte-identical projections to
    `replay`. Wave 1.7's property-based test verifies this against random valid
    event sequences.

    Missing log files yield empty projections (no events to apply).
    """
    projections = empty_projections()
    for event in read_events(log_path):
        apply_event(event, projections)
    return projections


import json


def projections_to_disk(state_dir: Path, projections: dict[str, Any]) -> None:
    """Write each projection to its canonical file under state_dir.

    Files written:
      docs/_architect_state/schema_version          (one-line probe)
      docs/_architect_state/identity.json
      docs/_architect_state/vision.json
      ...                                            (one per concern)
      docs/_architect_state/99-flat-index.json       (aggregate projection)

    Output is byte-deterministic: same input produces byte-identical files
    (sort_keys=True + indent=2 + trailing newline). check_30_decisions_index_fresh
    (Wave 5) will exploit this to detect projection drift.
    """
    state_dir.mkdir(parents=True, exist_ok=True)

    # Schema-version probe file (one-line; fastest version detection).
    (state_dir / "schema_version").write_text("4.0\n", encoding="utf-8")

    # Per-concern projection files.
    for name in CONCERN_NAMES:
        target = state_dir / f"{name}.json"
        target.write_text(
            json.dumps(projections[name], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    # Flat-index projection — special filename for sortable directory listing.
    target = state_dir / "99-flat-index.json"
    target.write_text(
        json.dumps(projections["_flat_index"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Decisions-index projection (Wave 2.11): elevated ADR ledger lives at
    # docs/_architect_state/decisions/index.json (subdir created if missing).
    # The regenerated_at stamp is set HERE (not at apply_event time) — it's
    # the moment the projection was last materialised to disk.
    decisions_dir = state_dir / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    decisions_index = dict(projections["_decisions_index"])  # shallow copy
    decisions_index["regenerated_at"] = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    target = decisions_dir / "index.json"
    target.write_text(
        json.dumps(decisions_index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
