<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Dispatch prompts

The orchestrator (`SKILL.md`) keeps the dispatch LOGIC (which agent, when, how to resolve the result); the verbose prompt BODIES live here and are loaded per-phase. Each dispatch prepends the **Shared dispatch header** below, then substitutes the `{{...}}` context from the flat decisions (`docs/_architect_state/99-flat-index.json`) as documented at the dispatch site in `SKILL.md`. The orchestration steps that surround each dispatch (parse the return, record via `architect-brain`, commit, transition) stay in `SKILL.md`.

State is event-sourced and multi-file (NOT a single monolith JSON) — see `references/state-schema.md`. Where a dispatch passes a "state slice" or a "state path", it points at the v8 state under **`docs/_architect_state/`**: the flat decision/ADR view is `docs/_architect_state/99-flat-index.json` (`{decisions: {dotted-key: value}, adrs: [...]}`), the ADR ledger projection is `docs/_architect_state/decisions/index.json`, and the ADR markdown files live in `docs/_architect_state/decisions/`. Subagents READ those projections; they never hand-edit any state file — every mutation flows back through `architect-brain` events (`set-decision`, `record-adr`, `record-doc`, …) that the orchestrator (or the agent, where it owns the write) issues.

**Path resolution in INPUTS (critical).** A dispatched agent runs with `cwd` = the USER's project, **not** the plugin. So any INPUT path that points INTO THE PLUGIN — templates, `catalog.json`, the integration recipes, the revision playbook (anything under `skills/project-architect/…`) — is written here as `${CLAUDE_PLUGIN_ROOT}/skills/project-architect/…`, and **the orchestrator MUST expand `${CLAUDE_PLUGIN_ROOT}` to its real absolute value when filling the dispatch** (the agent is not a shell — a literal `${CLAUDE_PLUGIN_ROOT}` or a bare `skills/…` reaches it unresolved and the `Read` fails silently → fabricated structure). INPUT paths that point at the USER's project (`docs/…` — state projections, research, output paths) stay relative; they ARE relative to the agent's cwd. Per `agent-common.md`, an agent handed a bare, unresolvable plugin-relative path treats it as a BLOCKER and returns the informational error state rather than guessing.

## Shared dispatch header

Prepend this verbatim to every `Agent({...})` prompt — the model directive, the identity-hygiene HARD RULE, and the post-return scrub all travel together:

```
[MODEL DIRECTIVE]
Run with maximum effort. Apply extended thinking. Be thorough.

[IDENTITY HYGIENE — HARD RULE]
Never write a real person's name, employer, personal email, physical location, government ID, or any
other deanonymizing identifier into any file you create or edit. Use only the project's declared identity
(role/handle/pseudonym) from the flat decisions. If a source you read contains such an identifier, do NOT
copy it forward — paraphrase or omit. This complements gitleaks (which catches secrets) for non-secret PII.

[POST-RETURN SCRUB]
Before returning, re-read every file you wrote and confirm none contains a forbidden identity term.
If you find one, remove it and note the removal in your return summary.
```

The identity-hygiene clause is enforced by the `identity_hygiene` check (24, BLOCKING) after research/doc writes — see the `Which check runs at which transition` map in `SKILL.md` (under `## Phase transition contract`). The orchestrator runs that check as `architect-brain audit --only 24` after each doc/research batch.

Dispatched agents report concise informational progress per `references/output-style.md` — they return a tight summary of what they produced (files written, decisions affected), NOT raw dumps of script output, findings JSON, or `find`/`grep` listings. The orchestrator renders the per-step status by RUNNING the binary (`${CLAUDE_PLUGIN_ROOT}/bin/architect-brain ui phase-bar <phase>` at each boundary, plus inline `✓`/`→`/`✗` step lines) — it never transcribes art.

A dispatched agent that hits a **BLOCKER** (a precondition it can't satisfy, a write it can't make) returns the **informational error state** — *what failed* and *what's known so far* (the inputs it had, what it managed to produce before stopping) — and stops. It does **NOT** silently fail, swallow the error, or fabricate a workaround. The orchestrator then runs the **self-healing error protocol** in [`references/output-style.md` §4](output-style.md) (informational error → `AskUserQuestion`: write a report and stop, or self-heal and continue after the user approves) — the agent surfaces, the orchestrator decides with the user.

## Phase 1 (Kickoff) — research-scout (domain)

```
[TOPIC]
domain

[CONTEXT]
Project: {{project.name}}
Type: {{project.type}} / {{project.sub_type}}
Stage: {{project.stage}}
Target users: {{project.target_users}}
Scale: {{scale}}
Constraints: {{constraints.*}}

[TASK]
Research the project domain. Find: (1) 3–5 similar existing projects with one-line summaries and links. (2) Common pitfalls for a {{project.sub_type}} {{project.type}}. (3) Regulatory implications for {{project.target_users}}. (4) Market context. (5) What's actually hard about this kind of project. Cite URLs. Market data must be < 12 months old.

[OUTPUT]
Write findings to: docs/research/phase1-domain.md
Return ≤20-line summary to me.
```

## Phase 3 (Architecture) — architecture-specialist

Dispatched in Phase 3 (Architecture), which in v8 runs **before** the tech stack (Phase 4) — the system's shape, boundaries, and data-flow constrain which technologies even make sense. The agent questions architectural STYLE, identifies boundaries, characterises data-flow, names the scaling axis, and recommends WITH rationale (**never microservices-by-default**). It does NOT pick the tech stack.

```
[CONTEXT]
Project: {{project.name}}
Type: {{project.type}} / {{project.sub_type}}
Vision / problem statement: {{vision summary from the vision projection}}
Scale: {{scale}}    Team size: {{team_size}}    Production-bound: {{production_bound}}
Constraints: {{constraints.*}}
Already-recorded feature gates: {{any *.enabled keys from the flat decisions}}
Research depth: {{quick|standard|deep}}

[QUESTIONS TO PRESS] (optional — you always run the full questioning workflow)
{{any specific architectural concerns the orchestrator wants raised}}

[TASK]
Drive the architectural-style decision per your agent body. Cover all 6+ styles
(monolith / modular monolith / SOA / microservices / serverless / event-driven /
hexagonal). Identify the boundaries (count + clarity), the data-flow shape, and the
scaling axis. Recommend ONE style with rationale tied to THIS project's named
scale/team/boundaries/constraints, plus 1–2 viable alternatives and what you
explicitly reject and why. Do NOT pick the tech stack (route any volunteered stack
preference to OUT_OF_SCOPE_FINDINGS:). Ground standard/deep recommendations in
current 2026 sources (llms.txt-first); flag uncertainty, never fabricate.

[OUTPUT]
Write the recommendation file to: docs/research/phase-3-architecture.md
Surface the recommended decision keys under architecture.* (architecture.style,
architecture.boundaries.count, architecture.data_flow, architecture.scaling_axis,
and architecture.hexagonal / architecture.event_driven if applicable) — propose them
for the orchestrator to record; you do NOT hand-edit 99-flat-index.json.
Return the ≤20-line ARCHITECTURE RECOMMENDATION summary to me.
```

After the user confirms, the orchestrator records each value via `architect-brain set-decision <key> <value> --phase architecture`, and files an ADR for the style decision via `architect-brain record-adr` (the architecture-specialist does not file ADRs — its rationale section is the raw material for the ADR body).

## Phase 6 (Doc-gen) — document-author (per catalog doc, parallel batches of 8)

The doc set is the output of `architect-brain catalog list` (declarative selection over `references/catalog.json`, already in topological order). One dispatch per selected doc.

```
[INPUTS]
template_name: {{template_name}}
template_path: ${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/templates/{{template_name}}.md
catalog_path: ${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/catalog.json
state_slice: {{the doc's required_decisions + optional_decisions, as a flat JSON object pulled from docs/_architect_state/99-flat-index.json}}
project_layout: {{the canonical directory/package map from the decisions (project_layout)}}
decisions_dir: docs/_architect_state/decisions/
research_paths: [{{paths to relevant research files}}]
output_path: docs/{{template_name}}.md
cross_references: [{{ONLY the doc filenames the catalog selection actually picked}}]

[TASK]
Read the template. Read the state slice + the canonical layout. Read the research findings.
Confirm every required_decisions key is present (return an informational error rather than
guessing if one is missing). Draft the document, populating sections with project-specific
decisions. Use the canonical project_layout + decisions_dir for any directory/package/ADR
reference — never invent a layout. Validate cross-references (link only to docs the catalog
selection picked) and placeholder resolution. Write to output_path.
```

After each batch the orchestrator records each generated doc via `architect-brain record-doc --phase docs <DOC_NAME> docs/<DOC_NAME>.md` (a `DocGenerated` event with a SHA-256 `content_hash`) and commits.

## Phase 6 (Doc-gen) — claude-md-author

```
[INPUTS]
flat_index_path: docs/_architect_state/99-flat-index.json
template_root_path: ${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/templates/CLAUDE_MD_ROOT.md
template_subfolder_path: ${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/templates/CLAUDE_MD_SUBFOLDER.md
doc_paths: {{the generated doc filenames recorded as DocGenerated events (from docs/_architect_state/docs.json or the catalog selection)}}
project_layout: {{the canonical directory/package map from the flat decisions (project_layout)}}

[TASK]
Read the flat decisions. Author docs/CLAUDE_MD_PLAN.md — the fully-resolved PLAN for the root
CLAUDE.md and any per-folder CLAUDE.md (the sections each must contain, a per-subfolder row for
every dir with materially different conventions, all structural decisions resolved), per the
templates. Do NOT write the final CLAUDE.md files here — Phase 9 (Tooling Execution) materializes
them from this plan and runs claude-md-management:claude-md-improver then. Cross-reference only
docs the catalog selection picked. Return a summary of the plan written + the subfolder set.
```

## Phase 6 (Doc-gen) — claude-tooling-author

```
[INPUTS]
flat_index_path: docs/_architect_state/99-flat-index.json
integration_path: ${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/claude-code-integration.md
project_root: {{user project root path}}
project_layout: {{the canonical directory/package map from the flat decisions (project_layout)}}
stack_summary: {{parsed summary of the stack.* decisions — language/frontend/backend/database/auth/hosting/testing — from the flat decisions}}

[TASK]
Read the integration recipe library + the flat decisions. Author docs/CLAUDE_TOOLING_PLAN.md —
the PLAN for the generated project's .claude/ tree: the settings.json permissions allow/deny
lists, the hooks list, the project-specific commands + agents, and the recommended-plugins
curation (stack-aware, derived from the canonical project_layout; note any of fewer-permission-prompts,
hookify:writing-rules, update-config, claude-code-setup:claude-automation-recommender to apply at
execution). Do NOT write the .claude/* files here — Phase 9 (Tooling Execution) materializes them
from this plan. Return a summary of the plan written.
```

## The Doc-gen + pre-lock audit is NOT a dispatched subagent

In v8 the quality gate is **`architect-brain audit`** — 34 in-process Python checks (4-tier severity: FATAL / BLOCKING / WARNING / INFO), run **directly by the orchestrator** as a Bash call, not via a dispatched `Agent({...})`. There is therefore **no auditor dispatch prompt**: the v7 `quality-gate-auditor` subagent (and its `run_all.sh` over `check_*.{sh,py}`) is removed.

- The **Doc-gen → Iteration** gate is `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --verbose` (all 36 checks; records an `AuditCompleted` event; exits 1 if any failure blocks LOCK).
- The **pre-lock** gate (Phase 8) is the same call — `audit_freshness` (19) reads the recorded `AuditCompleted` event to refuse a stale/post-lock audit.
- Spot-runs at phase boundaries use `--only NN` (e.g. `--only 20` for `no_oob_phase_advance`, `--only 17` for `adr_files_exist`, `--only 24` for `identity_hygiene`, `--only 27` for `required_docs_generated`).
- A BLOCKING finding may be downgraded only with an explicit, recorded `--ack=<reason>`; the three FATAL checks (`state_schema_valid` 29, `resume_test` 31, `catalog_topo_acyclic` 32) can never be acked.

Because the audit runs locally, it never depends on the model backend (no 529-Overloaded surface), and the auditor never crashes on one bad check — each check's `run()` is wrapped, so a single malfunctioning check degrades to a recorded failure rather than aborting the gate. See `SKILL.md` §"Audit robustness" and its `Which check runs at which transition` map (under `## Phase transition contract`).

## Phase 7 (Iteration) — decision-revisor

```
[INPUTS]
decision_key: {{decision_key}}        (a flat dotted key, e.g. stack.backend.language)
old_value: {{old_value}}
new_value: {{new_value}}
reason: {{user-supplied reason}}
flat_index_path: docs/_architect_state/99-flat-index.json
playbook_path: ${CLAUDE_PLUGIN_ROOT}/skills/project-architect/references/revision-playbook.md
decisions_dir: docs/_architect_state/decisions/

[TASK]
Look up decision_key in the playbook's affected-docs map. Surgically rewrite
only the affected sections in each listed doc; append a revision-log entry
per doc. Record the new decision and file the ADR THROUGH architect-brain (never
hand-edit any state file): emit the decision change with
`${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision <decision_key> <new_value> --phase iteration`,
then read the next sequential ADR id from docs/_architect_state/decisions/index.json
(highest existing id + 1) and file the ADR with
`${CLAUDE_PLUGIN_ROOT}/bin/architect-brain record-adr --phase iteration <NNNN> "<title>" Accepted --supersedes <prior_id>`
(record-adr stamps a real timestamp + phase and updates the projections + flat-index
atomically — a manual append is the back-dating hole). Write the ADR markdown file to
docs/_architect_state/decisions/<NNNN>-<slug>.md. Validate cross-references and return a
structured report.
```

## Phase 9 (Tooling Execution) — claude-md-author / claude-tooling-author (plan-driven execution)

In Phase 9 these two agents are re-dispatched against the *plans* generated in Phase 6 (rather than the templates directly).

### Phase 9 — claude-md-author (execute CLAUDE_MD_PLAN)

```
[INPUTS]
plan_path: docs/CLAUDE_MD_PLAN.md
flat_index_path: docs/_architect_state/99-flat-index.json

[TASK]
Read the plan. Resolve every placeholder against the flat decisions.
Write the root CLAUDE.md and any subfolder CLAUDE.md files per the
plan's hierarchy section. Run claude-md-management:claude-md-improver
on each and iterate until pass. Return the list of files written.
```

### Phase 9 — claude-tooling-author (execute CLAUDE_TOOLING_PLAN)

```
[INPUTS]
plan_path: docs/CLAUDE_TOOLING_PLAN.md
flat_index_path: docs/_architect_state/99-flat-index.json

[TASK]
Read the plan. Generate .claude/settings.json, .claude/hooks/*,
.claude/agents/*, .claude/commands/* (including /scaffold, /implement,
/iterate-design router slash commands), and .claude/recommended-plugins.md
exactly as the plan specifies. Return artifact counts.
```

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
