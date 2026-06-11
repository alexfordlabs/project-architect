<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Decision-Key Namespace (canonical)

The single canonical vocabulary for `99-flat-index.json` decision keys. Every
producer (`set-decision`, Golden Paths) and every consumer (`catalog.json`
conditions, `configs.py`, `diagrams.py`, the auditor) MUST use these dotted
keys verbatim — a golden path that sets `stack.database.engine` only drives
downstream doc-selection / config-gen if the consumers read the SAME key.

> **Why this file exists:** Wave 4's e2e smoke caught a namespace drift — the
> waves had each chosen keys independently (golden-paths `stack.*` vs catalog
> `frontend.framework`/`database.engine`). This file is the source of truth that
> prevents recurrence. Golden Paths (`references/golden-paths.json`) is the
> reference implementation of the namespace.

## `stack.*` — technology choices (the bulk)

`stack.<area>.<attr>`. A choice is "made" when the key is present and non-null.

| Key | Example value |
|---|---|
| `stack.frontend.framework` | `next.js`, `react`, `svelte` |
| `stack.frontend.version` | `15` |
| `stack.frontend.styling` | `tailwind` |
| `stack.frontend.language` | `typescript` |
| `stack.backend.language` | `typescript`, `python`, `rust`, `go` |
| `stack.backend.framework` | `fastapi`, `chi` |
| `stack.backend.runtime` | `node`, `bun` |
| `stack.database.engine` | `postgresql`, `sqlite`, `mongodb` |
| `stack.database.orm` | `drizzle`, `prisma`, `sqlc` |
| `stack.cache.engine` | `redis`, `valkey` |
| `stack.hosting.provider` | `vercel`, `fly`, `k8s` |
| `stack.auth.provider` | `next-auth`, `clerk` |
| `stack.payments.provider` | `stripe` |
| `stack.api.protocol` | `rest`, `graphql`, `grpc` |
| `stack.observability` | `opentelemetry` |
| `stack.containerization` | `docker` |
| `stack.mobile.framework` / `stack.mobile.*` | `react-native` … |
| `stack.license` | `MIT` |
| `stack.versions.<package>` | `^16.2.6` (next), `^19.2.0` (react), `24` (node), `3.13` (python), `17` (postgres), `7` (redis), `2.1.0` (biome) |

**Note (value vocabulary):** the engine value is the technology's own canonical
name — `postgresql`, not `postgres`. Consumers that branch on the value accept
the canonical spelling (e.g. `gen_docker_compose` treats `postgres`/`postgresql`
alike).

**`stack.versions.*` — resolved version pins (v8.0.1).** After research-scout
resolves the newest-stable version for each dependency (§ 1a of its mission),
the orchestrator records each as `stack.versions.<package>` (e.g.
`stack.versions.next = "^16.2.6"`). The config generators (`gen_package_json`,
`gen_dockerfile`, `gen_pyproject`, `gen_docker_compose`, `gen_biome_json`) read
these via `configs._pin` and emit them into the user's `package.json` /
`Dockerfile` / `pyproject.toml` / `docker-compose.yml` / `biome.json`; absent a
recorded pin they fall back to a conservative plugin floor that goes stale on the
plugin's release cadence. `<package>` is the dependency's own token (`next`,
`react` — drives `react-dom` too —, `node`, `python` — drives `requires-python` +
ruff `target-version` —, plus the Docker-image / tool tokens `postgres`, `redis`,
`biome`). This supersedes the older single-value
`stack.frontend.version` hint, which is framework-major-only and unread by the
generators.

## Other top-level namespaces

| Namespace | Keys | Set by |
|---|---|---|
| `project.*` | `project.type`, `project.sub_type`, `project.name` | kickoff |
| `architecture.*` | `architecture.style` (`monolith`/`modular_monolith`/`soa`/`microservices`/`serverless`/`event_driven`), `architecture.boundaries.count`, `architecture.data_flow` (`request_response`/`pipeline`/`streaming`/`mixed`), `architecture.scaling_axis`, `architecture.hexagonal`, `architecture.event_driven` | architecture-specialist (Phase 2) |
| `ai.*` | `ai.enabled`, `ai.agent`, `ai.provider`, `ai.model`, `ai.framework`, `ai.orchestration`, `ai.rag.*`, `ai.long_running`, `ai.persistent_memory` | AI questioning |
| `agent.*` | `agent.autonomy`, `agent.execution`, `agent.memory`, `agent.hitl`, `agent.tools.sandbox` | agentic_system type |
| `api.*` / `webhooks.*` | `api.enabled` (gate, pairs with `stack.api.protocol`), `api.public`, `api.idempotency_required`, `webhooks.outbound` | API questioning |
| type-specific | `cli.*`, `mcp.*`, `pl.*`, `plugin.*` | the matching project type |
| `constraints.*` | `constraints.regulated`, `constraints.supply_chain_security`, `constraints.gdpr`, `constraints.ccpa`, `constraints.hipaa` | constraints questioning |
| `deployment.*` | `deployment.orchestrator` (`kubernetes`/…), `deployment.containers`, `deployment.style` (`serverless`/…), `deployment.gitops`, `deployment.controller` (`argocd`/`flux`), `deployment.edge` | deployment/tooling questioning |
| `scm.*` | `scm.host` (`github`/`gitlab`/…) | kickoff / repo-init |
| `data.*` | `data.contracts` (pairs with the `data_pipeline.enabled` gate) | data questioning |
| feature flags | `<feature>.enabled` — `analytics`, `search`, `realtime`, `notifications`, `background_jobs`, `file_handling`, `monetization`, `ab_testing`, `feature_flags`, `data_pipeline`, `caching` | feature questioning |
| scale / team | `scale` (`hobby`/`growth`/`enterprise`), `team_size` (`solo`/`small_team`/`medium_team`/`large_team`), `production_bound`, `personal_data` | scope questioning |
| OSS / DDD | `open_source`, `community_size` (`small`/`medium`/`large`), `project.governance` (`foundation`/…), `project.ddd` | scope / governance questioning |
| platforms / i18n | `platforms.*`, `i18n.languages`, `integrations` | scope questioning |

## Template-input / doc-concern keyspace (advisory — template frontmatter)

These namespaces are referenced by the v8 templates' frontmatter `required_decisions` /
`optional_decisions` / `revision_triggers` (the decisions a generated doc draws on). They are
**advisory doc-input hints**, not catalog selectors — the load-bearing `catalog.json` conditions
use only the canonical keys above. Producer-side wiring (the questioning phase that SETS each)
lands incrementally; some are forward-looking. Listed here so the whole keyspace is canonical
(a key under a registered `<ns>.*` namespace is canonical by namespace).

| Namespace | Representative keys | Owning concern |
|---|---|---|
| `workflow.*` | `workflow.branching`, `workflow.pr_required`, `workflow.merge_strategy`, `workflow.commit_convention`, `workflow.feature_flags`, `workflow.release_branching`, `workflow.governance_model`, `workflow.maintainer_roles`, `workflow.contribution_agreement`, `workflow.decision_process`, `workflow.code_of_conduct`, `workflow.fiscal_host`, `workflow.open_source` | dev process / OSS governance |
| `team.*` | `team.structure`, `team.distribution`, `team.ci_cd`, `team.code_review` (distinct from the `team_size` scale key) | team questioning |
| `ci.*` | `ci.provider` | CI/CD questioning |
| `deployment.*` | (see above) + `deployment.cadence`, `deployment.trigger`, `deployment.target` | deployment questioning |
| `observability.*` | `observability.stack`, `observability.platform`, `observability.metrics`, `observability.tracing` | observability questioning |
| `ops.*` | `ops.runbooks`, `ops.observability`, `ops.slo_defined`, `ops.incident_tooling` | SRE/ops questioning |
| `analytics.*` | `analytics.enabled` (the feature gate) + `analytics.provider`, `analytics.id_strategy`, `analytics.casing_convention`, `analytics.consent`, `analytics.governance_owner`, `analytics.enforcement` | analytics questioning |
| `feature_flags.*` | `feature_flags.enabled` (gate) + `feature_flags.provider`, `feature_flags.sdk`, `feature_flags.flag_types`, `feature_flags.context_paradigm`, `feature_flags.experimentation`, `feature_flags.governance`, `feature_flags.local_dev` | feature-flag questioning |
| `docs.*` | `docs.surface`, `docs.tooling`, `docs.host`, `docs.versioned` | documentation questioning |
| `messaging.*` | `messaging.broker`, `messaging.async` | async/event questioning |
| `testing.*` | `testing.framework` | testing questioning |
| `infra.*` | `infra.cdn`, `infra.queue` | infra questioning |
| `quality.*` / `reliability.*` / `security.*` | `quality.priorities`, `reliability.sla`, `security.secrets_management` | quality/reliability/security questioning |
| `api.*` (doc-input) | `api.contract`, `api.style` (alongside the canonical `api.enabled`/`api.public`/`api.idempotency_required`/`stack.api.protocol`) | API questioning |
| `architecture.*` (DDD) | `architecture.ddd`, `architecture.cqrs`, `architecture.event_sourcing`, `architecture.messaging`, `architecture.bounded_contexts` (alongside the canonical `architecture.style`/`architecture.boundaries.count`/…) | DDD / architecture questioning |
| `data.*` | `data.store`, `data.contracts` | data questioning |

> **Drift normalized 2026-05-29:** the templates' earlier `deploy.cadence`/`deploy.trigger` were
> renamed to `deployment.*`. When wiring producer-side questioning, prefer one key per concept
> (e.g. converge `messaging.async` / `architecture.messaging` on a single canonical choice).

## Enabled-gate vs stack-choice (compound conditions)

Some concepts have BOTH a boolean gate (`<x>.enabled`, set by questioning) AND a
concrete stack choice (`stack.<x>.<attr>`, set by a Golden Path). Catalog
conditions for these accept EITHER signal:

- auth → `(auth.enabled == true OR stack.auth.provider != null)`
- caching → `(caching.enabled == true OR stack.cache.engine != null)`
- api → `(api.enabled == true OR stack.api.protocol != null)`

## Rule

When adding a decision key anywhere (a `set-decision` call, a Golden Path entry,
a catalog condition, a config/diagram generator, an auditor check): use a key
from this file. If a new concept is needed, add it HERE first, then everywhere
that reads or writes it.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
