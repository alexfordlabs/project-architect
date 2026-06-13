"""architect-brain CLI entrypoint.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Subcommands wired so far: init, detect, append-event, replay, set-decision,
set-phase, set-substep, record-adr, reserve-adr, record-doc, reconcile-adrs,
check-state.
audit (Wave 5), catalog, generate-configs, generate-diagram, golden-path, ui,
migrate (Wave 6a).
Remaining: snapshot.

Note: reconcile-adrs and check-state are READ/REPAIR operations — they do NOT
emit events, so (unlike the event-emitting commands) they do not use the
``_emit_and_project`` helper.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from architect_brain import __version__
from architect_brain.detect import detect_situation
from architect_brain.projections import empty_projections, projections_to_disk


def _cmd_init(args: argparse.Namespace) -> int:
    """Initialise docs/_architect_state/ for a fresh v8 project."""
    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "events.jsonl").touch()
    projections_to_disk(state_dir, empty_projections())
    print(f"architect-brain: initialised {state_dir}", file=sys.stderr)
    return 0


def _cmd_detect(args: argparse.Namespace) -> int:
    """Situation-router query — fast classification of architect history."""
    docs_dir = Path(args.docs_dir).resolve()
    result = detect_situation(docs_dir)
    print(json.dumps(result, indent=2))
    return 0


def _iso_now() -> str:
    """Current UTC time as ISO-8601 'YYYY-MM-DDTHH:MM:SSZ'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_projections_from_disk(state_dir: Path) -> dict:
    """Read all on-disk projection files back into the in-memory shape."""
    from architect_brain.projections import CONCERN_NAMES, empty_projections

    p = empty_projections()
    for name in CONCERN_NAMES:
        fp = state_dir / f"{name}.json"
        if fp.exists():
            p[name] = json.loads(fp.read_text())
    flat = state_dir / "99-flat-index.json"
    if flat.exists():
        p["_flat_index"] = json.loads(flat.read_text())
    # Restore the elevated ADR ledger too. Without this, every incremental emit
    # reset _decisions_index to empty and re-appended only the current event's
    # ADR — silently dropping all prior ADRs from decisions/index.json (while
    # _flat_index, restored above, kept them). check_30_decisions_index_fresh
    # surfaces that drift; this closes the root cause. The stale regenerated_at
    # read here is harmless — projections_to_disk overwrites it on write.
    dec_index = state_dir / "decisions" / "index.json"
    if dec_index.exists():
        p["_decisions_index"] = json.loads(dec_index.read_text())
    return p


def _emit_and_project(state_dir: Path, event, projections: dict | None = None) -> int:
    """Append ``event`` to the log, apply it to on-disk projections, persist, print ULID.

    Shared tail for every event-emitting subcommand. Behaviour is identical to
    the inline form each handler previously carried: append → read projections
    from disk → apply → write back → ``print(event.id)`` → return 0.

    ``projections`` lets a caller that has ALREADY read the on-disk projections
    (e.g. ``_cmd_set_phase``, which needs ``current_phase`` to build the event)
    pass them in, avoiding a redundant disk read. When ``None`` (the common
    case) the projections are read here.
    """
    from architect_brain.events import append_event
    from architect_brain.projections import apply_event, projections_to_disk

    log_path = state_dir / "events.jsonl"
    append_event(log_path, event)
    if projections is None:
        projections = _read_projections_from_disk(state_dir)
    apply_event(event, projections)
    projections_to_disk(state_dir, projections)
    print(event.id)
    return 0


def _payload_locks(payload: object) -> bool:
    """Whether a LockSet payload LOCKS the design.

    A bare LockSet (no ``locked`` key, or a non-dict payload) defaults to locked
    — mirroring ``projections.apply_event`` — so the gate must fire on it too.
    An explicit ``locked: false`` (the /iterate-design unlock) does not lock.
    """
    if not isinstance(payload, dict):
        return True
    return bool(payload.get("locked", True))


def _latest_audit_result(state_dir: Path) -> str | None:
    """Most recent recorded audit verdict ('clean'/'blocked'), or None if none.

    Reads the workflow projection's ``audits`` ledger and returns the newest
    entry's ``result`` (newest by ``ts``, matching check_19). Used by the
    mechanical LOCK gate; a degraded/unreadable projection returns None (which
    the gate treats as 'unverified' and refuses).
    """
    try:
        projections = _read_projections_from_disk(state_dir)
    except Exception:
        return None
    audits = projections.get("workflow", {}).get("audits", [])
    if not isinstance(audits, list) or not audits:
        return None
    # `audits` is append-ordered (chronological). Prefer the newest ts, but break
    # same-second ties by append position — `_iso_now()` is second-resolution, so
    # two audits in the same second tie and the LAST appended is the real newest.
    dated = [a for a in audits if isinstance(a, dict) and isinstance(a.get("ts"), str)]
    if dated:
        max_ts = max(a["ts"] for a in dated)
        newest = [a for a in dated if a["ts"] == max_ts][-1]
    else:
        newest = audits[-1]
    return newest.get("result") if isinstance(newest, dict) else None


def _cmd_append_event(args: argparse.Namespace) -> int:
    """Append one event + apply it to projections; write everything to disk."""
    from architect_brain.events import EventEnvelope
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    payload = json.loads(args.payload)

    # Mechanical LOCK gate (v8.0.1): a LockSet that LOCKS the design is refused
    # unless the most recent recorded audit verdict is 'clean'. This turns the
    # lock gate from advisory SKILL prose into a block the orchestrator cannot
    # step past. `--force` is the audited escape hatch.
    if args.type == "LockSet" and _payload_locks(payload):
        verdict = _latest_audit_result(state_dir)
        if verdict != "clean":
            if getattr(args, "force", False):
                print(
                    "architect-brain: WARNING --force — locking despite latest "
                    f"audit verdict {verdict!r} (expected 'clean')",
                    file=sys.stderr,
                )
            else:
                reason = (
                    "no pre-lock audit has been recorded"
                    if verdict is None
                    else f"the latest audit verdict is {verdict!r}"
                )
                print(
                    f"architect-brain: refusing to lock — {reason} (expected "
                    "'clean'). Run `architect-brain audit` to a clean verdict, "
                    "or pass --force to override.",
                    file=sys.stderr,
                )
                return 1

    event = EventEnvelope(
        id=new_ulid(),
        ts=_iso_now(),
        by=args.by,
        phase=args.phase,
        type=args.type,
        payload=payload,
    )
    return _emit_and_project(state_dir, event)


def _cmd_replay(args: argparse.Namespace) -> int:
    """Regenerate all projections from events.jsonl."""
    from architect_brain.projections import projections_to_disk, replay

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"
    log_path = state_dir / "events.jsonl"
    projections = replay(log_path)
    projections_to_disk(state_dir, projections)
    print(f"architect-brain: replayed {log_path} → projections", file=sys.stderr)
    return 0


def _parse_decision_value(value_str: str):
    """Parse a CLI string into the right JSON-typed value.

    Tries JSON parsing first (handles true/false/null/int/float/dict/list);
    falls back to raw string. Empty string stays empty string.
    """
    if value_str == "":
        return ""
    try:
        return json.loads(value_str)
    except (json.JSONDecodeError, ValueError):
        return value_str


def _cmd_set_decision(args: argparse.Namespace) -> int:
    """Convenience: emit a DecisionMade event for a single key/value pair."""
    from architect_brain.events import EventEnvelope
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    parsed_value = _parse_decision_value(args.value)
    event = EventEnvelope(
        id=new_ulid(),
        ts=_iso_now(),
        by=args.by,
        phase=args.phase,
        type="DecisionMade",
        payload={"key": args.key, "value": parsed_value},
    )
    return _emit_and_project(state_dir, event)


def _cmd_set_phase(args: argparse.Namespace) -> int:
    """Convenience: emit a PhaseAdvanced event for transitioning into args.phase."""
    from architect_brain.events import EventEnvelope
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    # set-phase is the outlier: it must read the workflow projection BEFORE
    # building the event (the event's ``from`` field is the current phase).
    # Pass the already-read projections into the shared tail to avoid a
    # redundant disk read.
    projections = _read_projections_from_disk(state_dir)
    current_phase = projections.get("workflow", {}).get("current_phase")

    event = EventEnvelope(
        id=new_ulid(),
        ts=_iso_now(),
        by=args.by,
        phase=None,
        type="PhaseAdvanced",
        payload={"from": current_phase, "to": args.phase},
    )
    return _emit_and_project(state_dir, event, projections=projections)


def _cmd_set_substep(args: argparse.Namespace) -> int:
    """Convenience: emit a SubstepRecorded event."""
    from architect_brain.events import EventEnvelope
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    event = EventEnvelope(
        id=new_ulid(),
        ts=_iso_now(),
        by=args.by,
        phase=args.phase,
        type="SubstepRecorded",
        payload={
            "phase": args.phase,
            "substep": args.substep,
            "status": args.status,
        },
    )
    return _emit_and_project(state_dir, event)


def _cmd_record_adr(args: argparse.Namespace) -> int:
    """Convenience: emit an ADRFiled event."""
    from architect_brain.events import EventEnvelope
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    payload = {
        "id": args.id,
        "title": args.title,
        "status": args.status,
    }
    if args.supersedes:
        payload["supersedes"] = list(args.supersedes)

    event = EventEnvelope(
        id=new_ulid(),
        ts=_iso_now(),
        by=args.by,
        phase=args.phase,
        type="ADRFiled",
        payload=payload,
    )
    return _emit_and_project(state_dir, event)


def _cmd_reserve_adr(args: argparse.Namespace) -> int:
    """Convenience: emit an ADRFiled event with status='Reserved' (placeholder)."""
    from architect_brain.events import EventEnvelope
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    title = args.title if args.title else f"Reserved ADR slot for {args.id}"
    payload = {
        "id": args.id,
        "title": title,
        "status": "Reserved",
    }

    event = EventEnvelope(
        id=new_ulid(),
        ts=_iso_now(),
        by=args.by,
        phase=args.phase,
        type="ADRFiled",
        payload=payload,
    )
    return _emit_and_project(state_dir, event)


def _cmd_record_doc(args: argparse.Namespace) -> int:
    """Convenience: emit a DocGenerated event with SHA-256 content_hash."""
    import hashlib

    from architect_brain.events import EventEnvelope
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    doc_path = Path(args.path)
    if not doc_path.exists():
        print(f"architect-brain: file not found: {doc_path}", file=sys.stderr)
        return 1

    content = doc_path.read_bytes()
    content_hash = hashlib.sha256(content).hexdigest()

    event = EventEnvelope(
        id=new_ulid(),
        ts=_iso_now(),
        by=args.by,
        phase=args.phase,
        type="DocGenerated",
        payload={
            "name": args.name,
            "path": str(doc_path),
            "content_hash": content_hash,
        },
    )
    return _emit_and_project(state_dir, event)


def _schemas_dir() -> Path:
    """Resolve the references/schemas/ directory relative to this module.

    ``__main__.py`` lives at ``lib/architect_brain/__main__.py`` so
    ``parents[2]`` is ``skills/project-architect/`` — the schemas then live
    under ``references/schemas/``. Verified against the on-disk layout.
    """
    return Path(__file__).resolve().parents[2] / "references" / "schemas"


def _default_catalog_path() -> Path:
    """references/catalog.json relative to this module (parents[2] = skills/project-architect/)."""
    return Path(__file__).resolve().parents[2] / "references" / "catalog.json"


def _default_golden_paths_path() -> Path:
    """references/golden-paths.json relative to this module."""
    return Path(__file__).resolve().parents[2] / "references" / "golden-paths.json"


def _cmd_reconcile_adrs(args: argparse.Namespace) -> int:
    """Rebuild decisions/index.json from on-disk ADR markdown files.

    The on-disk ADR markdown files (the authoritative, human-edited record)
    are the source of truth here; this is the recovery path for when
    events.jsonl has drifted from disk reality. READ/REPAIR only — no events
    emitted, so this does NOT use ``_emit_and_project``.
    """
    from architect_brain.adr import parse_frontmatter

    docs_dir = Path(args.docs_dir).resolve()
    decisions_dir = docs_dir / "_architect_state" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    adrs: list[dict] = []
    for md_path in sorted(decisions_dir.glob("*.md")):
        fm = parse_frontmatter(md_path.read_text(encoding="utf-8"))
        if not fm or "id" not in fm:
            continue  # skip files without valid ADR frontmatter
        adrs.append({
            "id": fm["id"],
            "title": fm.get("title", ""),
            "status": fm.get("status", "Proposed"),
            "date": fm.get("date", ""),
            "phase": fm.get("phase"),
            "supersedes": fm.get("supersedes", []),
            "superseded_by": fm.get("superseded_by", []),
        })
    adrs.sort(key=lambda a: a["id"])

    index = {
        "schema_version": "4.0",
        "regenerated_at": _iso_now(),
        "adrs": adrs,
    }
    (decisions_dir / "index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"architect-brain: reconciled {len(adrs)} ADRs into decisions/index.json",
        file=sys.stderr,
    )
    return 0


def _cmd_check_state(args: argparse.Namespace) -> int:
    """Validate every projection file against its JSON Schema.

    Loads each concern projection (docs/_architect_state/<concern>.json) and
    its Wave-2.9 schema (references/schemas/state-v4-<concern-kebab>.json),
    runs ``validate_schema``, and reports any errors prefixed with the concern
    name. Standalone operator command + the engine behind Wave 5's check_29.
    READ-only — no events emitted.

    Returns 0 if all projections validate, 1 if any error is found.
    """
    from architect_brain.projections import CONCERN_NAMES
    from architect_brain.validator import validate_schema

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"
    schemas_dir = _schemas_dir()

    all_errors: list[str] = []
    checked = 0
    for concern in CONCERN_NAMES:
        proj_path = state_dir / f"{concern}.json"
        schema_path = schemas_dir / f"state-v4-{concern.replace('_', '-')}.json"
        if not proj_path.exists() or not schema_path.exists():
            continue
        projection = json.loads(proj_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        checked += 1
        for err in validate_schema(projection, schema):
            all_errors.append(f"{concern}: {err}")

    if all_errors:
        for err in all_errors:
            print(err)
        return 1
    print(f"architect-brain: all {checked} projections valid")
    return 0


def _load_flat_index(state_dir: Path) -> dict:
    """Read 99-flat-index.json, or an empty flat index if absent."""
    flat = state_dir / "99-flat-index.json"
    if flat.exists():
        return json.loads(flat.read_text(encoding="utf-8"))
    return {"schema_version": "4.0", "decisions": {}, "adrs": []}


def _cmd_catalog_list(args: argparse.Namespace) -> int:
    """Print applicable documents in topological order (one per line)."""
    from architect_brain.catalog import filter_applicable, load_catalog, topo_sort

    catalog_path = Path(args.catalog) if args.catalog else _default_catalog_path()
    catalog = load_catalog(catalog_path)

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"
    flat_index = _load_flat_index(state_dir)

    applicable = filter_applicable(catalog, flat_index)
    order = topo_sort(applicable)
    if args.phase:
        order = [n for n in order if applicable[n].get("phase") == args.phase]
    for name in order:
        print(name)
    return 0


def _cmd_catalog_cycle(args: argparse.Namespace) -> int:
    """Detect dependency cycles across ALL catalog documents (ignores conditions)."""
    from architect_brain.catalog import detect_cycles, load_catalog

    catalog_path = Path(args.catalog) if args.catalog else _default_catalog_path()
    catalog = load_catalog(catalog_path)
    cycle = detect_cycles(catalog.get("documents", {}))
    if cycle:
        print("cycle detected: " + " -> ".join(cycle))
        return 1
    print("no cycles in catalog")
    return 0


def _cmd_golden_path_list(args: argparse.Namespace) -> int:
    """List the available Golden Paths (one `<id>\\t<label>` per line).

    An expired path (its ``valid_through`` has passed) is annotated so the
    orchestrator's menu warns the user the pre-filled stack snapshot is stale
    and version pins must be re-resolved, not trusted.
    """
    from architect_brain.golden_paths import list_paths, load_golden_paths

    gp_path = Path(args.golden_paths) if args.golden_paths else _default_golden_paths_path()
    gp = load_golden_paths(gp_path)
    for row in list_paths(gp):
        suffix = (
            f"\t[EXPIRED {row['valid_through']} — re-verify stack + versions]"
            if row["expired"]
            else ""
        )
        print(f"{row['id']}\t{row['label']}{suffix}")
    return 0


def _cmd_golden_path_apply(args: argparse.Namespace) -> int:
    """Apply a Golden Path: emit GoldenPathApplied + one DecisionMade per decision."""
    from architect_brain.events import EventEnvelope
    from architect_brain.golden_paths import GoldenPathError, decisions_for, load_golden_paths
    from architect_brain.ulid import new_ulid

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"
    gp_path = Path(args.golden_paths) if args.golden_paths else _default_golden_paths_path()
    gp = load_golden_paths(gp_path)

    try:
        decisions = decisions_for(args.id, gp)
    except GoldenPathError as exc:
        print(f"architect-brain: {exc}", file=sys.stderr)
        return 1

    applied = EventEnvelope(
        id=new_ulid(), ts=_iso_now(), by=args.by, phase=args.phase,
        type="GoldenPathApplied",
        payload={"path_id": args.id, "decision_count": len(decisions)},
    )
    _emit_and_project(state_dir, applied)

    for key, value in decisions.items():
        event = EventEnvelope(
            id=new_ulid(), ts=_iso_now(), by=args.by, phase=args.phase,
            type="DecisionMade", payload={"key": key, "value": value},
        )
        _emit_and_project(state_dir, event)

    print(
        f"architect-brain: applied golden path '{args.id}' ({len(decisions)} decisions)",
        file=sys.stderr,
    )
    return 0


def _cmd_generate_configs(args: argparse.Namespace) -> int:
    """Emit every config-as-code file applicable to the current state."""
    from architect_brain.configs import (
        dockerfile_language,
        gen_biome_json,
        gen_docker_compose,
        gen_dockerfile,
        gen_package_json,
        gen_pyproject,
        gen_tsconfig,
        gen_turbo_json,
        js_stack,
    )

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"
    flat_index = _load_flat_index(state_dir)
    dec = flat_index.get("decisions", {})

    out_dir = Path(args.out).resolve() if args.out else docs_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []

    def emit(fname: str, content: str) -> None:
        (out_dir / fname).write_text(content, encoding="utf-8")
        written.append(fname)

    # Emission conditions are the SHARED predicates in configs.py (also used by
    # audit check 36), so what we emit and what pins are owed cannot diverge.
    if js_stack(flat_index):
        # package.json's build script runs tsc; tsconfig ships with it always.
        emit("package.json", gen_package_json(flat_index))
        emit("biome.json", gen_biome_json(flat_index))
        emit("tsconfig.json", gen_tsconfig(flat_index))
    langs = {dec.get("stack.frontend.language"), dec.get("stack.backend.language")}
    if "python" in langs:
        emit("pyproject.toml", gen_pyproject(flat_index))
    if dockerfile_language(flat_index) is not None:
        # Only for runtimes we have an honest base image for — a rust/go stack
        # no longer receives a silent node Dockerfile.
        emit("Dockerfile", gen_dockerfile(flat_index))
    if dec.get("stack.database.engine") or dec.get("stack.cache.engine"):
        emit("docker-compose.yml", gen_docker_compose(flat_index))
    if dec.get("tooling.monorepo"):
        emit("turbo.json", gen_turbo_json(flat_index))

    for fname in sorted(written):
        print(fname)
    return 0


def _cmd_generate_diagram(args: argparse.Namespace) -> int:
    """Write a Mermaid C4 diagram (context|container|component) to stdout."""
    from architect_brain.diagrams import (
        gen_c4_component,
        gen_c4_container,
        gen_c4_context,
    )

    docs_dir = Path(args.docs_dir).resolve()
    flat_index = _load_flat_index(docs_dir / "_architect_state")
    generators = {
        "context": gen_c4_context,
        "container": gen_c4_container,
        "component": gen_c4_component,
    }
    sys.stdout.write(generators[args.type](flat_index))
    return 0


def _cmd_ui_banner(args: argparse.Namespace) -> int:
    """Write the project-architect banner to stdout."""
    from architect_brain.ui import banner

    sys.stdout.write(banner())
    return 0


def _cmd_ui_phase_bar(args: argparse.Namespace) -> int:
    """Write the phase-ladder row for a phase key (empty for banner-only/unknown keys)."""
    from architect_brain.ui import phase_bar

    sys.stdout.write(phase_bar(args.key))
    return 0


def _cmd_ui_progress(args: argparse.Namespace) -> int:
    """Write a progress-bar line to stdout."""
    from architect_brain.ui import progress

    sys.stdout.write(progress(args.current, args.total, args.label))
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    """Run the 35-check auditor, print results + verdict, record the run.

    A FULL run (no ``--only``) emits an ``AuditCompleted`` event so
    ``workflow.json:audits[]`` records it (check_19 reads that); ``--only`` runs
    are spot-checks and do not emit. Exit code is 1 when any failure blocks LOCK
    (FATAL always; BLOCKING unless ``--ack=<reason>`` is given), else 0.
    """
    from architect_brain.auditor import run_all_checks
    from architect_brain.checks import ALL_CHECKS

    docs_dir = Path(args.docs_dir).resolve()
    state_dir = docs_dir / "_architect_state"

    names = {getattr(c, "CHECK_ID", "??"): getattr(c, "NAME", "") for c in ALL_CHECKS}
    report = run_all_checks(state_dir, ALL_CHECKS, only=args.only, ack=args.ack)

    for r in report.results:
        glyph = "✓" if r.passed else "✗"
        print(f"  {glyph} {r.check_id} {names.get(r.check_id, ''):<26} {r.severity:<8} {r.summary}")
        if args.verbose and not r.passed:
            for finding in r.findings:
                loc = f" [{finding.location}]" if finding.location else ""
                print(f"        - {finding.message}{loc}")

    passed_count = sum(1 for r in report.results if r.passed)
    failed_count = len(report.results) - passed_count

    if report.blocking:
        print(f"Verdict: BLOCKED — {len(report.blocking)} blocking failure(s) "
              f"(worst severity: {report.worst})")
    elif report.worst:
        print(f"Verdict: PASS with non-blocking findings (worst severity: {report.worst})")
    else:
        print(f"Verdict: CLEAN — all {len(report.results)} checks passed")

    # Record the run on a full audit (spot-checks via --only don't gate LOCK).
    # Emits + re-projects via the shared incremental path (which now correctly
    # preserves the ADR ledger), so workflow.audits[] grows and the resume
    # invariant (replay == disk) is maintained for the next audit.
    if args.only is None:
        from architect_brain.events import EventEnvelope, append_event
        from architect_brain.projections import apply_event, projections_to_disk
        from architect_brain.ulid import new_ulid

        audit_payload = {
            "result": "blocked" if report.blocking else "clean",
            "checks_passed": passed_count,
            "checks_failed": failed_count,
        }
        # Record the worst FAILED severity so two same-count audits are
        # distinguishable in the ledger: "3 failed / clean" (all WARNING/INFO)
        # vs "3 failed / blocked" (a BLOCKING/FATAL among them). None when all pass.
        if report.worst is not None:
            audit_payload["worst_severity"] = report.worst
        # Persist the --ack reason so an acked-clean is distinguishable from a
        # genuinely-clean audit in the ledger (the override's accountability record).
        if args.ack:
            audit_payload["ack"] = args.ack
        event = EventEnvelope(
            id=new_ulid(), ts=_iso_now(), by="orchestrator", phase=None,
            type="AuditCompleted",
            payload=audit_payload,
        )
        append_event(state_dir / "events.jsonl", event)
        projections = _read_projections_from_disk(state_dir)
        apply_event(event, projections)
        projections_to_disk(state_dir, projections)
        print(
            f"architect-brain: recorded AuditCompleted "
            f"({event.payload['result']}, {passed_count} passed / {failed_count} failed)",
            file=sys.stderr,
        )

    return report.exit_code


def _cmd_migrate(args: argparse.Namespace) -> int:
    """Migrate a v7 monolith ``docs/_architect_state.json`` to v8 state.

    Prints a step-by-step progress summary to stderr and the verdict to stdout.
    Returns 0 on a clean migration (and a clean post-audit, unless ``--no-audit``),
    1 on a refusal (floor/ceiling), a drift-abort, or a blocking post-audit.
    ``--from`` is advisory (``detect`` reads the real schema_version);
    ``--no-audit`` skips the final audit step.
    """
    from architect_brain.migration import detect_legacy, migrate

    docs_dir = Path(args.docs_dir).resolve()

    legacy = detect_legacy(docs_dir)
    if legacy is None:
        print(
            f"architect-brain: no v7 _architect_state.json found under {docs_dir}",
            file=sys.stderr,
        )
        print("migrate: FAILED — nothing to migrate")
        return 1

    print(
        f"architect-brain: detected v7 monolith "
        f"(schema {legacy['schema_version']}, "
        f"plugin {legacy['state'].get('plugin_version')})",
        file=sys.stderr,
    )
    print("architect-brain: snapshotting + synthesizing events ...", file=sys.stderr)

    result = migrate(docs_dir, run_audit=not args.no_audit)

    if result["snapshot"] is not None:
        print(f"architect-brain: backup -> {result['snapshot']}", file=sys.stderr)

    if not result["ok"]:
        for line in result["drift"]:
            print(f"  drift: {line}", file=sys.stderr)
        print("migrate: FAILED — see drift/refusal above")
        return 1

    print(
        f"architect-brain: migrated {result['events']} event(s) -> "
        f"_architect_state/",
        file=sys.stderr,
    )
    audit_exit = result["audit_exit"]
    if audit_exit is not None and audit_exit != 0:
        print(
            "migrate: COMPLETE with a BLOCKING post-migration audit "
            "(state preserved; review before LOCK)"
        )
        return 1

    print(f"migrate: COMPLETE — {result['events']} events, backup kept")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="architect-brain",
        description="project-architect v8 brain — declarative event-sourced state, audit, and tooling.",
    )
    parser.add_argument("--version", action="version", version=f"architect-brain {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=False)

    p_init = sub.add_parser("init", help="initialise docs/_architect_state/")
    p_init.add_argument("--docs-dir", default="docs", help="path to docs/ directory (default: ./docs)")
    p_init.set_defaults(func=_cmd_init)

    p_detect = sub.add_parser("detect", help="situation-router query")
    p_detect.add_argument("--docs-dir", default="docs", help="path to docs/ directory")
    p_detect.set_defaults(func=_cmd_detect)

    p_append = sub.add_parser("append-event", help="append + apply one event to the log")
    p_append.add_argument("--docs-dir", default="docs")
    p_append.add_argument("--type", required=True, help="event type, e.g., DecisionMade")
    p_append.add_argument("--phase", default=None)
    p_append.add_argument("--by", default="orchestrator")
    p_append.add_argument("--payload", required=True, help="event payload as JSON")
    p_append.add_argument(
        "--force",
        action="store_true",
        help="override the LockSet audit gate (lock despite a non-clean audit)",
    )
    p_append.set_defaults(func=_cmd_append_event)

    p_replay = sub.add_parser("replay", help="regenerate projections from events.jsonl")
    p_replay.add_argument("--docs-dir", default="docs")
    p_replay.set_defaults(func=_cmd_replay)

    p_setdec = sub.add_parser("set-decision", help="emit a DecisionMade event for a single key/value pair")
    p_setdec.add_argument("--docs-dir", default="docs")
    p_setdec.add_argument("--phase", default=None)
    p_setdec.add_argument("--by", default="orchestrator")
    p_setdec.add_argument("key", help="dotted-path decision key (e.g., stack.frontend.framework)")
    p_setdec.add_argument("value", help="value (JSON-parsed if possible; else string)")
    p_setdec.set_defaults(func=_cmd_set_decision)

    p_setphase = sub.add_parser("set-phase", help="emit a PhaseAdvanced event (transition into a new phase)")
    p_setphase.add_argument("--docs-dir", default="docs")
    p_setphase.add_argument("--by", default="orchestrator")
    p_setphase.add_argument("phase", help="phase to advance into (e.g., 'architecture')")
    p_setphase.set_defaults(func=_cmd_set_phase)

    p_setsub = sub.add_parser("set-substep", help="emit a SubstepRecorded event")
    p_setsub.add_argument("--docs-dir", default="docs")
    p_setsub.add_argument("--by", default="orchestrator")
    p_setsub.add_argument("--status", default="in_progress", help="substep status (default: in_progress)")
    p_setsub.add_argument("phase", help="parent phase (e.g., 'architecture')")
    p_setsub.add_argument("substep", help="substep identifier (e.g., 'boundaries')")
    p_setsub.set_defaults(func=_cmd_set_substep)

    p_recadr = sub.add_parser("record-adr", help="emit an ADRFiled event")
    p_recadr.add_argument("--docs-dir", default="docs")
    p_recadr.add_argument("--phase", default=None)
    p_recadr.add_argument("--by", default="orchestrator")
    p_recadr.add_argument("--supersedes", action="append", default=[],
                          help="ID of ADR this supersedes; may be repeated")
    p_recadr.add_argument("id", help="ADR identifier (e.g., '0007')")
    p_recadr.add_argument("title", help="ADR title (short noun phrase)")
    p_recadr.add_argument("status", help="ADR status: Proposed | Accepted | Deprecated | Superseded | Rejected")
    p_recadr.set_defaults(func=_cmd_record_adr)

    p_reserve = sub.add_parser("reserve-adr", help="emit a Reserved-status ADR placeholder")
    p_reserve.add_argument("--docs-dir", default="docs")
    p_reserve.add_argument("--phase", default=None)
    p_reserve.add_argument("--by", default="orchestrator")
    p_reserve.add_argument("--title", default=None,
                           help="optional human-readable title (default: 'Reserved ADR slot for <id>')")
    p_reserve.add_argument("id", help="ADR identifier (e.g., '0007')")
    p_reserve.set_defaults(func=_cmd_reserve_adr)

    p_recdoc = sub.add_parser("record-doc", help="emit a DocGenerated event with SHA-256 content_hash")
    p_recdoc.add_argument("--docs-dir", default="docs")
    p_recdoc.add_argument("--phase", default=None)
    p_recdoc.add_argument("--by", default="orchestrator")
    p_recdoc.add_argument("name", help="logical doc name (e.g., 'PROJECT_OVERVIEW')")
    p_recdoc.add_argument("path", help="filesystem path to the markdown file")
    p_recdoc.set_defaults(func=_cmd_record_doc)

    p_reconcile = sub.add_parser(
        "reconcile-adrs", help="rebuild decisions/index.json from on-disk ADR files"
    )
    p_reconcile.add_argument("--docs-dir", default="docs")
    p_reconcile.set_defaults(func=_cmd_reconcile_adrs)

    p_check = sub.add_parser(
        "check-state", help="validate every projection against its JSON Schema"
    )
    p_check.add_argument("--docs-dir", default="docs")
    p_check.set_defaults(func=_cmd_check_state)

    p_catalog = sub.add_parser("catalog", help="document catalog queries")
    catalog_sub = p_catalog.add_subparsers(dest="catalog_cmd", required=True)

    p_clist = catalog_sub.add_parser("list", help="applicable docs in topo order")
    p_clist.add_argument("--docs-dir", default="docs")
    p_clist.add_argument("--catalog", default=None, help="override catalog.json path")
    p_clist.add_argument("--phase", default=None, help="filter to one phase")
    p_clist.set_defaults(func=_cmd_catalog_list)

    p_ccycle = catalog_sub.add_parser("cycle", help="detect dependency cycles")
    p_ccycle.add_argument("--catalog", default=None, help="override catalog.json path")
    p_ccycle.set_defaults(func=_cmd_catalog_cycle)

    p_gencfg = sub.add_parser("generate-configs", help="emit deterministic config-as-code files")
    p_gencfg.add_argument("--docs-dir", default="docs")
    p_gencfg.add_argument("--out", default=None, help="output dir (default: docs dir's parent)")
    p_gencfg.set_defaults(func=_cmd_generate_configs)

    p_gendiag = sub.add_parser("generate-diagram", help="emit a Mermaid C4 diagram to stdout")
    p_gendiag.add_argument("type", choices=["context", "container", "component"])
    p_gendiag.add_argument("--docs-dir", default="docs")
    p_gendiag.set_defaults(func=_cmd_generate_diagram)

    p_audit = sub.add_parser("audit", help="run the 36-check auditor + record an AuditCompleted event")
    p_audit.add_argument("--docs-dir", default="docs")
    p_audit.add_argument("--only", default=None, help="run only the check with this CHECK_ID (e.g. 31)")
    p_audit.add_argument("--ack", default=None,
                         help="reason to downgrade BLOCKING failures so they don't block LOCK (FATAL still blocks)")
    p_audit.add_argument("--verbose", action="store_true", help="print each finding under failing checks")
    p_audit.set_defaults(func=_cmd_audit)

    p_migrate = sub.add_parser(
        "migrate", help="migrate a v7 monolith _architect_state.json to v8 state"
    )
    p_migrate.add_argument("--docs-dir", default="docs")
    p_migrate.add_argument("--from", dest="from_version", default=None,
                           help="advisory source version (detect reads the real one)")
    p_migrate.add_argument("--no-audit", action="store_true",
                           help="skip the final post-migration audit step")
    p_migrate.set_defaults(func=_cmd_migrate)

    p_ui = sub.add_parser("ui", help="run-UI rendering (banner / phase-bar / progress)")
    ui_sub = p_ui.add_subparsers(dest="ui_cmd", required=True)

    p_ui_banner = ui_sub.add_parser("banner", help="print the wordmark banner")
    p_ui_banner.set_defaults(func=_cmd_ui_banner)

    p_ui_phasebar = ui_sub.add_parser("phase-bar", help="print the ladder row for a phase key")
    p_ui_phasebar.add_argument("key", help="phase key (e.g. architecture, stack, complete)")
    p_ui_phasebar.set_defaults(func=_cmd_ui_phase_bar)

    p_ui_progress = ui_sub.add_parser("progress", help="print a progress-bar line")
    p_ui_progress.add_argument("current", type=int)
    p_ui_progress.add_argument("total", type=int)
    p_ui_progress.add_argument("label", nargs="?", default="")
    p_ui_progress.set_defaults(func=_cmd_ui_progress)

    p_gp = sub.add_parser("golden-path", help="Golden Path queries (list / apply)")
    gp_sub = p_gp.add_subparsers(dest="golden_path_cmd", required=True)

    p_gp_list = gp_sub.add_parser("list", help="list available Golden Paths")
    p_gp_list.add_argument("--golden-paths", default=None, help="override golden-paths.json path")
    p_gp_list.set_defaults(func=_cmd_golden_path_list)

    p_gp_apply = gp_sub.add_parser("apply", help="apply a Golden Path's decisions")
    p_gp_apply.add_argument("id", help="golden path id (e.g. modern_saas_2026)")
    p_gp_apply.add_argument("--docs-dir", default="docs")
    p_gp_apply.add_argument("--golden-paths", default=None, help="override golden-paths.json path")
    p_gp_apply.add_argument("--phase", default=None)
    p_gp_apply.add_argument("--by", default="orchestrator")
    p_gp_apply.set_defaults(func=_cmd_golden_path_apply)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0
    if hasattr(args, "func"):
        try:
            return args.func(args)
        except Exception as exc:  # noqa: BLE001 — CLI boundary: a degraded state (corrupt
            # events.jsonl / projection, unreadable file) must surface as a clean one-line
            # message + non-zero exit, never a raw traceback in the user's transcript. The
            # offending data is check_05 (json_valid) / check_29 (state_schema_valid)'s
            # verdict to report; this just keeps the CLI from crashing on it. SystemExit /
            # KeyboardInterrupt are BaseException, not Exception, so they propagate normally.
            print(f"architect-brain: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
    print(f"architect-brain: subcommand '{args.cmd}' not yet implemented", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
