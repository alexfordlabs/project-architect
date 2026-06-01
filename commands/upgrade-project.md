---
description: Bring a project bootstrapped by an older project-architect forward to the current (v5) format — migrate state + decisions, re-derive docs/CLAUDE.md/tooling, re-gate to green, re-lock at a bumped version. Snapshot-first; nothing is lost.
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# /upgrade-project

You are running the project-architect **cross-version upgrade**. Follow the canonical nine-step flow in `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/upgrade-flow.md` exactly — read it now and execute its steps in order.

First, run the staleness detector to learn what you are dealing with:

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-ledger --state docs/_architect_state.json detect
```

- If the verdict's `below_floor` is true, or `newer_than_plugin` is true → REFUSE per the flow's Step 2 (do not attempt a partial migration).
- If `is_old` is false → tell the user the project is already current; STOP.
- Otherwise proceed through the flow: SNAPSHOT (old) → MIGRATE state → MIGRATE decisions → RE-WALK the stale-decision delta → RE-DERIVE docs + CLAUDE.md + `.claude/` tooling → RE-GATE (must be green) → RE-LOCK at a bumped major version + SNAPSHOT (new).

Everything is snapshotted to `docs/versions/<old-version>/` before any mutation (Step 3), so nothing is lost. On a project with a git repo, do the whole upgrade on an `upgrade/architect-<date>` branch + PR per the flow's branch discipline; the deploy/hosting integration reads `main`, so the upgrade is not live until merged.

This command never rewrites the user's source code — when a re-walked decision invalidates built code it FLAGS the affected areas and tells the user to re-run `/implement` or `/scaffold` there.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
