---
template_name: COST_MODEL
generate_when: "decisions.scale != 'hobby' OR decisions.managed_services_in_stack == true"
required_decisions: []
optional_decisions: [hosting.*, database.*, file_storage.*, payments.*, notifications.*]
depends_on: [DEPLOYMENT, DATABASE_DESIGN]
revision_triggers: [hosting.frontend, hosting.backend, database.host, file_storage.provider, ai.llm_provider]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Cost Model: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [💰 Cost Summary](#cost-summary)
- [Per-Service Breakdown](#per-service-breakdown)
- [💰 Hidden Cost Watchlist](#hidden-cost-watchlist)
- [💰 Free-Tier Limits](#free-tier-limits)
- [💰 Cost-Optimization Strategy](#cost-optimization-strategy)
- [💰 Cost-Alerting Thresholds](#cost-alerting-thresholds)
- [↻ Revision Log](#revision-log)

## 💰 Cost Summary
Table: tier | service | $/month at MVP | $/month at growth | $/month at enterprise. One row per priced service across all tiers so leadership can see the total bill at each stage.

## Per-Service Breakdown
One subsection per priced service (hosting, database, file storage, email, AI/LLM, monitoring, analytics, payments, etc.). Each captures pricing model (per-request / per-GB / per-seat / tiered), assumed usage, and the $/month math.

## 💰 Hidden Cost Watchlist
Egress fees, snapshot storage, log retention, dedicated IP addresses, inter-region replication, NAT gateway hours, observability sample overage, AI tokens beyond context window, premium support, and any other charges that don't appear on the headline price page.

## 💰 Free-Tier Limits
Per-provider free-tier quotas (requests, GB, seats, runtime minutes) and the projected month at which the project graduates from free tier on each service.

## 💰 Cost-Optimization Strategy
Concrete levers: caching, batching, reserved instances / commitments, storage tiering, region selection, autoscaling policy, and architectural choices (serverless vs always-on) that move the curve.

## 💰 Cost-Alerting Thresholds
Per-service alert configuration: warn threshold, page threshold, owner, and the response runbook. Anchors to MONITORING_AND_OBSERVABILITY.md alerting.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
