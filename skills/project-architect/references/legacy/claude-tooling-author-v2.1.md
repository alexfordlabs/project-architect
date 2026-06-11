<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

> Archived v2.1 `.claude/` tooling authoring workflow — superseded by the plan-driven v2.2 flow. Kept for archaeology / bare-Phase-4 fallback.

## Workflow (v2.1 — legacy, superseded by v2.2)

### Step 1: Read the integration recipe library

Read `integration_path`. This file lists, for every stack signal, the recommended plugins/skills/hooks/agents/commands. Memorize the relevant rows for this project's stack.

### Step 2: Write `.claude/settings.json`

Structure:
```json
{
  "model": "claude-opus-4-7",
  "env": {
    "ANTHROPIC_CONTEXT_VARIANT": "1m"
  },
  "permissions": {
    "allow": [
      // pulled from the "Permission allowlist templates" section of integration_path,
      // filtered to the stack signals present in state.decisions
    ]
  },
  "hooks": {
    "PreToolUse": [
      { "matcher": ".*", "command": "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/pre-tool-use.sh" }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write", "command": "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/post-tool-use.sh" }
    ],
    "Stop": [
      { "command": "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/stop.sh" }
    ],
    "SessionStart": [
      { "command": "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/session-start.sh" }
    ]
  }
}
```

Adjust hooks based on stack — e.g., skip `Stop` hook if there's no test command yet (greenfield with no tests).

**Optionally invoke** `Skill: fewer-permission-prompts` if available — it can review the allowlist and tighten it. Invoke `Skill: update-config` for any schema validation needed.

### Step 3: Write `.claude/hooks/` scripts

Copy the templates from `integration_path` (Hook templates section), customizing each for the project's stack:
- `pre-tool-use.sh` — block dangerous commands (universal).
- `post-tool-use.sh` — formatter (filled in based on language).
- `stop.sh` — test command (filled in based on test framework; skip if no tests).
- `session-start.sh` — recent commits + open TODOs (universal).

`chmod +x` each script after writing.

**Optionally invoke** `Skill: hookify:writing-rules` for hook design principles.

### Step 4: Write `.claude/agents/` project-local subagents

Based on stack, write 1–3 of these (templates in `integration_path`):
- `test-runner.md` — runs the project's test suite.
- `migration-checker.md` — only if a database is present.
- `deploy-verifier.md` — only if production-bound.

Fill the stack-specific test command, migration tool, deploy command into each agent's prompt.

### Step 5: Write `.claude/commands/` slash commands

Based on stack:
- `feature.md` — feature dev workflow (always).
- `run-tests.md` — dispatches `test-runner` (always if tests).
- `deploy-preview.md` — if web project.
- Other stack-specific commands per `integration_path`.

### Step 6: Write `.claude/recommended-plugins.md`

Curate the list:
1. Always include the "Universal recommendations" rows.
2. For every stack signal present in `state.decisions`, look up the matching row(s) in `integration_path` and include them.
3. For every project-type signal, include the type-specific rows.
4. Include the "Quality/process recommendations" rows if `production_bound == true`.

Format each entry:
```markdown
### {{plugin name}}
**Install:** `claude plugin install {{plugin}}`
**Why:** {{why for this project — reference the specific decision}}
```

Group by category (Cloud/Hosting, Database, Frontend, Mobile, Auth, Payments, etc.).

**Optionally invoke** `Skill: claude-code-setup:claude-automation-recommender` for an automated recommendation pass; merge with the recipe-library output.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
