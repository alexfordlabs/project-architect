"""Event envelopes for the architect-brain append-only event log.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

events.jsonl is the authoritative state-layer ground truth in v8. Per-concern
projections are materialised by replay (see projections.py — added in Wave 1.5).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_EVENT_TYPES = frozenset({
    "DecisionMade",
    "ADRFiled",
    "ADRSuperseded",
    "DocGenerated",
    "PhaseAdvanced",
    "PhaseSkipped",
    "SubstepRecorded",
    "AuditCompleted",
    "ResearchRefAdded",
    "GoldenPathApplied",
    "LockSet",
    "Upgraded",
})


@dataclass(frozen=True)
class EventEnvelope:
    id: str           # ULID (26 chars, Crockford-base32)
    ts: str           # ISO-8601 UTC, e.g., "2026-05-27T15:23:11Z"
    by: str           # "user" | "orchestrator" | "<agent-name>"
    phase: str | None  # phase identifier or None for phase-less events
    type: str         # one of ALLOWED_EVENT_TYPES
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if self.type not in ALLOWED_EVENT_TYPES:
            raise ValueError(
                f"Unknown event type {self.type!r}. "
                f"Allowed: {sorted(ALLOWED_EVENT_TYPES)}"
            )

    def to_json(self) -> str:
        """Serialise as a single JSONL line (no trailing newline)."""
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> "EventEnvelope":
        data = json.loads(line)
        return cls(
            id=data["id"],
            ts=data["ts"],
            by=data["by"],
            phase=data.get("phase"),
            type=data["type"],
            payload=data["payload"],
        )


from pathlib import Path
from typing import Iterator


def append_event(log_path: Path, event: EventEnvelope) -> None:
    """Atomically append one event as a JSONL line.

    Single-line writes ≤ PIPE_BUF (4 KB on most POSIX systems) are atomic at
    the OS level, so concurrent appends don't interleave. Events larger than
    4 KB are rare in our domain (payloads are small dicts); we don't special-
    case them.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(event.to_json() + "\n")


def read_events(log_path: Path) -> Iterator[EventEnvelope]:
    """Yield EventEnvelopes from a JSONL log. Missing files yield nothing.

    Blank lines are skipped (defensive — shouldn't occur in well-formed logs).
    """
    if not log_path.exists():
        return
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            yield EventEnvelope.from_json(stripped)
