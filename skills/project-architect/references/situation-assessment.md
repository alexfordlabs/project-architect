<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Situation assessment & routing

The routine the orchestrator runs at **Preflight** when it opens a project that already has architect history — i.e. a `docs/_architect_state/` directory exists, OR a v7-era monolith `docs/_architect_state.json` **file** exists (a pre-v8 project), OR the folder otherwise looks like a prior project (a `docs/` doc set, a lock, `docs/versions/` snapshots, an existing `CLAUDE.md` + `.claude/`). Instead of blindly re-entering a phase, the orchestrator first **assesses** the full situation — the recorded state, the whole project folder, AND every git branch — then **routes** the user to the right existing flow.

It also handles the **inverse** of architect history: a **foreign project** — a folder with real project material (source, package manifests, docs, a non-trivial tree) but **no architect state** at all, i.e. one project-architect never produced. That case is classified here and routed to the **reverse-engineer** companion (§2, "Reverse-engineer this foreign project"), which recovers a design into project-architect's own flat-decisions keyspace so the normal flow can pick it up. (A folder with material AND architect state is a prior project, handled by the routes below; a genuinely empty folder is a greenfield bootstrap, not this routine.)

This routine does **not** invent a new menu. It is the assessment + dispatch layer that sits in front of the gates already documented in `SKILL.md § Resumability` and `references/version-awareness.md`; every route below hands off to one of those existing flows. It adds **no new mutation** of the project — assessment is strictly read-only, and routing delegates to the chosen flow's own (already-tested, snapshot-first) machinery.

> Report progress per `references/output-style.md` — capture the mechanical output (the `detect` JSON, the branch listing, the folder inventory) and surface a **one-line situation summary**, not the raw blobs. Render the boundary by RUNNING `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui banner` (once, at the open) and `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar <phase>` (at each transition), never by transcribing its art.

---

## 1. Assess (read-only)

Gather four things, all without mutating the project or any branch.

### a. The recorded verdict

Run the shared detector and **capture** it (don't dump the JSON):

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect
```

`detect` reads whatever state layout it finds (the v8 `docs/_architect_state/` directory, or a v7 monolith `docs/_architect_state.json` file) under the default `--docs-dir docs` and returns the verdict. Its output is **exactly** `{situation, schema_version, state_layout}` — nothing else. Parse those three for the top-level classification:

- `situation` ∈ `greenfield` | `v8_project` | `pre_v8_project` — the top-level classification.
- `schema_version` — the raw probe string (e.g. `"4.0"`, `"3.1"`), or `null` when no state exists.
- `state_layout` ∈ `"v8_multi_file"` | `"v7_monolith"` | `"v7_monolith_unreadable"` | `null`. Concretely: `"4.0"` + `"v8_multi_file"` for a `v8_project`; a sub-`4.0` schema (e.g. `3.0`/`3.1`) + `"v7_monolith"` (or `"v7_monolith_unreadable"` if the monolith JSON won't parse) for a `pre_v8_project`; `null` schema_version + `null` state_layout for greenfield.

**Everything else that drives routing is DERIVED BY THE ORCHESTRATOR — it is NOT a field on `detect`'s output.** Compute these from the three primitives above plus the `workflow.json` projection:

- **Version-staleness** ⇐ compare `schema_version` against the plugin's current format generation (`"4.0"`). A `pre_v8_project` is the migrate route (§"Migrate" below). The newer-than-supported ceiling is enforced by the orchestrator against the band that `migrate`'s checks raise (`migration._check_band`) — not read off `detect`. See `references/version-awareness.md`.
- **Half-locked** (a relock/iterate crashed mid-way) ⇐ the `workflow.json` projection (`locked` / `locked_at` with no clean completion). Crash-safety; see `SKILL.md § "Resume from a half-locked state"`.
- **Interrupted flow** (a `/re-architect` or `/iterate-design` sub-flow stopped partway) ⇐ the `workflow.json` `substep` projection — a `{phase, substep, status}` record left at `status: "in_progress"` is the resume point.
- **Resumable** ⇐ the orchestrator's convenience derivation: there is an interrupted-flow substep at `status: "in_progress"` OR the workflow projection is half-locked.

### b. The project-folder inventory

Inventory what's on disk (capture, summarize):

- Which `docs/<NAME>.md` design docs exist (and whether the `generate_when: always` set is complete — the `required_docs_generated` check, 27, is the authoritative test of this set).
- Whether there's **code** (a populated source tree vs. docs-only).
- Whether the design is **locked** (read the `workflow` projection — `locked` + `version`) and at what version.
- Which **snapshots** exist under `docs/versions/`.
- Whether `CLAUDE.md` + `.claude/` tooling are present.

**Foreign-project classification.** If the assessment found **no architect state** (`detect` reports `situation: "greenfield"` — neither a `docs/_architect_state/` directory nor a `docs/_architect_state.json` file) but the folder nonetheless holds real project material — source files, a package manifest (`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` / …), a `README` or other docs, or a non-trivial folder tree — classify it as a **foreign project**: one project-architect never produced. This is distinct from (i) a **greenfield empty dir** (no material → the normal 12-phase bootstrap, not this routine) and (ii) a **project-architect-produced project** (has architect state, `v8_project` or `pre_v8_project` → the routes above). A foreign project routes to the reverse-engineer arm in §2.

### c. ALL git branches (read-only — never mutate)

The interrupted work, an in-flight upgrade, or a re-architect attempt may live on **another branch**, not the one checked out. Enumerate **all branches** (local + remote) and peek each candidate's architect state **without ever switching branches**:

```bash
# List all branches (local + remote tracking refs). Capture; surface a count, not the raw list.
git branch -a 2>/dev/null || true

# For each candidate branch, read its architect state WITHOUT checkout (tolerate missing).
# v8 branch: the flat-index projection. v7 branch: the legacy monolith file. Try both.
git show <branch>:docs/_architect_state/99-flat-index.json 2>/dev/null || true
git show <branch>:docs/_architect_state.json 2>/dev/null || true
```

`git show <ref>:<path>` reads a file's content **at that ref** without touching the working tree — so you can find architect work / WIP (an `upgrade/architect-*` or `rearchitect/architect-*` branch, an interrupted `iterate` sub-flow, a newer locked `version`) on branches the user isn't on, while staying entirely **read-only**. A v8 branch surfaces its decisions via `99-flat-index.json` (the flat `{decisions, adrs}` view); a v7 branch still carries the monolith `docs/_architect_state.json` file — peek whichever exists.

> **READ-ONLY is non-negotiable.** This routine NEVER runs `git checkout`, `git switch`, `git merge`, `git rebase`, `git reset`, `git stash`, `git restore`, or `git clean` — not on the current branch, not on any other branch. It only **observes** (`git branch -a`, `git show <ref>:<path>`, `git status`, `git log`). If interrupted work is found on another branch, the routine **reports** it and lets the user decide; it does not pull or merge it.

### d. The one-line summary

Synthesize the four sources into a single informational line (per `references/output-style.md`), e.g.:

```
Existing project: v8 design (schema 4.0), locked at v1.4.0 on `main`; an interrupted /re-architect (next step: triage) is on branch `rearchitect/architect-2026-05-23`.
```

or, for a pre-v8 project:

```
Existing project: pre-v8 monolith state (schema 3.1) at docs/_architect_state.json — migration required before resume.
```

Then present the routing menu.

---

## 2. Route

Present the menu via `AskUserQuestion`. Each option ties to an **existing** gate/flow — none reinvents one. Which options to surface depends on the assessment (e.g. only offer "Resume" when the orchestrator-derived *resumable* signal is true — an interrupted-flow substep at `status: "in_progress"` OR a half-locked workflow projection; only offer "Migrate" when `situation == "pre_v8_project"`); offer "Report only" always.

### Migrate — a pre-v8 monolith project — when `situation == "pre_v8_project"`

If `detect` reports `pre_v8_project` (a v7-era monolith `docs/_architect_state.json` file with `schema_version` below `"4.0"`), the project's state must be migrated to the v8 event-sourced layout **before** any phase resume. Route to:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate   # optionally --from 3.1
```

`migrate` snapshots the monolith, synthesizes the event log, replays it, re-stamps ADRs/docs, reindexes phases, compares (`replay(events) == projections`), and atomically flips the project onto `docs/_architect_state/` (reversible via the kept backup tarball). It runs a post-migration audit by default; a blocking post-migration audit leaves the original state preserved for review. After a clean migration the project is a `v8_project` and the routes below apply. See `SKILL.md § Resumability` and `references/state-schema.md` (migration policy).

### Resume the interrupted flow — when the orchestrator-derived *resumable* signal is true

- **An interrupted flow** (a `/re-architect` or `/iterate-design` sub-flow that stopped partway): resume it from the substep the `workflow.json` projection left at `status: "in_progress"`. The substep projection records the single LATEST step — `/re-architect` and `/iterate-design` write `architect-brain set-substep <phase> <step> --status in_progress` on entry to each step and `… <step> --status done` as it completes — so a step interrupted mid-way stays `status: "in_progress"` and is exactly the resume point. Re-enter that flow at that step (see `references/re-architect-flow.md` for the rearchitect step order; the `/iterate-design` template for the iterate steps).
- **A half-locked state** (a relock crashed mid-way): do NOT resume a phase blindly — defer to the existing T6 **finish / roll back** handling in `SKILL.md § "Resume from a half-locked state — interrupted /iterate-design"`. That section owns the crash-safety menu; this routine just routes to it.

### Upgrade — bring an old design forward

Run `/upgrade-project` (see `references/upgrade-flow.md`). This is the **version-staleness** route — equivalent to version-awareness options **(1)** (upgrade + continue) and **(2)** (upgrade + rebuild code). The canonical four-option intent menu and its per-option semantics live in `references/version-awareness.md`; this routine surfaces the upgrade arm and hands off there rather than restating it. (A `pre_v8_project` whose state must be migrated first takes the **Migrate** route above; the upgrade arm covers in-band format-generation differences that don't need the monolith→event-sourced flip.)

### Re-architect in place — preserve-and-update

Run `/re-architect` (see `references/re-architect-flow.md`): recover → triage → research + challenge → re-decide → re-derive, **in place** (the current design is snapshotted, then revised where it sits; old code becomes reference). This is the **in-place arm** of version-awareness option **(3)** ("Start fresh, revisiting decisions").

### Start fresh — seeded greenfield

The **other arm** of "start fresh": run the normal 12-phase bootstrap, but **pre-seed** Vision / Architecture / Stack / decisions from the recovered information so those phases open **pre-filled** (the user edits, not starts blank):

1. **Snapshot first**, then set the old artifacts aside. Copy the current `docs/` (+ scaffold) to `docs/versions/<old-version>/`; then move the old design docs / scaffold ASIDE (e.g. into the snapshot dir) so the fresh bootstrap starts on a clean tree. (Contrast with the **in-place re-architect arm**, which preserves the design where it sits — here the old material is reference-only, not preserved in place.)
2. **Recover the decisions.** Dispatch the `design-recovery` agent to emit the **flat decisions keyspace** (the same `{key: value}` shape `/re-architect` recovers, using the canonical flat dotted keys of `references/decision-keys.md`).
3. **Ingest them as seeds.** Replay the recovered flat object into fresh state by recording one `DecisionMade` event per recovered key — `architect-brain set-decision <key> <json-value>` for each (after a fresh `architect-brain init` if no state directory exists). The Vision / Architecture / Stack phases then read these decisions from the `99-flat-index.json` projection as **pre-filled defaults** to confirm or edit — a seeded greenfield, not a blank one.

Both arms of "start fresh" — **seeded-greenfield** (here) and **in-place re-architect** (above) — are offered; the user picks. (This is the two-sub-mode split documented on option (3) of `references/version-awareness.md`.)

### Reverse-engineer this foreign project — when there's material but **no architect state**

Offered **only** for the **foreign-project** case (§1b): the folder has real project material but **no architect state** (`detect` reports `situation: "greenfield"` yet the tree is non-trivial), so there are no recorded decisions to recover in-house. Hand off to the **reverse-engineer** companion plugin, which recovers a design from the existing code/docs/notes and emits it in project-architect's **own** format — `docs/RECOVERED_DESIGN.md` plus a flat decisions keyspace with `origin: "reverse-engineered"` (the same `{key: value}` shape `design-recovery` produces in §"Start fresh", keyed per `references/decision-keys.md`).

1. **Probe whether `reverse-engineer` is installed** (same soft-dependency probe Preflight uses for recommended plugins):
   ```bash
   claude plugin list 2>/dev/null | grep -i reverse-engineer \
     || ls ~/.claude/plugins/cache 2>/dev/null | grep -i reverse-engineer
   ```
2. **If installed → INVOKE it** (its `reverse-engineer` skill). It runs its own recovery flow against this folder and writes the native artifacts above. project-architect does **not** re-implement recovery — it consumes the result.
3. **If NOT installed → point the user to the companion**, with brief install guidance, and stop without mutating anything:
   > This looks like an existing project I didn't design (no architect state). Recovering its design is the job of the **reverse-engineer** companion plugin (`alexfordlabs/reverse-engineer`, in the same `alexfordlabs` marketplace). Install it, then re-run me here:
   > `claude plugin marketplace update alexfordlabs` · `claude plugin install reverse-engineer@alexfordlabs` · then `/reload-plugins`.

**Consume its output via the EXISTING path (no new ingest path).** Once reverse-engineer has run — a flat decisions keyspace with `origin: "reverse-engineered"` now exists in project-architect's own format — project-architect reads it **natively** (the recovered decisions land in the flat keyspace; `detect` treats a recovered v8 state as current) and continues through the **seeded-greenfield** flow above: the recovered flat decisions are exactly the pre-seeded defaults the Vision / Architecture / Stack phases confirm or edit. If reverse-engineer emitted only `docs/RECOVERED_DESIGN.md`'s flat keyspace without writing it into architect state, replay it the same way the seeded-greenfield arm does — one `architect-brain set-decision <key> <json-value>` per recovered key (after `architect-brain init` if needed) — so the decisions become `DecisionMade` events in `docs/_architect_state/`. Either way the recovered decisions seed project-architect's forward flow through the **same** event-sourced `set-decision` / seeded path — never a bespoke one.

### Report only

Write a **situation report** — the recorded state, what the folder + branch sweep gathered, and the version / migration / interrupted-flow findings — and stop without mutating anything. This is the "write a report and stop" arm of the **self-healing error protocol** in [`references/output-style.md` §4](output-style.md): the user can equally choose to **self-heal** instead — let the orchestrator propose a concrete remediation derived from the assessment (e.g. an ADR file missing for a recorded ADR, a state file that fails `architect-brain audit --only 29`/`--only 31`) and, after approving it, continue into the matching flow rather than just exiting.

---

## 3. Precedence (integrates with the existing chain)

This routine **front-ends** the precedence chain already documented in `SKILL.md § Resumability` and `references/version-awareness.md` — it does not replace it. When several gates could fire, resolve them in this order, deferring to the existing sections for the actual menus:

1. **Pre-v8 migration first** (`situation == "pre_v8_project"`) — route to `architect-brain migrate` (above) before any phase resume; the monolith→event-sourced flip must complete and pass its post-migration audit before the remaining gates even apply.
2. **Half-locked resolution** (crash-safety) — `SKILL.md § "Resume from a half-locked state"` (T6 finish / roll back).
3. **Interrupted-flow resume offer** — resume a `/re-architect` or `/iterate-design` sub-flow from the `workflow.json` substep left at `status: "in_progress"` (the orchestrator-derived *resumable* signal).
4. **Version-staleness routing** — the four-option intent menu in `references/version-awareness.md` (upgrade / re-architect / seeded-greenfield / proceed).
5. **Locked-resume** — `SKILL.md § "Resume from locked state"` (unlock / snapshot / exit).

If none fire (not pre-v8, no interrupted flow, not half-locked, not old, not locked), there's nothing to route — proceed with the normal resume from the `workflow` projection's `current_phase`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
