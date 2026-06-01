---
template_name: DATA_PIPELINE
generate_when: "decisions.data_pipeline.enabled == true"
required_decisions:
  - data_pipeline.orchestrator
optional_decisions:
  - data_pipeline.warehouse
  - data_pipeline.sources
  - data_pipeline.sinks
  - data_pipeline.sla
depends_on: []
revision_triggers:
  - data_pipeline.orchestrator
  - data_pipeline.warehouse
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Data Pipeline: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Sources & Sinks](#sources-sinks)
- [Orchestrator Choice](#orchestrator-choice)
- [🎯 DAG Overview](#dag-overview)
- [Schedule & SLAs](#schedule-slas)
- [🗄️ Data Quality & Validation](#data-quality-validation)
- [🗄️ Schema Evolution](#schema-evolution)
- [📊 Observability](#observability)
- [Failure / Retry Policy](#failure-retry-policy)
- [↻ Revision Log](#revision-log)

## Sources & Sinks
Catalog of input sources (operational DBs, event streams, third-party APIs, file drops) and output sinks (warehouse, lake, reverse-ETL targets, downstream services).

## Orchestrator Choice
Chosen orchestrator (Airflow / Astronomer, Dagster, Prefect, Temporal, Mage, native cloud schedulers) with rationale and hosting model.

## 🎯 DAG Overview
High-level diagram or list of the major DAGs/jobs, their inputs/outputs, ownership, and execution mode (batch, micro-batch, streaming).

## Schedule & SLAs
Per-DAG schedule (cron / event-driven), data-freshness SLA, end-to-end latency target, on-call SLA for breakage.

## 🗄️ Data Quality & Validation
Tests at ingest (schema, null checks, referential integrity), in-flight (anomaly detection, volume thresholds), and at the sink (dbt tests, Great Expectations, Soda).

## 🗄️ Schema Evolution
Backward-compatibility policy, schema registry (Confluent, Buf), additive-only column rules, breaking-change rollout playbook.

## 📊 Observability
OpenLineage / Marquez / DataHub lineage capture, dbt artifacts surfaced, job-level metrics (duration, rows in/out, cost), data-incident channel routing.

## Failure / Retry Policy
Retry semantics per task (exponential backoff, max attempts), idempotency strategy, partial-failure recovery, backfill playbook, alerting on SLA miss.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
