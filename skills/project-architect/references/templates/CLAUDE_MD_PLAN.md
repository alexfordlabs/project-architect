<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: CLAUDE_MD_PLAN
generate_when: always
required_decisions:
  - project.name
  - project.elevator_pitch
  - tech_stack.language
optional_decisions:
  - project.has_subfolders
  - tech_stack.frontend
  - tech_stack.backend
depends_on:
  - PROJECT_OVERVIEW.md
  - TECH_STACK.md
revision_triggers:
  - project.name
  - project.elevator_pitch
---

# CLAUDE.md plan — {{project.name}}

This document **describes** what the future root `CLAUDE.md` will contain. The actual `CLAUDE.md` is generated in Phase 7 by `claude-md-author` consuming this plan as input.

## Why a plan, not the file itself

Phase 4 produces design + plan docs only. Generating `CLAUDE.md` directly in Phase 4 conflated design with execution and made Phase 5 iteration awkward (you'd have to edit the produced file, not the plan). With a plan-first approach:
- Phase 5 lets you edit the plan
- Phase 7 executes the (possibly-edited) plan to produce `CLAUDE.md`
- The plan stays as a permanent record of intent

## Project context block (required)

The future `CLAUDE.md` will open with a one-paragraph summary:

> **{{project.name}}** is {{project.elevator_pitch}}.
> Built with {{tech_stack.language}}{{ if tech_stack.frontend then " + " + tech_stack.frontend }}{{ if tech_stack.backend then " + " + tech_stack.backend }}.
> {{ if state.locked then "Architecture locked at " + state.version + " (designed via project-architect)." else "Currently in design (project-architect bootstrap)." }}

## Working-in-this-project rules

The future `CLAUDE.md` will list invariants from the design:

- **Language**: {{tech_stack.language}} {{tech_stack.language_edition}} per ADR {{tech_stack.language.adr}}
- **Test discipline**: {{decisions.testing.discipline}} per ADR {{decisions.testing.adr}}
- **Commit style**: Conventional Commits per ADR {{tech_stack.release_automation.adr}}
- **Security boundary**: {{decisions.architecture.security.policy}} per ADR {{decisions.architecture.security.adr}}
- **(other invariants from ADRs)**

## Next-step menu

The future `CLAUDE.md` ends with a slash-command menu for fresh Claude sessions:

```
## Next steps
- `/scaffold` — invoke superpowers:writing-plans + SDD against SCAFFOLD_PLAN.md
- `/implement <feature>` — implement a specific feature from PROJECT_REQUIREMENTS.md
- `/iterate-design` — re-launch project-architect to revise locked design
```

## Per-subfolder CLAUDE.md plans

{{ if project.has_subfolders then "" else "v0.1 has a single root CLAUDE.md only. Subfolder CLAUDE.mds will be planned when src/ tree exists post-scaffold." }}

For projects with substantial subfolders (`src/`, `tests/`, `docs/`), each subfolder gets its own CLAUDE.md describing local conventions. List planned subfolder CLAUDE.mds here:

| Subfolder | Purpose | Source ADR |
|---|---|---|
| (none planned at v0.1) | | |

## Notes for the executor

When `claude-md-author` consumes this plan in Phase 7:
1. Substitute every `{{...}}` placeholder from `state.decisions`.
2. Resolve every "(see X)" reference into a literal cross-link.
3. Validate via `claude-md-management:claude-md-improver` if the skill is available.
4. Write the resolved file to `CLAUDE.md` at project root.
5. Commit: `architect(phase-7): execute CLAUDE_MD_PLAN`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
