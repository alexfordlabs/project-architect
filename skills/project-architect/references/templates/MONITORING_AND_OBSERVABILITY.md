---
template_name: MONITORING_AND_OBSERVABILITY
generate_when: "decisions.scale != \"hobby\" AND decisions.production_bound == true"
required_decisions: []
optional_decisions: [monitoring.*, analytics.product]
depends_on: []
revision_triggers: [monitoring.*, analytics.product]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Monitoring and Observability: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [📊 Monitoring Stack](#monitoring-stack)
- [📊 Logging Strategy](#logging-strategy)
- [📊 Alerting Rules](#alerting-rules)
- [📊 Dashboards](#dashboards)
- [📊 Health Checks](#health-checks)
- [📊 Performance Budgets](#performance-budgets)
- [↻ Revision Log](#revision-log)

## 📊 Monitoring Stack
Table: concern | tool | purpose. Rows for logs, metrics, traces, error tracking, uptime, RUM, product analytics, and synthetic monitoring as applicable.

## 📊 Logging Strategy
Log format (JSON structured), level conventions (debug/info/warn/error), PII-redaction rules, sampling policy, and retention windows per environment.

## 📊 Alerting Rules
Table: alert | condition | severity | owner | runbook link. One row per production alert (error rate, latency, saturation, business KPI deviation, third-party outage).

## 📊 Dashboards
List of dashboards owned, what each visualizes, who the audience is (eng / product / exec), and where they're hosted.

## 📊 Health Checks
Endpoint paths (`/health`, `/ready`, `/version`), what each verifies, and how upstream load balancers / orchestrators consume them.

## 📊 Performance Budgets
Brief summary of frontend / backend / DB performance targets. Link to PERFORMANCE_BUDGETS.md for the full table once generated.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
