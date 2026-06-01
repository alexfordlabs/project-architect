---
template_name: TENANT_AND_ORGANIZATION_MODEL
generate_when: "decisions.multi_tenancy == true"
required_decisions: [multi_tenancy.isolation_model, multi_tenancy.identification]
optional_decisions: [multi_tenancy.user_invitation, multi_tenancy.role_hierarchy, multi_tenancy.cross_tenant_access]
depends_on: [AUTHENTICATION_SYSTEM, DATABASE_DESIGN]
revision_triggers: [multi_tenancy.isolation_model, multi_tenancy.identification]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Tenant and Organization Model: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Tenant Hierarchy](#tenant-hierarchy)
- [Isolation Model](#isolation-model)
- [Tenant Isolation Patterns (silo / pool / bridge)](#tenant-isolation-patterns-silo--pool--bridge)
- [Identification](#identification)
- [Invitation & Onboarding Flow](#invitation-onboarding-flow)
- [Role Hierarchy & Permissions](#role-hierarchy-permissions)
- [Cross-Tenant Access](#cross-tenant-access)
- [Tenant Lifecycle](#tenant-lifecycle)
- [↻ Revision Log](#revision-log)

## Tenant Hierarchy
The concrete entities (workspace / organization / team / project / user) and the parent-child relationships between them. Name the entity terms the product uses and the cardinality at each level (one workspace -> N teams -> N users). Include a Mermaid diagram if the hierarchy is non-trivial.

## Isolation Model
Chosen isolation strategy (shared schema with `tenant_id` column / schema-per-tenant / database-per-tenant / silo-per-tenant) with rationale and ADR link. Note where isolation is enforced (row-level security policy, query middleware, separate connection pool) and the failure mode if isolation is bypassed.

## Tenant Isolation Patterns (silo / pool / bridge)
Frame the choice above with the [AWS SaaS Lens](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html) tenant-isolation taxonomy — and state it can be applied **per resource tier** (DB, compute, storage, cache), not just once globally:

| Pattern | What it means | Isolation strength | Cost / ops | Noisy-neighbour | Typical fit |
|---|---|---|---|---|---|
| **Silo** | Dedicated stack/resources per tenant (DB-per-tenant, sometimes account/VPC-per-tenant) | Strongest — physical separation | Highest per-tenant cost; provisioning + N-fold ops/migrations | None | Enterprise/regulated tenants; compliance or blast-radius isolation; few large tenants |
| **Pool** | All tenants share resources, separated logically by `tenant_id` (+ row-level security / query middleware) | Weakest — a logic bug can cross tenants | Lowest cost; one stack to operate + migrate | Real — needs throttling/quotas | Self-serve / high-volume small tenants; cost-sensitive scale |
| **Bridge** | Mixed — pooled for most, siloed for some (or pooled compute + siloed DB) | Per-tier | Middle | Partial | Most growth-stage SaaS: pool the long tail, silo the whale/regulated tenants |

State, for THIS product: the pattern per tier ({{db_isolation}} / {{compute_isolation}} / {{storage_isolation}}); the **isolation enforcement mechanism** (Postgres RLS policies, a tenant-scoped query layer, IAM/STS session scoping, per-tenant KMS keys); how a tenant could be **promoted silo→from→pool** as it grows (the bridge migration path); and the **isolation test** that proves cross-tenant access is denied (a negative test in TESTING_STRATEGY.md). The weakest tier sets the product's effective isolation guarantee — name it.

## Identification
How an incoming request is associated with a tenant (subdomain / URL path segment / header / JWT claim / API-key prefix). Cover precedence rules, the canonical identifier shape, what the router/middleware does on missing or malformed identifiers, and the fallback for unauthenticated routes.

## Invitation & Onboarding Flow
End-to-end flow for adding a user to a tenant: who can invite, invitation token shape and lifetime, acceptance path (existing-user vs new-user), email channel, and the data captured during acceptance. Reference AUTHENTICATION_SYSTEM.md for the identity bits.

## Role Hierarchy & Permissions
The role names (owner / admin / member / viewer / etc.) and the permission set each role grants. Note whether permissions are role-based, attribute-based, or hybrid; whether custom roles are allowed; and how role assignment is audited. Link to AUTHENTICATION_SYSTEM.md.

## Cross-Tenant Access
How admin/support users access data across tenants (impersonation flow / sudo mode / read-only support console), the audit trail required for each access, and the policy boundaries (PII access, write access). Note service-to-service cross-tenant calls and how they are authorized.

## Tenant Lifecycle
Provisioning at create time (resources allocated, default data, plan defaults), suspension semantics (read-only / billing-locked / hidden), archive vs delete behavior, the retention window before hard delete, and the data-export hook offered before delete. Link to BILLING_AND_PAYMENTS.md if plans gate features here.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
