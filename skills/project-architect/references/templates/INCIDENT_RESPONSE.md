---
template_name: INCIDENT_RESPONSE
generate_when: "decisions.production_bound == true AND decisions.scale >= 'growth'"
required_decisions: []
optional_decisions: [incident.severity_levels, incident.communication_channels, incident.post_mortem_policy]
depends_on: [MONITORING_AND_OBSERVABILITY, RUNBOOK]
revision_triggers: [monitoring.*]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Incident Response: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Severity Levels](#severity-levels)
- [Incident Commander Roles](#incident-commander-roles)
- [Communication](#communication)
- [Detection → Triage → Resolution Flow](#detection-triage-resolution-flow)
- [Post-Mortem Policy](#post-mortem-policy)
- [War Room Logistics](#war-room-logistics)
- [↻ Revision Log](#revision-log)

## Severity Levels
Table: severity | definition | example | response SLA | who pages | external comms required. Typically SEV-1 through SEV-4 with concrete impact thresholds (% users affected, revenue impact, data loss) so classification isn't subjective.

## Incident Commander Roles
Roles activated during a SEV-1 / SEV-2: Incident Commander, Communications Lead, Scribe, Subject-Matter Experts, Customer Liaison. Responsibilities, handoff rules across timezones, and the rule that the IC does not also fix the bug.

## Communication
Internal channels (incident Slack channel, status hooks, on-call paging) and external channels (status page, customer email cadence, social posts, regulator notification). Templates and approval chains for each. Defines who can speak publicly.

## Detection → Triage → Resolution Flow
The end-to-end lifecycle: alert fires → on-call acks → triage (gather facts, classify severity, declare incident) → mitigate (stop the bleeding) → resolve (root cause fixed) → close (post-mortem scheduled). Names the artifacts produced at each stage (incident channel, timeline doc, comms log).

## Post-Mortem Policy
When a post-mortem is mandatory (always for SEV-1/2, conditional for SEV-3), authoring template, blameless conventions, review meeting cadence, and the action-item tracking process (where they live, owner, due date, follow-up).

## War Room Logistics
Physical or virtual war room (Zoom / Meet bridge with persistent link), incident document template (Google Doc / Notion page), recording policy, and the protocol for handing off across regions / shifts.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
