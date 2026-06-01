<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Version-awareness gate (old-project intent menu)

The single source of truth for how project-architect's entry points react when they open a project whose design predates the current (v8) format. The main skill (at Resumability) and the three generated slash commands (`/implement`, `/scaffold`, `/iterate-design`) all run the SAME detector and present the SAME four-option menu, so every entry point behaves identically.

The current format is **schema_version `"4.0"`** — event-sourced, multi-file state under `docs/_architect_state/` (NOT a monolith JSON; see [`state-schema.md`](state-schema.md)). Two distinct staleness situations exist, and they take different routes:

- A **v7-and-earlier monolith** project (a single `docs/_architect_state.json` file, schema < 4.0) routes to **migration** (`architect-brain migrate`) — the structural cutover to the event-sourced model. That is handled directly in the main skill's Resumability section; it is NOT the four-option menu.
- A project that is **within the migratable band but a different format generation** (an older project-architect format that `detect` flags as old yet not a pre-v8 monolith) presents the **four-option intent menu** below.

## The detector predicate (reused, not reinvented)

Every entry point runs the shared staleness detector that ships with the plugin:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect
```

It emits EXACTLY three fields: `situation` ∈ `greenfield` | `v8_project` | `pre_v8_project`; `schema_version` (the raw probe string, e.g. `"4.0"` or `"3.1"`, or `null`); and `state_layout` ∈ `"v8_multi_file"` | `"v7_monolith"` | `"v7_monolith_unreadable"` | `null`. It does NOT emit any staleness verdict — **staleness is DERIVED by the orchestrator** from `situation` + `schema_version`:

- `situation == "pre_v8_project"` ⇒ **migrate** (the structural cutover to the event-sourced model).
- `situation == "v8_project"` with `schema_version` older than the plugin's current format generation (`"4.0"`) ⇒ **old**: show the four-option menu below.
- `schema_version` newer than this plugin supports ⇒ **upgrade the plugin** (the newer-than-supported ceiling is enforced by the orchestrator against the `migrate` band check — `migration._check_band` — NOT by `detect`).

Act on the situation + derived verdict:

- `situation == "pre_v8_project"` (a v7 monolith `docs/_architect_state.json`, schema < 4.0) → route to **migration**: run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate` (optionally `--from 3.1`) BEFORE proceeding. Do NOT show the four-option menu — migration is the structural cutover, not an intent choice. (See the main skill's Resumability section + [`state-schema.md`](state-schema.md) migration policy.)
- Orchestrator-derived **below-the-band** (unrecognizable layout / below the migratable band — the `migrate` band check refuses it) → do NOT show the menu; tell the user to re-bootstrap fresh.
- Orchestrator-derived **newer-than-supported** (`schema_version` is a higher format generation than this plugin produces — the band ceiling is enforced by `migration._check_band`, not by `detect`) → tell the user to upgrade the plugin; do not proceed.
- `situation == "v8_project"` but `schema_version` is an older in-band format generation than this plugin produces (and not a pre-v8 monolith) → present the four-option menu below.
- `situation == "v8_project"` with `schema_version` at the current generation → current project; proceed with the command's normal job.

**Precedence** (when several gates could fire at Resumability): resolve a **half-locked** state first (crash-safety) → THEN an **interrupted-flow resume** offer → THEN this **version-staleness** gate (which itself routes a `pre_v8_project` to migration, else shows the menu) → THEN the **locked-resume** menu. A half-locked old project finishes/rolls back its interrupted iteration before being offered an upgrade or migration.

**Don't re-ask:** if the user previously chose option (4) on this project, the orchestrator recorded a `DecisionMade` event for `version_gate_ack = true` (read it from the `99-flat-index.json` flat decisions); skip the menu and proceed.

## The four-option intent menu (verbatim)

```
This project's design was produced by an older project-architect (vX; current is v8).
The v8 hardening (event-sourced state, the 35-check audit gate, ADR provenance,
cross-link integrity) does not apply to it yet. What would you like to do?

  (1) Upgrade design, then continue        — run the cross-version upgrade, then proceed
                                              with what you invoked. KEEPS your existing scaffold/
                                              implementation; FLAGS the areas the changed
                                              decisions affect so you can re-run /implement or
                                              /scaffold there.            [continue / reuse what's built]

  (2) Upgrade design, then rebuild code     — run the upgrade, then re-scaffold / re-implement
                                              against the upgraded design.        [rewrite the build]

  (3) Start fresh, revisiting decisions     — full re-bootstrap with your old decisions pre-seeded
                                              as defaults to revisit; optionally reuse existing code
                                              as reference.                       [build from scratch]

  (4) Proceed without upgrading             — continue on the old version. WARNED: this design
                                              predates the v8 gates, so completeness is not enforced.
                                                                                  [not recommended]
```

## What each option does

| Option | Action | KEEPS code? | Re-bootstrap? |
|---|---|---|---|
| **(1) Upgrade, then continue** | Run the cross-version upgrade (`/upgrade-project` → [`upgrade-flow.md`](upgrade-flow.md)), then resume the invoked command. After upgrade, FLAG affected-code-areas (see [`revision-playbook.md`](revision-playbook.md)) and tell the user to re-run `/implement` / `/scaffold` there. For an older-format project the upgrade runs in **preserve mode** (migrate decisions into the flat keyspace + reconcile ADRs + keep docs + flag manual follow-ups; see upgrade-flow.md). | yes | no |
| **(2) Upgrade, then rebuild** | Run the upgrade flow (which regenerates docs + CLAUDE.md + `.claude/` tooling via the declarative `catalog.json` selection), then ALSO re-scaffold / re-implement the **code** against the upgraded design. | replaces code | no |
| **(3) Start fresh, revisiting decisions** | Offers TWO sub-modes (the user picks): **(3a) in-place re-architect** — run `/re-architect` (see [`re-architect-flow.md`](re-architect-flow.md)): recover the design from docs/ADRs → triage keep/revise/drop → research the deltas + challenge the keeps → re-decide → re-derive everything in place; old code becomes reference. **(3b) seeded greenfield** — run the normal 12-phase bootstrap with the recovered decisions **pre-seeded** as editable defaults (`design-recovery` emits the flat keyspace → the orchestrator replays it into fresh state with one `architect-brain set-decision <key> <value>` per recovered key), after the old docs/scaffold are snapshotted and set aside. See [`situation-assessment.md`](situation-assessment.md) for how Preflight detects an old/interrupted project and routes to either arm. | reference | re-derive |
| **(4) Proceed without upgrading** | Continue the invoked command on the old version, after a one-line warning that the v8 gates do not apply. Record the acknowledgement as a `DecisionMade` event for `version_gate_ack` (`architect-brain set-decision version_gate_ack true`) so it isn't re-asked every invocation. | yes | no |

## Which entry points gate, and how

| Entry point | Normal job | With an old design |
|---|---|---|
| **main skill** (`project-architect`) | Resume from the `workflow` projection's `current_phase`; on a locked project, offer unlock / snapshot / exit | At Resumability, run the detector. If a `pre_v8_project` → route to `architect-brain migrate`. Else if old → show this menu *before* the locked-resume options. |
| **`/iterate-design`** | Unlock locked design → bump `+0.1-draft` → re-enter Iteration | Detector first. `pre_v8_project` → migrate. Else old → menu (option 1 ≈ "upgrade then iterate"); option 4 falls through to the plain unlock. |
| **`/implement <feat>`** | Read `PROJECT_REQUIREMENTS.md`, plan + execute the feature | Detector first. `pre_v8_project` → migrate. Else old → menu (option 1 = upgrade then implement; option 4 = implement on the old design, warned). |
| **`/scaffold`** | Read `SCAFFOLD_PLAN.md`, scaffold via superpowers | Detector first. `pre_v8_project` → migrate. Else old → menu (option 1/2 = upgrade then scaffold; option 4 = scaffold the old plan, warned). |

The canonical detector logic (the `architect-brain detect` invocation) ships with the plugin; the generated commands reference the *behavior* described here, so a project bootstrapped under any version gets the identical gate. The pre-v8-monolith case routes to `architect-brain migrate` (the event-sourcing cutover) ahead of any intent menu; only an old-but-non-monolith format reaches the four-option menu.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
