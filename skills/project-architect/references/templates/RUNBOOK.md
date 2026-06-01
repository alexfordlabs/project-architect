---
template_name: RUNBOOK
generate_when: "decisions.production_bound == true AND decisions.scale >= 'growth'"
required_decisions: []
optional_decisions: []
depends_on: [DEPLOYMENT, MONITORING_AND_OBSERVABILITY]
revision_triggers: [hosting.*, monitoring.*]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Runbook: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🔧 Common Operations](#common-operations)
- [📊 Health Checks](#health-checks)
- [Maintenance Windows](#maintenance-windows)
- [Runbook Recipes](#runbook-recipes)
- [Escalation Path](#escalation-path)
- [↻ Revision Log](#revision-log)

## 🔧 Common Operations
Step-by-step recipes for the everyday actions on-call performs: deploy, rollback, scale up / down, restart a worker, drain a node, rotate secrets, rotate keys, flush cache, replay a queue, and put a feature flag into kill-switch state. Each recipe lists prerequisites, commands, verification, and rollback.

## 📊 Health Checks
Where to look first when something feels wrong: health-check endpoints, uptime dashboards, error-rate panels, and the canonical "is production healthy?" view. Includes expected steady-state values so a deviation is obvious.

## Maintenance Windows
Cadence (weekly / monthly / quarterly), notification policy (status page, customer email, internal Slack), allowed actions inside vs outside a window, and the procedure for emergency out-of-window changes.

## Runbook Recipes
One subsection per incident class. Cover at minimum: high latency, error-rate spike, database unhealthy / failover, third-party outage (auth / payments / email / AI provider), runaway cost / quota exhaustion, queue backlog, cache stampede, deployment failure, and security incident. Each recipe: symptoms → likely causes → diagnostic commands → mitigation → escalation.

## Escalation Path
Primary → secondary → tertiary on-call rotations, manager / VP escalation, vendor support contacts (with account / contract IDs), and the legal / comms escalation for customer-facing incidents.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
