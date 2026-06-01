<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: SLASH_SCAFFOLD
target_path: .claude/commands/scaffold.md
generate_when: always
depends_on:
  - SCAFFOLD_PLAN.md
---

# Slash command template: `/scaffold`

When `claude-tooling-author` consumes this template in Phase 9 (Tooling Execution), it produces `.claude/commands/scaffold.md`. The content below is what gets written (verbatim, no substitution other than the conditional language-specific snippets which `claude-tooling-author` may inline based on the flat decision `stack.backend.language` read from `docs/_architect_state/99-flat-index.json`).

## Target file content

```markdown
---
description: "Scaffold the codebase from docs/SCAFFOLD_PLAN.md"
---

Scaffold the codebase from `docs/SCAFFOLD_PLAN.md` using `superpowers:writing-plans` + `subagent-driven-development`.

**Version-awareness gate (first).** Run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect`. The verdict's `situation` routes the command:
- `pre_v8_project` (a v7 monolith `docs/_architect_state.json` with `schema_version` < 4.0): run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate` to bring state to the event-sourced 4.0 layout BEFORE scaffolding, then proceed.
- within the migratable band but an older format generation (`situation == "v8_project"` yet `schema_version` older than this plugin's current "4.0" format generation, and not a pre-v8 monolith): present the four-option intent menu from `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/version-awareness.md` and act on the choice BEFORE scaffolding — option 1/2 upgrades the design then scaffolds; option 4 scaffolds the old plan (warned, and records a `DecisionMade` for `version_gate_ack` via `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision version_gate_ack true` so the menu is not re-asked).
- `v8_project` / current: proceed.
If the reported `schema_version` has a major newer than this plugin supports (the band `migrate` enforces), refuse with a clear message rather than guessing.

Steps Claude will take:

1. Read `docs/SCAFFOLD_PLAN.md` — the plan describes build manifest, src/ tree, license files, toolchain pin, and bootstrap commands.
2. Read `docs/_architect_state/workflow.json` to confirm the project is locked at v1.0 (the `workflow` projection carries `locked` + `version`).
3. Invoke `Skill: superpowers:writing-plans` with `spec_path: docs/SCAFFOLD_PLAN.md` and execution mode `subagent-driven-development`.
4. Superpowers writes the implementation plan, then dispatches subagents to execute it.

After scaffolding:
- The codebase exists in src/ (and sibling dirs per the plan)
- All ADRs are crossed-referenced in source comments where the plan calls for it
- A `chore: bootstrap scaffold` commit lands

Fallback: if `superpowers:writing-plans` isn't installed, see `docs/NEXT_STEP_PLAN.md` for manual bootstrap.
```

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
