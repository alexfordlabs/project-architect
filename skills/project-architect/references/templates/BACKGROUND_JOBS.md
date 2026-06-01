---
template_name: BACKGROUND_JOBS
generate_when: "decisions.background_jobs.enabled == true"
required_decisions:
  - background_jobs.queue
optional_decisions:
  - background_jobs.scheduling
  - background_jobs.idempotency
  - background_jobs.retry_policy
depends_on: []
revision_triggers:
  - background_jobs.queue
  - background_jobs.scheduling
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Background Jobs: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🔧 Queue / Broker Choice](#queue-broker-choice)
- [Job Types](#job-types)
- [Idempotency Strategy](#idempotency-strategy)
- [Retry Policy](#retry-policy)
- [🔧 Dead-Letter Queues](#dead-letter-queues)
- [Scheduling](#scheduling)
- [Concurrency Limits](#concurrency-limits)
- [📊 Monitoring](#monitoring)
- [↻ Revision Log](#revision-log)

## 🔧 Queue / Broker Choice
Selected queue/broker (Inngest, Trigger.dev, Temporal, BullMQ + Redis, SQS, Cloudflare Queues, RabbitMQ, Sidekiq, Celery) with rationale, hosting model, and ordering/exactly-once semantics.

## Job Types
Table: job | trigger | frequency | priority | owner. Pulled from `background_jobs.*` decisions. Marks long-running, fan-out, and CPU/memory-heavy jobs.

## Idempotency Strategy
Idempotency-key conventions (per-event, per-business-action), dedupe window/storage, replay-safety guarantees, side-effect compensation when needed.

## Retry Policy
Per-job retry budgets, backoff curve (exponential with jitter), max attempts, partial-progress checkpointing, retryable vs terminal error classification.

## 🔧 Dead-Letter Queues
DLQ destination, alerting on entry, re-drive tooling, manual-resolution UX, retention policy on dead jobs.

## Scheduling
Cron-style recurring jobs vs event-driven, durable scheduling layer, time-zone handling, drift/missed-run policy, distributed-lock strategy to prevent duplicate fires.

## Concurrency Limits
Global, per-tenant, and per-queue concurrency caps, fair-scheduling rules, autoscaling signal (queue depth, age, latency).

## 📊 Monitoring
Per-job latency/error dashboards, queue-depth alerts, oldest-pending-message age, success-rate SLOs, integration with the broader observability stack.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
