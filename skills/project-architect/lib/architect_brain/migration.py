"""v3.1 -> 4.0 migrator: lift a v7 monolith state into v8 event-sourced state.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

The migrator reads a v7 monolithic ``docs/_architect_state.json`` (schema 3.0 /
3.1), snapshots it, synthesises an append-only event log, replays it into v8
per-concern projections, re-stamps ADRs/docs, reindexes the workflow phase,
compares the result against the v7 monolith for drift, and atomically flips —
keeping a backup tarball regardless. See design-doc §7.1 (13-step algorithm)
and ``docs/superpowers/specs/2026-05-29-v8-wave6-migrator-spec.md`` for the
field-name reconciliations.

Core principle: PRESERVE-FLAT. The nested v7 ``.decisions`` is flattened to
dotted keys VERBATIM — it is NOT translated to v8's ``stack.*`` namespace.
Migration preserves history faithfully; a user runs ``/re-architect`` if they
want full v8 doc-selection under v8 conventions.

Runtime code: ``datetime.now(timezone.utc)`` is acceptable here (unlike the
workflow scripts, which must use a real ``date -u`` stamp).
"""

from __future__ import annotations

import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architect_brain import __version__
from architect_brain.adr import emit_frontmatter, parse_frontmatter
from architect_brain.events import EventEnvelope, append_event
from architect_brain.projections import projections_to_disk, replay
from architect_brain.ulid import new_ulid


# Canonical v7 phase order — used to order the reconstructed PhaseAdvanced
# trajectory. Mirrors the state-schema phase enum.
_V7_PHASE_ORDER: tuple[str, ...] = (
    "preflight",
    "phase_0a",
    "phase_0",
    "phase_1",
    "phase_2",
    "phase_2.5",
    "phase_3",
    "phase_4",
    "phase_5",
    "phase_6",
    "phase_7",
    "phase_8",
    "complete",
)

# v7 phase token -> v8 ladder key.
#
# Head (the v8 reorder: Architecture BEFORE Tech stack, Cost its own phase):
#   preflight -> preflight     phase_0a -> kickoff     phase_0 -> kickoff
#   phase_1   -> vision        phase_2  -> stack       phase_2.5 -> cost
#   phase_3   -> architecture  complete -> complete
#
# Tail — DERIVED from the v7 SKILL.md phase definitions (read for this build):
#   v7 Phase 4 "Document Generation"     -> v8 "docs"
#   v7 Phase 5 "Iteration"               -> v8 "iteration"
#   v7 Phase 6 "Post-Generation Setup"   -> v8 "lock"      (LOCK happens here)
#   v7 Phase 7 "Tooling Execution"       -> v8 "tooling"
#   v7 Phase 8 "Handoff"                 -> v8 "handoff"
# The tail order is UNCHANGED from v7 (the v8 reorder only affects the head);
# every tail value is a valid key in ui.py ``_PHASE_LADDER``.
_PHASE_MAP: dict[str, str] = {
    "preflight": "preflight",
    "phase_0a": "kickoff",
    "phase_0": "kickoff",
    "phase_1": "vision",
    "phase_2": "stack",
    "phase_2.5": "cost",
    "phase_3": "architecture",
    "phase_4": "docs",
    "phase_5": "iteration",
    "phase_6": "lock",
    "phase_7": "tooling",
    "phase_8": "handoff",
    "complete": "complete",
}


def _now() -> str:
    """Current UTC time as ISO-8601 'YYYY-MM-DDTHH:MM:SSZ' (runtime code)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_legacy(docs_dir) -> dict[str, Any] | None:
    """Report a v7 monolith ``_architect_state.json`` under ``docs_dir``.

    Returns ``{"path", "schema_version", "state"}`` when the monolith file
    exists and parses; ``None`` otherwise. The caller decides whether a v8
    ``_architect_state/`` directory being present means "already migrated" —
    this function only reports the monolith.
    """
    import json

    path = Path(docs_dir) / "_architect_state.json"
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(state, dict):
        return None
    return {
        "path": path,
        "schema_version": state.get("schema_version"),
        "state": state,
    }


def _major(version: str | None) -> int | None:
    """Parse the integer major component of a dotted version string, or None."""
    if not version:
        return None
    head = str(version).split(".", 1)[0].strip()
    try:
        return int(head)
    except ValueError:
        return None


def migration_floor_ceiling_ok(
    schema_version: str | None, plugin_version: str | None
) -> tuple[bool, str]:
    """Whether this monolith is in the migrator's supported window.

    Floor: refuse ``schema_version`` major < 2 (those need the v5–v6 path).
    Ceiling: refuse ``plugin_version`` major > 8 (a future artifact this
    migrator must not touch). Missing/unparseable versions proceed with a note
    (defensive: ``detect`` reads the real values; an absent field is tolerated).
    """
    schema_major = _major(schema_version)
    if schema_major is not None and schema_major < 2:
        return (
            False,
            f"schema_version {schema_version!r} is below the 2.0 migration floor; "
            "use the v5–v6 upgrade path (/upgrade-project) for pre-2.0 state.",
        )

    plugin_major = _major(plugin_version)
    if plugin_major is not None and plugin_major > 8:
        return (
            False,
            f"plugin_version {plugin_version!r} is above the 8.x ceiling; this "
            "state was written by a newer plugin — upgrade project-architect.",
        )

    note = ""
    if schema_major is None:
        note = "schema_version missing/unparseable; proceeding."
    return (True, note)


def flatten_decisions(decisions: dict[str, Any]) -> dict[str, Any]:
    """Flatten a nested v7 ``.decisions`` dict to dotted keys (preserve-flat).

    A leaf is any NON-dict value: scalars AND lists are leaves (so
    ``*_alternatives_considered`` arrays survive as list-valued decisions).
    Keys are joined with ``.`` verbatim — no translation to ``stack.*``.
    """
    flat: dict[str, Any] = {}

    def _walk(prefix: str, node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                child = f"{prefix}.{k}" if prefix else str(k)
                _walk(child, v)
        else:
            flat[prefix] = node

    if isinstance(decisions, dict):
        for k, v in decisions.items():
            _walk(str(k), v)
    return flat


def phase_v7_to_v8(v7_phase: str) -> str:
    """Map a v7 phase token to the v8 ladder key (unknown -> pass-through)."""
    return _PHASE_MAP.get(v7_phase, v7_phase)


def snapshot_v7(docs_dir) -> Path:
    """Tar.gz the v7 monolith + ``decisions/`` dir to a timestamped backup.

    Written to ``docs_dir/_architect_state.json.v7-backup.<iso>.tar.gz`` (the
    colons in the ISO stamp replaced with ``-`` for filename safety). NEVER
    deletes anything. Returns the tarball path.
    """
    docs_dir = Path(docs_dir)
    stamp = _now().replace(":", "-")
    tarball = docs_dir / f"_architect_state.json.v7-backup.{stamp}.tar.gz"

    monolith = docs_dir / "_architect_state.json"
    decisions = docs_dir / "decisions"

    with tarfile.open(tarball, "w:gz") as tf:
        if monolith.exists():
            tf.add(monolith, arcname="_architect_state.json")
        if decisions.is_dir():
            tf.add(decisions, arcname="decisions")
    return tarball


def synthesize_events(v7_state: dict[str, Any]) -> list[EventEnvelope]:
    """Synthesise the v8 event log from a v7 monolith state (spec order).

    Order: 1 Upgraded, N DecisionMade (keys sorted), M ADRFiled (filed +
    reserved), K DocGenerated, >=1 PhaseAdvanced, 1 AuditCompleted (if
    last_audit non-null), 1 LockSet (if locked). Timestamps use the v7 source
    stamp where one exists, else ``started_at``, else now.
    """
    started_at = v7_state.get("started_at")
    last_updated = v7_state.get("last_updated_at")
    fallback_ts = started_at or last_updated or _now()

    events: list[EventEnvelope] = []

    def _mk(ev_type: str, payload: dict[str, Any], *, phase=None, ts=None) -> EventEnvelope:
        return EventEnvelope(
            id=new_ulid(),
            ts=ts or fallback_ts,
            by="migrator",
            phase=phase,
            type=ev_type,
            payload=payload,
        )

    # 1. Upgraded
    events.append(
        _mk(
            "Upgraded",
            {
                "from_schema": v7_state.get("schema_version"),
                "to_schema": "4.0",
                "from_plugin": v7_state.get("plugin_version"),
            },
        )
    )

    # 2. DecisionMade per flattened decision (sorted for determinism).
    flat = flatten_decisions(v7_state.get("decisions", {}) or {})
    for key in sorted(flat.keys()):
        events.append(_mk("DecisionMade", {"key": key, "value": flat[key]}))

    # 3. ADRFiled per adrs_filed[] then reserved_adrs[].
    for adr in v7_state.get("adrs_filed", []) or []:
        adr_ts = adr.get("filed_at") or adr.get("date") or fallback_ts
        events.append(
            _mk(
                "ADRFiled",
                {
                    "id": adr.get("id"),
                    "title": adr.get("title", ""),
                    "status": _norm_status(adr.get("status", "Accepted")),
                },
                phase=adr.get("phase"),
                ts=adr_ts,
            )
        )
    for reserved_id in v7_state.get("reserved_adrs", []) or []:
        events.append(
            _mk(
                "ADRFiled",
                {
                    "id": reserved_id,
                    "title": f"Reserved ADR slot for {reserved_id}",
                    "status": "Reserved",
                },
            )
        )

    # 4. DocGenerated per documents_generated[].
    for doc in v7_state.get("documents_generated", []) or []:
        doc_ts = doc.get("generated_at") or fallback_ts
        events.append(
            _mk(
                "DocGenerated",
                {
                    "name": doc.get("name"),
                    "path": doc.get("path", ""),
                    "content_hash": doc.get("content_hash") or "",
                },
                ts=doc_ts,
            )
        )

    # 5. PhaseAdvanced reconstruction.
    events.extend(_synthesize_phase_advances(v7_state, _mk))

    # 6. AuditCompleted from last_audit (if non-null).
    last_audit = v7_state.get("last_audit")
    if isinstance(last_audit, dict):
        blocker = int(last_audit.get("blocker", 0) or 0)
        warning = int(last_audit.get("warning", 0) or 0)
        info = int(last_audit.get("info", 0) or 0)
        events.append(
            _mk(
                "AuditCompleted",
                {
                    "result": "blocked" if blocker > 0 else "clean",
                    # v7 stored severity COUNTS, not pass/fail; passed is
                    # unknown (documented) -> 0; failed = blocker+warning+info.
                    "checks_passed": 0,
                    "checks_failed": blocker + warning + info,
                },
                ts=last_audit.get("ran_at") or fallback_ts,
            )
        )

    # 7. LockSet (if locked).
    if v7_state.get("locked"):
        locked_at = (
            v7_state.get("locked_at") or v7_state.get("last_updated_at") or _now()
        )
        events.append(_mk("LockSet", {"locked_at": locked_at}, ts=locked_at))

    return events


def _norm_status(status: Any) -> str:
    """Title-case a v7 ADR status (e.g. 'accepted' -> 'Accepted')."""
    if not isinstance(status, str) or not status:
        return "Accepted"
    return status[0].upper() + status[1:]


def _synthesize_phase_advances(v7_state, mk) -> list[EventEnvelope]:
    """Reconstruct the PhaseAdvanced trajectory from phase_progress + .phase.

    Take the phases in phase_progress that are complete (``complete: true`` or
    a ``completed_at``), order them by the canonical v7 order, append the
    current ``.phase`` if not already last, map each via ``phase_v7_to_v8``,
    de-dup consecutive equal v8 phases, then emit one PhaseAdvanced per
    consecutive pair (the first with ``from: null``).
    """
    progress = v7_state.get("phase_progress", {}) or {}
    completed: list[str] = []
    for phase in _V7_PHASE_ORDER:
        entry = progress.get(phase)
        if isinstance(entry, dict) and (entry.get("complete") or entry.get("completed_at")):
            completed.append(phase)

    current = v7_state.get("phase")
    if current and (not completed or completed[-1] != current):
        completed.append(current)

    # Map to v8 + de-dup consecutive repeats (the v7->v8 collapse, e.g.
    # phase_0a + phase_0 both -> kickoff, can produce a repeat).
    mapped: list[str] = []
    for phase in completed:
        v8 = phase_v7_to_v8(phase)
        if not mapped or mapped[-1] != v8:
            mapped.append(v8)

    events: list[EventEnvelope] = []
    prev: str | None = None
    for v8 in mapped:
        events.append(mk("PhaseAdvanced", {"from": prev, "to": v8}))
        prev = v8
    return events


def compare_v7_vs_v8(v7_state: dict[str, Any], projections: dict[str, Any]) -> list[str]:
    """Diff the replayed projections against the v7 monolith. [] == clean.

    Asserts: (a) the flat-index decisions equal ``flatten_decisions`` of the v7
    decisions, key-by-key (reports each missing/extra/changed key); and (b) the
    ADR id set in the flat-index equals the ``adrs_filed[] + reserved_adrs[]``
    id set. Returns a list of human-readable drift strings.
    """
    drift: list[str] = []

    expected = flatten_decisions(v7_state.get("decisions", {}) or {})
    flat_index = projections.get("_flat_index", {}) or {}
    actual = flat_index.get("decisions", {}) or {}

    for key, value in expected.items():
        if key not in actual:
            drift.append(f"decision missing from projections: {key}")
        elif actual[key] != value:
            drift.append(
                f"decision value changed for {key}: "
                f"v7={value!r} v8={actual[key]!r}"
            )
    for key in actual:
        if key not in expected:
            drift.append(f"extra decision in projections (not in v7): {key}")

    expected_adr_ids = {
        a.get("id") for a in (v7_state.get("adrs_filed", []) or [])
    }
    expected_adr_ids |= set(v7_state.get("reserved_adrs", []) or [])
    actual_adr_ids = {a.get("id") for a in flat_index.get("adrs", []) or []}

    for adr_id in expected_adr_ids - actual_adr_ids:
        drift.append(f"ADR missing from projections: {adr_id}")
    for adr_id in actual_adr_ids - expected_adr_ids:
        drift.append(f"extra ADR in projections (not in v7): {adr_id}")

    return drift


def _id_from_filename(md_path: Path) -> str:
    """Extract a leading numeric id from an ADR filename (e.g. '0001-x.md')."""
    stem = md_path.stem
    head = stem.split("-", 1)[0]
    return head if head else stem


def restamp_adrs(decisions_dir) -> int:
    """Prepend minimal structured-MADR frontmatter to free-form ADR markdowns.

    For each ``decisions/*.md`` that lacks a ``---`` frontmatter block, prepend
    one (``type: adr``, ``schema_version: "4.0"``, ``id`` from filename,
    ``status``, ``date``, ``plugin_version`` (resolved from plugin.json)). Idempotent: a file that
    already starts with ``---`` is left untouched. Returns the count restamped.
    """
    decisions_dir = Path(decisions_dir)
    if not decisions_dir.is_dir():
        return 0

    count = 0
    today = _now()[:10]
    for md_path in sorted(decisions_dir.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        if text.lstrip("﻿").startswith("---"):
            continue  # already has frontmatter — skip
        metadata = {
            "type": "adr",
            "schema_version": "4.0",
            "id": _id_from_filename(md_path),
            "status": "Accepted",
            "date": today,
            "plugin_version": __version__,
        }
        frontmatter = emit_frontmatter(metadata)
        md_path.write_text(frontmatter + "\n" + text, encoding="utf-8")
        count += 1
    return count


def restamp_docs(docs_dir) -> int:
    """Best-effort: stamp ``plugin_version``/``format_version`` into doc frontmatter.

    For each generated design doc under ``docs/`` (top-level + depth-2,
    excluding the state/decisions/research/versions trees) that HAS YAML
    frontmatter but no ``plugin_version``, add ``plugin_version`` (resolved from plugin.json) +
    ``format_version: "4.0"`` to that frontmatter. A doc WITHOUT frontmatter is
    SKIPPED (injecting frontmatter into a plain doc is too invasive). Returns
    the count touched.
    """
    docs_dir = Path(docs_dir)
    if not docs_dir.is_dir():
        return 0

    excluded = {"_architect_state", "decisions", "research", "versions"}
    touched = 0

    def _candidate_files() -> list[Path]:
        files: list[Path] = []
        for top in sorted(docs_dir.iterdir()):
            if top.is_file() and top.suffix == ".md":
                files.append(top)
            elif top.is_dir() and top.name not in excluded:
                for child in sorted(top.iterdir()):
                    if child.is_file() and child.suffix == ".md":
                        files.append(child)
        return files

    for md_path in _candidate_files():
        text = md_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if not fm:
            continue  # no frontmatter — skip (too invasive to inject)
        if "plugin_version" in fm:
            continue  # already stamped
        fm["plugin_version"] = __version__
        # PRESERVE an existing format_version — it is the doc-FORMAT constant
        # (e.g. "1.0"), NOT the state schema version. Clobbering it to "4.0"
        # silently rewrote every real doc's format_version on /upgrade-project
        # (tiger-panther). Only stamp it when absent.
        fm.setdefault("format_version", "4.0")
        # Replace the existing frontmatter block with the re-emitted one.
        new_fm = emit_frontmatter(fm)
        body = _body_after_frontmatter(text)
        md_path.write_text(new_fm + body, encoding="utf-8")
        touched += 1
    return touched


def _body_after_frontmatter(text: str) -> str:
    """Return the markdown body after a leading ``---``/``---`` block."""
    import re

    stripped = text.lstrip("﻿")
    if not stripped.startswith("---\n"):
        return text
    remainder = stripped[len("---\n"):]
    closing = re.search(r"^---\s*$", remainder, re.MULTILINE)
    if closing is None:
        return text
    return remainder[closing.end():]


def migrate(docs_dir, *, run_audit: bool = True) -> dict[str, Any]:
    """Orchestrate the v3.1 -> 4.0 migration (spec §7.1).

    Steps: detect -> floor/ceiling -> snapshot -> synthesize_events -> write
    events.jsonl into a NEW ``_architect_state/`` dir (temp-and-rename) ->
    replay -> projections_to_disk -> restamp ADRs/docs -> reindex the workflow
    projection's ``current_phase`` via ``phase_v7_to_v8`` -> compare (ABORT
    with the drift list if non-empty, leaving the v7 monolith untouched) ->
    keep the v7 monolith as a ``.migrated`` sidecar -> optionally run ``audit``.

    Returns ``{ok, snapshot, events, drift, audit_exit}``. The backup tarball is
    always kept; ``ok=False`` means the migration was refused/aborted and no v8
    state dir was left behind.
    """
    import os

    docs_dir = Path(docs_dir)

    legacy = detect_legacy(docs_dir)
    if legacy is None:
        return {
            "ok": False,
            "snapshot": None,
            "events": 0,
            "drift": ["no v7 monolith _architect_state.json found"],
            "audit_exit": None,
        }

    v7_state = legacy["state"]
    ok, _reason = migration_floor_ceiling_ok(
        legacy["schema_version"], v7_state.get("plugin_version")
    )
    if not ok:
        return {
            "ok": False,
            "snapshot": None,
            "events": 0,
            "drift": [_reason],
            "audit_exit": None,
        }

    # Snapshot FIRST — never proceed without a backup.
    snapshot = snapshot_v7(docs_dir)

    events = synthesize_events(v7_state)

    # Build the NEW state dir in a temp sibling, then rename into place.
    state_dir = docs_dir / "_architect_state"
    tmp_state_dir = docs_dir / "_architect_state.migrating"
    if tmp_state_dir.exists():
        import shutil

        shutil.rmtree(tmp_state_dir)
    tmp_state_dir.mkdir(parents=True, exist_ok=True)

    log_path = tmp_state_dir / "events.jsonl"
    log_path.touch()
    for ev in events:
        append_event(log_path, ev)

    projections = replay(log_path)

    # Reindex the workflow phase from the v7 .phase (the trajectory's final
    # PhaseAdvanced already set this, but make it explicit + robust for a state
    # whose phase_progress was empty).
    current_v8 = phase_v7_to_v8(v7_state.get("phase", "preflight"))
    projections["workflow"]["current_phase"] = current_v8

    projections_to_disk(tmp_state_dir, projections)

    # Compare BEFORE flipping — abort (and clean up the temp dir) on drift,
    # leaving the v7 monolith untouched.
    drift = compare_v7_vs_v8(v7_state, projections)
    if drift:
        import shutil

        shutil.rmtree(tmp_state_dir, ignore_errors=True)
        return {
            "ok": False,
            "snapshot": snapshot,
            "events": len(events),
            "drift": drift,
            "audit_exit": None,
        }

    # Atomic flip: move the temp state dir into place.
    if state_dir.exists():
        import shutil

        shutil.rmtree(state_dir)
    os.replace(tmp_state_dir, state_dir)

    # Re-stamp ADRs (move/copy the v7 decisions/*.md under the new state dir),
    # then re-stamp generated docs in place.
    _migrate_adr_files(docs_dir, state_dir)
    restamp_adrs(state_dir / "decisions")
    restamp_docs(docs_dir)

    # Keep the v7 monolith as a .migrated sidecar (backup tarball is kept too).
    monolith = docs_dir / "_architect_state.json"
    if monolith.exists():
        os.replace(monolith, docs_dir / "_architect_state.json.migrated")

    audit_exit: int | None = None
    if run_audit:
        audit_exit = _run_post_migration_audit(docs_dir)

    return {
        "ok": True,
        "snapshot": snapshot,
        "events": len(events),
        "drift": [],
        "audit_exit": audit_exit,
    }


def _migrate_adr_files(docs_dir: Path, state_dir: Path) -> None:
    """Copy v7 ``docs/decisions/*.md`` into the v8 ``_architect_state/decisions/``.

    v7 ADR markdowns live in ``decisions_dir`` (default ``docs/decisions``); v8
    keeps them under ``_architect_state/decisions/`` (where reconcile/check_17
    look). Copy any that aren't already present so ``restamp_adrs`` operates on
    the v8 location. ``projections_to_disk`` already created the dir + an
    ``index.json``.
    """
    import shutil

    v7_decisions = docs_dir / "decisions"
    v8_decisions = state_dir / "decisions"
    if not v7_decisions.is_dir():
        return
    v8_decisions.mkdir(parents=True, exist_ok=True)
    for md in sorted(v7_decisions.glob("*.md")):
        target = v8_decisions / md.name
        if not target.exists():
            shutil.copy2(md, target)


def _run_post_migration_audit(docs_dir: Path) -> int:
    """Run the full auditor against the migrated state; return its exit code.

    A non-zero (FATAL/BLOCKING) exit is surfaced to the caller for a possible
    rollback decision; the migrator does NOT auto-delete the new state.
    """
    from architect_brain.auditor import run_all_checks
    from architect_brain.checks import ALL_CHECKS

    state_dir = docs_dir / "_architect_state"
    report = run_all_checks(state_dir, ALL_CHECKS)
    return report.exit_code
