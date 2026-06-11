---
template_name: SLO_AND_ERROR_BUDGETS
generate_when: "decisions.scale >= 'growth'"
required_decisions: []
optional_decisions: [slo.targets, slo.error_budget_policy]
depends_on: [MONITORING_AND_OBSERVABILITY]
revision_triggers: [monitoring.*, slo.targets]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# SLOs and Error Budgets: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🚦 SLI Definitions](#sli-definitions)
- [🚦 SLO Targets](#slo-targets)
- [🚦 Error Budget Policy](#error-budget-policy)
- [🚦 Burn-Rate Alerting](#burn-rate-alerting)
- [📐 OpenSLO Specification](#openslo-specification)
- [↻ Revision Log](#revision-log)

## 🚦 SLI Definitions
Per-service indicators and how they're computed. Table: service | SLI | numerator | denominator | data source. Cover at minimum availability (good requests / total requests), latency (requests faster than threshold / total), and correctness (successful workflows / attempted) for each user-facing surface.

## 🚦 SLO Targets
Table: service | SLI | target (e.g., 99.9% availability over 30 days) | rolling window | error budget (minutes / requests). The targets here drive alerting, on-call urgency, and engineering investment trade-offs.

## 🚦 Error Budget Policy
What happens when budget is consumed: e.g., > 50% burned this quarter freezes risky launches, > 100% burned mandates a reliability sprint. Includes who arbitrates exceptions and how budget exhaustion rolls over.

## 🚦 Burn-Rate Alerting
Multi-window multi-burn-rate alert configuration (e.g., 2% budget in 1 hour pages, 10% in 6 hours pages). Table: alert | window | threshold | severity | runbook link. Anchored to MONITORING_AND_OBSERVABILITY.md.

## 📐 OpenSLO Specification
Express each SLO above as machine-readable [OpenSLO](https://github.com/OpenSLO/OpenSLO) `v1` so it can be version-controlled, code-reviewed, and synced to your SLO tooling (Nobl9, Sloth, OpenSLO-compatible exporters) — SLOs-as-code, not a wiki table that drifts. Emit one document per SLI:

```yaml
apiVersion: openslo/v1
kind: SLO
metadata:
  name: {{service}}-availability
  labels:
    service: {{service}}
spec:
  description: "{{slo_description}}"
  service: {{service}}
  indicator:
    metadata:
      name: {{service}}-availability-ratio
    spec:
      ratioMetric:
        counter: true
        good:    # numerator: "good" events
          metricSource: { type: {{metric_source}}, spec: { query: "{{good_query}}" } }
        total:   # denominator: all eligible events
          metricSource: { type: {{metric_source}}, spec: { query: "{{total_query}}" } }
  timeWindow:
    - duration: 30d
      isRolling: true            # rolling window (use a calendar window for compliance SLOs)
  budgetingMethod: Occurrences   # Occurrences (event-ratio) | Timeslices (good-minute-ratio)
  objectives:
    - displayName: "{{slo_target_label}}"
      target: 0.999              # 99.9% — must match the SLO Targets table above
```

Keep the YAML's `target`, window, and budgeting method in lockstep with the [SLO Targets](#slo-targets) table; a drift between the prose SLO and the OpenSLO file is exactly what `numerical_consistency` is meant to catch. Alerting rules ([Burn-Rate Alerting](#burn-rate-alerting)) derive from `budgetingMethod` + `objectives.target`.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
