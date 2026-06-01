<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: NEXT_STEP_PLAN
generate_when: always
required_decisions:
  - project.name
optional_decisions:
  - project.sub_type
  - tech_stack.language
depends_on: []
revision_triggers:
  - project.name
---

# Next-step plan — {{project.name}}

This document **describes** what the future `docs/NEXT_STEP_PLAN.md` will contain. The actual file is generated in Phase 7 by `claude-tooling-author` consuming this plan as input.

It is the **router doc** that closes the project-architect loop: once the design is locked and the `.claude/` tree is materialized, a fresh contributor (or a fresh Claude session) reads this single page to figure out which slash command to run next. It pairs with the "Next steps" block in the root `CLAUDE.md` — `CLAUDE.md` advertises the slash commands; this plan explains *when* to pick which one, and *how to recover* when one of them fails.

## Why a plan, not the file itself

Phase 4 produces design + plan docs only. Generating `NEXT_STEP_PLAN.md` directly in Phase 4 would conflate design (which downstream skills are correct for this project) with execution (writing the on-disk router page). With a plan-first approach:
- Phase 5 lets you edit this plan and re-run audit
- Phase 7 executes the (possibly-edited) plan to produce `docs/NEXT_STEP_PLAN.md`
- The plan stays as a permanent record of the intended user-facing routing, traceable back to Phase 8 hand-off options

## Per-option routing table

The future `NEXT_STEP_PLAN.md` will open with a single table that maps **user intent → slash command → downstream skill chain**. This is the primary navigation surface — everything else on the page is detail.

| User intent | Slash command | Downstream skill chain |
|---|---|---|
| Scaffold the codebase from the locked design | `/scaffold` | `superpowers:writing-plans` → `superpowers:executing-plans` → `superpowers:subagent-driven-development` (TDD per file from `SCAFFOLD_PLAN.md` §2) |
| Implement a single feature from `PROJECT_REQUIREMENTS.md` | `/implement <feature>` | Same chain as `/scaffold`, scoped to one feature spec |
| Revise the locked architecture or design | `/iterate-design` | Re-launch `project-architect:project-architect`, which bumps `state.version` (e.g., `v1.0 → v1.1-draft`), unlocks the design, and re-enters Phase 5 |

For every row, cite the originating Phase 8 option (a/b/c) so the routing decision is auditable back to the orchestrator log.

## If you want X, run /Y

The future `NEXT_STEP_PLAN.md` will repeat the routing table in **explicit prose pairings** for grep-ability — a fresh contributor scanning the page should find their exact intent in one Cmd-F.

- **If you want to scaffold the codebase from `docs/SCAFFOLD_PLAN.md`:** run `/scaffold`. No arguments. The command reads `state.json`, finds the locked design, and hands `SCAFFOLD_PLAN.md` to `superpowers:writing-plans`. Result: a working, committed scaffold ready for `/implement <feature>`.
- **If you want to implement a feature from `docs/PROJECT_REQUIREMENTS.md`:** run `/implement <feature>`, replacing `<feature>` with the feature ID or slug as it appears in `PROJECT_REQUIREMENTS.md` (e.g., `/implement F-007-pdf-export`). The command scopes the same superpowers chain to that single feature spec.
- **If you want to revise the locked architecture:** run `/iterate-design`. No arguments. The command prompts to confirm an unlock (bumps `state.version` from `v1.0` → `v1.1-draft`, sets `state.locked = false`), then re-launches `project-architect:project-architect` re-entering Phase 5 (locked design → audit → re-lock).

## Troubleshooting

The future `NEXT_STEP_PLAN.md` will close with a troubleshooting block keyed by failure mode. Each entry names the symptom, the root cause, and the manual fallback so the contributor is never stuck.

### If `/scaffold` fails because `superpowers` isn't installed

Symptom: `/scaffold` reports something like `skill superpowers:writing-plans not found` or the command silently returns with no plan written.

Recovery:
1. Install the `superpowers` plugin: `claude /plugin install superpowers@official-plugins` (or the v5.1.0+ marketplace path for your install).
2. Verify with `claude /plugin list | grep superpowers`.
3. Re-run `/scaffold`.

Manual fallback (if you can't or won't install `superpowers`):
1. Open `docs/SCAFFOLD_PLAN.md`.
2. Walk §5 bootstrap commands by hand, in order, in a clean directory.
3. For each row in §2 (`src/` tree), write a failing test first, then the stub file, then a passing test — one commit per file. This mirrors what `superpowers:subagent-driven-development` would do automatically.
4. Cite ADR numbers in each commit subject (e.g., `scaffold(src/lib.rs): library entry per ADR-0003`).

### If `/implement <feature>` fails because the feature isn't in `PROJECT_REQUIREMENTS.md`

Symptom: `/implement F-099-…` reports `feature not found in PROJECT_REQUIREMENTS.md` or returns an empty plan.

Recovery options (pick one):
- **Add the feature first.** Edit `docs/PROJECT_REQUIREMENTS.md` to add the missing feature spec (with acceptance criteria, ADR references, and an ID), commit, then re-run `/implement <id>`.
- **Use `/iterate-design`.** If the missing feature is significant enough that other docs (ARCHITECTURE, TESTING_STRATEGY) need updates too, run `/iterate-design` to unlock and re-enter Phase 5 properly. Add the feature spec across all affected docs there.

### If `/iterate-design` says "design is locked, cannot re-enter Phase 5"

Symptom: `/iterate-design` reports `state.locked = true`, refusing to proceed.

This is **expected** — locking is a deliberate barrier. The command will prompt: *"Unlock design and bump state.version from v1.0 → v1.1-draft? [y/N]"*. Answer `y` to proceed.

If the prompt does not appear (e.g., headless run), set `state.locked = false` and bump `state.version` manually in `state.json`, then re-run `/iterate-design`. The orchestrator picks up from Phase 5 of the bumped version.

### If `state.json` is missing or corrupted

Symptom: any of the three commands reports `state.json not found` or `state.json failed schema validation`.

Recovery:
1. Check `docs/state.json.bak` (created automatically before each phase write per Bug #14 fix in v2.1.5).
2. If `.bak` exists and is valid (`jq . docs/state.json.bak`), restore it: `cp docs/state.json.bak docs/state.json`.
3. If no backup exists, re-launch `project-architect:project-architect` and answer "resume" when prompted — the orchestrator rebuilds `state.json` from on-disk artifacts (ADRs, locked docs, agent commit subjects per `architect(phase-N): …` convention).

## Notes for the executor

When `claude-tooling-author` consumes this plan in Phase 7:

1. Substitute every `{{...}}` placeholder from `state.decisions` (most references here use `{{project.name}}` only — this template is intentionally near-static).
2. Resolve every "(see X)" reference into a literal cross-link to the locked doc under `docs/`.
3. Write the resolved file to `docs/NEXT_STEP_PLAN.md`.
4. Verify the three slash commands (`/scaffold`, `/implement`, `/iterate-design`) referenced here also exist as files under `.claude/commands/` after the rest of `CLAUDE_TOOLING_PLAN` execution — failure to find any one of them is a Phase 7 BLOCKER, not a warning.
5. Commit: `architect(phase-7): execute NEXT_STEP_PLAN`.

If the on-disk slash-command files are missing after Phase 7, fix `CLAUDE_TOOLING_PLAN` execution before declaring Phase 7 complete — `NEXT_STEP_PLAN.md` is the router doc and would 404 a fresh contributor.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
