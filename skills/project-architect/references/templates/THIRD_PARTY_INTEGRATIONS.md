---
template_name: THIRD_PARTY_INTEGRATIONS
generate_when: "decisions.integrations.length > 0"
required_decisions: [integrations]
optional_decisions: [webhooks.inbound, background_jobs.queue, scheduled_tasks]
depends_on: []
revision_triggers: [integrations, webhooks.inbound, background_jobs.queue]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Third-Party Integrations: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🎯 Integration Overview](#integration-overview)
- [🔧 Integration Details](#integration-details)
- [🌐 Event/Webhook Processing](#eventwebhook-processing)
- [🔧 Background Jobs & Queues](#background-jobs-queues)
- [🔧 Scheduled Tasks](#scheduled-tasks)
- [↻ Revision Log](#revision-log)

## 🎯 Integration Overview
Table: service | purpose | type (API / SDK / webhook / OAuth) | priority (P0 critical / P1 important / P2 nice-to-have). One row per integration.

## 🔧 Integration Details
One subsection per integration. Each subsection captures: purpose, official SDK / library + version, authentication method (API key / OAuth / JWT / mTLS), key endpoints used, rate limits and quotas, fallback / degraded-mode strategy, and pricing notes.

## 🌐 Event/Webhook Processing
Inbound webhook endpoints, signature-verification scheme, idempotency-key strategy, retry / replay handling, and the dead-letter destination. Skip this section if no inbound webhooks.

## 🔧 Background Jobs & Queues
Queue/broker choice for processing integration events (BullMQ / SQS / Inngest / Trigger.dev / Temporal), retry policy, and concurrency limits. Skip if N/A. Defer detail to BACKGROUND_JOBS.md when generated.

## 🔧 Scheduled Tasks
Cron / scheduled jobs that touch third-party services (sync, reconcile, sweep), their cadence, and ownership. Skip if N/A.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
