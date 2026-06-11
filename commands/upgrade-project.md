---
description: Bring a project bootstrapped by an older project-architect forward to the current format — migrate state + decisions, re-derive docs/CLAUDE.md/tooling, re-gate to green, re-lock at a bumped version. Snapshot-first; nothing is lost.
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# /upgrade-project

You are running the project-architect **cross-version upgrade**. Follow the canonical flow in `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/upgrade-flow.md` exactly — read it now and execute its steps in order.

First, run the situation detector to learn what you are dealing with (it is read-only):

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect
```

It returns JSON with `situation` ∈ `greenfield` | `v8_project` | `pre_v8_project`, plus `schema_version` and `state_layout`. From those the orchestrator DERIVES the staleness signals the flow branches on (`below_floor`, `newer_than_plugin`, `can_rederive`) — they are computed, **not** emitted by `detect`. Route on the verdict:

- `situation == "v8_project"` (a `docs/_architect_state/` directory already at `schema_version "4.0"`) → tell the user the project is already current; STOP (idempotent no-op).
- `situation == "greenfield"` (no architect state) → there is nothing to migrate; this flow does not apply. Re-bootstrap fresh with `project-architect` instead.
- `situation == "pre_v8_project"` (a v7 monolith `docs/_architect_state.json`, schema below `"4.0"`) → this is the upgrade target. REFUSE only if the flow's Step 2 floor-check trips (`below_floor` → below the migratable band; `newer_than_plugin` → produced by a newer plugin). Otherwise proceed through the flow: PRESERVE (old) → MIGRATE state (`architect-brain migrate`) → CHOOSE MODE (`can_rederive`) → RE-DERIVE docs + CLAUDE.md + `.claude/` tooling (Full mode) or PRESERVE + FLAG (Preserve mode) → RE-GATE (must be green) → RE-LOCK at a bumped version.

Everything is snapshotted to `docs/versions/<old-version>/` before any mutation (Step 3), so nothing is lost. On a project with a git repo, do the whole upgrade on an `upgrade/architect-<date>` branch + PR per the flow's branch discipline; the deploy/hosting integration reads `main`, so the upgrade is not live until merged.

This command never rewrites the user's source code — when a re-walked decision invalidates built code it FLAGS the affected areas and tells the user to re-run `/implement` or `/scaffold` there.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
