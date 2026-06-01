<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Re-architect flow (`/re-architect`)

> See [`situation-assessment.md`](situation-assessment.md) for how the Preflight detects an old/interrupted project and routes here.

The canonical procedure for **revisiting a docs-rich project's design from first principles**: recover the existing design into a reviewable artifact, let the user triage every decision (keep / revise / drop / add), research the deltas AND challenge the keeps with current sources, re-decide into the flat keyspace, then re-derive every generated artifact from the new decisions. Invoked by the `/re-architect` command and by version-awareness **option 3** ("Start fresh, revisiting decisions").

This is the opposite end of the spectrum from `/upgrade-project` **preserve mode**: preserve mode *freezes* the design and modernizes state around it; re-architect *re-decides* the design. Both ride the **same plumbing** — the one binary `bin/architect-brain` (`detect` / `migrate` / `reconcile-adrs` + the `set-decision` / `set-phase` / `record-adr` / `record-doc` / `append-event` event writers + the 35-check `audit` + the declarative `catalog`), `research-scout`, the `document-author` / `claude-md-author` / `claude-tooling-author` generators, and the `revision-playbook` affected-code map. The **only new logic** is the `design-recovery` agent (Step 2) and the bespoke triage surface (Step 3). It adds **no new transformer**: re-derived artifacts are authored fresh from the re-decided decisions, never patched in place.

> Report progress per `references/output-style.md` (capture mechanical output; one ✓ line per step; render the advancing bar by RUNNING `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar …` / `ui progress …` — never by transcribing its art).
>
> **On a BLOCKER, follow the self-healing error protocol** in [`references/output-style.md` §4](output-style.md) — surface a concise *informational error state* (what failed / what's known so far / what's at risk), then `AskUserQuestion`: **write a report and stop**, OR **self-heal** (apply a remediation derived from the gathered info — e.g. `record-adr` for a missing ADR file, re-run `architect-brain audit` after re-stamping a doc — after the user approves) and continue from the stopped step. Never silently fail or dump a raw trace.

> **Snapshot-first + branch-isolated (mirrors the bootstrap + upgrade rules).** Nothing is destroyed: the current design is snapshotted to `docs/versions/<old-version>/` BEFORE any mutation, and the entire flow runs on a **`rearchitect/architect-<date>`** branch (e.g. `rearchitect/architect-2026-05-23`) + a PR — never directly on `main`. Deploys / hosting integrations read `main`, so the re-architect is **not live until merged**; the final handoff names the branch, states this, and offers a clean `--ff-only` merge.
>
> **Never rewrites code.** Re-derives design artifacts only (docs, ADRs, `CLAUDE.md`, `.claude/` tooling). When a re-decided decision invalidates already-built code, the flow emits an **affected-code-areas** list and tells the user to re-run `/implement` / `/scaffold` deliberately — it never edits the user's source.
>
> **State is event-sourced + multi-file.** Every mutation in this flow flows through an `architect-brain` event (a `DecisionMade` / `ADRFiled` / `DocGenerated` / `SubstepRecorded` / `LockSet` / `PhaseAdvanced` appended to `docs/_architect_state/events.jsonl`, the projections re-materialised by `replay`). **Never hand-edit any file under `docs/_architect_state/`** — the replay invariant `replay(events) == projections` (audit `check 31 resume_test`, FATAL) is the central correctness property and a hand-edited projection breaks it. Decisions are FLAT dotted keys (`database.engine`, `backend.api_style`, `architecture.style`, …) per [`references/decision-keys.md`](decision-keys.md); `schema_version` is `"4.0"`.
>
> **Two scope choices are NOT baked in — the flow is opinionated but always confirms.** It will **ask every run** how to triage (Step 3) and how broadly to challenge the keeps (Step 4): each has a maximally-thorough default, but the user can narrow it per run. These are the only two interaction-shape choices; everything else follows the fixed order above.

```text
DETECT + SAFETY + migrate-to-v8 + reconcile-adrs
   → RECOVER (design-recovery → RECOVERED_DESIGN.md)
   → TRIAGE (keep / revise / drop / add  +  validate the recovery)
   → RESEARCH the deltas (+ challenge the keeps)
   → RE-DECIDE (→ flat decision set)
   → RE-DERIVE docs + superseding ADRs + CLAUDE.md + tooling
   → RE-GATE (must be green) → RE-LOCK (major bump) + SNAPSHOT(new)
```

> **Progress sub-ledger (resumability).** At the START of each step, record it as a `SubstepRecorded` event: `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-substep rearchitect <step> --status in_progress`; on COMPLETION, mark it done: `… set-substep rearchitect <step> --status done`. Step keys, in order: `detect`, `recover`, `triage`, `research`, `redecide`, `rederive`, `regate`. `SubstepRecorded` stores only the single LATEST substep in the `workflow` projection's `substep` field (`{phase, substep, status}`) — there is no per-step map. A session interrupted mid-flow is found by the Preflight situation-assessment ([`references/situation-assessment.md`](situation-assessment.md)), which reads the `workflow.json` projection: a `substep` left at `status: "in_progress"` is exactly the resume point, and the routine offers to resume from that stopped step. Recording each step `--status in_progress` on entry is what makes a *mid-step* interruption detectable — marking only `--status done`-on-completion would make an interrupted run read as fully complete.

---

## Step 1 — DETECT + SAFETY + migrate-to-v8

> Sub-ledger: `set-substep rearchitect detect --status in_progress` on entry; `set-substep rearchitect detect --status done` once SAFETY + migrate-to-v8 + reconcile-adrs below have all run.

Run the shared situation-router and parse its verdict:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect
```

It emits `{ situation, schema_version, state_layout }` where `situation` ∈ `greenfield` | `v8_project` | `pre_v8_project`. Gating:

- **`situation == "greenfield"`** (no architect state at all — neither a `docs/_architect_state/` directory nor a v7 monolith `docs/_architect_state.json`) → **REFUSE the cross-version re-architect**: there is no recorded design to recover. If the tree is otherwise non-trivial (real source/manifests but no architect state), this is a **foreign project** — route to the reverse-engineer path in [`references/situation-assessment.md`](situation-assessment.md) §2 instead. If it is genuinely empty, re-bootstrap fresh with `project-architect`.
- **`schema_version` newer than this plugin supports** (the orchestrator compares the raw `schema_version` probe string against the plugin's current format generation `"4.0"` — `detect` does NOT itself flag this) → **REFUSE**: the project was produced by a newer plugin than is installed. The newer-than-supported ceiling is enforced by the migrator's band checks (`migration._check_band`), not by `detect`. Upgrade the plugin, then retry.
- **`situation == "v8_project"`** (a `docs/_architect_state/` directory with `schema_version` `"4.0"` — already current) → there is nothing to migrate via this cross-version flow; the design is already on the v8 model. Suggest **`/iterate-design`** for an in-place revision of a current design, and STOP. (Re-architect from a *current* design is still possible — it is `/re-architect` invoked deliberately — but it does NOT need the Step-1 migration; skip straight to Step 2 on a current project.)
- **`situation == "pre_v8_project"`** (`state_layout` `v7_monolith` — a v7 monolith `docs/_architect_state.json` with schema < 4.0) → **proceed**; Step 1 migrates it onto the v8 event-sourced model below.

> **Narrative / sparse-decision projects are exactly the target.** Re-architect deliberately works on projects whose decisions live in prose rather than a flat keyspace — that is its whole point. Where `/upgrade-project` *refuses* to re-derive a narrative project (it falls back to preserve mode), `/re-architect` *reconstructs* the design so the user can re-decide it into the flat keyspace. After re-decide the project's `99-flat-index.json` carries a complete flat decision set and the project is henceforth re-derivable.

Then make the run safe and put the state in sync with reality, reusing tested machinery:

- **SNAPSHOT the current design** to `docs/versions/<old-version>/` so nothing is lost. There is no `architect-brain snapshot` subcommand and no Snapshot event type — copy the design surface with a plain `cp -r` and record the snapshot label as a `DecisionMade`:
  ```
  mkdir -p docs/versions/<old-version-label>
  cp -R docs/*.md docs/decisions docs/research docs/versions/<old-version-label>/ 2>/dev/null || true
  ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision snapshots.<old-version-label> '"<ISO8601-or-label>"'
  ```
  `<old-version-label>` is the project's current locked version (e.g. `v1.4`) or, if unlocked, a synthesized `pre-rearchitect-<date>`. This copies the design docs, the ADR markdown, and the research; the `set-decision` records the label so the snapshot is part of the event log.
- **Work on a `rearchitect/architect-<date>` branch + PR** (create it now). Deploys read `main`; the re-architect is not live until merged.
- **MIGRATE the v7 monolith onto the v8 event-sourced model** so the run sits on the current schema (`"4.0"`, `docs/_architect_state/`):
  ```
  ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate
  ```
  `migrate` snapshots the monolith, synthesizes events into `events.jsonl`, replays to materialise the per-concern projections + `99-flat-index.json` + `decisions/index.json`, re-stamps ADRs/docs, reindexes phases, compares (replay == projections), and atomically flips to `docs/_architect_state/` — reversible via the kept backup tarball. It runs a post-migration `audit` by default; a blocking post-migration audit leaves the state preserved for review. (`--from <ver>` is advisory; `migrate` reads the real `schema_version` itself.) Idempotent.
- **RECONCILE the ADR ledger from disk** — the on-disk ADR markdown files are the authoritative decision record (a pre-v8 ADR list is typically stale/incomplete), and the recovery agent in Step 2 reads the ADRs as source of truth, so the `decisions/index.json` ledger projection MUST match disk first:
  ```
  ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain reconcile-adrs
  ```
  This emits the `ADRFiled` events needed so the ledger projection (and the flat-index `adrs[]`) match the ADR markdown files actually present under `docs/_architect_state/decisions/`.

## Step 2 — RECOVER DESIGN (new)

> Sub-ledger: `set-substep rearchitect recover --status in_progress` on entry; `… recover --status done` once `RECOVERED_DESIGN.md` is written.

Dispatch the **`design-recovery`** subagent (`model: "opus"`, max effort). It reads `docs/*.md`, the reconciled ADR markdown under `docs/_architect_state/decisions/*.md` (authoritative), and `docs/research/*.md`, and emits a structured **`docs/RECOVERED_DESIGN.md`** from the `RECOVERED_DESIGN.md` template — pass it as the absolute `template_path` INPUT `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/templates/RECOVERED_DESIGN.md` (the agent's cwd is the user's project, so a bare `references/…` path is unresolvable; expand `${CLAUDE_PLUGIN_ROOT}` when dispatching). Every recovered decision is one row, grouped by area (project/vision, architecture, tech-stack, security, ops, …), carrying:

- `key` — the **canonical flat decision key** whenever the decision maps to one (`architecture.style`, `database.engine`, `backend.api_style`, `cicd.platform`, `platforms`, `crypto.ratchet`, `infra.runtime`, … per [`references/decision-keys.md`](decision-keys.md)), with the project's own naming recorded as an `alias` when it differs (so Step-6 `catalog` selection + each template's `required_decisions` slicing resolve); a purely project-specific decision with no canonical equivalent keeps a descriptive slug,
- `current_value` — the choice as it stands,
- `rationale` — a ≤3-line summary of *why*, from the prose/ADR,
- `source` — pointer(s) back to `docs/X.md` and/or `docs/_architect_state/decisions/NNNN-*.md`,
- `confidence` — `high` | `low`.

The agent is told it RECONSTRUCTS, never decides and never invents; uncertain or conflicting recoveries are marked **`confidence: low`** rather than guessed. Every ADR in `docs/_architect_state/decisions/` and every material doc-decision MUST be represented. `RECOVERED_DESIGN.md` is itself a run artifact (snapshotted with the run, not a permanent doc).

## Step 3 — REVIEW & TRIAGE (new — the bespoke surface)

> Sub-ledger: `set-substep rearchitect triage --status in_progress` on entry; `… triage --status done` once the triage column is complete (every decision annotated keep/revise/drop, plus any add[]).

Present `RECOVERED_DESIGN.md` and capture, per decision, one of **keep / revise / drop**, plus **add** for anything missing. This is ALSO the **human validation gate** for Step 2: the user corrects any mis-recovered value or rationale here, scrutinizing each `confidence: low` row against its `source`. **Nothing is researched or re-derived until the triage column is complete** — recovery is validated, not trusted.

**The flow asks every run how to triage** before starting, presenting an opinionated default with an explicit override:

> *"How would you like to triage the recovered design? (a) the default — grouped by area, **low-confidence** entries first, **resumable** across sessions (recommended for a large design); or (b) all-at-once in a single pass."*

- **Default presentation: grouped by area, `confidence: low` entries first, and resumable** — triage proceeds area-by-area, with progress tracked as `SubstepRecorded` events (the same sub-ledger mechanism), so a large design (dozens of decisions) is not one overwhelming pass. A resumed session picks up at the next un-triaged area.
- Surfacing **low-confidence** rows first routes the user's attention to exactly the recoveries that need scrutiny.

Output: an annotated triage list — `keep[]`, `revise[]`, `drop[]`, `add[]`.

**At triage-accept, ingest the keep set.** `design-recovery` emits the recovered design as a **flat decisions keyspace** (a flat `{key: value, …}` object keyed by the canonical flat keys from Step 2). Once triage is complete, persist the accepted/kept rows — never by hand-editing a projection. Emit one `DecisionMade` per kept key with `set-decision`; batch them into one `&&`-chained Bash call per the output-style "batch mechanical sequences" rule:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision <kept-key-1> <json-value-1> \
  && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision <kept-key-2> <json-value-2> \
  && …   # one set-decision per kept row
```

Each `set-decision` appends a `DecisionMade` event; the projections (`99-flat-index.json` + the per-concern views) re-materialise. The `revise` / `add` rows (and any challenge-promoted `keep`) are then set **individually** with `set-decision` in Step 5 — the keep set is ingested at triage-accept; the deltas are set one by one as they're decided.

## Step 4 — RESEARCH THE DELTAS (+ challenge the keeps)

> Sub-ledger: `set-substep rearchitect research --status in_progress` on entry; `… research --status done` once both the delta research and the (confirmed-scope) challenge pass have landed in `docs/research/`.

For every `revise` and `add` decision, dispatch **`research-scout`** (reused, `model: "opus"`) with **current** sources (the universal research checklist + the `llms.txt` discipline already in the plugin), framed to (a) inform the new choice and (b) report where the landscape moved since the decision was last set.

THEN run the **challenge pass**. By default it **challenges every kept decision** — `research-scout` actively hunts credible newer/stronger alternatives so the user can promote a `keep` to a `revise`. Because that is research-heavy on a large design, **the flow asks every run** to confirm or narrow the challenge scope first:

> *"The challenge pass will research fresh alternatives for **every kept decision** (maximally thorough). Confirm 'challenge all N keeps', or narrow to specific areas (e.g. just crypto / anonymity / infra)?"*

The opinionated default is **all keeps**; the per-run override lets the user scope it down (e.g. to constraint-flagged areas). Research findings land in `docs/research/` (timestamped, **additive** — old research is preserved alongside the new), each recorded as a `ResearchRefAdded` event (`${CLAUDE_PLUGIN_ROOT}/bin/architect-brain append-event --type ResearchRefAdded --payload '{…}'`).

## Step 5 — RE-DECIDE

> Sub-ledger: `set-substep rearchitect redecide --status in_progress` on entry; `… redecide --status done` once the complete flat decision set is recorded (the keep set ingested in Step 3 + every revise/add/challenge-promoted delta set here).

For each `revise` / `add` (and any `keep` promoted by the challenge pass), ask the user one focused question with the research in hand → the new value. `keep` decisions (not promoted) carry forward unchanged (they were ingested at triage-accept in Step 3).

**Persist each re-decided value through an `architect-brain` event — never hand-edit a projection.** Write every value with:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision <key> <json-value>
```

where `<key>` is the **canonical flat decision key** resolved in Step 2 / by `design-recovery` (`architecture.style`, `database.engine`, `backend.api_style`, `cicd.platform`, `platforms`, …), falling back to the project-specific descriptive slug when there's no canonical equivalent; and `<json-value>` is the value encoded as JSON (e.g. `'"PostgreSQL"'`, `42`, `true`, `'["web","cli"]'`). Each `set-decision` emits a `DecisionMade` event and re-materialises the projections.

> **Ingest the keep set in Step 3, then set the deltas individually here.** The kept (and validation-corrected) rows from Step 3 — `design-recovery` emits the recovered design as a **flat decisions keyspace** — were ingested at triage-accept with one `set-decision` per kept key (see Step 3). Here in Step 5, the `revise` / `add` (and challenge-promoted `keep`) rows are each updated with `set-decision`. So the keep set is ingested at triage-accept; the deltas are set **one by one** as they're decided.

The result is a complete, current **decision set in the flat keyspace**, recorded entirely via `DecisionMade` events (no hand-edited JSON), so the project is henceforth a flat-keyspace, **re-derivable** project — `99-flat-index.json` carries the full `{decisions: {dotted-key: value}}` set that Step-6 `catalog list` evaluates and each template's `required_decisions` slices. Recovered decisions that don't map to a known canonical flat key are kept as **project-specific keys** (descriptive slug); re-derive consumes what it can.

## Step 6 — RE-DERIVE everything (full re-bootstrap scope)

> Sub-ledger: `set-substep rearchitect rederive --status in_progress` on entry; `… rederive --status done` once docs + superseding ADRs + `CLAUDE.md` + `.claude/` tooling are all regenerated.

From the re-decided flat decision set, regenerate the generated artifacts against the current v8 templates — but **preserve-and-update** rather than blank-skeleton overwrite for docs that are richer than (or absent from) the catalog, per the policy below. The old copies were snapshotted in Step 1, so nothing is lost regardless:

- **Design docs + superseding ADRs** — compute the applicable, topologically-ordered doc set declaratively with `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain catalog list` (it evaluates each doc's `conditions` in [`references/catalog.json`](catalog.json) against the re-decided `99-flat-index.json` and returns them in dependency order), then dispatch **`document-author`** per selected doc. Each **changed** decision files a **new ADR that supersedes** the prior one via `architect-brain record-adr --phase iteration <NNNN> "<title>" Accepted --supersedes <id>` (an `ADRFiled` / `ADRSuperseded` event) — the originals are preserved as history (ADRs are superseded, never deleted). Record each regenerated doc with `architect-brain record-doc` (a `DocGenerated` event with a SHA-256 `content_hash`). See [`document-catalog.md`](document-catalog.md) for the per-doc semantics the catalog encodes.
- **`CLAUDE.md` (root + per-folder)** — dispatch **`claude-md-author`** against the current `CLAUDE_MD_*` templates.
- **`.claude/` tooling** (settings.json, hooks, agents, commands, recommended-plugins) — dispatch **`claude-tooling-author`** against the current tooling templates. This carries the version-awareness gate into the re-architected project's generated `/implement` `/scaffold` `/iterate-design` commands (the single source of truth those commands cite is [`references/version-awareness.md`](version-awareness.md)).

**Preserve-and-update, not blank-skeleton (the from-old-version reality).** A from-old-version project frequently hand-authored docs that are RICHER than the current v8 catalog template, or carries **bespoke docs the catalog has no template for at all**. For those, do NOT regenerate from a blank template skeleton — that discards the hand-authored substance:

- **Doc is richer than its catalog template** (the old project captured detail the template doesn't), OR is a **bespoke doc with no catalog template** → dispatch **`document-author`** with the **existing doc + the relevant research + the re-decided decisions as the PRIMARY input** and update it **in place**. The author refreshes it against the new decisions while keeping the hand-authored richness; it never overwrites a rich doc from a blank skeleton. (The Step-1 snapshot preserves the original regardless — but the *live* re-derived doc must keep the substance, not just the template's headings.)
- **Bespoke docs with no template: keep, stamp, link.** A doc the catalog has **no template** for is NOT dropped — keep it, stamp it with the current `format_version`, record it via `architect-brain record-doc`, and ensure it is linked from the doc set's cross-references so the `cross_link_integrity` check (22, BLOCKING) sees it.
- **The doc set may grow.** The v8 catalog will select docs the old project lacked (`catalog list` returns them) → generate *those* fresh from template. Net: the live **doc set may grow** after re-derive (new catalog docs added on top of the preserved bespoke docs) — that is expected, not an error.

Because the catalog docs are authored new (and the preserved/bespoke docs are re-stamped + re-recorded), the doc set carries the current `format_version` + provenance stamps and resolves cross-links by construction.

**Existing CODE is NOT regenerated.** The flow emits an **affected-code-areas** list (reuse the coarse `project_layout` → top-level-component mapping in [`revision-playbook.md`](revision-playbook.md)) telling the user where the changed decisions invalidate built code, so they can re-run `/implement` / `/scaffold` there deliberately. The flow NEVER rewrites the user's source.

## Step 7 — RE-GATE + RE-LOCK (major bump)

> Sub-ledger: `set-substep rearchitect regate --status in_progress` on entry; `… regate --status done` as the FINAL action, once the gate is green AND the relock + new snapshot have been recorded — this clears the last incomplete step so the situation-assessment routine no longer reports the flow as interrupted.

Reconcile the **phase trajectory** so the re-architected (fully re-decided) design reads as a completed run — the project genuinely walked every phase, so emit the `PhaseAdvanced` events that bring the `workflow` projection to a completed trajectory before the gate (otherwise a sparse phase history makes `phase_gates` (16) / `no_oob_phase_advance` (20) fail). Walk the v8 ladder in order with `set-phase` (each emits a real-timestamped `PhaseAdvanced` event; phases are projections of these events, never a hand-edited pointer):

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase architecture \
  && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase stack \
  && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase cost \
  && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase docs \
  && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase iteration \
  && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase lock
```

(Emit only the phases the re-decided design actually covers, in ladder order — `no_oob_phase_advance` (20) verifies the entered-phase sequence is monotonic in ladder order (no backward jump); `phase_gates` (16) verifies chain continuity (`this.from == prev.to`) — so the trajectory must be coherent.)

Because re-architect is design-only (it never rebuilds code), record `scaffold.deferred = true` before re-gating — the `scaffold_executed` (26, BLOCKING) check treats a deferred scaffold as satisfied:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision scaffold.deferred true
```

(If the user chose option 2 "upgrade then rebuild", the subsequent `/scaffold` clears the deferral.)

Run the full **35-check audit** (must be green):

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --verbose
```

The audit runs all 35 in-process Python checks (4-tier severity: FATAL / BLOCKING / WARNING / INFO), prints one line per check + a verdict, **records an `AuditCompleted` event itself** (so `audit_freshness` (19) sees a fresh pre-lock audit — there is no separate "record the audit" step), and exits non-zero if any failure blocks LOCK. The re-architect **cannot COMPLETE until the audit's verdict is clean** — no FATAL and no un-acked BLOCKING (identical enforcement to the bootstrap gate): mechanical gaps auto-remediate (a missing ADR file → `record-adr` + write the file; a missing required doc → re-dispatch `document-author` + `record-doc`; then re-run the audit), while a genuine BLOCKING hard-stops with its remediation defaulted. The three FATALs — `state_schema_valid` (29), `resume_test` (31, the replay invariant), `catalog_topo_acyclic` (32) — can never be acked. A BLOCKING finding may be downgraded only with an explicit, recorded `--ack=<reason>`.

Then re-lock at a **bumped MAJOR version** (e.g. `v1.4 → v2.0`, signaling a from-first-principles re-architect, not an in-place `+0.1` iteration) by emitting a `LockSet` event (the lock is part of the event log, not a hand-edited field), and snapshot the new design:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain append-event --type LockSet \
  --payload '{"locked": true, "version": "<new-version>"}'
# the binary stamps the real locked_at into the event ts; the workflow projection re-materialises
mkdir -p docs/versions/<new-version>
cp -R docs/*.md docs/_architect_state/decisions docs/research docs/versions/<new-version>/ 2>/dev/null || true
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision snapshots.<new-version> '"<ISO8601>"'
```

The project is now a flat-keyspace, gate-green, fully decision-anchored v8 project with a complete `docs/versions/` trail from `<old-version-label>` to `<new-version>`. Present the branch-merge handoff: name the `rearchitect/architect-<date>` branch, note deploys read `main` (not live until merged), and offer the `--ff-only` merge.

---

## What is reused vs. new

| Concern | Mechanism |
|---|---|
| Detect / migrate-to-v8 / reconcile-adrs | `bin/architect-brain` (`detect` / `migrate` / `reconcile-adrs`) — reused |
| Snapshot / re-lock | `docs/versions/<v>/` copy + a `LockSet` event (`append-event --type LockSet`) — reused plumbing |
| Recover design from docs → structured artifact | **`design-recovery` agent (new)** |
| Triage surface (keep/revise/drop/add, validation gate) | **bespoke prose in this flow (new)** |
| Research the deltas + challenge the keeps | `research-scout` — reused |
| Ingest decisions (keep set + deltas) | `architect-brain set-decision` (one `DecisionMade` per key) — reused |
| Declarative doc selection | `architect-brain catalog list` over `references/catalog.json` — reused |
| Re-derive docs / ADRs / `CLAUDE.md` / tooling | `document-author` / `claude-md-author` / `claude-tooling-author` (+ `record-adr` / `record-doc`) — reused |
| Affected-code-areas map | `revision-playbook.md` — reused |
| Quality gate | the 35-check `architect-brain audit` (4-tier severity) — reused |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
