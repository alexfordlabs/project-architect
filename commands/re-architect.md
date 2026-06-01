---
description: Re-architect an existing project — recover its design from docs/ADRs/research into a reviewable artifact, triage every decision (keep/revise/drop/add), research the deltas + challenge the keeps with fresh sources, re-decide into the flat keyspace, and re-derive docs/ADRs/CLAUDE.md/tooling. Snapshot-first, branch-isolated; never rewrites code.
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# /re-architect

You are running the project-architect **ingest & re-architect** flow — for a mature, docs-rich project whose design you want to revisit from first principles. Follow the canonical seven-step flow in `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/re-architect-flow.md` exactly — read it now and execute its steps in order.

First, run the situation detector to learn what you are dealing with (it is read-only):

```
${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect
```

It emits `{ situation, schema_version, state_layout }` with `situation` ∈ `greenfield` | `v8_project` | `pre_v8_project`. Route on the verdict:

- `situation == "greenfield"` (no architect state at all) → REFUSE the cross-version re-architect: there is no recorded design to recover. If the tree has real source/manifests but no architect state, it is a **foreign project** — route to the reverse-engineer path. If genuinely empty, re-bootstrap fresh with `project-architect`.
- `schema_version` newer than this plugin supports → REFUSE: the project was produced by a newer plugin than is installed (the ceiling is enforced by the migrator's band checks, not by `detect`). Upgrade the plugin, then retry.
- `situation == "v8_project"` (already at `schema_version "4.0"`) → the design is already on the v8 model. Suggest **`/iterate-design`** for an in-place revision, and STOP. (A deliberate re-architect of a *current* design is still possible — skip straight to the flow's Step 2; no migration needed.)
- `situation == "pre_v8_project"` (a v7 monolith, schema below `"4.0"`) → proceed; Step 1 migrates it onto the v8 model. Note: `can_rederive == false` (orchestrator-derived) is EXPECTED and fine here — re-architect's whole purpose is to take a narrative/sparse-decisions project and re-decide it into a flat, re-derivable keyspace.

Then drive `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/re-architect-flow.md` step by step:

1. **DETECT + SAFETY** — snapshot the current design to `docs/versions/<old-version>/`, do the whole flow on a `rearchitect/architect-<date>` branch + PR, reconcile the ADR ledger from disk, and migrate the v7 monolith onto the v8 event-sourced model (`architect-brain migrate`, schema `"4.0"`).
2. **RECOVER** — dispatch the `design-recovery` agent to reconstruct the design into `docs/RECOVERED_DESIGN.md`.
3. **TRIAGE** — present `RECOVERED_DESIGN.md` and capture keep / revise / drop / add per decision (this is the human validation gate for the recovery). Ask every run how to triage (grouped + low-confidence-first + resumable by default).
4. **RESEARCH** the revise/add deltas, then run the challenge pass over the keeps (ask every run to confirm or narrow the scope).
5. **RE-DECIDE** — one focused question per revise/add (and any promoted keep) → a complete flat decision set; the project becomes re-derivable.
6. **RE-DERIVE** — regenerate docs (with superseding ADRs), `CLAUDE.md`, and `.claude/` tooling from the new decisions. Flag affected-code-areas; never rewrite code.
7. **RE-GATE + RE-LOCK** — green quality gate, then re-lock at a bumped major version + snapshot the new design.

Everything is snapshotted to `docs/versions/<old-version>/` before any mutation, and all work happens on the `rearchitect/architect-<date>` branch; the deploy/hosting integration reads `main`, so the re-architect is not live until merged. This command never rewrites the user's source code — when a re-decided decision invalidates built code it FLAGS the affected areas and tells the user to re-run `/implement` or `/scaffold` there.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
