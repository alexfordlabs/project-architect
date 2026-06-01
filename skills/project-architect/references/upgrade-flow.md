<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Cross-version upgrade flow (`/upgrade-project`)

> See [`situation-assessment.md`](situation-assessment.md) for how the Preflight detects an old/interrupted project and routes here.

The canonical procedure for ingesting a project bootstrapped by an **older** project-architect and bringing it forward to the locked v8 format — the event-sourced, multi-file state under `docs/_architect_state/` at `schema_version "4.0"`. Invoked by the `/upgrade-project` command and auto-offered at Resumability when the staleness detector flags an old project. Nothing is destroyed: the pre-v8 monolith is preserved in the migrator's backup tarball (the authoritative reversible preservation), and a human-readable labelled copy of the pre-upgrade docs can optionally be made by hand into `docs/versions/<label>/`.

> Report progress per `references/output-style.md` (capture mechanical output; RENDER the UI by RUNNING `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar <phase>` — never by transcribing its art — and add one `✓` step line per step).
>
> **On a BLOCKER, follow the self-healing error protocol** in [`references/output-style.md` §4](output-style.md) — surface a concise *informational error state* (what failed / what's known so far / what's at risk), then `AskUserQuestion`: **write a report and stop**, OR **self-heal** (apply a remediation derived from the gathered info — e.g. `record-adr` for a missing ADR file — after the user approves) and continue. Never silently fail or dump a raw trace.

This flow **reuses** existing, tested machinery — the one binary `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain` (`detect` / `migrate` / `reconcile-adrs` / `audit` / `set-decision` / `record-adr` / `record-doc` / `set-phase`), the declarative `references/catalog.json` doc selection, and the `document-author` / `claude-md-author` / `claude-tooling-author` / `decision-revisor` generators. It adds **no new transformer**: state modernization is the migrator's job (it synthesizes events and re-stamps artifacts), and any re-derived artifacts are RE-DERIVED from the migrated flat decisions, never patched in place (spec §4, locked decision #3). The state migration policy + the event synthesis it performs are documented in [`state-schema.md`](state-schema.md); the doc-format / decision-key tables it reads live in [`artifact-migration.md`](artifact-migration.md).

> **Branch discipline (mirrors the bootstrap rule).** When upgrading an EXISTING project that has a git repo, do the whole flow on an `upgrade/architect-<date>` branch (e.g. `upgrade/architect-2026-05-29`) + a PR — never directly on `main`. The handoff names the branch, states that deploys / hosting integrations read `main` (so the upgrade is **not live until merged**), and offers a clean `--ff-only` merge. This is the v8 "branch-handoff clarity" decision (Phase 10) applied to upgrades.

```text
DETECT → FLOOR-CHECK → PRESERVE(optional docs/versions copy) → MIGRATE (monolith → events, kept backup tarball; replay == projections)
   → CHOOSE MODE → [Preserve: reconcile ADRs + keep docs + flag]  |  [Full: re-walk diff → re-derive docs+CLAUDE.md+tooling]
   → RE-GATE (architect-brain audit, must be green) → RE-LOCK(bumped)
```

---

## Step 1 — DETECT

Run the shared detector and parse its verdict (it is read-only):

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect
```

It returns JSON with `situation` ∈ `greenfield` | `v8_project` | `pre_v8_project`, plus `schema_version` and `state_layout`. From those — and a read of the project's `decisions` shape — the orchestrator DERIVES the three version-staleness signals this flow branches on below (`below_floor`, `newer_than_plugin`, `can_rederive`); they are orchestrator-computed, **not** emitted by `detect`. The routing:

- **`situation == "pre_v8_project"`** (a v7 monolith `docs/_architect_state.json` exists, `schema_version` below `"4.0"`): this is the upgrade target — proceed through the steps below (the heart is the `architect-brain migrate` in Step 4).
- **`situation == "v8_project"`** (a `docs/_architect_state/` directory at `schema_version "4.0"` already): the project is already current; tell the user there is nothing to upgrade and STOP (idempotent no-op).
- **`situation == "greenfield"`**: there is no architect state to migrate; this flow does not apply.

`can_rederive` selects the flow mode in Step 5 (Preserve vs Full). `state_layout` and `schema_version` are reported for context.

## Step 2 — FLOOR-CHECK (reuses the two state-framework guards)

- **`below_floor == true`** (schema below the migratable band, OR no `docs/`, OR no `decisions` namespace) → **REFUSE**:
  > *"This project predates project-architect's migratable layout. Re-bootstrap fresh with `project-architect`; your existing docs become reference material."*
- **`newer_than_plugin == true`** (`schema_version` or any doc `format_version` exceeds what this plugin supports) → **REFUSE**:
  > *"This project was produced by a newer project-architect than is installed. Upgrade the plugin, then retry."*

No partial migration below the floor; no pretending to understand a newer artifact. (The orchestrator computes both signals from the reported `schema_version` — `newer_than_plugin` against the band `migrate` enforces — not from a `detect` field.)

## Step 3 — PRESERVE the pre-upgrade state (nothing is lost)

The authoritative reversible preservation is the migrator's own backup: `architect-brain migrate` (Step 4) keeps a backup tarball of the pre-v8 monolith, and the migration is reversible from it. There is **no separate snapshot step or `architect-brain snapshot` subcommand** — the migrator's tarball is the preservation mechanism, so nothing is lost when the state is modernized.

If you also want a **human-readable, labelled copy of the pre-upgrade docs** (the v7 `docs/versions/` convention), make it explicitly with a plain copy BEFORE anything mutates the docs:

```
cp -r docs/ docs/versions/<old-version-label>/
```

`<old-version-label>` is the project's current locked version (e.g. `v1.0`) or, if unlocked/unversioned, a synthesized label (`pre-upgrade-<date>`). This is a **manual/optional** copy — it preserves the human-readable `docs/*.md`, `docs/decisions/`, and `docs/research/` as a labelled design version that the user can `diff` against. It is not an automatic side effect of any binary subcommand, and it does not record anything into the `workflow` projection (there is no Snapshot event type). The migrator's backup tarball remains the authoritative reversible preservation regardless of whether this copy is made.

## Step 4 — MIGRATE (monolith → event-sourced state; the existing migrator, no new code)

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate [--from 3.1]
```

This is the keystone. The migrator takes the v7 monolith `docs/_architect_state.json` (schema < `4.0`) and brings it to the v8 event-sourced layout under `docs/_architect_state/` (`events.jsonl` + per-concern projections + `99-flat-index.json` + `decisions/index.json` + the `schema_version` probe at `"4.0"`). Per the [state migration policy](state-schema.md) it:

1. **Snapshots** the monolith to a kept backup tarball (the migration is reversible).
2. **Synthesizes events** — replays the monolith's recorded history (decisions, filed ADRs, generated docs, phase progress, lock state) into the append-only `events.jsonl` as `DecisionMade` / `ADRFiled` / `DocGenerated` / `PhaseAdvanced` / `LockSet` / `Upgraded` events, each stamped with a real ULID + timestamp.
3. **Replays** the synthesized events to materialise the 11 per-concern projections, `99-flat-index.json`, and `decisions/index.json`.
4. **Re-stamps ADRs/docs** with the v8 `format_version` / provenance (MADR-4 + structured-MADR frontmatter where applicable).
5. **Reindexes phases** — maps the pre-v8 phase pointer onto the v8 12-phase ladder (`preflight → kickoff → vision → architecture → stack → cost → docs → iteration → lock → tooling → handoff → complete`); a brought-forward locked project's trajectory is recorded as complete via the synthesized `PhaseAdvanced` events.
6. **Compares** — asserts the central invariant `replay(events) == projections` (the same property `audit --only 31` enforces, FATAL). A mismatch aborts the flip and leaves the monolith untouched.
7. **Atomically flips** the project to `docs/_architect_state/` and runs a **post-migration audit** by default. A blocking post-migration audit leaves the migrated state preserved for review rather than completing.

The migration is idempotent (re-running on an already-migrated v8 project is a no-op — `detect` would report `v8_project` and Step 1 short-circuits) and **reversible** via the kept backup tarball. After this step the project's decisions are FLAT dotted keys (`stack.frontend.framework`, `architecture.style`, … per [`decision-keys.md`](decision-keys.md)) — never the v7 nested form.

## Step 5 — CHOOSE MODE (`can_rederive`)

The orchestrator-derived `can_rederive` signal decides how the rest of the flow runs:

- **`can_rederive == false`** (the project's pre-v8 `decisions` were narrative/sparse rather than a complete flat keyspace — EVERY project bootstrapped by v4.x and earlier) → **Preserve mode**. The narrative decisions cannot faithfully regenerate the project's hand-evolved docs, so the flow KEEPS all docs and FLAGS what needs manual modernization. It never re-derives (which would error or emit thin docs and churn the real design).
- **`can_rederive == true`** (the project carries a complete flat keyspace — e.g. a v5/v6/v7 flat-keyspace project being brought to v8) → **Full mode**: the re-derive path below (Steps 6–8).

> **Honest scope:** for every project bootstrapped before the flat keyspace existed, `/upgrade-project` runs in **Preserve mode** — state-modernization (the migrator) + ADR-reconcile + preserve + flag. Full doc re-derivation is reserved for projects whose decisions are already complete in the flat keyspace.

### Preserve mode (`can_rederive == false`)

The migrator (Step 4) has already done the heavy state lift — it synthesized the event log, materialised the projections, and re-stamped the ADR ledger. Preserve mode adds an ADR reconcile against on-disk reality and a read-only assessment, then re-locks:

1. **RECONCILE the ADR ledger from disk** — the on-disk ADR markdown files (`docs/_architect_state/decisions/*.md`, or the pre-migration `docs/decisions/*.md` the migrator carried forward) are the source of truth (a pre-v8 ADR ledger is typically stale/incomplete):
   ```
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain reconcile-adrs
   ```
   This emits the `ADRFiled` / `ADRSuperseded` events needed so `decisions/index.json` matches the files on disk. Do NOT re-walk the decision diff — the narrative decisions are left as-is (opaque).
2. **PRESERVE docs — do NOT re-derive.** Skip the Full-mode Steps 6–8. Every existing doc stays byte-for-byte.
3. **GATE as a read-only ASSESSMENT** — run the audit to SURFACE the project's health, then **flag** (do not auto-fix-by-regeneration):
   ```
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --verbose
   ```
   Flag: missing `generate_when: always` docs (e.g. an absent `PROJECT_REQUIREMENTS.md`, which `/implement` reads feature specs FROM — surfaced by `required_docs_generated`, check 27, BLOCKING), docs lacking the v8 `format_version` stamps, and any cross-link gaps (`cross_link_integrity`, check 22, BLOCKING). Tell the user these are manual follow-ups (re-author the specific doc, or use `/iterate-design`). The upgrade is NOT blocked by findings that only a re-derive would have fixed — present those as flags and acknowledge them with an explicit recorded `--ack=<reason>` so the lock can proceed; it IS blocked by a corrupt state (a FATAL like `state_schema_valid` (29) or `resume_test` (31), which the migrator's compare step would already have caught). A FATAL can never be acked.
4. **RE-LOCK + re-snapshot** (Step 9) — bump the version, re-snapshot.

The result: the project is on the v8 event-sourced state at `schema_version "4.0"`, its ADR ledger matches reality, its rich docs are intact, and the user has a precise list of what to modernize by hand.

## Step 6 — RE-WALK decisions (focused on what CHANGED)

> **Full mode only** (`can_rederive == true`). In Preserve mode this step is replaced by the ADR-reconcile in Step 5 and is skipped.

The migrator already speaks the current flat keyspace. Surface the migrated decisions for review, but focus the user's attention only on the **stale** ones via a **stale-decision diff**. A decision is stale when:

- **(a)** its key was renamed / split / re-typed by the **decision-key migration table** in [`artifact-migration.md`](artifact-migration.md) between the project's old keyspace generation and the current one (definitely stale); OR
- **(b)** the catalog entry it feeds gained or changed `conditions` / `depends_on` between the old and current [`catalog.json`](catalog.json) (its consequences changed → surface it). The v8 reorder — Architecture decided BEFORE Stack — can also surface decisions: an old project that recorded stack choices without an explicit `architecture.style` may need that architectural decision filled in (dispatch the `architecture-specialist` to recover/confirm it).
- **(c)** *(best-effort)* the option set for the decision changed since the old version.

For each stale decision: keep-or-revise via the existing `decision-revisor` (which files a superseding ADR via `architect-brain record-adr` + rewrites affected docs per the playbook). **Unchanged decisions are confirmed in bulk, not re-asked** — an upgrade is a focused review of the delta, not a fresh interview.

When a kept-or-revised decision invalidates already-built code, emit an **affected-code-areas** list (coarse `project_layout` → top-level-component mapping; see [`revision-playbook.md`](revision-playbook.md)) and tell the user to re-run `/implement` / `/scaffold` there. The flow NEVER rewrites the user's source code.

## Step 7 — RE-DERIVE all generated artifacts

> **Full mode only** (`can_rederive == true`). In Preserve mode this step is replaced by the ADR-reconcile in Step 5 and is skipped.

Regenerate **every generated artifact** fresh from the migrated + reviewed flat decisions against the **current v8 templates** (the old copies were snapshotted in Step 3 + preserved in the migrator's backup, so this overwrites without loss):

- **Design docs** — ask the binary which docs apply, in topological order, for the current decisions, then dispatch `document-author` per the declarative catalog:
  ```
  ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain catalog list
  ```
  This returns the applicable docs (the union of always-generated docs + the docs whose `conditions` the current flat decisions satisfy + any ADR-affected docs) in `depends_on` topo order. Record each generated doc via `architect-brain record-doc` (emits a `DocGenerated` event).
- **`CLAUDE.md` (root + per-folder)** — dispatch `claude-md-author` against the current `CLAUDE_MD_*` templates.
- **`.claude/` tooling** (settings.json, hooks, agents, commands, recommended-plugins) — dispatch `claude-tooling-author` against the current tooling templates. This also carries the version-awareness gate into the upgraded project's generated `/implement` / `/scaffold` / `/iterate-design` commands.

Because everything is authored new, it carries the current `format_version` + provenance stamps by construction, cross-links resolve by construction, and doc / CLAUDE.md / tooling versions move together. **Only user CODE is NOT auto-regenerated** — that is gated behind the intent menu's rebuild-vs-keep choice (see [`version-awareness.md`](version-awareness.md)).

## Step 8 — RE-GATE (must be green)

Run the full v8 audit:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit [--verbose]
```

The audit runs all 35 in-process checks (4-tier severity: FATAL / BLOCKING / WARNING / INFO) and records an `AuditCompleted` event. The upgrade **cannot COMPLETE while any FATAL or BLOCKING finding is open.** Mechanical, auto-fixable gaps (a WARNING — e.g. a missing ADR file, an incomplete ledger entry) auto-remediate (file the missing ADR via `architect-brain record-adr` + write the file, record the missing doc via `record-doc`) then re-run the audit; genuine BLOCKERs hard-stop with the remediation defaulted (a BLOCKING finding may be downgraded only with an explicit, recorded `--ack=<reason>`); a FATAL (`state_schema_valid` 29, `resume_test` 31, `catalog_topo_acyclic` 32) can never be acked and must be fixed — identical policy to the v8 enforcement model in `SKILL.md`. The `AuditCompleted` event the run records is what `audit_freshness` (check 19, BLOCKING) reads to allow the lock menu to render.

## Step 9 — RE-LOCK

Lock the upgraded design at a **bumped MAJOR version** (e.g. `v1.0 → v2.0`, signaling a cross-version upgrade rather than an in-place `/iterate-design` `+0.1`). The lock is a `LockSet` event through the binary:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain append-event --type LockSet --payload '{"locked": true, "version": "<new-version>", "locked_at": "<binary stamps it>"}'
```

(The orchestrator never types the timestamp — the binary's own UTC clock stamps the event; pass `locked_at` as the binary's responsibility, never a hand-typed literal.)

If you want a post-lock human-readable design-version copy (the same optional `docs/versions/` convention as Step 3), make it explicitly with a plain copy:

```
cp -r docs/ docs/versions/<new-version>/
```

This is a manual/optional copy — not an automatic side effect of any binary subcommand, and it records nothing into the `workflow` projection (there is no Snapshot event type).

The project is now a first-class v8 project: event-sourced state at `schema_version "4.0"`, every artifact stamped, audit-green, with the migrator's reversible backup tarball preserved as the authoritative pre-upgrade preservation (plus any manual `docs/versions/<label>/` copies you chose to make in Steps 3 and 9). If on an `upgrade/architect-<date>` branch, present the Phase-10 branch-merge handoff (name the branch, note deploys read `main`, offer the `--ff-only` merge).

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
