---
template_name: BACKUP_AND_DR
generate_when: "decisions.database.engine != null AND decisions.scale != 'hobby'"
required_decisions: [database.engine]
optional_decisions: [backup.frequency, backup.retention, backup.encryption, backup.testing_cadence]
depends_on: [DATABASE_DESIGN]
revision_triggers: [database.engine, database.host, backup.frequency, backup.retention]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Backup and DR: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Backup Strategy](#backup-strategy)
- [Backup Frequency & Retention](#backup-frequency-retention)
- [🗄️ Backup Storage Location](#backup-storage-location)
- [Encryption at Rest](#encryption-at-rest)
- [Restore Procedure](#restore-procedure)
- [🧪 Restore Testing Cadence](#restore-testing-cadence)
- [↻ Revision Log](#revision-log)

## Backup Strategy
Full + incremental + continuous (WAL / binlog / CDC) layered approach per data store. One subsection per priced data system (primary DB, replicas, object storage, cache snapshots if relevant, search index, vector store). Each names the mechanism and the tooling.

## Backup Frequency & Retention
Table: data store | full cadence | incremental cadence | continuous capture | retention (daily / weekly / monthly / yearly). Retention reflects business + regulatory needs (e.g., 7y for financial records, 30d for ephemeral data).

## 🗄️ Backup Storage Location
Where backups physically live: same-region (fast restore) vs cross-region (DR) vs cross-cloud (vendor-failure protection). Object lifecycle policy (Glacier / archive tier), and the rule that backups never share blast radius with primary.

## Encryption at Rest
Algorithm (AES-256-GCM default), KMS provider, key rotation cadence, and whether backups use customer-managed keys vs platform-managed. Aligns with SECURITY_AND_COMPLIANCE.md encryption policy.

## Restore Procedure
Step-by-step recipe to restore from each backup tier: prerequisites (access, credentials, target environment), commands, expected duration, verification queries, and the cut-over plan if restoring into the primary. Includes the partial-table / point-in-time-restore path, not just full-cluster.

## 🧪 Restore Testing Cadence
Schedule for proving backups actually restore (table-top monthly, real restore quarterly, full DR drill annually), success criteria, and the report owner. Untested backups are presumed broken.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
