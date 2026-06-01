<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: SLASH_ITERATE_DESIGN
target_path: .claude/commands/iterate-design.md
generate_when: always
depends_on: []
---

# Slash command template: `/iterate-design`

When `claude-tooling-author` consumes this template in Phase 9 (Tooling Execution), it produces `.claude/commands/iterate-design.md`.

## Target file content

```markdown
---
description: "Re-open the locked architecture for revision (bumps v1.0 → v1.1-draft)"
---

Re-launch `project-architect:project-architect` to revise the locked design.

**Progress sub-ledger (resumability).** At the START of each step below, record it: `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-substep iterate <step> --status in_progress`; on COMPLETION, mark it done: `… set-substep iterate <step> --status done`. Step keys, in order: `version-gate`, `unlock`, `revise`, `relock`. `set-substep` appends a `SubstepRecorded` event whose latest value lands in the `workflow` projection's `substep` field, so a session interrupted mid-iteration is detectable: the Preflight situation-assessment (`references/situation-assessment.md`) reads `workflow.json`'s `substep` and offers to resume from a step left at `status: "in_progress"`. Recording each step `in_progress` on entry is what makes a *mid-step* interruption detectable — a step left `in_progress` is exactly the resume point; marking only `done`-on-completion would make an interrupted iteration read as fully complete.

**Version-awareness gate (`version-gate`, first).** `set-substep iterate version-gate --status in_progress`, then run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect`. Route on the verdict's `situation`:
- `pre_v8_project` (a v7 monolith `docs/_architect_state.json` with `schema_version` < 4.0): run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate` to bring state to the event-sourced 4.0 layout under `docs/_architect_state/` BEFORE iterating, then proceed to `unlock`.
- within the migratable band but an older format generation (`situation == "v8_project"` yet `schema_version` older than this plugin's current format generation, and not a pre-v8 monolith): present the four-option intent menu from `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/version-awareness.md` and act on the choice BEFORE iterating — option 1 upgrades the design then iterates; option 4 records `version_gate_ack` (`architect-brain set-decision version_gate_ack true`) and falls through to the plain `unlock` below.
- `v8_project` / current: proceed.
If the reported `schema_version` has a major newer than this plugin supports (the band `migrate` enforces), refuse with a clear message rather than guessing. Then `set-substep iterate version-gate --status done`.

Steps:

1. **`unlock`** — `set-substep iterate unlock --status in_progress`. Read the `workflow` projection at `docs/_architect_state/workflow.json` — confirm `locked == true` and read `version`. (Never hand-edit the state files; the projection is materialised from the event log.) If locked: prompt the user to confirm unlocking. On confirmation:
   - Snapshot the locked v1.0 docs to `docs/versions/v1.0/` for reference BEFORE unlocking — this preserves the immutable lock-point so the user can always diff against it.
   - Emit a `LockSet` event setting `locked = false`, bumping `version` to `"<prev>+0.1-draft"` (e.g. `"v1.0" → "v1.1-draft"`), and clearing `locked_at` to null: `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain append-event --type LockSet --payload '{"locked": false, "version": "v1.1-draft", "locked_at": null}'`. The projection re-materialises; `replay(events) == projections` holds.
   - **Run the layout-vs-disk check early.** Before iterating, validate the recorded `project_layout` (carried in the `workflow` projection) against the real tree — the same `scaffold_executed` logic (check 26) the final re-gate runs, but surfaced HERE so drift between the recorded layout and the on-disk scaffold is caught at the *start* of the iteration rather than deferred to the final re-gate: `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --only 26 --verbose`. If a path in `project_layout` no longer resolves on disk, flag it to the user before revising — the recorded layout has drifted from reality and should be reconciled first.

   Then `set-substep iterate unlock --status done`.
2. **`revise`** — `set-substep iterate revise --status in_progress`. Invoke `Skill: project-architect:project-architect`. The skill resumes from the Iteration phase with the previously-locked decisions loaded (read from the `99-flat-index.json` flat-decisions projection). The user iterates on the design and approves it. **Persist each revised decision through the binary as an event — never hand-edit the state files:** `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision <key> <json-value>` (the canonical flat dotted key per `references/decision-keys.md`; the value as JSON, e.g. `'"PostgreSQL"'`). `set-decision` appends a `DecisionMade` event against `schema_version` "4.0", so the revised design stays a flat-keyspace, re-derivable project. Then `set-substep iterate revise --status done`.
3. **`relock`** — `set-substep iterate relock --status in_progress`. After the user approves, the Lock phase re-locks at the bumped version: emit a `LockSet` event with `locked = true`, a fresh `locked_at`, and `version` stripped of the `-draft` suffix (e.g. `"v1.1-draft" → "v1.1"`), then re-snapshot the new locked docs to `docs/versions/<new_version>/`. Then `set-substep iterate relock --status done` as the FINAL action — clearing the last in-progress step so the situation-assessment resume check (reading `workflow.json`'s `substep`) no longer sees the iteration as interrupted.

If the state is already unlocked (mid-iteration), this command resumes the in-progress iteration. Read the `workflow` projection at `docs/_architect_state/workflow.json` — its `substep` field holds the latest `SubstepRecorded` (`{phase, substep, status}`); a step left at `status: "in_progress"` is the resume point — and pick up there rather than restarting.
```

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
