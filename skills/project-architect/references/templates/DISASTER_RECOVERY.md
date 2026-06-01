---
template_name: DISASTER_RECOVERY
generate_when: "decisions.production_bound == true AND decisions.scale >= 'growth'"
required_decisions: []
optional_decisions: [dr.rto, dr.rpo, dr.replication_strategy]
depends_on: [BACKUP_AND_DR, DEPLOYMENT]
revision_triggers: [hosting.backend, database.host, dr.rto, dr.rpo]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Disaster Recovery: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [RTO / RPO Targets](#rto-rpo-targets)
- [Failure Modes Considered](#failure-modes-considered)
- [Recovery Procedures](#recovery-procedures)
- [🧪 Drills & Verification Schedule](#drills-verification-schedule)
- [Communication Plan During DR](#communication-plan-during-dr)
- [↻ Revision Log](#revision-log)

## RTO / RPO Targets
Table: tier | RTO (recovery time objective) | RPO (recovery point objective) | justification. Different data classes / services typically get different targets — be explicit so the architecture is sized correctly.

## Failure Modes Considered
Subsections for each disaster scenario covered by this plan: full region outage, single-AZ outage, database corruption / accidental drop, cryptographic key loss, vendor failure / acquisition / sudden EOL, ransomware / supply-chain compromise, and account lockout (admin keys lost). Explicitly list which failures are out-of-scope.

## Recovery Procedures
Per-scenario step-by-step playbook: detection signal, decision criteria (declare DR vs operate-degraded), pre-conditions, recovery steps, verification checklist, and the cut-over communication plan. References RUNBOOK.md recipes where they overlap.

## 🧪 Drills & Verification Schedule
Drill cadence per scenario (table-top quarterly, partial annually, full bi-annually), participants, success criteria, and the post-drill report owner. Drills update this document — undocumented changes don't count.

## Communication Plan During DR
Internal incident-response activation (see INCIDENT_RESPONSE.md) plus DR-specific notifications: board / executives, key customers under SLA, regulators if applicable, and the cadence of status updates while degraded.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
