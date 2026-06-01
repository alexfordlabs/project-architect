---
template_name: DATABASE_DESIGN
generate_when: "decisions.database.engine != null"
required_decisions: [database.engine, database.host, database.orm]
optional_decisions: [database.normalization, database.migration_strategy, database.soft_delete, database.audit_log, database.multi_tenancy_isolation, database.indexing_strategy, database.backup]
depends_on: []
revision_triggers: [database.engine, database.host, database.orm, database.migration_strategy, database.multi_tenancy_isolation]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Database Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🗄️ Database Choice](#database-choice)
- [ORM/Query Layer](#ormquery-layer)
- [🎯 Schema Overview](#schema-overview)
- [Relationships](#relationships)
- [🗄️ Indexing Strategy](#indexing-strategy)
- [🗄️ Migration Strategy](#migration-strategy)
- [Data Policies](#data-policies)
- [Multi-Tenancy Data Model](#multi-tenancy-data-model)
- [🗄️ Seeding & Test Data](#seeding-test-data)
- [↻ Revision Log](#revision-log)

## 🗄️ Database Choice
Engine (e.g. PostgreSQL 17, MySQL, SQLite, MongoDB, DynamoDB), host/provider (Supabase, Neon, RDS, self-hosted), and one-paragraph rationale citing the ADR.

## ORM/Query Layer
ORM or query builder chosen (Drizzle, Prisma, SQLAlchemy, ActiveRecord, raw SQL), connection-pooling strategy, and any read-replica routing rules.

## 🎯 Schema Overview
Embedded ERD (Mermaid) plus a "Core Entities" subsection with one table per entity. Each entity table lists: column | type | nullable | description.

## Relationships
Narrative + diagram of foreign-key relationships, cascade rules, and any join-table conventions.

## 🗄️ Indexing Strategy
List of indexes (composite + partial + unique), the queries they support, and any covering-index decisions.

## 🗄️ Migration Strategy
Tool (Drizzle Kit / Prisma Migrate / Flyway / Atlas), naming convention, forward-only vs reversible policy, and how migrations run in CI/CD vs production.

## Data Policies
Soft-delete convention, audit-log table layout, data retention rules (per entity), backup cadence and storage location.

## Multi-Tenancy Data Model
Row-level / schema-level / database-level isolation choice and how tenant_id is enforced (RLS / app-layer filter). Skip this section if not multi-tenant.

## 🗄️ Seeding & Test Data
Seed script location, test-fixture strategy, and any factory/builder libraries used.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
