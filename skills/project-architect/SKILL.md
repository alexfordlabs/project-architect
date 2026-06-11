---
name: project-architect
description: Use when the user wants to set up a new project, scaffold project docs, plan a new project, initialize project architecture, bootstrap with planning documents, design a system architecture, choose a tech stack, revisit existing project architecture decisions, or generate CLAUDE.md and .claude/ config for an existing project. Works for any project type — web apps, mobile, multi-platform, APIs, CLI tools, libraries, desktop, browser extensions, games, AI/ML, data pipelines, embedded/IoT, infrastructure, Claude Code plugins, MCP servers, agentic systems, Web3, scientific code, AR/VR, programming language design.
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Project Architect

You orchestrate a 12-phase project bootstrap (preflight → 0a repo init → kickoff → vision → **architecture** → **stack** → cost → docs → iteration → lock → tooling → handoff). You do not do the heavy lifting yourself — you dispatch subagents, invoke skills, run the `architect-brain` binary, and synthesize. Load references on-demand from `references/`.

**The one binary.** Every mechanical operation — state mutation, phase advance, doc selection, the audit gate, the UI, golden paths, config/diagram generation, migration — goes through `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain` (a thin shim over `python -m architect_brain`). It reads/writes the event-sourced state under `docs/_architect_state/` (the default `--docs-dir` is `docs`). You never hand-edit the state files.

**Output style:** surface clean informational progress per `references/output-style.md`. **You RENDER the UI by RUNNING the binary — never by transcribing its art.** Open the run by running `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui banner` (its stdout prints the banner into the tool result the user sees); then at every phase boundary the transition contract's `set-phase` write ALSO runs `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar <phase>` in the SAME Bash call (`architect-brain set-phase <phase> && architect-brain ui phase-bar <phase>`), so the advancing bar prints in that same tool result. The banner + bar are your curated narration: you RUN the binary and let its stdout show — **the tool-result block IS the user-visible surface; never suppress it.** Add `✓`/`→`/`✗` step lines (`architect-brain ui` has no `step` subcommand — render them inline, or via the `step()` helper's symbols) for what completed. Capture *every other* mechanical output (event ULIDs echoed by `set-decision`/`record-*`, the audit's per-check lines when you only need the verdict, `find`/`grep`) and never dump it raw.

## Phase order

```
-1. Preflight              — model + effort + 1M-context verification
 0a. Repo Init (optional)  — git init + remote
 1.  Universal Kickoff     — Golden-Path offer (0a) + Q1–Q8 + first research dispatch
 2.  Vision & Scope        — type-specific drill-down + research + universal CLI-UX gate
 3.  Architecture          — architecture-specialist: STYLE/boundaries/data-flow/scaling BEFORE the stack + inline consistency check
 4.  Tech Stack            — type-aware options + per-language CLI-UX picker + ADR per major decision
 5.  Cost Modeling         — pricing research → COST_MODEL.md draft
 6.  Document Generation   — declarative catalog.json selection → parallel document-author dispatch + architect-brain audit
 7.  Iteration             — decision-revisor loop, audit-seeded menu, snapshot option
 8.  Lock / Post-Generation — commit/push, plugin install offers, LOCK v1.0
 9.  Tooling Execution     — menu: execute CLAUDE_MD_PLAN / CLAUDE_TOOLING_PLAN / hand off SCAFFOLD_PLAN to superpowers
 10. Handoff               — print restart instructions; future sessions auto-load CLAUDE.md router
```

The v8 reorder (vs v7): **Architecture is decided BEFORE the tech stack** — domain shape and boundaries first (Spec-Kit / DDD / Anthropic alignment: decide *what the system is* before *what it's built with*), infrastructure second. **Cost** is its own phase. The `set-phase` keys are the bare ladder keys: `preflight`, `kickoff`, `vision`, `architecture`, `stack`, `cost`, `docs`, `iteration`, `lock`, `tooling`, `handoff`, `complete` (see `references/decision-keys.md` and the UI ladder).

## State

Persistent across the bootstrap: **`docs/_architect_state/`** — an event-sourced, multi-file directory (NOT a single monolith JSON). Its model, files, lockfile protocol, and migration policy are documented in `references/state-schema.md`. The pieces:

- **`docs/_architect_state/events.jsonl`** — the append-only, authoritative event log (the ground truth). Every state change is one event (`DecisionMade`, `ADRFiled`, `DocGenerated`, `PhaseAdvanced`, `AuditCompleted`, `GoldenPathApplied`, `LockSet`, …). Each event is `{id (ULID), ts, by, phase, type, payload}`.
- **Per-concern projections** (`<concern>.json`, 11 concerns: `identity`, `vision`, `architecture`, `stack`, `cost`, `ai_agent`, `api_contract`, `docs`, `workflow`, `tooling`, `handoff`) — materialised views derived by `replay`.
- **`docs/_architect_state/99-flat-index.json`** — the flat `{decisions: {dotted-key: value}, adrs: […]}` fast-query + reverse-engineer-interop view.
- **`docs/_architect_state/decisions/index.json`** — the ADR ledger projection; **`decisions/*.md`** — the ADR markdown files.
- **`docs/_architect_state/schema_version`** — a one-line probe file, the literal `"4.0"`.

The invariant `replay(events) == projections` is the central correctness property (enforced by audit `check 31 resume_test`, FATAL). **Never hand-edit any state file** — every mutation flows through an `architect-brain` event. The state directory is **never deleted by the orchestrator** (it is the canonical cross-session entry point and must persist past LOCK for re-invocations and for `/iterate-design`).

Lock file: `docs/_architect_state/.lock` with `{pid, host, acquired_at}`. Held throughout the session. If a stale lock (>30 min old) exists at startup, offer to clear it.

## Phase transition contract

Every phase transition is a **mechanically-gated operation**, not a prose suggestion. The orchestrator never hand-edits the phase pointer and never moves forward on a "looks done" judgment. Each transition runs these five steps in order:

```
1. SET-PHASE + UI → ONE Bash call:
                   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase <next_phase> && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar <next_phase>
                   `set-phase` emits a PhaseAdvanced event (real `ts` from the binary's own UTC
                   clock — never a typed literal) recording the move from the current phase to
                   <next_phase>; the projections re-materialise and `workflow.current_phase`
                   updates. It prints only the event ULID (capture it). `architect-brain ui
                   phase-bar` then prints the advancing bar for <next_phase> into the SAME
                   tool-result block: the user-visible progress heartbeat. Because the bar rides
                   on the mandatory set-phase event, it can never be skipped (the whole reason
                   inline rendering kept failing).
2. RUN PRE-GATE  → run the checks mapped to this transition (table below) by running
                   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit [--only NN] [--verbose]
                   (`--only NN` spot-runs one check; no flag runs all 35 and records an
                   AuditCompleted event). The audit prints one line per check + a verdict and
                   exits 1 if any failure blocks LOCK.
3. RESOLVE       → mechanical / auto-fixable gap (a WARNING — e.g. a missing ADR file, an
                     incomplete ledger entry): the orchestrator AUTO-PERFORMS the skipped step
                     itself — file the missing ADR (architect-brain record-adr + write the
                     file), record the missing doc (architect-brain record-doc), fix the
                     failed-open glob — then RE-RUNS the audit.
                   judgment finding / BLOCKING / FATAL: HARD STOP. Surface the finding and its
                     remediation. The remediation is the DEFAULT option presented to the user —
                     NEVER label "proceed anyway" / "approve" as recommended while a BLOCKING or
                     FATAL finding is open. (A BLOCKING finding may be downgraded only with an
                     explicit `--ack=<reason>`; FATAL can never be acked. The ack reason is
                     persisted into the `AuditCompleted` ledger entry, so an acked-clean audit
                     is distinguishable from a genuinely-clean one and the waiver is auditable.)
4. ADVANCE       → only after the gate is clean does the next phase's work begin. The continuous
                   `no_oob_phase_advance` check (20, BLOCKING) detects any phase that advanced
                   without its predecessor's PhaseAdvanced event, so a bypassed gate is itself caught.
5. NARRATE (UI)  → the bar printed by step 1 IS the boundary's visible heartbeat — let that tool
                   result show, never suppress it. Then add the `✓`/`→`/`✗` step lines for what
                   just completed (render them inline). The banner opens the FIRST reply of the
                   run, in Preflight (run `architect-brain ui banner` once); the bar then leads
                   every boundary thereafter via step 1.
```

The orchestrator still *invokes* the audit at each transition (one mechanical step), but the gate logic is in-process Python code with fixtures and tests (the 35-check `architect_brain.checks` library) — not prose the model can rationalize past. The rationalization table below is belt-and-suspenders, never the sole control.

### Which check runs at which transition

The 35 checks live in `architect_brain.checks` (4-tier severity: FATAL / BLOCKING / WARNING / INFO). A full `architect-brain audit` runs them all; `--only NN` spot-runs one at the boundaries below.

| Check (ID, severity) | Runs at | On fail |
|---|---|---|
| `no_oob_phase_advance` (20, BLOCKING) | every transition (continuous) | block |
| `phase_gates` (16, BLOCKING) | Doc-gen entry (pre-dispatch) | block |
| `ledger_complete` (18, WARNING) | every phase exit | auto-remediate |
| `adr_files_exist` (17, WARNING) | Architecture→Stack entry + pre-lock | auto-remediate |
| `dependency_freshness` (23, WARNING) | Doc-gen pre-plan-write | surface |
| `settings_permissions_valid` (21, WARNING) | Doc-gen + Tooling audit | auto-remediate |
| `cross_link_integrity` (22, BLOCKING) | Doc-gen + Tooling audit + pre-lock | block |
| `required_docs_generated` (27, BLOCKING) | Doc-gen exit (pre-audit) | block |
| `audit_freshness` (19, BLOCKING) | pre-lock | block |
| `identity_hygiene` (24, BLOCKING) | after research/doc writes (kickoff–doc-gen) | block |
| `anonymity_threat_preflight` (25, WARNING) | Preflight + Cost | surface |
| `scaffold_executed` (26, BLOCKING) | Handoff | block |
| `state_schema_valid` (29, FATAL) | every full audit | block (no ack) |
| `resume_test` (31, FATAL) | every full audit | block (no ack) |
| `catalog_topo_acyclic` (32, FATAL) | every full audit | block (no ack) |

### Red flags — STOP

If you catch yourself reaching for any of these rationalizations mid-run, STOP — the gate exists precisely to catch this.

| Rationalization | Reality |
|---|---|
| "I'll file ADRs later to save time." | A run that defers ADRs back-fills them post-lock with fabricated timestamps. `adr_files_exist` (17) blocks Stack-phase entry AND lock until each recorded ADR has a file. File it the moment the decision is made — `architect-brain record-adr` stamps a real time. |
| "The audit can run after lock — it's just a formality." | An audit that runs after lock is too late; `audit_freshness` (19, BLOCKING) refuses to let the lock menu render without a fresh pre-lock audit. The full `architect-brain audit` is the Doc-gen→Iteration gate, not a closing ceremony. |
| "Skip the gate this once — it's probably fine." | "Probably fine" is exactly what shipped a Tor product with a Firebase backend and the operator's real name in a research doc. The audit is one mechanical call; skipping it is the failure mode it was built to stop. |
| "I'll set the phase directly, faster than the binary." | There is no phase to hand-edit — the phase pointer is a projection of the PhaseAdvanced events. Always `architect-brain set-phase`; anything else leaves no event and `no_oob_phase_advance` (20) catches the gap. |
| "The scaffold plan is written, so the project is done." | A written plan is not an executed scaffold. `scaffold_executed` (26, BLOCKING) blocks the COMPLETE message until `project_layout` paths exist on disk (or scaffolding was explicitly deferred). |
| "The doc set is close enough — I'll generate the last doc later." | A run that silently skips a `generate_when: always` doc (e.g. `PROJECT_REQUIREMENTS.md`, which `/implement` reads feature specs FROM) surfaces only a dangling cross-link symptom, post-hoc. `required_docs_generated` (27, BLOCKING) blocks the Doc-gen→Iteration audit until every always-generated doc-class doc (`docs/<NAME>.md`) exists. Generate it now via `document-author`. |

## Resumability

At startup, classify the project with one read-only query:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect
```

`detect` returns JSON with `situation` ∈ `greenfield` | `v8_project` | `pre_v8_project`, plus `schema_version` and `state_layout`.

- **`v8_project`** (`docs/_architect_state/` with `schema_version` `"4.0"`): read the projections (`workflow.json` for `current_phase`; `99-flat-index.json` for decisions), print a resume summary, and jump to the recorded phase.
- **`pre_v8_project`** (a v7 monolith `docs/_architect_state.json` exists with schema < 4.0): route to migration. Run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate` (optionally `--from 3.1`) BEFORE proceeding. Migration snapshots the monolith, synthesizes events, replays, re-stamps ADRs/docs, reindexes phases, compares (replay == projections), and atomically flips to `docs/_architect_state/` (reversible via the kept backup tarball). It runs a post-migration audit by default; a blocking post-migration audit leaves the state preserved for review. See `references/state-schema.md` migration policy.
- **`greenfield`** (no architect state): refine foreign-vs-empty (see "State file initialization" below), then bootstrap.

If `schema_version` is **newer** than this plugin supports, refuse with a clear message rather than guessing — the orchestrator compares the reported `schema_version` against the band `migrate` enforces (`migration._check_band`) and refuses; `detect` itself reports only the raw `schema_version`, it does not compute the verdict.

### Resume from locked state (sketch D)

If the `workflow` projection reports the design is **locked** at a named version (e.g. `v1.0`), the orchestrator does NOT silently re-enter Iteration — that would risk overwriting locked decisions. Instead, surface the locked status to the user and offer three explicit options:

```
This project's design is locked at {{version}} (locked at {{locked_at}}).

What would you like to do?
  (a) Unlock and revise — bump to {{version}}+0.1-draft, re-enter Iteration
  (b) Open the v1.0 snapshot for reference (read-only)
  (c) Exit — no changes
```

On **(a) Unlock and revise**:
- Snapshot the currently-locked docs to `docs/versions/{{version}}/` BEFORE unlocking (preserves the immutable lock-point so the user can always diff against it).
- Emit a `LockSet` event setting locked = false with version `"<previous>+0.1-draft"` (e.g. `"v1.0" → "v1.1-draft"`) and a null `locked_at` (via `architect-brain append-event --type LockSet`).
- Re-enter Iteration with all prior ADRs and docs intact; the user revises in place.
- When the user re-locks at end of the Lock phase, version becomes `<previous>+0.1` without the draft suffix (e.g. `"v1.1-draft" → "v1.1"`), and re-snapshot the new locked docs to `docs/versions/{{new_version}}/`.

On **(b) Open the v1.0 snapshot for reference (read-only)**:
- Surface the path `docs/versions/{{version}}/` and list its top-level files. Do not modify state. Do not enter any phase. Exit cleanly.

On **(c) Exit**:
- Save no changes. Release the lockfile and exit.

This is also the path that the `/iterate-design` slash command takes (see `references/templates/SLASH_ITERATE_DESIGN.md` template). When `/iterate-design` is invoked on a locked project, it short-circuits directly to option (a) without re-prompting.

### Resume from a half-locked state — interrupted `/iterate-design`

A clean `/iterate-design` unlock emits a `LockSet` event with locked = false AND a `-draft`-suffixed version (e.g. `"v1.0" → "v1.1-draft"`); the matching re-lock at end of the Lock phase emits a `LockSet` with locked = true and strips the suffix (`"v1.1-draft" → "v1.1"`). If a session is interrupted between those steps, the state is **half-locked** — a crash-safety hazard the orchestrator MUST detect at resume rather than silently re-entering a phase.

Detect a half-locked state when ALL hold (read from the `workflow` projection): locked == false AND `version` is set (non-null) AND `version` does NOT end in `-draft` AND `current_phase` is past `iteration`. When detected, do NOT silently resume — surface the interruption and let the user choose to **finish or roll back**:

```
This project has an interrupted design revision (unlocked at {{version}}, phase {{current_phase}}).
Finish or roll back?
  (a) Finish — re-enter Iteration to complete the revision, then re-lock at {{version}}
  (b) Roll back — restore the last locked snapshot (most recent recorded snapshot) and re-lock at that version
```

On **(a) Finish**: re-enter Iteration with the current docs and ADRs intact; the user completes the revision and re-locks at the end of the Lock phase (the version keeps its current value, suffix-free).
On **(b) Roll back**: restore the docs from the most recent snapshot recorded in the `workflow` projection's snapshot list — `docs/versions/{{last_snapshot}}/`, the last design version actually written to disk. (Do NOT key the restore on `{{version}}`: in a half-locked state it may already hold the rewritten, suffix-free version whose snapshot directory does not exist yet.) Then emit a `LockSet` event with locked = true, a fresh `locked_at`, and `version` set to the restored snapshot's version, and exit cleanly — leaving the project re-locked at the last good locked point as if the interrupted `/iterate-design` had not started.

### Version-staleness gate (Plan F)

Runs at Resumability **after** any half-locked state is resolved (crash-safety first), and before the locked-resume menu. `detect` reports the situation; for a `pre_v8_project` (schema < 4.0) you route to `architect-brain migrate` (above). For projects that are within the migratable band but a different format generation, present the **four-option intent menu** *before* the locked-resume options. The canonical menu text + per-option semantics live in [`references/version-awareness.md`](references/version-awareness.md) (the single source of truth the generated `/implement`, `/scaffold`, and `/iterate-design` commands also cite, so every entry point behaves identically):

> **(1) Upgrade design, then continue** — run `/upgrade-project` (see `references/upgrade-flow.md`), then resume here; KEEPS your build, FLAGS affected-code-areas.
> **(2) Upgrade design, then rebuild code** — upgrade, then re-scaffold / re-implement.
> **(3) Start fresh, revisiting decisions** — full re-bootstrap with old decisions pre-seeded as defaults.
> **(4) Proceed without upgrading** — continue on the old version, warned; record the version-gate acknowledgement (a `DecisionMade` for `version_gate_ack`) so the menu isn't re-asked.

**Precedence** (when several gates could fire at Resumability): half-locked resolution → interrupted-flow resume offer → this version-staleness gate → the locked-resume menu. If none fire, proceed normally.

### Situation assessment & routing (the Resumability entry routine)

The orchestrator runs the [`references/situation-assessment.md`](references/situation-assessment.md) routine whenever it opens a project that already has architect history (a `docs/_architect_state/` directory exists, or a v7 monolith `docs/_architect_state.json` exists, or the folder otherwise looks like a prior project). That routine **assesses** the full situation read-only — the `architect-brain detect` verdict, the project-folder inventory, AND **every git branch** (`git branch -a` + `git show <branch>:docs/_architect_state/99-flat-index.json` or `git show <branch>:docs/_architect_state.json` for a v7 branch, never a checkout/merge/reset) so interrupted work on another branch is found — then **routes** to the right existing flow. It is the assessment + dispatch front-end for the precedence chain above; it does not introduce a new menu.

The same routine also handles the **inverse** case (reverse-engineer interop): a **foreign project** — a folder with real project material (source, package manifests, docs, a non-trivial tree) but **no architect state** (`detect` reports `greenfield` yet the tree is non-trivial), i.e. one project-architect never produced. There it offers the **reverse-engineer** route: if the `reverse-engineer` companion plugin is installed, invoke it (it recovers a design and emits project-architect's own flat-decisions keyspace with `origin: "reverse-engineered"`); if not, point the user to it (`alexfordlabs/reverse-engineer`, same `alexfordlabs` marketplace). Its output is then consumed through the **existing** seeded-greenfield / import-decisions path — no new ingest path. See `references/situation-assessment.md` §2 ("Reverse-engineer this foreign project").

One route the chain now offers explicitly: an **interrupted-flow resume**. When the `workflow.json` projection's `substep` shows a `/re-architect` or `/iterate-design` sub-flow left at `status: "in_progress"` (each sub-flow records its progress per step via `SubstepRecorded`), offer to resume it from that step — the situation-assessment routine reads this from the projection, not from `detect` (which reports only `situation` / `schema_version` / `state_layout`). This sits between half-locked resolution (crash-safety) and the version-staleness gate in the precedence above. (A half-locked state defers to the "Resume from a half-locked state" finish/roll-back handling; the version-staleness routing defers to `references/version-awareness.md`.) The situation-assessment doc also documents the **seeded-greenfield** arm of "start fresh" (fresh bootstrap with recovered decisions pre-seeded via `architect-brain set-decision` per recovered key, old scaffold snapshot+aside), the sibling of the in-place `/re-architect` arm.

---

## Phase -1: Preflight

**Open the run.** Preflight is the run's first phase, so this is your first reply — open it by RUNNING `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui banner` (a Bash call; its stdout prints the banner into the tool result the user sees — do NOT merely describe or transcribe it). The banner appears ONCE, here. The first phase bar follows at the first transition, via the folded `set-phase … && architect-brain ui phase-bar …` of the transition contract's step 1.

**Interpreter floor (the python3 probe).** The `architect-brain` wrapper guards its own interpreter floor: every invocation first checks `python3` exists and is `>= 3.10`, and exits with a clean one-line message (not a raw traceback) otherwise. So if this opening `ui banner` call fails with `architect-brain: Python … too old` or `python3 not found`, STOP and tell the user the gate cannot run until a Python `>= 3.10` is on PATH — do not proceed. (This is the guard the later "Preflight should have caught this" lock-gate note relies on.)

### Ambient hooks tolerance

Runs FIRST in Preflight so the `remember` plugin's PostToolUse hook (if installed) sees its log directory exist starting from its very first invocation, avoiding any transient hook-error noise in the user's transcript during the rest of Preflight.

Silently pre-create `.remember/logs/` in cwd so the `remember` plugin's PostToolUse hook (if installed) can write its error log without erroring out. Run as `Bash`:

```bash
mkdir -p .remember/logs 2>/dev/null || true
```

The `|| true` ensures failure never blocks Preflight — the architect doesn't depend on this directory. This is a courtesy to a separate plugin and is harmless when `remember` isn't installed (the dir is empty + listed in `.gitignore` by Phase 0a). It lives in Preflight (not Phase 0a) because the hook fires on the first Bash/Read call regardless of whether the user opts into git init. PostToolUse hooks fire AFTER the tool completes, so the very first `mkdir` call's hook sees the directory already created by that same call, and every subsequent tool call is clean.

### Model/effort verification

Verify the harness is running a current-generation Opus (Opus 4.x) with 1M context at max effort.

1. Read the model identifier from the system env metadata. Look for the line `The exact model ID is claude-<...>` in your context.
2. **If model is a current Opus with the `[1m]` 1M-context variant** (e.g. `claude-opus-4-8[1m]`): silently proceed.
3. **If model is a current Opus WITHOUT the `[1m]` variant**: invoke `Skill: update-config` to set the latest Opus model + `env.ANTHROPIC_CONTEXT_VARIANT: "1m"` in global settings; then prompt the user:
   > This skill requires a current-generation Opus with 1M context at maximum effort.
   > Settings file updated for future sessions. For *this* session, please run:
   >   /model       → select the latest Opus (1M context)
   >   /effort max
   > Reply "continue" when done.

   Wait for "continue."
4. **If model is anything else** (sonnet, haiku, or an older generation): same prompt as step 3 but without the autofix (since the user's current session won't have inherited the desired model yet).
5. **If the user declines to switch**: refuse to start. Output a clear message: "project-architect requires a current-generation Opus (1M context) for the quality of reasoning needed across phases. Please restart with the correct model."

Effort verification: not directly detectable from env. Trust the user's `/effort max` confirmation. As a fallback, include the directive `"Run with maximum effort. Apply extended thinking. Be thorough."` in every subagent prompt header and every `Skill` invocation context.

### Soft-dependency check

Claude Code's plugin schema only supports hard `dependencies`; there is no declarative soft / recommended-plugin field. We surface recommended plugins via a runtime probe here so missing ones are obvious before Kickoff.

Recommended plugins (qualified names): `superpowers`, `claude-md-management`, `claude-code-setup`, `hookify`, `document-skills`, `fewer-permission-prompts`.

1. For each recommended plugin, probe installation:
   ```bash
   claude plugin list 2>/dev/null | grep -i "<plugin>" \
     || ls ~/.claude/plugins/cache 2>/dev/null | grep -i "<plugin>"
   ```
   Treat a non-empty match as installed.
2. For each missing plugin, emit one line to the user, e.g.:
   - `superpowers` — `claude plugin install superpowers` — used by Doc-gen (`superpowers:dispatching-parallel-agents`) and Tooling Execution (`superpowers:writing-plans`).
   - `claude-md-management` — `claude plugin install claude-md-management` — used by the `claude-md-author` agent.
   - `claude-code-setup` — `claude plugin install claude-code-setup` — used by the `claude-tooling-author` agent for `.claude/` scaffolding.
   - `hookify` — `claude plugin install hookify` — used by `claude-tooling-author` when generating project hooks.
   - `document-skills` — `claude plugin install document-skills` — used by `document-author` for diagrams / artifacts.
   - `fewer-permission-prompts` — `claude plugin install fewer-permission-prompts` — used by `claude-tooling-author` to tighten the generated `.claude/settings.json` permissions allowlist.
3. If any are missing, ask once via `AskUserQuestion` (load via `ToolSearch` if needed):
   > "Continue with current plugins? (yes / install missing now / abort)"
4. On `install missing now`: run each `claude plugin install <plugin>` sequentially; on each install failure, record and surface but do not abort the whole batch.
5. On `yes`: for every plugin still missing, record a `DecisionMade` event noting the missing recommended plugin (`recommended_plugins.<name>.missing = true`). The `claude-tooling-author` agent reads this in Doc-gen when generating `.claude/recommended-plugins.md` so the user's runtime choices are reflected in the final doc.
6. On `abort`: leave the phase at `preflight` and exit cleanly.

Skip the prompt entirely if every recommended plugin is already installed; just record each as not-missing and proceed silently.

If the kickoff has already flagged the project privacy-sensitive, note `references/anonymity-preflight.md` — the `anonymity_threat_preflight` check (25) will surface deanonymizing services at Cost.

### Version freshness check

Detect if the loaded skill is older than the latest release at the source repo, so users running a stale cache are warned and offered a refresh path. Best-effort: network errors, missing `gh`, or no published releases all degrade silently.

1. **Read the loaded version** from this plugin's own manifest. Claude Code exposes the install path via `${CLAUDE_PLUGIN_ROOT}`:

   ```bash
   LOADED=$(jq -r .version "${CLAUDE_PLUGIN_ROOT:-/dev/null}/.claude-plugin/plugin.json" 2>/dev/null || echo unknown)
   ```

2. **Read the latest released version** from the source repo. Try `gh` first (fastest, lowest rate-limit impact), then fall back to the public GitHub Releases API via `curl` (no auth needed for public repos):

   ```bash
   # Try gh first (fastest, lowest rate-limit impact)
   LATEST=$(gh release view --repo alexfordlabs/project-architect --json tagName --jq .tagName 2>/dev/null | sed 's/^v//')
   # Fall back to public GitHub API via curl (no auth needed for public repos)
   if [ -z "$LATEST" ]; then
     LATEST=$(curl -fsSL --max-time 5 https://api.github.com/repos/alexfordlabs/project-architect/releases/latest 2>/dev/null \
                | jq -r '.tag_name // empty' 2>/dev/null \
                | sed 's/^v//')
   fi
   LATEST="${LATEST:-unknown}"
   ```

3. **Compare** with semver-style ordering:
   - If `LOADED == LATEST` OR either is `unknown`: proceed silently.
   - If `LOADED < LATEST`: surface a one-time notice:

     > Loaded version v{{LOADED}} — a newer release v{{LATEST}} is available.
     >
     > To update (Claude Code with slash commands — recommended):
     >   `/plugin`                  → detects + downloads the update
     >   `/reload-plugins`          → applies it to the current session
     >
     > Fallback (older Claude Code without `/plugin` slash command):
     >   `claude plugin marketplace update <marketplace>`
     >   `claude plugin uninstall project-architect@<marketplace>`
     >   `claude plugin install project-architect@<marketplace>`
     >   `/reload-plugins`          (in this Claude session)
     >
     > Continue with v{{LOADED}} for this run? (yes / pause to update)

     If "pause to update": exit cleanly. If "yes": proceed and record a `DecisionMade` for `version_warning_acknowledged = true` so the warning doesn't repeat on the next phase.

4. **Skip the check** silently if:
   - `${CLAUDE_PLUGIN_ROOT}` is unset (rare; older Claude Code versions).
   - `curl` is not installed AND `gh` is not authenticated.
   - The repo has no releases yet.
   - Network is unreachable.

The check is best-effort and non-blocking. The architect's correctness does not depend on running the absolute latest version — this is purely a user-experience nudge so cache-staleness bugs (like loading v1 SKILL.md when v2 has shipped) surface immediately rather than mid-interview.

### Cache hygiene

Remove stale plugin-cache version directories so future invocations can't accidentally load an older copy. The architect knows its own install path via `${CLAUDE_PLUGIN_ROOT}`; sibling directories under the same plugin folder that aren't the current version are leftover from prior uninstall/install cycles.

```bash
# CLAUDE_PLUGIN_ROOT points at the *installed* version dir, e.g.
#   ~/.claude/plugins/cache/local/project-architect/8.0.0
# Its parent is the plugin folder containing every version that was ever installed.
if [ -n "${CLAUDE_PLUGIN_ROOT}" ]; then
  CURRENT_VERSION_DIR=$(basename "${CLAUDE_PLUGIN_ROOT}")
  PLUGIN_PARENT_DIR=$(dirname "${CLAUDE_PLUGIN_ROOT}")
  if [ -d "${PLUGIN_PARENT_DIR}" ]; then
    find "${PLUGIN_PARENT_DIR}" -mindepth 1 -maxdepth 1 -type d ! -name "${CURRENT_VERSION_DIR}" -exec rm -rf {} + 2>/dev/null || true
  fi
fi
```

Best-effort:
- Only acts when `${CLAUDE_PLUGIN_ROOT}` is set (older Claude Code versions: skip).
- Only removes sibling directories at the same depth — never touches files outside the plugin folder.
- `|| true` so failure never blocks Preflight.

After this step, if the freshness check found a newer version available but the user chose to continue, the cache for this specific plugin contains only the currently-loaded version — no ambiguity about which version a future session would load.

### State directory initialization

Run `architect-brain detect` (see Resumability). If it reports `greenfield`, the project has **no architect state**. Before initializing a fresh greenfield state, check whether the folder is actually a **foreign project** (real material — source, a package manifest, docs, a non-trivial tree — that project-architect never produced). If so, run the [`references/situation-assessment.md`](references/situation-assessment.md) foreign-project route (offer **reverse-engineer**: invoke the companion if installed, else point the user to `alexfordlabs/reverse-engineer`) instead of silently bootstrapping over it. If the folder is genuinely empty (greenfield), or the user opts to bootstrap fresh anyway, initialize:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain init   # creates docs/_architect_state/ (events.jsonl + empty projections + schema_version "4.0")
```

`init` writes `docs/_architect_state/` with an empty `events.jsonl`, the empty per-concern projections, `99-flat-index.json`, `decisions/index.json`, and the `schema_version` probe file at the literal `"4.0"`. Then record the run's opening facts as events — never by hand-writing JSON:

```bash
# the orchestrator's first events: who/when/what (the binary stamps real timestamps + ULIDs)
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase preflight
```

CRITICAL: the `schema_version` file is the literal string `"4.0"` (`init` writes it) — never the plugin version. Plugin provenance is carried in events' `by`/`payload`, not in `schema_version`.

---

## Phase 0a: Repo Init (optional)

1. Detect repo state:
   ```bash
   git rev-parse --is-inside-work-tree 2>/dev/null
   ```
   If exits 0: already a repo. Print remote info from `git remote -v` and confirm with user. Skip to Kickoff.
2. If not a repo: ask via `AskUserQuestion`:
   - Q: "Initialize git here?" options: "Yes — local only" | "Yes — with GitHub remote" | "No, skip"
3. If "Yes — with GitHub remote" was chosen:
   - Check `gh auth status` exit code.
   - If not authed: warn user, fall back to local-only with instructions for adding remote later.
   - If authed: ask via `AskUserQuestion`:
     - Repo name (default: `basename "$PWD"`)
     - Visibility: private / public / internal
     - One-line description (placeholder — refined after Kickoff Q1)
4. Execute:
   ```bash
   git init
   ```
   Write `.gitignore` with universal defaults (OS files: `.DS_Store`, `Thumbs.db`; editor files: `.idea/`, `.vscode/settings.json`, `*.swp`; env: `.env`, `.env.local`; ambient: `.remember/` — foreign-plugin courtesy, pre-created in Preflight). Stack-specific entries are appended in the Lock phase.
5. If remote requested and authed:
   ```bash
   gh repo create "$NAME" --"$VIS" --source . --remote origin --description "$DESC"
   ```
6. Determine branch strategy from prior knowledge (the stage question won't be answered yet — default to `main` for now; revisit if stage = "extending"/"rewriting"/"migrating", create `bootstrap/architect-<date>` branch at that point).
7. Record the repo facts as `DecisionMade` events: `scm.host`, `git.repo_init`, `git.has_remote`, `git.remote_url`, `git.branch` (`architect-brain set-decision <key> <value>`).
8. Commit via `Skill: commit-commands:commit` with hint message: `chore: initialize project repo`.
9. Transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase kickoff && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar kickoff` (this records the move into Kickoff). Then run the continuous gate (`architect-brain audit --only 20` + `--only 18`).
10. **Memory persistence:** Create the project memory file at `~/.claude/projects/<project-id>/memory/project_architect_<slug>.md` per `references/memory-persistence.md`. Append one-line entry to `MEMORY.md`. Record the pointer via a `DecisionMade` for `memory_pointer` (`{name, path, last_synced}`).

---

## Phase 1: Universal Kickoff

Load `references/questioning-flow.md` (Section: Universal Kickoff).

### Phase 0a — Golden Paths (the FIRST kickoff question)

Before the open-ended interview, offer the Golden Paths. List them with the binary so the labels stay authoritative:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain golden-path list
```

The 9 paths (`references/golden-paths.json`): `modern_saas_2026` (Modern SaaS 2026), `ai_rag_app` (AI/RAG), `mobile_cross_platform` (cross-platform mobile), `high_perf_api` (high-perf API), `pl_interpreter` (PL interpreter), `cli_rust` (Rust CLI), `cc_plugin` (Claude Code plugin), `mcp_server` (MCP server), `agentic_system` (agentic system). Ask via `AskUserQuestion`: "Start from a Golden Path (pre-fills 10–14 decisions you can revise), or interview me from scratch?"

- **If the user picks a path**: apply it — `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain golden-path apply <id>`. This emits a `GoldenPathApplied` event + one `DecisionMade` per pre-filled decision; the applied decisions become defaults the user can revise during the interview and Iteration.
- **If "interview me from scratch"**: proceed straight to the batches below with no pre-fill.

### Kickoff batches

Ask 3 batches via `AskUserQuestion` (load the tool via `ToolSearch` if not already available — see "Tool availability" below):

**Batch 1** (Identity & Type):
- Elevator pitch (open-ended).
- Top-level project type (multiple choice from the taxonomy — includes `agentic_system`).
- Sub-type (multiple choice, options depend on type; `agentic_system` → `single_agent` / `multi_agent_orchestrator` / `agentic_tool`).

**Batch 2** (Stage & Problem):
- Project stage (greenfield / extending / rewriting / migrating / PoC).
- Primary problem & target users (open-ended).

**Batch 3** (Constraints & Scale):
- Constraints (multi-select).
- Team & scale (combined multiple choice).
- Hard pre-existing decisions (open-ended).

After Batch 3:
1. Save all answers as `DecisionMade` events with **`--by user`** (`architect-brain set-decision <key> <value> --by user` — `project.type`, `project.sub_type`, `scale`, `team_size`, etc. per `references/decision-keys.md`). **Provenance rule:** a decision the user actually answered (via `AskUserQuestion`) is recorded `--by user`; only *derived/mechanical* keys the orchestrator computed without asking (repo facts, `memory_pointer`, `scaffold.deferred`) keep the default `--by orchestrator`. This is enforced: `user_provenance` (check 35, WARNING) flags a locked project whose decisions are ALL orchestrator-sourced — the signature of a skipped interview.
2. If stage ≠ greenfield: switch to `bootstrap/architect-<YYYY-MM-DD>` branch (`git checkout -b bootstrap/architect-2026-05-12`).
3. Commit via `commit-commands:commit`: `architect(kickoff): record kickoff decisions`.
4. Dispatch `research-scout` for domain research:
   Dispatch `project-architect:research-scout` (model `opus`, description "Kickoff domain research") with the **Shared dispatch header** + the **Kickoff — research-scout (domain)** body from `references/dispatch-prompts.md`, substituting the `{{...}}` context from the flat decisions.
5. Record the resulting research file as a `ResearchRefAdded` event (`architect-brain append-event --type ResearchRefAdded --payload '{...}'`).
6. Commit via `commit-commands:commit`: `architect(kickoff-research): domain research`.
7. Transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase vision && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar vision`, then run the gate (`architect-brain audit --only 20` + `--only 18`).
8. **Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with a Kickoff entry (kickoff decisions + domain research summary). If the memory pointer is null (e.g. user skipped Phase 0a), create it now.

---

## Agent dispatch — observer wrapper (sketch C)

Every `Agent({...})` dispatch is wrapped with the runtime-budget observer per `references/runtime-budgets.md`. The observer:
- Records dispatch start/end timestamps (as events) in the `workflow` projection's dispatch log
- Surfaces "silent for too long" warnings inline
- Surfaces "over budget" warnings inline
- Pre-populates the Iteration menu with `"review scope of <agent>"` items for over-budget runs
- **Never auto-kills** the agent — observation only

This is the bug-#9 mitigation (decision-revisor 6× cost overrun). With observation, the user sees the overrun in real time and can `Esc` if appropriate; the orchestrator records the telemetry for future tuning.

### Audit robustness

The audit is **in-process Python**, not a dispatched subagent — `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit` runs all 35 checks locally and never depends on the model backend (no 529-Overloaded failure surface). The auditor **never crashes on one bad check**: each check's `run()` is wrapped, so a single malfunctioning check degrades to a recorded failure rather than aborting the whole gate.

**HARD RULE — the orchestrator MUST NOT invent, estimate, or hand-wave findings, and MUST NOT skip the audit.** The gate is `architect-brain audit` — real in-process checks against the real `docs/_architect_state/` bundle. Never improvise an opinion about quality in place of running it. If `architect-brain` itself cannot run (e.g. `python3` unexpectedly missing — Preflight should have caught this), **STOP and tell the user the gate cannot be evaluated**; do not proceed past the gate on a guess. See the **Phase transition contract** "Red flags — STOP" table.

---

## Memory persistence (sketch D)

Every phase boundary updates a persistent memory file per `references/memory-persistence.md`. This keeps cross-session continuity for multi-day project-architect runs.

Cadence:
- **Phase 0a** (first write): create `~/.claude/projects/<project-id>/memory/project_architect_<slug>.md`; append one-line entry to `MEMORY.md`; record the pointer (a `DecisionMade` for `memory_pointer`).
- **Kickoff, Vision, Architecture, Stack, Cost, Doc-gen, Iteration** (per-phase updates): Edit the pointed-to file with a new dated entry summarizing what was decided/generated.
- **Lock** (major update): write "LOCKED at v1.0" header + full design summary; update `MEMORY.md` to mark project as locked.
- **Tooling, Handoff** (final updates): record execution outcome + handoff summary.

If the memory pointer is null at startup: this is the first write; create it.
If non-null but the pointed-to file is missing: regenerate from the projections (`99-flat-index.json` + `decisions/index.json`) and refresh the pointer.

See `references/memory-persistence.md` for the entry template and `MEMORY.md` index format.

---

## Tool availability

The `AskUserQuestion` tool is deferred — it may not be loaded into your context at startup. Before Kickoff Batch 1, run:

```
ToolSearch(query: "select:AskUserQuestion", max_results: 1)
```

If it loads, use it for all batches. If it doesn't load (rare edge case), fall back to plain-text prompts: print the questions inline, ask the user to reply with comma-separated answers, parse manually.

Similarly, `Skill` tool invocations require the referenced skill to be enabled. Before Phase 0a (the first `commit-commands:commit` call), verify the dependency is satisfied:

```bash
ls ~/.claude/plugins/cache | grep -i commit-commands
```

If not present: refuse to start with: "Required dependency `commit-commands` is not installed. Run `claude plugin install commit-commands` and retry."

---

## Phase 2: Vision & Scope

Load `references/questioning-flow.md` Section: "Per-Type Drill-Downs (Vision)" — read only the subsection for the project's `project.type`.

Loop until phase complete:
1. Ask one batch of 2–4 questions via `AskUserQuestion` covering the next unanswered area of the type-specific drill-down.
2. Save answers as `DecisionMade` events with `--by user` (per the Kickoff provenance rule).
3. Detect red flags in the answers (see `references/research-prompts.md` "Ad-hoc red-flag prompts"). For each flag, dispatch `research-scout` ad-hoc with the matching prompt. Record findings as `ResearchRefAdded` events.
4. Commit via `commit-commands:commit`: `architect(vision): {{batch summary}}`.
5. Decide if Vision is complete (all relevant areas for this project type answered).

At end of phase:
1. Dispatch `research-scout` with the Vision prompt (scope realism) — see `references/research-prompts.md`.
2. Commit findings.
3. Optionally surface major implications to the user; offer to revisit Vision answers if research suggests scope problems.
4. Transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase architecture && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar architecture`, then run the gate (`architect-brain audit --only 20` + `--only 18`).
5. **Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with a Vision entry (domain research summary + scope/feasibility framing).

### CLI sub-question routing

When `project.sub_type` is one of `cli_tool`, `cli_with_subcommands`, `tui_app`, or `interactive_cli`, dispatch the CLI experience-model gate question from `references/questioning-flow.md` (section "CLI experience model"). Save the answer as `cli.experience_model` (`--by user`). Route follow-up questions per the table in that reference. (The per-language CLI-UX library picker runs in the Stack phase.)

---

## Phase 3: Architecture (BEFORE the stack)

In v8 the architecture is decided **before** the tech stack: the system's shape, boundaries, and data-flow constrain which technologies even make sense. This phase runs the **`architecture-specialist`** agent.

Load `references/questioning-flow.md` Section: "Architecture Deep Dive (Architecture phase)".

1. **Dispatch `architecture-specialist`** to drive the architectural-style decision:
   Dispatch `project-architect:architecture-specialist` (model `opus`, description "Architecture style + boundaries") with the **Shared dispatch header** + the **Architecture — architecture-specialist** body from `references/dispatch-prompts.md`, substituting the `{{...}}` context (the vision + kickoff decisions). It questions architectural STYLE (monolith / modular monolith / SOA / microservices / serverless / event-driven / hexagonal), boundaries, data-flow, scaling axis — and recommends WITH rationale (**never microservices-by-default**). It records the `architecture.*` decisions: `architecture.style`, `architecture.boundaries.count`, `architecture.data_flow`, `architecture.scaling_axis`, `architecture.hexagonal`, `architecture.event_driven` (each via `architect-brain set-decision … --by user` once the user confirms the recommendation — the agent proposes, the orchestrator records the confirmed choice; per `references/decision-keys.md`).
2. For each major architectural decision, file an ADR via the ADR workflow (see "Filing an ADR" below).
3. Drill into the per-area concerns that the style implies (auth shape, data boundaries, API surface, security stance, integration topology). Ask 1–3 batches; record decisions as events.
4. Detect red flags; dispatch ad-hoc `research-scout`.
5. Commit: `architect(architecture/{{area}}): {{summary}}`.

### Inline consistency check (end of Architecture, before the stack)

Before exiting Architecture, cross-check the architectural decisions for internal contradictions (the stack-vs-architecture cross-checks come later, once a stack exists):
- **Style vs scaling axis**: e.g. monolith + "scale services independently" — flag.
- **Boundaries vs team size**: e.g. microservices + solo team — flag (recommend modular monolith).
- **Data-flow vs style**: e.g. event-driven claim + request/response data-flow only — flag.
- **Compliance vs boundaries**: e.g. HIPAA + a shared data boundary crossing trust zones — flag.

For each contradiction: surface to user with explanation and choices ("revise A, revise B, accept tradeoff"). User-chosen revisions dispatch `decision-revisor`.

End of phase: dispatch `research-scout` with the Architecture prompt (pattern validation). Commit findings. Transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase stack && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar stack`, then run the Architecture→Stack gate (`architect-brain audit --only 20` + `--only 18` + `--only 17` for `adr_files_exist`). **Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with an Architecture entry (`architecture.*` decisions + per-area ADR ids + consistency-check outcomes).

---

## Phase 4: Tech Stack

The stack is chosen to FIT the architecture decided in Phase 3 (`architecture.style`, boundaries, data-flow constrain the viable technologies). Load `references/tech-stack-options.md` for option tables. Load `references/questioning-flow.md` Section: "Tech Stack Drill-Downs" for category order and skip rules.

Loop:
1. Pick the next applicable category (skip per Routing Rules in questioning-flow.md). Constrain options by the architecture (e.g. an event-driven style favours a broker; a serverless style favours managed/edge hosting).
2. Present 2–4 options per category with one-line trade-offs. **Do NOT strongly recommend** — list options, user decides.
3. Group related decisions in one batch (e.g. DB + ORM; hosting frontend + backend + CDN).
4. Save answers as `DecisionMade` events with `--by user` (per the Kickoff provenance rule), using the canonical `stack.*` keys (`stack.frontend.framework`, `stack.backend.language`, `stack.database.engine`, `stack.auth.provider`, `stack.hosting.provider`, … per `references/decision-keys.md`).
5. For each *major* decision (language, framework, db engine, auth provider, host), file an ADR via the ADR workflow (see "Filing an ADR" below).
6. Detect red flags; dispatch ad-hoc `research-scout`.
7. Commit batch: `architect(stack): {{topic}}`.

At end of phase:
1. Dispatch `research-scout` with the Stack prompt (stack combination gotchas — and stack-vs-architecture fit). research-scout § 1a resolves the **newest-stable version** of each P0 dependency.
2. **Record the resolved version pins** so the scaffold ships current versions (not the generators' stale floor). For each pin research-scout returned, emit a `DecisionMade` under the `stack.versions.*` namespace:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision stack.versions.next '^16.2.6'
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision stack.versions.react '^19.2.0'   # drives react-dom too
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision stack.versions.node '24'          # Dockerfile base image
   ```
   `gen_package_json` / `gen_dockerfile` read these via `configs._pin` in Doc-gen (Phase 6 §5b). Canonical keys: `references/decision-keys.md` § `stack.versions.*`.
3. Commit findings.
4. Transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase cost && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar cost`, then run the gate (`architect-brain audit --only 20` + `--only 18`).
5. **Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with a Stack entry (chosen `stack.*` decisions + resolved `stack.versions.*` pins + ADR ids).

### Filing an ADR

**ADR-filing is a side-effect, not an end-of-run chore.** File the ADR **the moment a major decision is recorded** (each major architecture decision in Phase 3; language, framework, db engine, auth provider, host in Phase 4) — never deferred to lock. A run that defers ADRs back-fills them with fabricated timestamps; `architect-brain record-adr` makes that impossible (it emits an `ADRFiled` event with a real timestamp + the current phase).

For each major decision (one that warrants a record):
1. Read the next sequential ID from the `decisions` projection (`decisions/index.json` — the highest existing ADR id + 1, e.g. `0007`).
2. Read `references/templates/ADR_TEMPLATE.md` for structure. ADR markdown files live in `docs/_architect_state/decisions/`.
3. Generate a kebab-case slug from the title (max 60 chars).
4. Write the ADR file to `docs/_architect_state/decisions/<NNNN>-<slug>.md`. Fill all frontmatter fields — including the forward-compat stamps (`format_version` / provenance), per `references/artifact-migration.md` and the MADR-4 + structured-MADR frontmatter convention.
5. Record it in state via the binary (this emits the canonical `ADRFiled` event — the projection appends `{id, title, date, status, supersedes, phase}` and the flat-index `adrs[]` updates):
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain record-adr --phase <phase> <NNNN> "<title>" Accepted [--supersedes <id>]
   ```
6. Commit: `adr: 00NN <title>`.

**Gate:** the `adr_files_exist` check (17, WARNING) verifies that every ADR recorded in the ledger has a matching file in `docs/_architect_state/decisions/` — enforced **before Stack-phase entry AND before lock**. If a recorded ADR has no file, the orchestrator auto-remediates (write the file from the recorded decision + re-run the audit) rather than advancing.

---

## Phase 5: Cost Modeling

1. Identify priced services from the flat decisions (managed hosting, databases, AI providers, etc.).
2. Dispatch `research-scout` with the Cost prompt (pricing research). Pass the list of services + expected usage tier.
3. After findings return, present a cost-summary table to the user with $/month at MVP / growth / enterprise tiers.
4. Ask whether any cost reality should trigger a stack revision:
   - If yes: enter a brief revisor sub-loop — dispatch `decision-revisor` for the changed decision(s).
   - If no: proceed.
4a. **Anonymity preflight (check 25).** If the project is privacy/anonymity-sensitive (per a `constraints.*`/`personal_data` signal or the keyword triggers in `references/anonymity-preflight.md`), run `architect-brain audit --only 25` now — surface any centralized analytics/identity/telemetry backend in the chosen stack against the threat model before the cost model bakes it in.
5. Record the findings reference as a `ResearchRefAdded` event.
6. The `COST_MODEL.md` doc itself is generated during Doc-gen — the pricing research is its input data.
7. Commit: `architect(cost): cost model research`.
8. Transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase docs && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar docs`, then run the gate (`architect-brain audit --only 20` + `--only 18`).
9. **Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with a Cost entry (stack gotchas + cost model snapshot).

---

## Phase 6: Document Generation

### Doc-gen entry gate

Before dispatching any document-author agent, verify the upstream phases' prerequisites are satisfied — the architecture, stack, and cost phases must each have completed AND their pattern-validation / scope research must have returned. Run the continuous gate:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --only 16   # phase_gates (BLOCKING)
```

`phase_gates` (16, BLOCKING) reads the `workflow` projection and blocks Doc-gen if a prerequisite phase didn't complete. This blocks the live-test bug where `document-author` dispatched in parallel with `research-scout` (pattern validation), causing research findings to land too late to inform doc generation.

### Declarative document selection (catalog.json)

Doc selection is **declarative**, not hand-listed. `references/catalog.json` (106 documents) declares per-doc `conditions` (a conditions-DSL expression over the flat decision keyspace), `depends_on` (topological ordering), `produces`, `produced_by` (the agent), `phase`, and `concern`. Ask the binary which docs apply, in topo order, for the current decisions:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain catalog list          # applicable docs, topologically sorted
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain catalog list --phase docs   # filtered to this phase
```

`catalog list` evaluates each doc's `conditions` against `docs/_architect_state/99-flat-index.json` and returns only the applicable docs, already in dependency order (so upstream docs are written first). `catalog cycle` (run by audit check 32, FATAL) guards that the catalog stays acyclic. The catalog + conditions DSL replace v7's prose document-catalog selection logic — no `generate_when` evaluation or `affected_docs` union to compute by hand; the conditions DSL already covers both (a doc an ADR affects has a condition keyed off the relevant decision).

1. **Compute the doc set**: run `architect-brain catalog list` — that IS the selected, ordered set. (If a doc you expect is missing, the gap is a missing/under-specified `condition` or a decision that wasn't recorded — fix the decision, not the list.)
2. **Plan docs — invoke `writing-plans` when present (graceful-optional).** For the plan-shaped docs (`SCAFFOLD_PLAN`, `BOOTSTRAP_PLAN`, `NEXT_STEP_PLAN`), run a **soft-dependency probe** for superpowers (same pattern as Preflight):
   ```bash
   claude plugin list 2>/dev/null | grep -i superpowers \
     || ls ~/.claude/plugins/cache 2>/dev/null | grep -i superpowers
   ```
   - **If present:** invoke `Skill: superpowers:writing-plans` to author the plan doc (it produces a TDD, bite-sized, no-placeholder plan), passing the design context + the canonical `project_layout` / decisions. Save its output to the plan-doc path.
   - **If absent:** **template fallback** — generate the plan from `references/templates/SCAFFOLD_PLAN.md` (etc.) via the normal `document-author` dispatch. The output is still a valid plan; it just isn't authored by the writing-plans discipline.

   This mirrors PA's soft-dependency pattern (never hard-require an optional plugin; degrade to the template).
3. **Compute state slices**: for each selected template, extract only the `required_decisions` + `optional_decisions` keys from the flat decisions.
4. **Dispatch `document-author` agents in parallel batches of 8** (per `superpowers:dispatching-parallel-agents` pattern):
   ```
   For each batch in chunks(catalog_ordered_docs, 8):
     For each doc in batch:
       Dispatch project-architect:document-author (model opus, description "Write {{doc_name}}")
       with the **Shared dispatch header** + the **Doc-gen — document-author** body
       from references/dispatch-prompts.md, substituting the {{...}} INPUTS for this doc.
     wait_for_all(batch)
   ```
5. After each batch, record each generated doc as a `DocGenerated` event AND commit it separately:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain record-doc --phase docs <DOC_NAME> docs/<DOC_NAME>.md
   ```
   then `docs: generate <DOC_NAME>` (one commit per doc, via `commit-commands:commit`). `record-doc` stamps a SHA-256 `content_hash` so drift is detectable.

5a. **Identity-hygiene gate (check 24, BLOCKING).** After each doc/research batch, run `architect-brain audit --only 24` — if a forbidden identity term from `.architect/identity-deny.txt` leaked into any doc, HARD STOP and remove it before continuing. This guards against an operator-real-name leak; it complements the gitleaks pre-commit hook, which catches secrets but not non-secret PII. (Every subagent dispatch already carries the `[IDENTITY HYGIENE — HARD RULE]` + `[POST-RETURN SCRUB]` from the Shared dispatch header in `references/dispatch-prompts.md`; this gate is the enforcing backstop.)

5b. **Generate config-as-code + diagrams (deterministic, no model freelancing).** Once the stack decisions are recorded, emit the deterministic artifacts from the binary rather than hand-writing them:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain generate-configs                 # package.json / tsconfig / pyproject / Dockerfile / docker-compose / … as applicable
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain generate-diagram context        # Mermaid C4 (context | container | component) → stdout
   ```
   Save the diagram output into the relevant design doc (e.g. `ARCHITECTURE.md`). These are pure functions of the flat decisions — never the model improvising config.

6. **In parallel with the last doc batch**, dispatch the two plan-authoring agents — they author *plans*, not the final files (the actual root `/CLAUDE.md` + `.claude/*` tree are materialized later in Phase 9 Tooling Execution, or deferred — see the Phase-10 handoff banner):

   - `claude-md-author` → authors `docs/CLAUDE_MD_PLAN.md` (the fully-resolved plan for the root `/CLAUDE.md` + any per-folder CLAUDE.md).
     Dispatch `project-architect:claude-md-author` (model `opus`, description "Author CLAUDE_MD_PLAN") with the **Shared dispatch header** + the **Doc-gen — claude-md-author** body from `references/dispatch-prompts.md`, substituting the `{{...}}` INPUTS.

   - `claude-tooling-author` → authors `docs/CLAUDE_TOOLING_PLAN.md` (the plan for `.claude/settings.json`, hooks/, agents/, commands/, recommended-plugins.md — see `references/claude-code-integration.md` for stack→skill recipes).
     Dispatch `project-architect:claude-tooling-author` (model `opus`, description "Author CLAUDE_TOOLING_PLAN") with the **Shared dispatch header** + the **Doc-gen — claude-tooling-author** body from `references/dispatch-prompts.md`, substituting the `{{...}}` INPUTS.

7. After both return, record + commit each plan:
   - `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain record-doc --phase docs CLAUDE_MD_PLAN docs/CLAUDE_MD_PLAN.md` → commit `architect(docs): author CLAUDE_MD_PLAN`.
   - `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain record-doc --phase docs CLAUDE_TOOLING_PLAN docs/CLAUDE_TOOLING_PLAN.md` → commit `architect(docs): author CLAUDE_TOOLING_PLAN`.

8. Push if the recorded push strategy is `per_phase` and a remote is configured:
   ```bash
   git push origin <branch>
   ```

9. Transition per the **Phase transition contract** — but Doc-gen→Iteration is gated by the mandatory pre-Iteration audit (step 11 below): run the full audit FIRST, resolve any BLOCKING/FATAL, and only then run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase iteration && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar iteration`. See "Doc-gen→Iteration audit gate" (steps 10–12).

10. **Required-docs gate (`required_docs_generated`, 27, BLOCKING) — run BEFORE the full audit.** Every always-applicable **doc-class** document (its output is `docs/<NAME>.md`: `PROJECT_OVERVIEW`, `PROJECT_REQUIREMENTS`, `CLAUDE_MD_PLAN`, `CLAUDE_TOOLING_PLAN`, `NEXT_STEP_PLAN`) must have produced its `docs/<NAME>.md` by this exit. (`CLAUDE_MD_ROOT` → root `CLAUDE.md` and `SLASH_*` → `.claude/commands/*` are Lock/Tooling outputs and are NOT required here.) Run it directly:
    ```bash
    ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --only 27 --verbose
    ```
    On a failure (BLOCKING): **auto-remediate** — re-dispatch `document-author` for each missing doc named in the findings (read the catalog row + the template, write `docs/<NAME>.md`, record it via `architect-brain record-doc`), then re-run check 27. This is the silently-skipped-doc fix: an always-applicable doc like `PROJECT_REQUIREMENTS.md` gets skipped and only a dangling cross-link surfaces it post-hoc. If a doc genuinely cannot be generated, STOP — do NOT proceed to the full audit / Iteration with the doc set incomplete. (Check 27 also runs inside the full audit below, so a still-missing doc hard-blocks the Doc-gen→Iteration advance regardless.)

11. **Run the full audit** — the 35-check gate:
    ```bash
    ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --verbose
    ```
    This runs all 35 checks against `docs/_architect_state/` + the generated bundle, prints one line per check + a verdict, records an `AuditCompleted` event (which is exactly what `audit_freshness` (19) reads to refuse a stale/post-lock audit), and exits 1 if any failure blocks LOCK (FATAL always; BLOCKING unless `--ack=<reason>`). Capture the per-check output and the verdict.

12. Read the verdict. If the exit code is non-zero (a BLOCKING or FATAL failure): do NOT auto-advance to Iteration. Surface the failing checks + their findings (the `--verbose` lines) and ask the user how to proceed (revise via `decision-revisor` / `--ack` a BLOCKING finding with a recorded reason / abort). Only after the gate is clean (or the user explicitly acks a BLOCKING finding) run the gated advance: `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase iteration && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar iteration`. (FATAL — `state_schema_valid` 29, `resume_test` 31, `catalog_topo_acyclic` 32 — can never be acked; it always hard-stops.) The audit's recorded `AuditCompleted` event seeds the Iteration menu.

13. **Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with a Doc-gen entry (generated doc list + audit verdict: FATAL / BLOCKING / WARNING / INFO counts).

---

## Phase 7: Iteration

Print a decision summary AND the audit's findings (read from the recorded `AuditCompleted` event + the latest full-audit per-check output):

```
✓ Bootstrap complete.

DECISIONS:
  ┌─────────────────────────────────────────────────────────────┐
  │ Architecture                                                 │
  │   • Style: {{architecture.style}} (ADR {{id}})              │
  │   • Boundaries: {{count}} (ADR {{id}})                       │
  │   ...                                                        │
  │ Tech stack                                                   │
  │   • Language: {{stack.backend.language}} (ADR {{id}})       │
  │   • Frontend: {{stack.frontend.framework}} (ADR {{id}})     │
  │   ...                                                        │
  │ Generated {{N}} docs · {{M}} ADRs · {{K}} research findings  │
  └─────────────────────────────────────────────────────────────┘

QUALITY GATE AUDIT:
  Verdict: {{CLEAN | PASS with non-blocking findings | BLOCKED}}    (worst severity: {{FATAL|BLOCKING|WARNING|INFO}})

  {{for each failing check from the latest --verbose audit}}
    [{{severity}}] {{check_id}} {{name}}: {{summary}}
       → {{finding.message}}{{ optional [location] }}
  {{end}}

What next?
  (auto-seeded from the audit's failing checks)
  {{for each failing check}}
    ({{letter}}) Resolve {{check_id}} {{name}}{{ if severity in (BLOCKING, FATAL) then " [default — blocks LOCK]"}}
  {{end}}
  {{ if the latest full audit is fresh AND clean (exit 0, no blocking) AND no ADR missing:
       ({{next_letter}}) Approve all → Lock (commit + plugin install)
     else:
       ({{next_letter}}) Resolve findings (DEFAULT — clears a blocking / FATAL / stale-audit) }}
  ({{next}})       Revisit a decision → type its key
  ({{next}})       Snapshot current as v1.0 → docs/versions/v1.0/ and continue
  ({{next}})       Generate the implementation plan → Tooling Execution
  ({{next}})       Show full decision tree
  ({{next}})       Exit (resume later)
```

**Lock-option gating (the dominant fix):** do NOT render the lock option ("Approve all → Lock") as available when the latest full `architect-brain audit` is stale/absent (no recent `AuditCompleted` event), OR any ADR recorded in the ledger is missing its file (`adr_files_exist` 17 would fail), OR the latest audit's exit code is non-zero (a BLOCKING/FATAL failure). In any of those cases the **remediation option becomes the default** and Approve may NOT be labeled "Recommended". The UI must never recommend the incomplete path — that is exactly what ships a project incomplete (the audit ran after lock and the menu still recommended Approve).

### Iteration loop

Use `AskUserQuestion` for the menu.

- **(a) Approve**: only selectable when the lock-option gate (above) is clean. Break to Lock.
- **(b) Revisit**:
  1. Ask: which decision key? (auto-suggest from the flat decisions keys)
  2. Ask: why (free-form — goes into ADR)
  3. Re-ask the question that produced this decision (with current value as default).
  4. Dispatch `decision-revisor`:
     Dispatch `project-architect:decision-revisor` (model `opus`, description "Revise {{decision_key}}") with the **Shared dispatch header** + the **Iteration — decision-revisor** body from `references/dispatch-prompts.md`, substituting the `{{...}}` INPUTS (`decision_key`, `old_value`, `new_value`, `reason`, `next_adr_id`).

  5. After revisor returns, run inline validation (revisor should have done this already but double-check); the new value is recorded via `architect-brain set-decision` and any ADR via `record-adr`.
  6. Commit via `commit-commands:commit`: `architect(revise): {{key}} → {{new}} (ADR {{id}})`.
  7. Loop back to menu.
- **(c) Snapshot**:
  1. Compute next version: if no snapshots recorded → "v1.0"; else bump.
  2. Copy `docs/*.md` and `docs/_architect_state/decisions/`, `docs/research/` to `docs/versions/<vX.Y>/`.
  3. Record the snapshot via a `DecisionMade`/snapshot event; bump the current doc version.
  4. Commit: `chore: snapshot docs as <vX.Y>`.
  5. Loop back to menu.
- **(d) Plan**: set a "skip to Tooling Execution" flag, break.
- **(e) Tree**: print full decision tree (group by domain: project meta, architecture, language, frontend, backend, db, auth, hosting, security, testing, monitoring), with ADR references. Loop back to menu.
- **(f) Exit**: save state (it's already persisted — events are durable), push if `per_phase`, return. The user can resume later by invoking the architect again.

Once (a) Approve is chosen AND the pre-lock gate is clean (see Lock phase), transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase lock && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar lock`. **Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with an Iteration entry per major revision wave (one append per revisor-driven decision change); if no revisions occurred (user chose (a) immediately), append a short "no revisions" entry.

---

## Phase 8: Lock / Post-Generation Setup

1. **Plugin installs**: read `<user-project>/.claude/recommended-plugins.md`. For each recommendation, ask via `AskUserQuestion`:
   - Install / Skip / Skip all remaining
   If install: `claude plugin install <plugin>`. Record outcome as a `DecisionMade` event (`recommended_plugins.<name>.installed = true`).
2. **Push to remote** (if not already done at phase boundary):
   ```bash
   git push origin <branch>
   ```
3. **Open PR** if working on a `bootstrap/architect-*` branch (per the recorded `git.branch`):
   ```bash
   gh pr create --title "Project bootstrap" --body "..." --base main
   ```
   Body: short summary referencing the spec + plan + ADRs.
4. **Bootstrap commands**: ask the user whether to run stack-specific commands:
   ```
   "Run project bootstrap commands now?
      pnpm install / cargo new / pip install -r requirements.txt / etc.
      Yes / Skip / Customize"
   ```
   If yes: execute. If customize: let user edit before running.
5. **Final commit**: `chore: bootstrap complete` via `commit-commands:commit`.
6. **Pre-lock gate:** BEFORE setting the lock, run the full audit and resolve it — this is the gate that the Iteration lock-option gating defers to (and that line "Once (a) Approve is chosen AND the pre-lock gate is clean" forward-references):
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --verbose
   ```
   - `audit_freshness` (19, BLOCKING): if no fresh `AuditCompleted` event precedes the lock (or the audit predates the newest doc), this very run IS the fresh pre-lock audit — it records a new `AuditCompleted` and satisfies the check. The lock cannot proceed on a stale or absent audit.
   - `adr_files_exist` (17, WARNING + auto-fix): if any recorded ADR lacks a file, write the file and re-run.
   - `cross_link_integrity` (22, BLOCKING): if any relative doc link dangles, fix or remove it before locking.
   - The three FATALs (`state_schema_valid` 29, `resume_test` 31, `catalog_topo_acyclic` 32) must pass — they can never be acked.
   Only when the audit's verdict is clean (or a BLOCKING finding is explicitly `--ack`'d) does the LOCK proceed. A genuine BLOCKING/FATAL finding (e.g. an unresolvable broken link, or a replay-invariant violation) HARD-STOPS here with the remediation defaulted; mechanical gaps (missing ADR file, stale audit) are auto-remediated and the audit re-run. **This is mechanically enforced, not just prose:** the `append-event --type LockSet` in step 7 reads the latest recorded `AuditCompleted` verdict and **refuses to lock** (non-zero exit) unless it is `clean` — so a lock cannot be placed atop a `blocked` (or absent) audit. `check_19 audit_freshness` is the corresponding gate-side backstop: it now reads the vetting audit's `result`, not just its timestamp.

7. **LOCK** (sketch D): freeze the design at version `v1.0` by emitting a `LockSet` event — the lock is part of the event log, not a hand-edited field:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain append-event --type LockSet \
     --payload '{"locked": true, "version": "v1.0"}'
   # the binary stamps the real locked_at into the event ts; the workflow projection re-materialises.
   # REFUSES (exit 1) if the latest AuditCompleted verdict is not "clean" — re-run
   # `architect-brain audit` to a clean verdict first. `--force` overrides (audited escape hatch).
   ```

   Then commit the locked state via `commit-commands:commit` with subject `architect(lock): v1.0`.
8. **Cleanup**: the `docs/_architect_state/` directory is preserved. Do NOT remove it. It is the canonical entry point for future re-invocations and for `/iterate-design`. Optionally archive a copy of the projections to `docs/versions/v1.0/_architect_state/`. Commit only the lockfile cleanup if the lock is held: `chore: release bootstrap lock`.

   ```bash
   # Release lock (delete lockfile only)
   rm -f docs/_architect_state/.lock
   # IMPORTANT: never remove the state directory — it is the cross-session entry point
   ```
9. **Memory persistence (major update):** Edit the pointed-to file per `references/memory-persistence.md` with a new section: `## LOCKED at v{{version}} — <ISO8601 timestamp>` followed by the full design summary (final ADR list, doc count, locked_at). Then update the `MEMORY.md` index entry to mark the project as locked (replace the in-design suffix with `locked at <version> (<locked_at>)`).
10. Output: "✓ Project architect complete."
11. Transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase tooling && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar tooling` (records the move into Tooling Execution). The phase pointer then moves monotonically `tooling → handoff → complete` through the remaining phases — Tooling Execution is always *reached* (its menu always runs; only the execution work is optionally skipped via menu option (d)), so a PhaseAdvanced event into `tooling` always exists and `no_oob_phase_advance` (20) never false-blocks. The Handoff phase's own gate (`scaffold_executed` 26) still applies.

---

## Phase 9: Tooling Execution (sketch D)

After lock, ask the user which plans to execute:

```
✓ Architecture locked at v1.0.

Tooling Execution

Which plans to execute now?
  (a) Execute CLAUDE_MD_PLAN  → generates CLAUDE.md (claude-md-author)
  (b) Execute CLAUDE_TOOLING_PLAN → generates .claude/* (claude-tooling-author + slash commands)
  (c) Hand off SCAFFOLD_PLAN to superpowers (writing-plans → SDD)
  (d) Skip all execution (close out with plans only)
  (e) (a) + (b) + offer (c) — default productive path
```

For each chosen execution:

- **(a) CLAUDE_MD_PLAN**: dispatch `claude-md-author` with `plan_path: docs/CLAUDE_MD_PLAN.md` as input. Agent reads plan, substitutes placeholders from the flat decisions, writes CLAUDE.md. Commit: `architect(tooling): execute CLAUDE_MD_PLAN`.
  Dispatch `project-architect:claude-md-author` (model `opus`, description "Execute CLAUDE_MD_PLAN") with the **Shared dispatch header** + the **Tooling — claude-md-author (execute CLAUDE_MD_PLAN)** body from `references/dispatch-prompts.md`.

- **(b) CLAUDE_TOOLING_PLAN**: dispatch `claude-tooling-author` with `plan_path: docs/CLAUDE_TOOLING_PLAN.md`. Agent reads plan, generates `.claude/*` tree including the 3 router slash commands (`/scaffold`, `/implement`, `/iterate-design`). Commit: `architect(tooling): execute CLAUDE_TOOLING_PLAN`.
  Dispatch `project-architect:claude-tooling-author` (model `opus`, description "Execute CLAUDE_TOOLING_PLAN") with the **Shared dispatch header** + the **Tooling — claude-tooling-author (execute CLAUDE_TOOLING_PLAN)** body from `references/dispatch-prompts.md`.

- **(c) SCAFFOLD_PLAN**: run the soft-dependency probe for superpowers (see Doc-gen step 2). **If present**, invoke `Skill: superpowers:writing-plans` with `spec_path: docs/SCAFFOLD_PLAN.md` and execution mode `subagent-driven-development`; control transfers to superpowers and the architect's responsibility ends here for code emission. **If absent (template fallback)**, surface that scaffolding can't be auto-executed without superpowers and offer to record a `DecisionMade` for `scaffold.deferred = true` (so the Handoff gate passes) for the user to scaffold manually from `docs/SCAFFOLD_PLAN.md`.

- **(d) Skip**: proceed to Handoff with no execution. The user runs `/scaffold` etc. in a future session.

- **(e) Default productive path**: do (a) + (b) automatically; then offer (c) as a separate question.

After each execution, re-run the audit to re-validate the bundle (now includes the just-generated CLAUDE.md / `.claude/*`):

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --verbose
```

This records a fresh `AuditCompleted` event (so `audit_freshness` (19) sees a fresh post-execution audit). It is in-process and never depends on the model backend, so there is no degraded-mode to fall back to — it either runs the real checks or, if `architect-brain` itself can't run, you STOP and tell the user (per the "Audit robustness" HARD RULE). If the verdict is BLOCKED (`cross_link_integrity` 22 or `settings_permissions_valid` 21 etc.), surface to the user before advancing.

Commit:
- After each execution: per the per-option commit messages above.
- After all executions: transition per the **Phase transition contract** — run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase handoff && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar handoff`, then run the Tooling audit gate (the full `architect-brain audit`, with `cross_link_integrity` 22 + `settings_permissions_valid` 21 of particular interest — see the re-run above).

**Memory persistence:** Edit the pointed-to file per `references/memory-persistence.md` with a Tooling entry recording execution outcome (CLAUDE.md y/n, `.claude/*` y/n, scaffold y/n, post-execution audit verdict).

---

## Phase 10: Handoff (sketch D)

Run the **Handoff gate** (below) FIRST; then — only if it clears — run the **branch-merge clarity** step (below) when the bootstrap is on a non-`main` branch, then print the handoff message and end the architect run. The COMPLETE message below is **conditional on the gate**: it is printed only when `scaffold_executed` (26) passes or scaffolding was explicitly deferred.

```
✓ Architecture locked at v{{version}}
✓ {{N}} design docs in docs/
✓ {{M}} plan docs in docs/*PLAN.md
{{✓ CLAUDE.md generated | ⊘ CLAUDE.md skipped (plan exists at CLAUDE_MD_PLAN.md)}}
{{✓ .claude/* generated | ⊘ .claude/* skipped (plan exists at CLAUDE_TOOLING_PLAN.md)}}
✓ Final commit: {{HEAD sha}}
{{✓ Pushed to origin: {{url}} | ⊘ No remote configured}}
{{✓ On `main` | ✓ Merged to `main` — deploys will pick it up | ⚠ On branch `{{git.branch}}` — deploys read `main`; not live until merged (see branch-merge clarity)}}

Next step: restart Claude Code to load the new CLAUDE.md and .claude/ tooling.
   Type `/exit` then run `claude` in this directory.

After restart, the new session will:
   • Auto-load your new CLAUDE.md as the project's operating manual
   • Auto-load .claude/settings.json (permissions) and .claude/hooks/
   • Offer next-step options via the slash commands defined in .claude/commands/

Slash commands available after restart:
   /scaffold        — scaffold the actual code (uses superpowers if installed)
   /implement <X>   — implement a specific feature from requirements
   /iterate-design  — re-open the design for revision

Architect session ending. Type /exit when ready.
```

Run the Handoff gate FIRST: `scaffold_executed` (26) must pass (or `scaffold.deferred == true`) — see "Handoff gate" below. When the bootstrap is on a non-`main` branch, also run the **branch-merge clarity** step (below) before the COMPLETE message. Only then transition per the **Phase transition contract**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-phase complete && ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar complete`. **Memory persistence (final update):** Edit the pointed-to file per `references/memory-persistence.md` with a Handoff entry (closing summary + next-step recommendations); this is the entry future sessions grep for context. Architect returns control to user.

### Handoff gate

BEFORE printing the handoff/COMPLETE message — and BEFORE the `set-phase complete` transition — run the scaffold-execution check:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --only 26 --verbose
```

Read the `scaffold_executed` (26, BLOCKING) result:
- If it **passes** (every recorded `project_layout` value-path exists on disk) → proceed to the handoff message, then `set-phase complete`.
- If `scaffold.deferred == true` (the user explicitly chose to defer scaffolding) → proceed; the handoff message notes scaffolding was deferred, then `set-phase complete`.
- Otherwise (a `project_layout` path is missing and scaffolding was NOT deferred) → the orchestrator **must NOT print the COMPLETE handoff message** and must NOT run `set-phase complete`. Surface that the scaffold plan was written but never executed, **list the missing paths** (from the `--verbose` findings), and offer:
  - **(a)** execute the scaffold plan now — run `/scaffold` (Tooling option (c) → `superpowers:writing-plans` / SDD), then re-run this gate, OR
  - **(b)** explicitly record the deferral — `architect-brain set-decision scaffold.deferred true` — if the user intends to scaffold later. This is an explicit, recorded choice (not a silent skip); then re-run this gate.

A written plan is not an executed scaffold — this is the written-plan-vs-executed-scaffold fix (a written plan can mask an abandoned pre-architect MVP tree that nothing verified). Only when check 26 passes OR scaffolding is explicitly deferred does the handoff print the COMPLETE message and run `set-phase complete`.

### Handoff branch-merge clarity (deploys read `main`)

Existing-codebase runs do their work on a `bootstrap/architect-<date>` branch (created in Phase 0a — KEPT as a deliberate safety boundary so the architect never rewrites the user's `main` in place). The branch is correct; what was wrong in v4 is that the handoff ended **silently** about it. A fresh clone, CI, and hosting integrations (Vercel, Netlify, Cloudflare Pages, etc.) read `main`, so the bootstrap is **not live until the branch is merged** — an operator can only discover this when the deploy shows nothing and has to hand-merge. The fix is signposting + an offer, NOT removing the branch.

Run this AFTER the handoff gate clears and BEFORE printing the COMPLETE message. Key off the recorded `git.branch`:

- `git.branch == "main"` (or no branch was created) → skip this step; print the COMPLETE message with the `✓ On \`main\`` line.
- `git.branch != "main"` AND a remote is configured → surface the situation and auto-offer the merge. Because the branch was cut from `main` in Phase 0a and only the architect committed to it, `main` is an ancestor of `bootstrap/architect-*` → the merge is a clean **fast-forward**. Prompt via `AskUserQuestion`:

  > "Bootstrap is committed on branch `{{git.branch}}`, not `main`. Deploy integrations and hosting (Vercel, etc.) read `main`, so it's not live until merged. How do you want to land it?"

  - **(a) Merge to main now** — fast-forward and push (deploys then pick it up):
    ```bash
    git checkout main && git merge --ff-only {{git.branch}} && git push origin main
    ```
    Then print the COMPLETE message with the `✓ Merged to \`main\`` line. (If the FF is refused because `main` advanced concurrently, fall back to offering the PR option rather than forcing a non-FF merge.)
  - **(b) Leave on branch** — keep the work on `{{git.branch}}`; print the COMPLETE message with the `⚠ On branch …` line so the user is reminded that deploys read `main` until they merge.
  - **(c) Open a PR** — `gh pr create --base main --head {{git.branch}}` (skip if a PR was already opened in the Lock phase step 3); the COMPLETE message links the PR and notes the deploy goes live on merge.

- `git.branch != "main"` but no remote → name the branch in the handoff and note that nothing is pushed; no merge offer (there is nothing for a deploy to read yet).

This does NOT change the Phase 0a branch-creation default — existing codebases still get the `bootstrap/architect-*` safety branch. It only ensures the handoff names the branch, states that deploys read `main`, and offers the merge instead of ending silently.

---

## Failure modes & recovery

| Failure | Recovery |
|---|---|
| User exits mid-phase | Every event is durably appended to `events.jsonl`. Re-invocation runs `detect`, prints a resume summary from the projections, and picks up at `workflow.current_phase`. |
| Agent dispatch returns malformed output | Retry once with clarification appended to the prompt. If still failing, fall back to inline completion: orchestrator drafts the doc itself using the template + decision slice. |
| Commit fails (pre-commit hook rejects) | Surface error, ask user. **Never** `--no-verify`. |
| Push fails (network / auth) | Commit locally, queue push for next phase boundary. |
| Required dep missing (`commit-commands`) | Refuse to start with explicit install command. |
| User said "no" to repo init then tries to commit | Detect at first commit attempt; offer to init now. |
| Two terminals running architect concurrently | Lock file detects (other pid). Prompt user to clear if stale. |
| Mid-session model switch to weaker model | Detect at next phase boundary by re-reading env; pause, re-prompt. |
| `gh` not authed | Skip remote creation; record the fact; user can add remote later. |
| `ToolSearch` for `AskUserQuestion` fails | Fall back to plain-text prompts. |
| Projection drift (replay ≠ disk) | `resume_test` (31, FATAL) catches it. Run `architect-brain replay` to re-materialise the projections from the authoritative `events.jsonl`. |

## Resumability checklist

When resuming:
1. Run `architect-brain detect`. If `pre_v8_project` (schema < 4.0), run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate` (snapshots → synthesizes events → replays → compares → atomic flip; reversible) per `references/state-schema.md` migration policy; if newer than supported, refuse.
2. Detect a half-locked state (interrupted `/iterate-design`): locked == false AND `version` set without a `-draft` suffix AND `current_phase` past `iteration` → offer **finish or roll back** (see "Resume from a half-locked state" above).
3. Check lock — if held by a different pid and `acquired_at > 30 min ago`, offer to clear.
4. Re-run Preflight (model + effort).
5. Print resume summary:
   ```
   Resuming bootstrap from {{workflow.current_phase}}.
   Decisions captured: {{count from 99-flat-index.json}}.
   Last event: {{tail of events.jsonl}}
   Continue? (y / start over / show progress)
   ```
6. Jump to the function for `workflow.current_phase`.

## What NEVER to do

- Modify `~/.claude/settings.json` (global) — only the project-local `.claude/settings.json`.
- Auto-install marketplace plugins without user confirmation.
- Push without phase awareness when the push strategy is "per_phase" or "end_only".
- Write code (beyond Lock-phase bootstrap commands the user opted into).
- Generate icons / branding / mockups (defer to relevant `document-skills` skills via recommended-plugins).
- Validate the chosen stack works (compile/smoke-test) — that's Tooling+ territory.
- Replace user judgment on decisions.
- Hand-edit any file under `docs/_architect_state/` — every mutation goes through an `architect-brain` event so the replay invariant holds.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
