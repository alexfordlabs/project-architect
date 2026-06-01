<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# State Schema Reference

Canonical runtime reference for the **event-sourced, multi-file state** that lives under `docs/_architect_state/`. The orchestrator reads this file to know what the state directory contains, how it is materialised, what invariant must hold, and how a pre-v8 monolith is migrated forward. Self-contained: no need to consult the design spec.

In v8 there is **no monolithic `docs/_architect_state.json`**. State is an append-only event log plus derived projections, all mutated exclusively through the `architect-brain` binary (`${CLAUDE_PLUGIN_ROOT}/bin/architect-brain`, a thin shim over `python -m architect_brain`). **Never hand-edit any state file** — every mutation flows through an event, because the replay invariant (below) depends on the log being the sole source of truth.

---

## The directory: `docs/_architect_state/`

State is a **directory** in the generated project's root, committed at every phase boundary. Its layout:

| Path | Role |
|---|---|
| `docs/_architect_state/events.jsonl` | **Authoritative ground truth.** Append-only event log — one JSON event per line. Everything else is derived from this. |
| `docs/_architect_state/schema_version` | One-line probe file containing the literal `4.0\n`. The fastest version detection (`detect` reads this first). |
| `docs/_architect_state/<concern>.json` | 11 per-concern materialised projections (see "Concerns" below), derived by `replay`. |
| `docs/_architect_state/99-flat-index.json` | The flat aggregate projection: `{schema_version, decisions:{dotted-key:value}, adrs:[…]}`. The fast-query + `reverse-engineer`-interop view. |
| `docs/_architect_state/decisions/index.json` | The dedicated ADR-ledger projection: `{schema_version, regenerated_at, adrs:[…]}`. |
| `docs/_architect_state/decisions/*.md` | The ADR markdown files (MADR 4 + structured-MADR frontmatter). |
| `docs/_architect_state/.lock` | Lockfile. Single-writer guard. Held throughout a session; not committed. |

All paths are relative to the **generated project's** root, not the plugin. The directory is created by `architect-brain init` and **is never deleted by the orchestrator** — it is the canonical cross-session entry point and must persist past LOCK for re-invocations and for `/iterate-design`.

---

## Why event-sourced (the model in one paragraph)

The v7 monolith stored *current state* as one mutable JSON blob; every save rewrote it, and provenance (who decided what, when, in which phase) was reconstructed after the fact — which is exactly how a run could back-fill ADRs with fabricated timestamps. v8 inverts this: the log of **what happened** is authoritative, and the *current state* is a pure function of that log. Every decision, ADR, generated doc, phase advance, audit, golden-path application, and lock is one immutable, timestamped event appended to `events.jsonl`. The per-concern projections, the flat index, and the ADR ledger are all **derived** by folding the events from empty. This makes provenance free (the event's `ts`/`by`/`phase` ARE the record), makes resume trivial (re-read the log), and makes drift detectable (re-derive and compare).

---

## The event log: `events.jsonl`

Each line is one event envelope:

```jsonc
{
  "id":      "01J...",          // ULID — 26-char Crockford-base32, sortable, unique
  "ts":      "2026-05-27T15:23:11Z", // ISO-8601 UTC. Stamped by the binary's own clock — NEVER a typed literal.
  "by":      "orchestrator",    // "user" | "orchestrator" | "<agent-name>" | "migrator"
  "phase":   "stack",           // the v8 ladder key active when the event fired, or null for phase-less events
  "type":    "DecisionMade",    // one of the 12 event types below
  "payload": { "key": "stack.database.engine", "value": "postgresql" }
}
```

Events are appended with single-line writes (≤ PIPE_BUF, atomic at the OS level, so concurrent appends don't interleave). Blank lines are skipped defensively. The log is append-only — events are never edited or removed in place. A correction (e.g. superseding an ADR, unlocking a design) is itself a **new** event.

### Event taxonomy (12 types)

| Type | Emitted by | Payload (representative) | Effect on projections |
|---|---|---|---|
| `DecisionMade` | `set-decision`, `golden-path apply` | `{key, value}` (a flat dotted key) | Sets `decisions[key]` in the routed concern AND in `99-flat-index.json`. |
| `ADRFiled` | `record-adr`, `reserve-adr` | `{id, title, status, supersedes?}` (date+phase come from the event's `ts`/`phase`) | Appends `{id,title,status,date,phase,supersedes,superseded_by}` to both `99-flat-index.json.adrs[]` and `decisions/index.json.adrs[]`. |
| `ADRSuperseded` | `append-event --type ADRSuperseded` | `{id, by}` | Marks the matching ADR `status: "Superseded"` and appends `by` to its `superseded_by[]` in both ledgers. (`record-adr --supersedes` records a `supersedes` field on the NEW `ADRFiled` event but does NOT itself emit `ADRSuperseded` or mark the prior ADR; `reconcile-adrs` emits no events — it rebuilds `decisions/index.json` from on-disk frontmatter.) |
| `DocGenerated` | `record-doc` | `{name, path, content_hash}` (SHA-256, for drift detection) | Appends to `docs.completed[]`. |
| `PhaseAdvanced` | `set-phase` | `{from, to}` (both v8 ladder keys; `from` is null on the first advance) | Sets `workflow.current_phase = to`; clears `workflow.substep`. |
| `PhaseSkipped` | (skip-path routing) | `{phase, reason}` | Informational — preserved in the log; downstream events do the real work. |
| `SubstepRecorded` | `set-substep` | `{phase, substep, status}` | Sets `workflow.substep`. |
| `AuditCompleted` | `audit` (a full run) | `{result, checks_passed, checks_failed}` | Appends to `workflow.audits[]`. `audit_freshness` (19) reads the latest entry. |
| `ResearchRefAdded` | `append-event --type ResearchRefAdded` | `{phase, topic, file, dispatched_at}` | Informational — preserved in the log; the doc-author dispatch reads the referenced files. |
| `GoldenPathApplied` | `golden-path apply` (alongside the per-decision `DecisionMade` events) | `{id}` | Informational — the actual pre-fills are the accompanying `DecisionMade` events. |
| `LockSet` | `append-event --type LockSet` (Lock phase + `/iterate-design`) | `{locked, version?, locked_at?}` | Sets `workflow.locked` from `payload.locked` (default `true`); stamps `workflow.locked_at` from the event `ts` on a lock (or `payload.locked_at` if given explicitly; `null` on an unlock); sets `workflow.version` if present. |
| `Upgraded` | `migrate` | `{from_schema, to_schema, from_plugin}` | Informational — the migrator's provenance marker; the synthesized `DecisionMade`/`ADRFiled`/… events carry the actual state. |

An event with an unknown `type` is rejected at construction time — the allowed set is closed.

---

## Concerns (the 11 per-concern projections)

Each `DecisionMade` is routed to exactly one **concern** projection by the head of its dotted key (the segment before the first `.`), so each concern file holds the decisions it owns. The 11 concerns and their routing:

| Concern file | Receives keys with head | Example keys |
|---|---|---|
| `identity.json` | `identity`, `project`, `team`, `scm` | `project.type`, `project.name`, `scm.host` |
| `vision.json` | `vision`, `requirements`, `constraints`, `scale` *(also the catch-all)* | `constraints.gdpr`, `scale`, `requirements.*` |
| `architecture.json` | `architecture` | `architecture.style`, `architecture.boundaries.count`, `architecture.data_flow` |
| `stack.json` | `stack`, `frontend`, `backend`, `database`, `hosting` | `stack.backend.language`, `stack.database.engine` |
| `cost.json` | `cost`, `monetization` | `cost.*`, `monetization.*` |
| `ai_agent.json` | `ai`, `agent` | `ai.provider`, `agent.autonomy` |
| `api_contract.json` | `api`, `webhooks` | `api.protocol`, `webhooks.outbound` |
| `docs.json` | `docs` | `docs.surface`, `docs.tooling` — plus `completed[]` (the generated-doc ledger from `DocGenerated`) |
| `workflow.json` | `workflow` — plus the run-pointer fields | `workflow.branching`; `current_phase`, `substep`, `locked`, `locked_at`, `version`, `audits[]` |
| `tooling.json` | `deployment`, `tooling`, `ci_cd` | `deployment.orchestrator`, `tooling.*` |
| `handoff.json` | `handoff` | `handoff.*` |

Each per-concern file is `{schema_version: "4.0", concern: "<name>", decisions: {…}}` (plus the extra run-pointer fields on `workflow.json`, and `completed[]` on `docs.json`). A key whose head matches no entry routes to `vision` (the catch-all). The canonical key vocabulary lives in [`decision-keys.md`](./decision-keys.md) — every producer and consumer MUST use those exact dotted keys; `99-flat-index.json` is the denormalised union of all concerns' decisions.

### The `workflow` projection (the run pointer)

`workflow.json` is the projection the resumability routine reads. Beyond any `workflow.*` decision keys, it carries the run state derived from events:

- `current_phase` — the v8 ladder key of the latest `PhaseAdvanced.to` (null before the first advance).
- `substep` — the latest `SubstepRecorded` (`{phase, substep, status}`), or null.
- `locked` — `true` after a `LockSet{locked:true}`; `false` after a `LockSet{locked:false}` (the `/iterate-design` unlock).
- `locked_at` — the ISO-8601 UTC lock time, stamped from the most recent locking `LockSet`'s event `ts` (the binary's own clock); `null` after an unlock.
- `version` — the locked design version (e.g. `"v1.0"` → `"v1.1-draft"` → `"v1.1"`) from the most recent `LockSet` that carried a `version`; `null` before any lock.
- `audits[]` — one `{ts, result, checks_passed, checks_failed}` entry per `AuditCompleted` event. `audit_freshness` (19) refuses LOCK if the latest entry is stale or absent.

---

## The flat index + ADR ledger

- **`99-flat-index.json`** — `{schema_version:"4.0", decisions:{<dotted-key>:<value>}, adrs:[…]}`. The single denormalised map of every decision plus every ADR. This is what `catalog list` evaluates conditions against, what `generate-configs` / `generate-diagram` read, and the **`reverse-engineer`-interop view** (the companion plugin emits this same flat keyspace). When the orchestrator needs "what's been decided?" it reads here.
- **`decisions/index.json`** — `{schema_version:"4.0", regenerated_at:"<ISO8601>", adrs:[…]}`. The dedicated, canonical ADR-ledger projection. Each ADR entry: `{id, title, status, date, phase, supersedes[], superseded_by[]}`. `regenerated_at` is stamped at materialisation time (when projections are written to disk), so it is also a freshness signal (`decisions_index_fresh`, check 30). `99-flat-index.json.adrs[]` carries the same ADR set for fast querying; `decisions/index.json` is the canonical home going forward.

ADR markdown files live under `decisions/*.md` named `<NNNN>-<slug>.md` (e.g. `0007-use-postgres.md`), with MADR-4 + structured-MADR frontmatter (`type: adr`, `schema_version: "4.0"`, `id`, `status`, `date`, `plugin_version`, …). `adr_files_exist` (17, WARNING) flags any non-Reserved recorded ADR that has no matching file under `decisions/` (Reserved-status ADRs are skipped); it never blocks LOCK — the orchestrator can mechanically close the gap.

---

## The replay invariant (the central correctness property)

```
replay(events.jsonl) == the projections on disk
```

`replay` reconstructs every projection by folding `apply_event` over the log from `empty_projections()`. The live, incremental updates the binary writes at each event MUST produce **byte-identical** projections to a from-scratch replay (`projections_to_disk` is deterministic: `sort_keys=True` + `indent=2` + trailing newline). This is what makes the event log authoritative and the projections disposable — they can always be regenerated.

- **Enforced by `resume_test` (check 31, FATAL).** It re-derives the projections from `events.jsonl` and compares against disk; any divergence is a FATAL audit failure that blocks LOCK and can never be `--ack`'d.
- **Repaired by `architect-brain replay`.** If projection drift is ever detected (e.g. a file was hand-edited, or a partial write was interrupted), run `replay` to re-materialise the projections from the authoritative log. The fix is always "re-derive from events," never "edit the projection."

Two related checks: `state_schema_valid` (29, FATAL) validates the on-disk shape against the schema; `decisions_index_fresh` (30) confirms the ADR-ledger projection matches the events. `catalog_topo_acyclic` (32, FATAL) is a catalog property, not a state property, but rounds out the three never-ackable FATALs.

---

## Lifecycle

| Event | Action |
|---|---|
| Preflight (Phase -1) initialises | `architect-brain init` creates `docs/_architect_state/` with an empty `events.jsonl`, empty per-concern projections, `99-flat-index.json`, `decisions/index.json`, and the `schema_version` probe at `"4.0"`. Then `architect-brain set-phase preflight` emits the first `PhaseAdvanced`. |
| Any decision / ADR / doc / phase move / audit / lock | The orchestrator emits the corresponding event via `architect-brain` (`set-decision`, `record-adr`, `record-doc`, `set-phase`, `audit`, `append-event --type LockSet`, …). The projections re-materialise; the binary stamps the real `ts` + ULID. |
| Resume invocation | `architect-brain detect` classifies the project; for a `v8_project` the orchestrator reads `workflow.json` (`current_phase`) + `99-flat-index.json` (decisions), prints a resume summary, and jumps to the recorded phase. |
| LOCK (Phase 8) | `architect-brain append-event --type LockSet --payload '{"locked":true,"version":"v1.0"}'` freezes the design. The lock is an **event**, not a hand-edited field. |
| Clean exit (any phase) | Release the lock (delete `docs/_architect_state/.lock`); the state directory is **preserved** for the next resume / `/iterate-design`. |

To re-bootstrap from scratch: do **not** delete the state directory mid-run. A genuine fresh start is a new `init` in an empty folder; an existing project routes through resume/migrate/upgrade (below). Existing generated docs become reference material — the orchestrator diffs and asks rather than overwriting.

---

## `schema_version` vs the plugin version — DO NOT CONFUSE

These are **independent**:

- `schema_version` (the probe file's `"4.0"`) describes the **layout of the state directory** — the event taxonomy, the projection shapes, the file set. It bumps only when the state model changes (it went 3.0/3.1 → 4.0 at the v8 monolith→event-sourced cutover).
- The **plugin version** (`8.0.0`, from `.claude-plugin/plugin.json`) describes which release of `project-architect` is running. Plugin provenance is carried in each event's `by`/`payload` (e.g. the migrator's `Upgraded.from_plugin`) and in ADR/doc frontmatter (`plugin_version`) — **never** in `schema_version`.

CRITICAL: the `schema_version` file is the literal string `"4.0"` (`init` writes it) — never the plugin version. A future v8.x or v9 plugin can keep writing `schema_version "4.0"` if the state model is unchanged.

---

## Lock / unlock semantics (`LockSet` events)

The "locked" lifecycle (frozen design at a named version) is expressed entirely as `LockSet` events — there is no mutable lock field to edit:

- **LOCK** (end of Phase 8): emit `LockSet{locked:true, version:"v1.0"}`. The binary stamps the real `locked_at` into the event `ts`; `workflow.json` re-materialises with `locked:true`, `version:"v1.0"`, `locked_at:<ts>`.
- **`/iterate-design` unlock**: emit `LockSet{locked:false, version:"<prev>+0.1-draft"}` (e.g. `"v1.0" → "v1.1-draft"`) with a null `locked_at`. Re-enter Iteration.
- **Re-lock** (after a `/iterate-design` revision): emit `LockSet{locked:true, version:"<prev>+0.1"}` (drops the `-draft` suffix, e.g. `"v1.1-draft" → "v1.1"`) with a fresh `locked_at`.

A **half-locked** state — `locked == false` AND `version` set AND `version` does NOT end in `-draft` AND `current_phase` past `iteration` — signals an interrupted `/iterate-design` between the unlock and the re-lock. The orchestrator MUST detect this at resume (reading `workflow.json`) and offer **finish or roll back** rather than silently re-entering a phase. See SKILL.md "Resume from a half-locked state."

---

## Timestamps — always ISO8601 UTC, never date-only

Every event `ts` and every materialised timestamp uses **ISO-8601 UTC**: `YYYY-MM-DDTHH:MM:SSZ` (e.g. `"2026-05-27T15:23:11Z"`). These are stamped by the binary's own clock at the moment the event is appended — never a model-typed literal. The fields:

- `events.jsonl` event `ts` (the provenance of every state change)
- `workflow.audits[].ts`, `workflow.locked_at`
- `decisions/index.json.regenerated_at`
- `.lock` `acquired_at`
- ADR `date` (the ledger entry's `date` is the event `ts`'s date component; the ADR markdown's `date:` frontmatter matches, date-only by ADR convention)

The binary uses the equivalent of `date -u +"%Y-%m-%dT%H:%M:%SZ"` internally; the `-u` guarantees UTC, the `Z` is the ISO-8601 UTC marker. **Validation:** `iso8601_timestamps` (check 12) verifies every timestamp parses cleanly and is not date-only.

---

## Phase keys (the v8 ladder)

`PhaseAdvanced` and `set-phase` use the bare v8 ladder keys, in this order — note **Architecture comes BEFORE Stack**, and **Cost is its own phase**:

```
preflight → kickoff → vision → architecture → stack → cost → docs → iteration → lock → tooling → handoff → complete
```

The v8 reorder vs v7: the system's shape, boundaries, and data-flow (Architecture) are decided **before** the tech stack — domain first, infrastructure second (Spec-Kit / DDD / Anthropic alignment). The valid key set is exactly these 12 (see the UI ladder and SKILL.md "Phase order"). `current_phase` in `workflow.json` is the latest `PhaseAdvanced.to`. `no_oob_phase_advance` (20, BLOCKING) catches any phase reached without its predecessor's `PhaseAdvanced` event — a bypassed gate leaves no event and is therefore detected.

---

## Lockfile protocol

Path: `docs/_architect_state/.lock`. Contents:

```jsonc
{ "pid": 42, "host": "macbook-air", "acquired_at": "2026-05-27T14:00:00Z" }
```

1. **Acquire at startup.** Before mutating any state, create the lockfile (atomic write: `mkstemp` in `docs/_architect_state/` + `rename` — never write directly).
2. **Stale window: 30 minutes.** If `now - acquired_at > 30 min`, the lock is stale — offer the user: `"Stale lock from pid X on host Y (acquired 47 min ago). Clear and continue? (y/n)"`.
3. **Live lock, same host, pid alive** (`now - acquired_at <= 30 min` AND `host` matches AND `kill -0 <pid>` succeeds): refuse with `"Another project-architect session appears to be running (pid X). If this is wrong, delete docs/_architect_state/.lock and retry."`.
4. **Live lock, different host or dead pid:** treat as stale; offer to clear.
5. **Release at clean exit.** Phase 8 cleanup deletes the lockfile only — the **state directory is preserved** (it is the cross-session entry point for resume and `/iterate-design`). Any other phase's clean exit also deletes only the lockfile.

The lockfile guards the writer; the event log itself is durable across crashes (every appended event survives), so a hard interruption loses at most the in-flight step, not committed state.

---

### Programming language project sub_types (Sketch F)

Specialised `project.sub_type` values for designing a new programming language. The 6 variants partition the design space by intended scope/audience; they gate the PL design templates (LANGUAGE_GRAMMAR, SEMANTICS, TYPE_SYSTEM, STDLIB, TOOLCHAIN, BOOTSTRAP_PLAN, STABILITY_AND_RFC) via `catalog.json` conditions over `project.sub_type`.

| sub_type | Description | Exemplars |
|---|---|---|
| `general_purpose_language` | Broad, full-featured language. Needs stdlib, type system, GC/ownership, full toolchain. | Rust, Go, Python clone |
| `domain_specific_language` | Narrow grammar; embedded use or standalone. | HCL, regex, Terraform-class |
| `query_language` | Declarative data querying; needs schema model + optimizer. | SQL/GraphQL/OQL dialects |
| `configuration_language` | Total functions, hermetic; type system + import semantics. | Nix, Dhall, CUE, Jsonnet |
| `educational_language` | Teaching tool; minimal stdlib, clarity over performance. | Crafting Interpreters-class, BF clone |
| `transpiler_target` | Compiles to existing language; needs host-language interop. | TypeScript→JS, Elm→JS, CoffeeScript |

### Programming language decisions (Sketch F)

When `project.sub_type` is one of the PL variants, four additional `pl.*` decision axes are recorded as `DecisionMade` events (routed to the `vision` concern by the catch-all; canonicalised under `pl.*` in [`decision-keys.md`](./decision-keys.md)). Enum values are normative — agents and templates assume these exact strings.

#### `pl.impl_strategy` — how the language is implemented in v0.1

| Value | When to pick |
|---|---|
| `tree_walking_interpreter` | Simplest path; educational or DSL bootstrapping. |
| `bytecode_vm` | Moderate complexity; custom VM, portable. |
| `native_compiler` | Highest performance; AOT to machine code. |
| `transpiler` | Compiles to existing language; fastest path to "real" language. |
| `hosted_embedded` | DSL inside a host language (Lua-in-C-style). |

#### `pl.host_runtime` — what runs the compiled/interpreted code

Research-informed enum (as of 2026-05). 14 values; choose by use-case fit, not familiarity.

| Value | When to pick (2026 status) |
|---|---|
| `llvm` | Industrial default (LLVM 22.x stable); broadest target coverage. |
| `mlir` | Accelerator-friendly (GPU/FPGA/TPU/quantum); dialect-driven design. Mojo proves general-purpose viability. |
| `cranelift` | Wasm runtimes or fast-debug-build Rust codegen (production for Wasm/JIT). |
| `qbe` | Small-backend alternative (~14 kLOC C); teaching/bootstrap. x86-64/aarch64/riscv64 only. |
| `truffle` | Host a new language on GraalVM (24/25 LTS) — free JIT + Native Image + polyglot. |
| `jvm` | Target JVM bytecode directly (Java 25 LTS). |
| `beam` | Functional/actor-shaped languages only (Gleam exemplar). |
| `wasm` | Raw Wasm 3.0 target (W3C standard since Sept 2025: WasmGC + EH + tail calls + multi-memory). |
| `wasm_component` | Component Model target for cross-component composition (WASI 0.2 stable; 0.3 RC). |
| `js_host` | Compile to JavaScript for web embedding or polyglot piggyback. |
| `python_embedded` | DSL inside Python 3.14+ — prototyping/education. (No-GIL opt-in only.) |
| `rust_host` | Embedded DSL in Rust — proc-macro or runtime interpreter. |
| `native_no_runtime` | Hand-rolled native codegen; expert-only. |
| `custom_vm` | Hand-rolled bytecode VM; teaching/niche. |

#### `pl.paradigm` — primary programming paradigm

| Value | Examples |
|---|---|
| `imperative` | C, Go |
| `functional` | Haskell, OCaml |
| `logic` | Prolog, miniKanren |
| `oop` | Smalltalk, Java |
| `multi_paradigm` | Rust, Scala, Swift |
| `data_oriented` | Clojure, APL |

#### `pl.type_system` — primary static-analysis stance

| Value | Description |
|---|---|
| `static_strong` | Statically typed, no implicit coercion. Rust, Haskell, OCaml. |
| `static_gradual` | Static with opt-in/opt-out gradual typing. TypeScript, Python+mypy. |
| `dynamic` | Runtime types only. Python, Ruby, JavaScript. |
| `dependent` | Types depend on values. Lean 4 (closest to general-purpose 2026), Idris 2 (research), Agda (research). |
| `affine_linear` | Linear or affine resource types. Rust ownership, Linear Haskell. |
| `none_untyped` | No types (untyped lambda calc, Forth). |

---

## Agentic-system project types + bounded contexts (v8)

The `agentic_system` project type carries three sub-types and the matching decision namespaces:

- `project.sub_type` ∈ `single_agent` | `multi_agent_orchestrator` | `agentic_tool`.
- `agent.*` decisions (routed to the `ai_agent` concern): `agent.autonomy`, `agent.execution`, `agent.memory`, `agent.hitl`, `agent.tools.sandbox`.
- The `ai_agent` and `api_contract` projections are the bounded contexts for these systems (AI/model/orchestration decisions under `ai.*`/`agent.*`; service contracts under `api.*`/`webhooks.*`).

---

## Migration policy (pre-v8 monolith → v8 event-sourced)

A project carrying a v7 **monolith** `docs/_architect_state.json` (schema < 4.0) is migrated forward by `architect-brain migrate [--from 3.1]`. `detect` classifies it as `pre_v8_project`; the orchestrator routes there BEFORE proceeding. The migrator is **PRESERVE-FLAT**: the nested v7 `.decisions` are flattened to dotted keys **verbatim** — not translated to v8's `stack.*` namespace. (A user who wants full v8 doc-selection under v8 conventions runs `/re-architect`.)

### Supported window

- **Floor:** refuses `schema_version` major < 2 (pre-2.0 state uses the v5–v6 `/upgrade-project` path).
- **Ceiling:** refuses `plugin_version` major > 8 (a future artifact this migrator must not touch — surface a "newer plugin" refusal).

### The migration algorithm (13 steps, reversible)

1. **`detect_legacy`** — confirm a monolith `_architect_state.json` exists and parses.
2. **Floor/ceiling check** — refuse out-of-window state with a clear message.
3. **Snapshot FIRST** — tar.gz the monolith + any `decisions/` dir to `docs/_architect_state.json.v7-backup.<iso>.tar.gz`. Never proceed without this backup; it is the reverse-out.
4. **Synthesize events** (deterministic order): one `Upgraded`, then N `DecisionMade` (flattened decisions, keys sorted), then M `ADRFiled` (from `adrs_filed[]` then `reserved_adrs[]`), then K `DocGenerated` (from `documents_generated[]`), then the `PhaseAdvanced` trajectory, then one `AuditCompleted` (if `last_audit` non-null), then one `LockSet` (if locked). Timestamps reuse the v7 source stamps (`filed_at`/`generated_at`/`locked_at`/`started_at`) where present.
5. **Write `events.jsonl`** into a temp sibling dir `_architect_state.migrating/`.
6. **`replay`** the temp log into projections.
7. **Reindex the workflow phase** — map the v7 `.phase` through `phase_v7_to_v8` (the head reorders: v7 `phase_2` Tech-Stack → v8 `stack`, `phase_3` Architecture → v8 `architecture`, `phase_2.5` Cost → v8 `cost`; the tail `phase_4`→`docs`, `phase_5`→`iteration`, `phase_6`→`lock`, `phase_7`→`tooling`, `phase_8`→`handoff`).
8. **`projections_to_disk`** — materialise the temp dir's full projection set + `schema_version "4.0"`.
9. **Compare** the replayed flat-index against the v7 monolith (every flattened decision key/value; the ADR id set). **Abort on any drift** — delete the temp dir, leave the monolith untouched, return the drift list.
10. **Atomic flip** — `os.replace` the temp dir into `docs/_architect_state/`.
11. **Migrate ADR files** — copy v7 `docs/decisions/*.md` into `_architect_state/decisions/` (where check 17 / reconcile look), then `restamp_adrs` (prepend structured-MADR frontmatter to any free-form ADR markdown). `restamp_docs` adds `plugin_version`/`format_version` to generated-doc frontmatter (best-effort; docs without frontmatter are skipped).
12. **Keep the monolith as a `.migrated` sidecar** (`_architect_state.json.migrated`) — the backup tarball is kept regardless.
13. **Post-migration audit** (default) — run the full 35-check `architect-brain audit`; a non-zero (FATAL/BLOCKING) exit is surfaced for a rollback decision. The migrator does **not** auto-delete the new state; rollback is via the kept backup tarball.

`migrate` is **reversible** (restore from the backup tarball) and **fails safe** (drift aborts before the flip, so the monolith is never lost). The phase map only reorders the head (the v8 Architecture-before-Stack swap); the tail (`docs`/`iteration`/`lock`/`tooling`/`handoff`) is unchanged from v7.

---

## Revision Log

- **4.0 (v8 cutover, 2026-05).** Replaced the monolith `docs/_architect_state.json` with the event-sourced `docs/_architect_state/` directory: `events.jsonl` authoritative + 11 per-concern projections + `99-flat-index.json` + `decisions/index.json` + the `schema_version` probe. 12-event taxonomy; the `replay(events) == projections` invariant (FATAL `resume_test`). Phase ladder reordered (Architecture before Stack; Cost its own phase). Decisions are flat dotted keys. Pre-v8 monoliths migrate forward via `architect-brain migrate` (PRESERVE-FLAT, reversible).

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
