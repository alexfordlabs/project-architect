<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Revision Playbook

The `decision-revisor` agent reads this file to learn which docs are affected when a specific decision changes. The orchestrator passes the revisor a `decision_key`; the revisor looks it up here and rewrites every doc listed.

## Table of Contents
- [How the revisor uses this](#how-the-revisor-uses-this)
- [Decision → affected docs map](#decision--affected-docs-map)
- [ADR conventions](#adr-conventions)
- [Revision Log conventions](#revision-log-conventions)
- [Cross-reference preservation rules](#cross-reference-preservation-rules)

---

## How the revisor uses this

```
Input: { decision_key, old_value, new_value, reason }

Steps:
  1. Look up decision_key in the map below.
  2. For each affected doc in the list:
     a. Read the current doc.
     b. Identify sections that reference the old decision (search for old_value
        plus any common synonyms).
     c. Rewrite only those sections; preserve everything else.
     d. Append a Revision Log entry: "{date} — {decision_key} changed
        {old_value} → {new_value} (ADR {new_adr_id})"
  3. File a new ADR with full diff, rationale, alternatives reconsidered,
     consequences, rollback plan. Set supersedes: <prior_adr_id> if applicable.
  4. Update state.json: set decisions[decision_key] = new_value;
     append to adrs_filed.
  5. Run inline validation:
     - All cross-references in modified docs still resolve to files that exist.
     - No remaining mentions of old_value in unchanged sections.
     - ADR frontmatter validates.
  6. Return { files_changed: [...], adr_id: NNNN }
```

If validation in step 5 fails, surface to orchestrator, which surfaces to user. Do not commit until the user confirms or revises further.

---

## Decision → affected docs map

A `*` annotation means "regenerate only if the doc contains a section referencing this decision" (conditional propagation).

### Project meta

| decision_key | affected docs |
|---|---|
| project.name | PROJECT_OVERVIEW, CLAUDE_MD_ROOT, all per-folder CLAUDE.md, README* |
| project.type | PROJECT_OVERVIEW, CLAUDE_MD_ROOT, *(type change may invalidate other docs — flag user)* |
| project.sub_type | PROJECT_OVERVIEW, type-anchored doc *(formerly `project.subtype`)* |
| project.scale | PROJECT_OVERVIEW, COST_MODEL, MONITORING_AND_OBSERVABILITY, SLO_AND_ERROR_BUDGETS, BACKUP_AND_DR |
| project.constraints | SECURITY_AND_COMPLIANCE, THREAT_MODEL, DEPLOYMENT*, ALL docs* (revisor flags scope) |
| project.target_users | PROJECT_OVERVIEW, PROJECT_REQUIREMENTS, ANALYTICS_AND_TELEMETRY*, ACCESSIBILITY* |

### Scope / scale

These are the canonical bare top-level scope keys (per `decision-keys.md`). `project.scale` above is the legacy spelling; producers record the bare `scale`.

| decision_key | affected docs |
|---|---|
| scale | PROJECT_OVERVIEW, COST_MODEL, MONITORING_AND_OBSERVABILITY, SLO_AND_ERROR_BUDGETS, BACKUP_AND_DR |
| team_size | PROJECT_OVERVIEW, COST_MODEL, DEVELOPMENT_WORKFLOW* |
| production_bound | PROJECT_OVERVIEW, COST_MODEL, DEPLOYMENT*, MONITORING_AND_OBSERVABILITY* |
| platforms.ios | PROJECT_OVERVIEW, PLATFORMS, MOBILE_SPECIFIC* |
| platforms.android | PROJECT_OVERVIEW, PLATFORMS, MOBILE_SPECIFIC* |
| platforms.web | PROJECT_OVERVIEW, PLATFORMS, UI_UX_DESIGN* |

### Architecture

The `architecture.*` keys are set by the architecture-specialist in Phase 2 (per `decision-keys.md`).

| decision_key | affected docs |
|---|---|
| architecture.style | ARCHITECTURE_DIAGRAMS, PROJECT_OVERVIEW, SCAFFOLD_PLAN, TECH_STACK* |
| architecture.data_flow | ARCHITECTURE_DIAGRAMS, PROJECT_OVERVIEW* |
| architecture.scaling_axis | ARCHITECTURE_DIAGRAMS, PROJECT_OVERVIEW, COST_MODEL* |
| architecture.hexagonal | ARCHITECTURE_DIAGRAMS, SCAFFOLD_PLAN |
| architecture.boundaries.count | ARCHITECTURE_DIAGRAMS, SCAFFOLD_PLAN, PROJECT_OVERVIEW* |

### Language / runtime

| decision_key | affected docs |
|---|---|
| stack.backend.language | CLAUDE_MD_ROOT, all per-folder CLAUDE.md in that language, TESTING_STRATEGY, CI_CD |
| stack.frontend.language | CLAUDE_MD_ROOT, UI_UX_DESIGN, TESTING_STRATEGY, CI_CD |
| stack.backend.runtime | CLAUDE_MD_ROOT, DEPLOYMENT, CI_CD |
| stack.versions.* (any pin) | TECH_STACK, the generated config the token feeds (package.json / Dockerfile / pyproject.toml / docker-compose.yml / biome.json) |
| stack.package_manager | CLAUDE_MD_ROOT, CI_CD |
| stack.monorepo | CLAUDE_MD_ROOT, CI_CD, per-folder CLAUDE.md |

### Frontend

| decision_key | affected docs |
|---|---|
| stack.frontend.framework | UI_UX_DESIGN, DEPLOYMENT, CI_CD, CLAUDE_MD_ROOT, apps/web/CLAUDE.md* |
| stack.frontend.styling | UI_UX_DESIGN, BRAND_AND_DESIGN_TOKENS* |
| stack.frontend.component_library | UI_UX_DESIGN |
| stack.frontend.state | UI_UX_DESIGN |
| stack.frontend.data_fetching | UI_UX_DESIGN, API_GATEWAY* |
| stack.frontend.rendering | UI_UX_DESIGN, DEPLOYMENT, PERFORMANCE_BUDGETS |
| stack.frontend.routing | UI_UX_DESIGN |

### Backend / API

| decision_key | affected docs |
|---|---|
| stack.backend.framework | API_GATEWAY, DEPLOYMENT, CI_CD, CLAUDE_MD_ROOT |
| stack.api.protocol | API_GATEWAY |
| stack.backend.versioning | API_GATEWAY, RELEASE_PROCESS* |
| stack.backend.rate_limiting | API_GATEWAY, SECURITY_AND_COMPLIANCE |
| stack.backend.realtime_protocol | API_GATEWAY, REAL_TIME |

### Database

| decision_key | affected docs |
|---|---|
| stack.database.engine | DATABASE_DESIGN, API_GATEWAY, BACKUP_AND_DR, COST_MODEL, CLAUDE_MD_ROOT |
| stack.cache.engine | DATABASE_DESIGN, PERFORMANCE_BUDGETS, COST_MODEL, docker-compose.yml |
| stack.database.host | DATABASE_DESIGN, DEPLOYMENT, COST_MODEL, BACKUP_AND_DR |
| stack.database.orm | DATABASE_DESIGN, API_GATEWAY, CLAUDE_MD_ROOT |
| stack.database.migration_strategy | DATABASE_DESIGN, CI_CD, RUNBOOK |
| stack.database.normalization | DATABASE_DESIGN |
| stack.database.multi_tenancy_isolation | DATABASE_DESIGN, TENANT_AND_ORGANIZATION_MODEL, SECURITY_AND_COMPLIANCE |

### Auth

| decision_key | affected docs |
|---|---|
| stack.auth.provider | AUTHENTICATION_SYSTEM, SECURITY_AND_COMPLIANCE, API_GATEWAY*, CLAUDE_MD_ROOT |
| stack.auth.methods | AUTHENTICATION_SYSTEM, UI_UX_DESIGN* |
| stack.auth.session_strategy | AUTHENTICATION_SYSTEM, SECURITY_AND_COMPLIANCE |
| stack.auth.oauth_providers | AUTHENTICATION_SYSTEM |
| stack.auth.multi_tenancy | AUTHENTICATION_SYSTEM, TENANT_AND_ORGANIZATION_MODEL, DATABASE_DESIGN |
| stack.auth.mfa | AUTHENTICATION_SYSTEM, SECURITY_AND_COMPLIANCE |

### Hosting / deployment

| decision_key | affected docs |
|---|---|
| stack.hosting.provider | DEPLOYMENT, CI_CD, COST_MODEL, MONITORING_AND_OBSERVABILITY *(canonical; supersedes the legacy `stack.hosting.frontend`/`stack.hosting.backend` split)* |
| stack.hosting.cdn | DEPLOYMENT, PERFORMANCE_BUDGETS, EDGE_COMPUTE_DESIGN* |
| deployment.style | DEPLOYMENT, CI_CD*, COST_MODEL* |
| deployment.environments | DEPLOYMENT, CI_CD |
| deployment.iac | DEPLOYMENT, CI_CD |

### Security

| decision_key | affected docs |
|---|---|
| security.encryption_at_rest | SECURITY_AND_COMPLIANCE, DATABASE_DESIGN, BACKUP_AND_DR |
| security.encryption_in_transit | SECURITY_AND_COMPLIANCE, API_GATEWAY |
| security.secrets_management | SECURITY_AND_COMPLIANCE, DEPLOYMENT, CI_CD *(formerly `security.secret_management`)* |
| security.input_validation | SECURITY_AND_COMPLIANCE, API_GATEWAY |
| security.cors | API_GATEWAY, SECURITY_AND_COMPLIANCE |
| security.csp | UI_UX_DESIGN, SECURITY_AND_COMPLIANCE |
| security.dep_scanning | CI_CD, SECURITY_AND_COMPLIANCE |

### Testing

| decision_key | affected docs |
|---|---|
| testing.framework | TESTING_STRATEGY, CI_CD, CLAUDE_MD_ROOT *(canonical; supersedes the legacy `testing.unit_framework`/`testing.e2e_framework` split)* |
| testing.strategy | TESTING_STRATEGY, CI_CD |

### Observability / monitoring

Canonical `observability.*` keys (per `decision-keys.md`). These supersede the legacy `monitoring.error_tracking`/`monitoring.apm`/`monitoring.logging`/`monitoring.uptime`/`monitoring.analytics` spellings.

| decision_key | affected docs |
|---|---|
| observability.platform | MONITORING_AND_OBSERVABILITY, INCIDENT_RESPONSE *(error/crash-tracking + uptime vendor — formerly `monitoring.error_tracking`/`monitoring.uptime`)* |
| observability.stack | MONITORING_AND_OBSERVABILITY, DEPLOYMENT *(logging/telemetry stack — formerly `monitoring.logging`)* |
| observability.metrics | MONITORING_AND_OBSERVABILITY, PERFORMANCE_BUDGETS *(APM/metrics — formerly `monitoring.apm`)* |
| observability.tracing | MONITORING_AND_OBSERVABILITY, PERFORMANCE_BUDGETS |

### Payments / billing

| decision_key | affected docs |
|---|---|
| stack.payments.provider | BILLING_AND_PAYMENTS, COST_MODEL, SECURITY_AND_COMPLIANCE* |
| stack.payments.model | BILLING_AND_PAYMENTS |

### Notifications

| decision_key | affected docs |
|---|---|
| notifications.email_provider | EMAIL_AND_NOTIFICATIONS, COST_MODEL |
| notifications.push_provider | EMAIL_AND_NOTIFICATIONS, MOBILE_SPECIFIC* |
| notifications.multi_channel_provider | EMAIL_AND_NOTIFICATIONS |

### File storage

| decision_key | affected docs |
|---|---|
| file_storage.provider | FILE_STORAGE, COST_MODEL, SECURITY_AND_COMPLIANCE* |
| file_storage.cdn | FILE_STORAGE, PERFORMANCE_BUDGETS, EDGE_COMPUTE_DESIGN* |

### AI / ML

| decision_key | affected docs |
|---|---|
| ai.provider | AI_AND_ML, COST_MODEL, SECURITY_AND_COMPLIANCE* |
| ai.framework | AI_AND_ML |
| ai.rag.vector_store | AI_AND_ML, DATABASE_DESIGN |
| ai.rag.embeddings | AI_AND_ML, COST_MODEL |

### Real-time

| decision_key | affected docs |
|---|---|
| realtime.protocol | REAL_TIME, API_GATEWAY |
| realtime.broker | REAL_TIME, COST_MODEL |

### Game

For `project.type == game`. The producer records `game.*` (and `stack.game.*` for engine/language) per `decision-keys.md`; the canonical anchor doc is `GAME_SPECIFIC` with cross-doc propagation as noted.

| decision_key | affected docs |
|---|---|
| stack.game.engine | GAME_SPECIFIC, TECH_STACK, ARCHITECTURE_DIAGRAMS, SCAFFOLD_PLAN |
| game.engine | GAME_SPECIFIC, TECH_STACK, ARCHITECTURE_DIAGRAMS, SCAFFOLD_PLAN *(alias of `stack.game.engine`)* |
| stack.game.engine_preference | GAME_SPECIFIC, TECH_STACK *(a SOFT, non-binding preference note — revising it touches only the engine-preference discussion, NOT the hard-choice doc set of `stack.game.engine`)* |
| stack.game.language | GAME_SPECIFIC, TECH_STACK, CLAUDE_MD_ROOT |
| game.genre | GAME_SPECIFIC, PROJECT_OVERVIEW* |
| game.visual_dimension | GAME_SPECIFIC, TECH_STACK, ARCHITECTURE_DIAGRAMS* |
| game.monetization_model | GAME_SPECIFIC, BILLING_AND_PAYMENTS, COST_MODEL* |
| game.multiplayer | GAME_SPECIFIC, ARCHITECTURE_DIAGRAMS, REAL_TIME* |
| game.save_model | GAME_SPECIFIC, AUTHENTICATION_SYSTEM, DATABASE_DESIGN |
| game.player_identity | GAME_SPECIFIC, AUTHENTICATION_SYSTEM, DATABASE_DESIGN |
| game.platform_services_impl | GAME_SPECIFIC, AUTHENTICATION_SYSTEM, DATABASE_DESIGN |
| game.web_v1_mode | GAME_SPECIFIC, DEPLOYMENT*, UI_UX_DESIGN* |
| game.lookdev_gate | GAME_SPECIFIC, SCAFFOLD_PLAN |
| game.d18_deviation | GAME_SPECIFIC, SCAFFOLD_PLAN |
| game.content_lfs | GAME_SPECIFIC, SCAFFOLD_PLAN, GIT_BRANCHING* |

### Data pipeline

| decision_key | affected docs |
|---|---|
| data_pipeline.orchestrator | DATA_PIPELINE, COST_MODEL |
| data_pipeline.warehouse | DATA_PIPELINE, COST_MODEL |

### CI / CD

| decision_key | affected docs |
|---|---|
| ci.provider | CI_CD, DEPLOYMENT |
| cicd.branch_strategy | CI_CD, CONTRIBUTING* |

### Misc

| decision_key | affected docs |
|---|---|
| i18n.languages | INTERNATIONALIZATION, UI_UX_DESIGN |
| feature_flags.provider | EXPERIMENTS, ANALYTICS_AND_TELEMETRY |
| ab_testing.provider | EXPERIMENTS, ANALYTICS_AND_TELEMETRY |
| analytics.provider | ANALYTICS_AND_TELEMETRY, MONITORING_AND_OBSERVABILITY *(formerly `analytics.product`)* |
| open_source | CONTRIBUTING, README, LICENSE |

### Feature gates

A `<feature>.enabled` toggle flips whether a feature doc generates at all; revising it propagates to the matching feature doc(s) (per the catalog's `generate_when` conditions in `decision-keys.md`).

| decision_key | affected docs |
|---|---|
| analytics.enabled | ANALYTICS_AND_TELEMETRY, EVENT_TRACKING_PLAN* |
| auth.enabled | AUTHENTICATION_SYSTEM, SECURITY_AND_COMPLIANCE* |
| monetization.enabled | BILLING_AND_PAYMENTS, COST_MODEL* |
| notifications.enabled | EMAIL_AND_NOTIFICATIONS |
| realtime.enabled | REAL_TIME, API_GATEWAY* |

---

## Affected code areas (for `/upgrade-project`)

The map above lists which **docs** a decision change affects. The cross-version upgrade flow (`references/upgrade-flow.md`, Step 6) additionally needs to know which **code** a changed decision may have invalidated, so it can FLAG it (the flow never rewrites code).

This is a **coarse** mapping: a changed `decision_key` → the top-level component(s) in `state.project_layout` whose code embodies that decision. It is intentionally NOT a fine file-glob map (spec §10 ratified coarse for v5).

| decision_key | coarse affected code area (resolve via state.project_layout) |
|---|---|
| stack.backend.language | ALL code components in `project_layout` (a language change invalidates the whole build) |
| stack.database.engine | the persistence/data component(s) in `project_layout` (e.g. the `core`/`db`/`api` entries) |
| stack.auth.provider | the auth/gateway component(s) in `project_layout` |
| stack.backend.framework (web/server) | the web/server component(s) in `project_layout` |

**How the flow uses it:** for each stale-and-revised decision in Step 6, look the key up here, resolve the named component(s) to their paths via `state.project_layout`, and emit an `affected-code-areas` list in the upgrade summary: *"The change to `database.engine` may affect code under `<project_layout.core>`; re-run `/implement` or `/scaffold` there."* If a key is absent from this table, flag the whole project conservatively. Keys not in `project_layout` resolve to "(layout unknown — review manually)".

---

## ADR conventions

- File path: `docs/decisions/NNNN-<kebab-slug>.md`
- NNNN is sequential, zero-padded to 4 digits, never reused
- Slug is kebab-case of title, max 60 chars
- Frontmatter required: `adr_id`, `title`, `date`, `status`, `supersedes`, `superseded_by`, `affected_docs`, `decision_keys`, `research_refs`
- Status values: `proposed | accepted | superseded | deprecated`
- When ADR Y supersedes ADR X: set Y.supersedes = X.adr_id AND update X.superseded_by = Y.adr_id (revisor MUST update the old ADR's frontmatter, not just write the new one)

## Revision Log conventions

Every generated doc ends with `## Revision Log`. Initial value is `(none yet)`. Each revision appends one line:

```
- 2026-05-12 — database.engine changed PostgreSQL → SQLite+Turso (ADR 0007)
```

Ordered newest-to-oldest at the top of the list (most recent change first).

## Cross-reference preservation rules

When the revisor rewrites a section:
1. **Preserve all `[text](path)` links to other docs** unless the linked doc is being deleted in the same revision.
2. **Preserve ADR references** (`see ADR 0007`); add new ADR reference for the current change.
3. **Preserve diagrams** unless the diagram explicitly depicts the changing decision.
4. **Preserve `## Revision Log` ordering** (append, don't reorder).
5. If a section heading changes, **grep the rest of the doc-set** for back-references and update them in the same revision.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
