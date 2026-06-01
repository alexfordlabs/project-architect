<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: SLASH_IMPLEMENT
target_path: .claude/commands/implement.md
generate_when: always
depends_on:
  - PROJECT_REQUIREMENTS.md
---

# Slash command template: `/implement <feature>`

When `claude-tooling-author` consumes this template in Phase 9 (Tooling Execution), it produces `.claude/commands/implement.md`.

## Target file content

```markdown
---
description: "Implement a specific feature from docs/PROJECT_REQUIREMENTS.md"
argument-hint: feature-name
---

Implement the feature `$1` from `docs/PROJECT_REQUIREMENTS.md`.

**Version-awareness gate (first).** Run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain detect`. It emits `{situation, schema_version, state_layout}`; the orchestrator routes off `situation` and compares `schema_version` against the plugin's current "4.0" format generation:
- `pre_v8_project` (a v7 monolith `docs/_architect_state.json`): run `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain migrate` to bring state to the event-sourced 4.0 layout (`docs/_architect_state/`) BEFORE implementing, then proceed.
- `v8_project` yet `schema_version` older than the current "4.0" format generation (an old-but-recognized design): present the four-option intent menu from `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/version-awareness.md` and act on the choice BEFORE implementing — option 1 upgrades the design then continues here; option 4 implements on the old design (warned, and records a `DecisionMade` for `version_gate_ack` so the menu isn't re-asked).
- `v8_project` with `schema_version` at the current "4.0" generation: proceed.

If the reported `schema_version` has a major newer than this plugin supports (the band `migrate` enforces), refuse with a clear message rather than guessing.

Steps:

1. Read `docs/PROJECT_REQUIREMENTS.md` and locate the feature spec for `$1`.
2. If the feature isn't found, surface that and propose adding it via `/iterate-design`.
3. Use `superpowers:writing-plans` to produce an implementation plan scoped to this feature.
4. Use `subagent-driven-development` to execute the plan.

Output:
- Code changes implementing the feature
- Test changes covering the feature
- One commit per atomic change, citing ADR numbers where applicable

If `superpowers:writing-plans` is unavailable, fall back to a manual TDD loop: write failing test → impl → green test → commit.
```

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
