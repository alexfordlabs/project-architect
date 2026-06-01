---
template_name: PERFORMANCE_BUDGETS
generate_when: "decisions.frontend.framework != null OR decisions.api.enabled == true"
required_decisions: []
optional_decisions: [performance.frontend_targets, performance.backend_targets, performance.bundle_size_budget]
depends_on: [UI_UX_DESIGN, API_GATEWAY]
revision_triggers: [frontend.framework, frontend.rendering, backend.framework, performance.*]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Performance Budgets: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Core Web Vitals Targets](#core-web-vitals-targets)
- [JS Bundle Size Budget](#js-bundle-size-budget)
- [🌐 API Latency Targets](#api-latency-targets)
- [Backend Throughput Targets](#backend-throughput-targets)
- [🗄️ Database Query Time Targets](#database-query-time-targets)
- [🧪 Performance Testing Tools](#performance-testing-tools)
- [Enforcement](#enforcement)
- [↻ Revision Log](#revision-log)

## Core Web Vitals Targets
Table: metric | target | measured-at | tool. At minimum LCP (< 2.5s), INP (< 200ms), CLS (< 0.1), TTFB (< 800ms), and FCP (< 1.8s). Targets stated for both field (RUM p75) and lab (Lighthouse) data.

## JS Bundle Size Budget
Per-route / per-entry-point budget in gzipped KB. Table: route | initial JS budget | CSS budget | total transfer budget | image-weight budget. Names the bundle analyzer in use and the rule for adding heavy dependencies.

## 🌐 API Latency Targets
Table: endpoint class | p50 | p95 | p99 | timeout. Differentiates read endpoints, write endpoints, search / aggregation, and long-running jobs. Aligns with SLO_AND_ERROR_BUDGETS.md latency SLOs.

## Backend Throughput Targets
Requests-per-second per service / endpoint at MVP / growth / scale, the load profile assumed (steady vs spiky), and the autoscaling triggers that protect these numbers.

## 🗄️ Database Query Time Targets
Table: query class | p50 | p95 | rule (e.g., "no query > 100ms in hot path", "no full-table scan in production"). Names the query-monitoring tool (pg_stat_statements / Performance Insights / Datadog DBM / etc.).

## 🧪 Performance Testing Tools
Tooling per layer: Lighthouse / Lighthouse CI for frontend lab, real-user-monitoring (RUM) for field, k6 / artillery / Gatling for backend load, pgbench / sysbench for DB. How and when each runs.

## Enforcement
CI gates (Lighthouse CI thresholds, bundle-size regressions, k6 thresholds) and production monitoring (RUM alerts, SLO burn-rate, query-time alerts) that block / page when budgets are exceeded. Names the dashboard + alert configuration anchored to MONITORING_AND_OBSERVABILITY.md.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
