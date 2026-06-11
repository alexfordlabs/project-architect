<!--
Author: Alexander Ford <alex@alexfordlabs.com>
License: Apache-2.0
Project: project-architect (https://github.com/alexfordlabs/project-architect)
-->

# Memory Persistence Reference

How project-architect writes per-phase progress notes to the user's persistent memory file so future Claude sessions can resume context.

---

## Why memory persistence

A multi-day project-architect run spans multiple Claude Code sessions. Without persistent notes:

- Each fresh session starts cold (replays the event log under `docs/_architect_state/` + reconstructs context from generated docs)
- The user has to re-explain context if the agent drifts
- Decisions made in earlier sessions can be forgotten between phases
- `/iterate-design` has no narrative record of *why* earlier decisions were made — only the event log + locked projections

Per-phase memory writes keep a running log of "what was decided, when, why" in the user's `~/.claude/projects/<project>/memory/<project_slug>.md` file, indexed by `MEMORY.md`. The event log + projections remain the canonical machine-readable record; the memory file is the human-readable narrative.

---

## Memory file location

The orchestrator writes to:

```
~/.claude/projects/<project-id>/memory/project_architect_<project_slug>.md
```

Where:

- `<project-id>` is Claude Code's project directory (the actual filesystem path Claude is in, slugified by Claude Code itself)
- `<project_slug>` is a slug of the `project.name` decision read from `docs/_architect_state/99-flat-index.json` (e.g., `md2pdf-cli`, `ledger-app`); lowercased, non-alphanumeric collapsed to `-`, trimmed

The pointer to this file is recorded as a flat decision via a `DecisionMade` event — `architect-brain set-decision memory_pointer '{"name","path","last_synced"}'` (see `state-schema.md`). Subsequent phases Edit this same file rather than re-resolving the slug each time — the resolved path is canonical for the run.

---

## Cadence — when to write

The write cadence (one entry per phase boundary) is summarized in the table below; each phase's entry is appended at the moment that phase's `PhaseAdvanced` event lands (reflected as the new `current_phase` in `docs/_architect_state/workflow.json`).

| Phase | Action | Content |
|---|---|---|
| Phase 0a (Repo Init / Golden Paths) | **Create** the memory file; append index entry to `MEMORY.md` | Project name, elevator pitch, `started_at`, link to `docs/_architect_state/` |
| Phase 1 (Kickoff) | **Update** with kickoff decisions + domain-research summary | 2-3 sentence summary + research findings file path |
| Phase 2 (Vision) | **Update** with chosen scope + key constraints | What's in/out of scope; load-bearing constraints |
| Phase 3 (Architecture) | **Update** with architectural style/boundaries + its ADR ids | Architectural decisions + ADR file paths |
| Phase 4 (Tech Stack) | **Update** with chosen tech stack + its ADR ids | Stack decisions + ADR file paths |
| Phase 5 (Cost) | **Update** with the cost model | Cost-model snapshot |
| Phase 6 (Document Generation) | **Update** with generated-docs list + audit result | Doc count, audit summary (FATAL / BLOCKING / WARNING / INFO counts) |
| Phase 7 (Iteration) | **Update** each revision wave (one entry per major decision change) | What changed, why, ADR cross-ref |
| Phase 8 (Lock) | **Major update**: write "LOCKED at v1.0" header + design summary | Final ADR list, `locked_at`, full doc count |
| Phase 9 (Tooling Execution) | **Update** with execution outcome (what was generated, what was skipped) | `CLAUDE.md` y/n, `.claude/*` y/n, scaffold y/n |
| Phase 10 (Handoff) | **Final update** with handoff summary + next-step recommendations | Closing entry; future sessions can grep here |

Each write is **append-only** — the orchestrator never rewrites a prior entry. If Phase 7 revises a Phase 3 or Phase 4 decision, Phase 7 appends a new entry that cross-references the original; the original stays put.

---

## Memory entry template

Each entry uses this shape:

```markdown
## <Phase N name> — <ISO8601 timestamp>

<2-3 sentence summary of what happened in this phase.>

**Decisions made:**
- <decision 1> (ADR <NNNN>)
- <decision 2> (ADR <NNNN>)

**Files generated/modified:**
- <file path>

**Open questions:**
- <if any>

**Next:** <what the next phase will do>

---
```

Notes:

- The `<ISO8601 timestamp>` is stamped by the binary's clock (the event `ts`, ISO-8601 UTC) at the time of write.
- "Decisions made" cross-references ADR ids when relevant; pre-ADR phases (0a, 1, 2) may have none.
- "Open questions" is omitted when empty.
- The trailing `---` separates entries visually.

---

## MEMORY.md index format

The user's `MEMORY.md` (one level up from the per-project memory file) gets one line per memory file. project-architect appends:

```markdown
- [project-architect: <project name>](project_architect_<slug>.md) — <one-line elevator pitch>, locked at <version> (<locked_at>)
```

If the project is still in design (not locked), the suffix is `— in design (last update: <phase>)`. The orchestrator updates this single line on each phase boundary; the index never grows multiple lines per project.

If `MEMORY.md` does not exist when Phase 0a runs, the orchestrator creates it with a minimal header and the first entry.

---

## The `memory_pointer` decision

After the Phase 0a write, the orchestrator records the memory file path as a flat decision via `architect-brain set-decision memory_pointer '{"name","path","last_synced"}'` (a `DecisionMade` event; surfaced in `99-flat-index.json`). See `state-schema.md` for the schema. Subsequent phases Edit this file directly (not re-resolve the slug).

---

## Conflict resolution

If the `memory_pointer` decision is present at startup but the pointed-to file is missing or moved:

1. Regenerate the file by replaying the event log under `docs/_architect_state/` (best-effort reconstruction of past entries from the `PhaseAdvanced` / `DecisionMade` / ADR events, read via the `99-flat-index.json` flat decision index + `decisions/index.json` ADR ledger projections)
2. Append a one-line entry to `MEMORY.md` if its line is missing
3. Re-record the `memory_pointer` decision with `last_synced` set to the regeneration timestamp (a fresh `DecisionMade` event)
4. Continue the current phase as normal

The `MEMORY.md` index is the source of truth for "which memory files exist"; the per-file content is the source of truth for "what happened in this project-architect run" (the event log is its machine-readable counterpart). If both are missing, the orchestrator falls back to writing fresh as if from Phase 0a (no harm — append-only).

---

## Cross-references

- State field schema: `references/state-schema.md` § `memory_pointer`
- Phase boundaries that trigger writes: `SKILL.md` Phases 0a, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- `/iterate-design` workflow reads the memory file to seed the diff prompt: `commands/iterate-design.md`

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
