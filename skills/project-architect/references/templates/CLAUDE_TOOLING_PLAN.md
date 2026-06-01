<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: CLAUDE_TOOLING_PLAN
generate_when: always
required_decisions:
  - project.name
  - tech_stack.language
optional_decisions:
  - decisions.security.policy
  - decisions.release.cadence
  - tech_stack.build_tool
  - tech_stack.test_runner
  - decisions.hooks.required
  - decisions.commands.required
  - decisions.agents.required
  - decisions.recommended_plugins
depends_on:
  - SECURITY_AND_COMPLIANCE.md
  - TECH_STACK.md
  - RELEASE_PROCESS.md
revision_triggers:
  - decisions.security.policy
  - tech_stack.language
  - tech_stack.build_tool
  - decisions.release.cadence
---

# `.claude/` tooling plan — {{project.name}}

This document **describes** what the future `.claude/` tree will contain. The actual `.claude/settings.json`, `.claude/hooks/*`, `.claude/commands/*`, `.claude/agents/*`, and `.claude/recommended-plugins.md` are generated in Phase 7 by `claude-tooling-author` consuming this plan as input.

## Why a plan, not the files themselves

Phase 4 produces design + plan docs only. Generating `.claude/*` directly in Phase 4 conflated design (what permissions / hooks / commands should we have, given the ADRs) with execution (writing concrete JSON and bash). It also made Phase 5 iteration awkward — you'd have to edit shipped tooling, not the plan that produced it. With a plan-first approach:
- Phase 5 lets you edit this plan and re-run audit
- Phase 7 executes the (possibly-edited) plan to produce the `.claude/` tree
- The plan stays as a permanent record of intent, traceable back to specific ADRs

## `settings.json` permissions plan

The future `.claude/settings.json` will encode permissions derived from `SECURITY_AND_COMPLIANCE.md` and the tech-stack ADRs. Allow only what the project actually needs; deny everything that ADR-derived security policy forbids.

Example shape (substituted from state):

```json
{
  "permissions": {
    "allow": [
      "Bash({{tech_stack.build_tool}} *)",
      "Bash({{tech_stack.test_runner}} *)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Read({{project.name}}/**)",
      "Write({{project.name}}/**)"
    ],
    "deny": [
      "Bash(rm:*)",
      "Bash(sudo:*)",
      "Bash(curl:*|sh)",
      "WebFetch(domain:{{decisions.security.disallowed_domains}})"
    ]
  },
  "env": {
    "{{tech_stack.env_var}}": "{{tech_stack.env_value}}"
  }
}
```

For each `allow` and `deny` row added, cite the ADR that mandates it (e.g., `# ADR 0007 — no network egress during tests`).

## `hooks/` plan

The future `.claude/hooks/` directory will contain one bash file per hook. List each planned hook below with its trigger, intent, and bash content. Hooks fire deterministically (the harness runs them, not the model), so they're the right home for invariants from `SECURITY_AND_COMPLIANCE.md` and `RELEASE_PROCESS.md`.

### Hook: `{{hook.name}}` (example)

- **Event:** `{{hook.event}}` (e.g., `PreToolUse`, `PostToolUse`, `Stop`)
- **Matcher:** `{{hook.matcher}}` (e.g., `Bash(git push:*)`)
- **Source ADR:** {{hook.adr}}
- **Intent:** {{hook.intent}}

```bash
#!/usr/bin/env bash
# {{hook.purpose_one_liner}}
set -euo pipefail
{{hook.body}}
```

Common hook patterns to plan, when applicable to the project:
- **Pre-commit lint/format** — guards against shipping unformatted code (cite TECH_STACK ADR)
- **Pre-push test gate** — runs the test suite before any push (cite TESTING_STRATEGY ADR)
- **Block destructive bash** — e.g., refuse `git push --force` to protected branches (cite RELEASE_PROCESS ADR)
- **Stop-hook session report** — appends to a session log on `Stop` events (cite ONBOARDING / observability ADR)

## `commands/` plan

The future `.claude/commands/` directory will contain one markdown file per slash command. Each command is a frozen entrypoint into the project's lifecycle. List each planned command below with its description, argument shape, and target intent. (Note: Phase 7 will also generate the three router commands `/scaffold`, `/implement`, `/iterate-design` from the canonical templates — list only project-specific additions here.)

### Command: `/{{command.name}}` (example)

- **Description:** {{command.description}}
- **Argument hint:** {{command.argument_hint}}
- **Target intent:** {{command.intent}}
- **Source ADR:** {{command.adr}}

```markdown
---
description: {{command.description}}
argument-hint: {{command.argument_hint}}
---

{{command.body}}
```

## `agents/` plan

The future `.claude/agents/` directory will contain one markdown file per custom project agent. Agents encapsulate multi-step workflows that benefit from their own context and tool set (e.g., `release-prep`, `bump-typst`, `regen-fixtures`). List each planned agent below with its scope and source ADR.

### Agent: `{{agent.name}}` (example)

- **Scope:** {{agent.scope}}
- **Tools allowed:** {{agent.tools}}
- **Source ADR:** {{agent.adr}}
- **When to invoke:** {{agent.trigger}}

```markdown
---
name: {{agent.name}}
description: {{agent.description}}
tools: [{{agent.tools}}]
---

{{agent.body}}
```

Common agent patterns to consider, when applicable:
- **`release-prep`** — orchestrates CHANGELOG bump + tag dry-run + release-notes draft (cite RELEASE_PROCESS ADR)
- **`bump-{{tech_stack.toolchain_name}}`** — pins a new toolchain version across the repo (cite TECH_STACK ADR)
- **`regen-fixtures`** — re-runs golden-file generators for fixtures committed under `tests/` (cite TESTING_STRATEGY ADR)

## `recommended-plugins.md` plan

The future `.claude/recommended-plugins.md` will be a human-readable curation document — not auto-installed, just a curated shortlist for a fresh contributor. Each entry must tie back to a concrete ADR or document section explaining *why* this plugin is relevant to this project.

Example shape:

```markdown
# Recommended plugins for {{project.name}}

These plugins amplify the workflows defined by this project's ADRs. None are auto-installed; pick what suits your machine.

## Code review
- **coderabbit:code-review** — automates PR review against our `CONTRIBUTING.md` style (ADR 0003)

## Testing & validation
- **playwright-cli** — only relevant if {{tech_stack.frontend}} is involved (ADR 0008)
- **semgrep:setup-semgrep-plugin** — recommended by SECURITY_AND_COMPLIANCE §Static analysis (ADR 0007)

## Release & deployment
- **commit-commands:commit-push-pr** — matches our Conventional Commits + protected-branch flow (RELEASE_PROCESS ADR 0011)

## Language-specific
- **{{tech_stack.language}}-…** — tied to TECH_STACK §Toolchain (ADR 0002)
```

## Notes for the executor

When `claude-tooling-author` consumes this plan in Phase 7:

1. Read `state.decisions` and substitute every `{{...}}` placeholder.
2. Resolve every "(cite ADR …)" reference into a literal link to `docs/decisions/000X-*.md`.
3. Write `.claude/settings.json` (JSON, validated against the schema in `references/state-schema.md` → settings shape).
4. For every hook block, write `.claude/hooks/<name>.sh` (chmod +x, shellcheck-clean).
5. For every command block, write `.claude/commands/<name>.md` (frontmatter + body).
6. For every agent block, write `.claude/agents/<name>.md` (frontmatter + body).
7. Also generate the three router slash commands `/scaffold`, `/implement`, `/iterate-design` from the canonical templates in `references/templates/slash-commands/` (registered in `document-catalog.md`).
8. Write `.claude/recommended-plugins.md` from the curation list above.
9. Run inline validators before declaring done:
   - `shellcheck` on every `.claude/hooks/*.sh`
   - `jq empty < .claude/settings.json` (JSON well-formed)
   - YAML frontmatter parser on every command and agent file
10. Commit: `architect(phase-7): execute CLAUDE_TOOLING_PLAN`.

If any validator fails, fix the offending file and re-run the loop; do not commit a partially valid `.claude/` tree.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
