<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Output style — fast, quiet, beautiful

How the orchestrator narrates a run. Every flow — the bootstrap `SKILL.md`, `/upgrade-project`, `/re-architect`, `/iterate-design` — follows this. The plugin runs a lot of mechanical machinery (`architect-brain` event writes, the 35-check `architect-brain audit`, `find`/`grep`/`jq` reads). Left unattended that machinery dumps raw chatter into the user's transcript: event ULIDs echoed by `set-decision`/`record-*`, the audit's per-check lines, directory listings. **This convention turns that plumbing into clean, advancing, informational progress.** The user should see *what the orchestrator is doing*, not *how the tools say it*.

Three rules, in priority order: **capture don't dump** (§1) · **be fast** (§2) · **render it beautifully via `architect-brain ui`** (§3).

---

## 1. Output discipline — capture, don't dump

The orchestrator runs mechanical machinery; the user reads a curated narrative. These never both happen at once.

- **Capture, then summarize.** Run a mechanical command with stdout **captured** — assign to a variable (`OUT="$(... )"`) or redirect (`>/dev/null`) — then parse it and emit ONE concise informational line per meaningful step. Examples of the line you emit (NOT the raw output you captured):
  - `✓ State migrated to schema 4.0`
  - `✓ Filed ADR 0007 (database engine)`
  - `✓ Quality gate: green (0 blockers, 2 warnings)`
  - `✓ Snapshotted current design → docs/versions/1.4.0/`
- **Never paste raw command stdout, the audit's findings, or `find`/`grep` output into the user-facing narration.** `architect-brain set-decision`/`record-adr`/`record-doc` echo the ULID of the event they appended; `architect-brain audit` returns one line per check plus a verdict (and, under `--verbose`, the findings detail); `find`/`grep`/`jq` emit lists. All of that is **for the orchestrator to parse**, not for the user to read. Capture it, act on it, then surface a one-line summary. The audit's verdict (the blockers / warnings / info tallies across the 35 checks) becomes one `✓`/`✗` line — not a pasted blob.
- **Surface progress, not plumbing.** A phase or step boundary gets a short headline + a `✓` on completion:
  - `→ Phase 6: generating 8 design docs…` then, on completion, `✓ Phase 6: 8 design docs generated`.
  - The dozens of underlying tool calls (each `Read`, each `architect-brain` event write, each `Agent` dispatch's internal steps) are **NOT narrated individually**. They roll up into the boundary line.
- **Errors are the exception — they DO surface their detail.** A success stays terse; a BLOCKER, a FATAL, or a command failure surfaces enough for the user to act (the failing check's name + severity, the file + reason, the remediation). Don't bury an error behind a `✓`. (The full self-healing error protocol — how the orchestrator pauses, explains the situation, and offers to fix it — lives in **§4 Error handling** below; the principle in one line: success terse, failure detailed.)

**The litmus test:** if a line in the transcript is something a *tool printed*, it's plumbing — capture it. If it's something *you decided to tell the user*, it's progress — surface it as one clean line.

**The one mechanical output you do NOT capture-and-suppress:** `architect-brain ui`'s stdout. You **RUN** the binary — `ui banner` once at the start, `ui phase-bar <phase>` folded into each `set-phase` call, and `ui progress <current> <total> <label>` for ad-hoc sub-step bars — and let its output land in the **tool-result block**. That block IS the user-visible banner / bar; it is your curated narration (§3). The `✓`/`→`/`✗` step lines are rendered **inline** (there is no `ui step` subcommand). Every OTHER mechanical stdout (event ULIDs echoed by `set-decision`/`record-*`, the audit's per-check lines, `find`/`grep`) is still captured + summarized.

---

## 2. Speed

Fast is part of the experience. Don't make the user wait on work that could be parallel, and don't redo work that's already done.

- **Parallelize independent work.** When two or more units of work share no state and have no ordering dependency, dispatch them in a **single message with multiple tool calls** — the documented default for the research-scout batch (domain / tech / cost scouts) and the doc-author batch (the document-author generators dispatched over the topo-ordered `catalog list` set). One round-trip, not N sequential ones.
- **Don't re-run unchanged work.** Don't re-invoke the audit if nothing has changed since the last green run — reuse the last `AuditCompleted` event recorded in the `workflow` projection. Same for re-deriving an artifact whose source decisions didn't move. Re-running a green gate just to watch it pass again is wasted wall-clock and wasted transcript.
- **Batch mechanical sequences.** Prefer ONE bash invocation over many small ones for a run of `architect-brain` event writes (e.g. recording several decisions or sub-steps at once via `&&`-chained `set-decision`/`set-substep` calls). Read the projections (`99-flat-index.json`) once and reuse them rather than re-reading state before every step. Fewer, fatter calls = less latency and less chatter.

---

## 3. Beautiful — `architect-brain ui` (banner + advancing bars + step lines)

You render boundaries by **RUNNING** `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui …` — a Bash call whose stdout lands in the tool-result block. **That tool-result block IS the user-visible surface** for the banner and the bar. It is pure stdout — no ANSI, no color, no cursor control — so it renders faithfully as monospace. You do **NOT** transcribe, paste, or describe the art; you RUN the binary and let it print.

Why run it instead of pasting the art inline? Because inline rendering is a *discretionary* act the orchestrator drops under load — it is precisely what kept the banner/bars from ever showing (the v7.0/7.1 failure). Running the binary makes the UI ride on actions you already take: the banner is one Bash call at the start, and the bar is **folded into the mandatory `set-phase` event write** — `architect-brain set-phase <phase> && architect-brain ui phase-bar <phase>` — so it prints at every transition-contract boundary (enforced by the `no_oob_phase_advance` audit check (20, BLOCKING)) whether or not you remember to narrate. `set-phase` emits a `PhaseAdvanced` event and prints only the event ULID (capture it); the folded `ui phase-bar` then prints ONLY the bar into that same tool result. `phase-bar` maps the bare phase key to its row, and an unknown key is a chain-safe no-op.

**Banner** — run `architect-brain ui banner` (shown here for reference, NOT to transcribe):

```
   ▄▀█ █▀█ █▀▀ █░█ █ ▀█▀ █▀▀ █▀▀ ▀█▀
   █▀█ █▀▄ █▄▄ █▀█ █ ░█░ ██▄ █▄▄ ░█░

   project-architect · design-first project bootstrapping
   ─────────────────────────────────────────────────────
```

**Phase ladder** — the 11 rows `ui phase-bar` walks, one per `set-phase` (Preflight is the banner-only opener, so the first bar is `kickoff` = 1/11 and `complete` = 11/11). The v8 ladder is **reordered**: **Architecture comes BEFORE the tech stack** (domain shape and boundaries first, infrastructure second), and **Cost is its own phase**. Shown here for reference; the binary is the source of truth — regenerate any row with `architect-brain ui phase-bar <key>`:

```
  Phase 1/11  [█░░░░░░░░░░░░░░░░░░░]   9%  Universal kickoff
  Phase 2/11  [███░░░░░░░░░░░░░░░░░]  18%  Vision & requirements
  Phase 3/11  [█████░░░░░░░░░░░░░░░]  27%  Architecture
  Phase 4/11  [███████░░░░░░░░░░░░░]  36%  Tech stack
  Phase 5/11  [█████████░░░░░░░░░░░]  45%  Cost model
  Phase 6/11  [██████████░░░░░░░░░░]  54%  Doc generation
  Phase 7/11  [████████████░░░░░░░░]  63%  Iteration
  Phase 8/11  [██████████████░░░░░░]  72%  Lock
  Phase 9/11  [████████████████░░░░]  81%  Tooling
  Phase 10/11  [██████████████████░░]  90%  Handoff
  Phase 11/11  [████████████████████] 100%  Complete
```

The bare phase keys `set-phase`/`ui phase-bar` take are: `preflight`, `kickoff`, `vision`, `architecture`, `stack`, `cost`, `docs`, `iteration`, `lock`, `tooling`, `handoff`, `complete` (the source of truth is the `_PHASE_LADDER` in the plugin's UI engine; regenerate any row with `architect-brain ui phase-bar <key>`).

| Call | When | What prints into the tool result |
|---|---|---|
| `architect-brain ui banner` | ONCE, at flow start (Preflight) | the ASCII-art mark + tagline |
| `architect-brain ui phase-bar <phase_key>` | folded into EACH `set-phase` (`architect-brain set-phase <k> && architect-brain ui phase-bar <k>`) | the advancing 11-step bar for that phase |
| `architect-brain ui progress <current> <total> <label>` | ad-hoc sub-step bars | a block-char bar (`█`/`░`) + `%` + label |
| inline `✓` / `→` / `✗` `"<text>"` | each meaningful step | the status line you write into the reply — `✓` done · `→` in progress · `✗` failure (there is NO `ui step` subcommand) |

You RUN the `ui` calls at boundaries and let their stdout show; you do **not** separately echo the `set-decision`/`record-*`/audit output that triggered them. A typical boundary: `architect-brain set-phase docs && architect-brain ui phase-bar docs` (the bar prints into that tool result) → (capture the document-author dispatch + the audit run, summarized) → inline `✓ Phase 6: 8 design docs generated, gate green`.

**Claude Code reality (stated honestly):** the CC transcript is **append-only markdown, not a live TTY**. There is NO in-place frame animation — no spinner, no `\r` redraw; Claude Code captures the command's *final* stdout, not intermediate frames. So "animated" here does **not** mean a bar redrawing in place. It means the bar **ADVANCES down the transcript**: each phase boundary's `set-phase && ui phase-bar` prints a fresh, fuller bar into a new tool result, so the user watches it fill as the flow progresses (`9%` → `27%` → `54%` → `100%` on successive tool results). `architect-brain ui` is deliberately pure stdout with no ANSI cursor control precisely because there is no TTY to drive.

---

## 4. Error handling — informational + self-healing

Errors are §1's one exception: success stays terse, **a failure surfaces its detail**. But surfacing detail is not the same as dumping a stack trace and dying. **On any BLOCKING/FATAL finding or command failure, the orchestrator never silently fails and never pastes a raw trace.** It runs this protocol instead.

### Step 1 — surface a concise *informational error state* (not a raw trace)

First, in one short block, tell the user three things — derived from the state + what was gathered so far, NOT from the tool's raw stdout:

- **What failed** — the headline. Lead with an inline `✗ "<one-line failure>"` status line (the error headline; e.g. `✗ Quality gate: 1 blocker — ADR 0007 recorded but no file on disk (adr_files_exist, 17)`).
- **What's known so far** — the current state (the `workflow` projection's phase / version / locked flag), what was already produced this run (docs written, decisions set, ADRs filed, snapshots taken), and the specific signal that fired (the `detect` verdict, the audit verdict + the offending finding under `--verbose`, the missing path). This is the §1 captured output, *parsed* — surface the meaningful fields, not the raw blob.
- **What's at risk** — what is NOT yet applied / could be left inconsistent if we stop here, and what is safe (e.g. "nothing locked yet; the snapshot already exists, so a stop loses no work"). Recall that state is event-sourced: nothing partial is half-written — every applied change is an event in `docs/_architect_state/events.jsonl`, and the projections always reflect a clean `replay`.

This is an **informational error** state: enough for the user to decide, nothing they have to dig a trace out of.

### Step 2 — `AskUserQuestion`: report-or-continue (two paths)

Then call **`AskUserQuestion`** offering exactly two paths:

- **Write a report and stop** — emit a structured **diagnostic report** (the current state from the projections, what was gathered this run, the blocker + its severity tier + its likely cause, and the safe next actions the user could take) and **halt cleanly**. Nothing is half-applied: no partial lock, no partial re-derive — the run stops where it is, the event log + snapshot intact, and the report tells the user exactly where things stand.
- **Self-heal and continue** — the orchestrator proposes **concrete remediation(s) derived from the information already gathered**, applies them **only after the user approves**, and continues the flow from where it stopped. Concrete examples (so this isn't abstract):
  - **Decisions aren't actually flat / re-derivable** (the orchestrator finds the project's `decisions` are narrative/sparse rather than a complete flat keyspace — the derived `can_rederive` signal is false — but the flow needs a flat keyspace) → run the **`design-recovery`** agent to reconstruct the decisions into the flat dotted keyspace, then seed each via `architect-brain set-decision <key> <value>` (one `DecisionMade` per recovered key).
  - **An ADR is recorded in the ledger but has no file on disk** (`adr_files_exist`, 17, WARNING) → write the file from the recorded decision, then `architect-brain record-adr --phase <phase> <NNNN> "<title>" Accepted` (or dispatch `decision-revisor` to author the full ADR), then re-run `architect-brain audit --only 17`.
  - **`project_layout` drifted from disk** (`scaffold_executed`, 26 — recorded layout names paths that no longer exist, or the tree grew paths the layout doesn't list) → re-record the layout from the actual tree (`architect-brain set-decision project_layout …`) or flag the specific missing paths for the user, then re-run `architect-brain audit --only 26`.
  - **The audit has an auto-fixable WARNING** (e.g. a missing forward-compat stamp, an absent `generate_when: always` doc such as `PROJECT_REQUIREMENTS.md`) → apply the documented remediation (re-stamp / re-author that one doc via `document-author`, then `architect-brain record-doc`) and **re-run the audit**.

  The proposals come from the **SAME information the flow already has** — the `detect` verdict, the audit's findings (`--verbose`), the projections — so it is *informed remediation, not guessing*. **The user always approves each remediation before anything is applied**; the orchestrator proposes, the user disposes. A FATAL finding (e.g. `state_schema_valid` 29, `resume_test` 31, `catalog_topo_acyclic` 32) can NEVER be acked past — it must be genuinely fixed; a BLOCKING finding may only be downgraded with an explicit, recorded `architect-brain audit --ack=<reason>`.

### Why this and not a bare failure

A bare failure (silent skip, or a raw trace dumped into the transcript) gives the user neither the picture nor a move. The informational-error + `AskUserQuestion` protocol gives both: a clean read of *what failed / what's known / what's at risk*, and a choice between a clean documented stop and an approved, informed fix-and-continue. It is the §1 "errors surface their detail; success stays terse" principle, fully specified. Mechanical, well-understood gaps (a missing ADR stub, a stale layout, an absent always-generated doc) are exactly the auto-fixable cases self-heal proposes; genuine design BLOCKERs — and any FATAL finding — are the cases where the report-and-stop path is usually the honest one.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
