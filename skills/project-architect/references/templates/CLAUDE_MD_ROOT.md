<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: CLAUDE_MD_ROOT
target_path: CLAUDE.md
generate_when: always
required_decisions:
  - project.name
  - project.elevator_pitch
  - tech_stack.language
depends_on:
  - CLAUDE_MD_PLAN.md
revision_triggers:
  - project.name
  - project.elevator_pitch
  - state.locked
---

# CLAUDE.md (router) template

When `claude-md-author` consumes this template in Phase 7, it writes the resolved content to `<project_root>/CLAUDE.md` — a short router doc that fresh Claude sessions auto-load.

## Target file content

```markdown
# {{project.name}}

## State

{{ if state.locked then "Architecture locked at " + state.version + " (designed via project-architect; see docs/PROJECT_OVERVIEW.md)." else "Currently in design — run /iterate-design to revise." }}

Locked at: {{state.locked_at}}

## Quick context

{{project.name}} is {{project.elevator_pitch}}.

Built with {{tech_stack.language}}{{ if tech_stack.frontend then " + " + tech_stack.frontend }}{{ if tech_stack.backend then " + " + tech_stack.backend }}.

See `docs/PROJECT_OVERVIEW.md` for the full pitch, `docs/ARCHITECTURE.md` for system design, `docs/TECH_STACK.md` for runtime/build choices.

## Working in this project

Invariants pulled from the locked ADRs:

- **Language**: {{tech_stack.language}} {{tech_stack.language_edition}} per ADR {{tech_stack.language.adr}}
- **Test discipline**: {{decisions.testing.discipline}} per ADR {{decisions.testing.adr}}
- **Commit style**: Conventional Commits ({{decisions.release_automation.commit_convention}}) per ADR {{decisions.release_automation.adr}}
- **Security boundary**: {{decisions.security.policy}} per ADR {{decisions.security.adr}}

Edit `CLAUDE_MD_PLAN.md` (in `docs/`) to change which invariants land here.

## Next steps

- `/scaffold` — scaffold the codebase from `docs/SCAFFOLD_PLAN.md` (uses `superpowers:writing-plans` + subagent-driven-development)
- `/implement <feature-name>` — implement a specific feature from `docs/PROJECT_REQUIREMENTS.md`
- `/iterate-design` — re-launch `project-architect` to revise the locked design (bumps {{state.version}} → next draft)

Each slash command is defined in `.claude/commands/`. If a command appears missing, check that Phase 7 (Tooling Execution) actually ran — see `docs/NEXT_STEP_PLAN.md` for manual recovery.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
```

## Notes for the executor

When `claude-md-author` consumes this template in Phase 7:
1. Substitute every `{{...}}` placeholder from `state.decisions` and `state` root fields.
2. Resolve every conditional (`{{ if X then Y else Z }}`) inline.
3. Write the resolved content to `<project_root>/CLAUDE.md`.
4. Commit: `architect(phase-7): execute CLAUDE_MD_PLAN`.

This template is a router — short, focused, with explicit pointers to deeper docs. The detailed content lives in `docs/`; CLAUDE.md is the table of contents + invariants header for fresh Claude sessions.
