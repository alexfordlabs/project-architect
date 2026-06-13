---
template_name: TECH_STACK
generate_when: "decisions.stack.backend.language != null OR decisions.stack.frontend.framework != null"
required_decisions: [stack.frontend.framework, stack.backend.language]
optional_decisions: [stack.frontend.styling, stack.frontend.language, stack.backend.framework, stack.backend.runtime, stack.database.engine, stack.database.orm, stack.auth.provider, stack.hosting.provider, stack.api.protocol, stack.package_manager, stack.monorepo, stack.versions.next, stack.versions.react, stack.versions.node, stack.versions.python, stack.versions.typescript, stack.versions.biome, stack.versions.postgres, stack.versions.redis]
depends_on: [PROJECT_OVERVIEW]
revision_triggers: [stack.frontend.framework, stack.backend.language, stack.database.engine, stack.versions.next, stack.versions.react, stack.versions.node, stack.versions.python, stack.versions.typescript, stack.versions.biome, stack.versions.postgres, stack.versions.redis]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Technology Stack: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

The chosen technologies and their resolved version pins. The framework/stack
_choices_ live in the per-decision ADRs; this page records both the choices and
the concrete _versions_ they currently resolve to.

## Table of contents
- [Stack at a glance](#stack-at-a-glance)
- [Version pins](#version-pins)
- [Rationale](#rationale)

## Stack at a glance

| Layer | Choice |
| --- | --- |
| Frontend framework | {{stack.frontend.framework}} |
| Frontend language | {{stack.frontend.language}} |
| Frontend styling | {{stack.frontend.styling}} |
| Backend language | {{stack.backend.language}} |
| Backend framework | {{stack.backend.framework}} |
| Backend runtime | {{stack.backend.runtime}} |
| Database engine | {{stack.database.engine}} |
| ORM | {{stack.database.orm}} |
| Auth provider | {{stack.auth.provider}} |
| Hosting | {{stack.hosting.provider}} |
| API protocol | {{stack.api.protocol}} |
| Package manager | {{stack.package_manager}} |

## Version pins

The concrete, **current-stable** versions resolved during the Tech Stack phase
(`research-scout` § 1a) and recorded under the `stack.versions.*` decision
namespace (see [`references/decision-keys.md`](../decision-keys.md)). These are
the source ALL the deterministic config generators (`gen_package_json`,
`gen_dockerfile`, `gen_pyproject`, `gen_docker_compose`, `gen_biome_json`) read
via `configs._pin`, so the scaffold ships **these exact versions** rather than
a stale plugin-baked floor. A pin absent here means the generator fell back to
its floor — audit check 36 (`version_pins_recorded`) flags that; resolve and
re-record to refresh. Include only the rows the stack makes applicable.

| Dependency | Pin | Notes |
| --- | --- | --- |
| `next` | {{stack.versions.next}} | |
| `react` / `react-dom` | {{stack.versions.react}} | move in lockstep; drives `@types/react`* too |
| `node` (runtime + Docker base) | {{stack.versions.node}} | drives `@types/node` |
| `python` (runtime + Docker base) | {{stack.versions.python}} | drives `requires-python` + ruff target |
| `typescript` (toolchain devDependency) | {{stack.versions.typescript}} | |
| `biome` (lint/format; `$schema` + config shape) | {{stack.versions.biome}} | |
| `postgres` (compose image tag) | {{stack.versions.postgres}} | |
| `redis` (compose image tag) | {{stack.versions.redis}} | |

> **Refresh:** re-run the Stack-phase version resolution (or `/iterate-design`)
> to update these pins; the change flows into the generated manifests on the
> next `architect-brain generate-configs`. The `dependency_freshness` audit
> check (23, WARNING) flags pre-release pins.

## Rationale

{{stack_rationale}}

See the per-decision ADRs for why each technology was chosen over its
alternatives: {{adr_links}}.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
