---
template_name: SERVERLESS_DESIGN
generate_when: "conditional"
required_decisions:
  - deployment.model
  - deployment.serverless
optional_decisions:
  - deployment.serverless_provider
  - deployment.target
  - deployment.runtime
  - deployment.event_sources
  - deployment.concurrency_model
  - deployment.iac
  - observability.stack
  - architecture.style
depends_on: []
revision_triggers:
  - deployment.model
  - deployment.serverless
  - deployment.serverless_provider
  - deployment.runtime
  - deployment.event_sources
  - deployment.concurrency_model
  - observability.stack
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Serverless Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This serverless / FaaS design follows the AWS
> *[Best practices for working with AWS Lambda functions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)*.
> That guide is organized into six areas — **Function code**, **Function configuration**,
> **Function scalability**, **Metrics and alarms**, **Working with streams**, and **Security
> best practices** — and this document mirrors them. The recommendations are grounded in AWS
> Lambda but stated provider-neutrally where the principle generalizes (Cloud Functions,
> Azure Functions, Cloudflare Workers). Provider for {{project_name}}: `{{deployment_serverless_provider}}`.

## Table of contents
- [⚡ Function Inventory & Single-Purpose Design](#function-inventory-single-purpose-design)
- [🧩 Handler / Init Separation & Statelessness](#handler-init-separation-statelessness)
- [📦 Packaging, Dependencies & Layers](#packaging-dependencies-layers)
- [⚙️ Function Configuration (Memory, Timeout, Arch)](#function-configuration-memory-timeout-arch)
- [🧊 Cold Starts & Provisioned Concurrency](#cold-starts-provisioned-concurrency)
- [📈 Scalability, Concurrency & Throttling](#scalability-concurrency-throttling)
- [🔌 Event Sources & Triggers](#event-sources-triggers)
- [🌊 Working with Streams & Batches](#working-with-streams-batches)
- [💵 Cost Model & the Per-Invocation Cliff](#cost-model-the-per-invocation-cliff)
- [👁️ Observability (Logs, Metrics, Traces)](#observability-logs-metrics-traces)
- [🛡️ Security & Least Privilege](#security-least-privilege)
- [✅ Pre-Deploy Checklist](#pre-deploy-checklist)
- [↻ Revision Log](#revision-log)

## ⚡ Function Inventory & Single-Purpose Design

Each function does **one thing**. A function with one responsibility is easier to size, reason
about, observe, and grant least-privilege permissions to. List every function in {{project_name}}:

| Function | Responsibility (single purpose) | Trigger | Sync / Async |
|---|---|---|---|
| {{function_1_name}} | {{function_1_purpose}} | {{function_1_trigger}} | {{function_1_invocation}} |
| {{function_2_name}} | {{function_2_purpose}} | {{function_2_trigger}} | {{function_2_invocation}} |
| {{additional_functions}} | … | … | … |

> **Delete functions you are no longer using.** AWS: unused functions *"needlessly count
> against your deployment package size limit."* Stale functions also widen the attack surface
> and the observability noise floor. Decommission policy for {{project_name}}: {{decommission_policy}}

> **Avoid recursive invocations.** AWS: a function that *"invokes itself or initiates a
> process that may invoke the function again"* can produce *"an unintended volume of function
> invocations and escalated costs."* Break-glass: **set reserved concurrency to `0`** to throttle
> all invocations immediately while you fix the code. Recursion guard for {{project_name}}: {{recursion_guard}}

## 🧩 Handler / Init Separation & Statelessness

The single most impactful Lambda code rule is **execution-environment reuse**. Initialization
work done *outside* the handler runs once per cold environment and is reused across every
warm invocation that lands on it.

```text
┌─ module / global scope (INIT — runs once per execution environment) ──────┐
│  • create SDK clients, DB connection pools, config, compiled regexes      │
│  • read environment variables, warm caches, load static assets to /tmp    │
├─ handler(event, context) (runs EVERY invocation) ─────────────────────────┤
│  • validate the event, do the per-request work, return                    │
│  • NO heavy setup here — reuse what init built                            │
└───────────────────────────────────────────────────────────────────────────┘
```

- **Init outside the handler** — AWS: *"Initialize SDK clients and database connections
  outside of the function handler, and cache static assets locally in the `/tmp` directory.
  Subsequent invocations processed by the same instance of your function can reuse these
  resources."* What {{project_name}} initializes once: {{init_outside_handler}}
- **Statelessness** — AWS: *"don't use the execution environment to store user data, events,
  or other information with security implications,"* to *"avoid potential data leaks across
  invocations."* If mutable state can't live in memory within the handler, *"consider creating
  a separate function or separate versions of a function for each user."* State for
  {{project_name}} lives in: {{state_store}} (e.g. DynamoDB / S3 / external cache — never the
  warm container).
- **Keep-alive on persistent connections** — Lambda purges idle connections; reusing a dead
  one errors. Use the runtime's keep-alive directive. Keep-alive config: {{keep_alive_config}}
- **`/tmp` is per-environment scratch** (and shared across warm invocations) — assume it is
  dirty on reuse and gone on a cold start. `/tmp` usage: {{tmp_usage}}

## 📦 Packaging, Dependencies & Layers

Smaller packages cold-start faster and stay under quota. Control exactly what ships.

| Concern | Decision for {{project_name}} |
|---|---|
| Package format | {{package_format}} (zip archive / container image) |
| Dependency strategy | {{dependency_strategy}} — tree-shake, prune dev deps, vendor only what's used |
| Shared code via layers | {{layer_strategy}} — shared libs / runtime deps as a layer vs. bundled |
| Build / bundler | {{build_tool}} (e.g. esbuild / webpack / SAM build / container build) |

- **Do not use non-documented, non-public APIs.** AWS periodically applies *"security and
  functional updates to Lambda's internal APIs"* that *"may be backwards-incompatible,"*
  risking invocation failures. Only depend on published APIs/SDKs.
- **Be familiar with quotas.** AWS calls out that *"payload size, file descriptors and /tmp
  space are often overlooked"* — plus the deployment-package size limit. Quota headroom for
  {{project_name}}: {{quota_headroom}}
- **Layers ≠ free.** Layers help share/slim code but still load at init; count their size in
  the cold-start budget. {{layer_tradeoff}}

## ⚙️ Function Configuration (Memory, Timeout, Arch)

> **Memory is the master dial.** AWS: *"Any increase in memory size triggers an equivalent
> increase in CPU available to your function."* Right-size empirically — read `Max Memory Used:`
> from the CloudWatch `REPORT` line and use **AWS Lambda Power Tuning** to find the cost/latency
> sweet spot. More memory can be *cheaper* per invocation when it cuts duration.

| Function | Memory | Timeout | Architecture | Rationale |
|---|---|---|---|---|
| {{function_1_name}} | {{function_1_memory}} | {{function_1_timeout}} | {{function_1_arch}} | {{function_1_config_rationale}} |
| {{additional_functions}} | … | … | … | … |

- **Architecture / instruction set** — `{{instruction_set}}` (e.g. arm64/Graviton vs. x86_64);
  arm64 is typically cheaper per ms. For demanding numeric/ML workloads, AWS recommends
  libraries that *"leverage Advanced Vector Extensions 2 (AVX2)."*
- **Timeout** — load-test to set it; AWS warns an undersized timeout masks *"problems with a
  dependency service that may increase the concurrency of the function beyond what you expect."*
- **Environment variables** — AWS: *"instead of hard-coding the bucket name… configure the
  bucket name as an environment variable."* Config surface for {{project_name}}:
  {{environment_variables}} (secrets via {{secret_source}}, never plaintext env vars).
- **SQS event source caveat** — if triggered by SQS, the function's expected invocation time
  **must not exceed the queue's Visibility Timeout**, or you risk duplicate invocations.
  Visibility-timeout sizing: {{sqs_visibility_timeout}}

## 🧊 Cold Starts & Provisioned Concurrency

A **cold start** is the latency of spinning up a fresh execution environment (download code,
start runtime, run init) before the handler runs. Warm environments skip all of that.

| Lever | Decision |
|---|---|
| Cold-start latency budget | {{cold_start_budget}} (p99 acceptable init+first-invoke latency) |
| Provisioned concurrency | {{provisioned_concurrency}} — pre-warmed environments for latency-sensitive paths |
| Init-time minimization | {{init_minimization}} — slim deps, lazy-load rarely-used clients |
| Runtime choice impact | {{runtime_coldstart_notes}} (interpreted vs. compiled vs. snapshot/SnapStart) |

> **Provisioned concurrency** is, per AWS, *"the number of pre-initialized execution
> environments that Lambda allocates to your function. Lambda handles incoming requests using
> provisioned concurrency when available,"* and can still scale beyond it on demand.
> **It incurs additional charges** — provision only the floor that latency SLOs require, and
> autoscale it on a schedule/utilization target. Justification for {{project_name}}: {{pc_justification}}

## 📈 Scalability, Concurrency & Throttling

Functions scale seamlessly, but **the things around them may not.**

- **Know your upstream/downstream throughput constraints.** AWS: dependencies *"may not have
  the same throughput capabilities."* The bottleneck for {{project_name}}: {{throughput_bottleneck}}
- **Reserved concurrency** caps how high a function scales (protecting a fragile downstream,
  or fencing off a noisy function from the account pool). Reservations: {{reserved_concurrency}}
- **Throttle tolerance** — when traffic exceeds Lambda's scaling rate, AWS recommends:
  - **Timeouts, retries, and backoff with jitter** to *"smooth out retried invocations"* so
    Lambda can *"scale up within seconds to minimize end-user throttling."*
  - **Provisioned concurrency** for the latency-critical share (see above).
- **Account-level cap awareness** — all functions share the regional concurrency pool unless
  reserved. Concurrency model: `{{deployment_concurrency_model}}`.

## 🔌 Event Sources & Triggers

How invocations arrive shapes retry semantics, idempotency needs, and error handling.

| Event source | Function | Invocation model | Retry / failure behavior |
|---|---|---|---|
| {{event_source_1}} | {{event_source_1_fn}} | {{event_source_1_model}} (sync / async / poll) | {{event_source_1_failure}} |
| {{additional_event_sources}} | … | … | … |

Invocation models and what they imply:

- **Synchronous** (API Gateway / function URL / ALB) — caller waits; you own retry/backoff;
  throttling surfaces as `429` to the client.
- **Asynchronous** (S3, SNS, EventBridge) — Lambda queues, retries on failure (default 2
  retries), and routes terminal failures to an **on-failure destination / dead-letter queue (DLQ)**.
  DLQ / failure destination for {{project_name}}: {{dlq_destination}}
- **Poll-based / event source mapping** (SQS, Kinesis, DynamoDB Streams, Kafka) — Lambda polls
  and batches; see [Working with Streams](#working-with-streams-batches).

> **Write idempotent code.** AWS: *"Writing idempotent code… ensures that duplicate events
> are handled the same way. Your code should properly validate events and gracefully handle
> duplicate events."* This is non-optional for async and stream sources (at-least-once
> delivery). Idempotency mechanism for {{project_name}}: {{idempotency_mechanism}} (e.g. a
> dedupe key in DynamoDB with a conditional write; Powertools Idempotency utility).

## 🌊 Working with Streams & Batches

> Applies when an event source mapping reads from a stream/queue (Kinesis, DynamoDB Streams,
> SQS, Kafka). Omit if {{project_name}} has no poll-based sources.

- **Tune batch + record sizes.** AWS: tune *"so that the polling frequency of each event
  source is tuned to how quickly your function is able to complete its task."* `BatchSize` caps
  records per invoke; a **batching window** (up to 5 minutes) buffers until a full batch, the
  window expires, or the **6 MB payload limit** is hit. Batch/window for {{project_name}}:
  {{batch_config}}
- **Enable partial batch response** for streams so Lambda *"retries only the failed records
  instead of the entire batch"* — avoids reprocessing the whole batch on one bad record.
  Partial-batch config: {{partial_batch_response}}
- **Kinesis throughput scales with shards.** AWS: *"The rate at which Lambda can read data
  from Kinesis scales linearly with the number of shards,"* and shard count sets max concurrent
  invocations. Pick a good **partition key** so *"related records end up on the same shards and
  your data is well distributed."* Sharding plan: {{shard_plan}}
- **Watch `IteratorAge`.** AWS: monitor the **`IteratorAge`** metric *"to determine if your
  [stream] is being processed,"* e.g. *"configure a CloudWatch alarm with a maximum setting to
  30000 (30 seconds)."* A climbing `IteratorAge` means the consumer is falling behind.
  Alarm threshold for {{project_name}}: {{iterator_age_alarm}}

## 💵 Cost Model & the Per-Invocation Cliff

Serverless cost is **per-invocation × (GB-seconds + request fee) + data/egress**, not
per-server-hour. This is the headline win at low/spiky volume and the **cliff** at sustained
high volume.

| Cost driver | For {{project_name}} |
|---|---|
| Billed unit | {{billed_unit}} (e.g. requests + GB-seconds; memory × duration) |
| Per-invocation request fee | {{request_fee_basis}} |
| Compute (GB-seconds) | {{compute_cost_basis}} — memory size × billed duration |
| Provisioned concurrency surcharge | {{pc_cost}} (if used — pre-warming is billed even when idle) |
| Data transfer / NAT / VPC egress | {{egress_cost}} (often the hidden line item) |

> **The per-invocation cliff.** Serverless is cheapest when load is **bursty or low-duty-cycle**
> — you pay nothing at idle. Past a **sustained, high-throughput** threshold, the per-invocation
> economics cross over the cost of an always-on provisioned host (a container/VM). Estimate the
> crossover for {{project_name}} so the bill doesn't surprise anyone: {{cliff_analysis}}
> (model invocations/month × avg GB-seconds vs. a baseline always-on instance; revisit if
> traffic shape changes). Right-sizing memory (cheaper per ms when it shortens duration) and
> arm64 are the first cost levers; consolidating chatty fan-out is the second.

## 👁️ Observability (Logs, Metrics, Traces)

AWS: track health via platform metrics and alarms *"instead of creating or updating a metric
from within your Lambda function code."* Observability stack for {{project_name}}: `{{observability_stack}}`.

- **Structured JSON logging** — AWS: *"Structured logging makes it easier to search, filter,
  and analyze your function's logs."* Use a JSON logger (e.g. Powertools Logger). Log schema /
  correlation IDs: {{log_schema}}
- **Custom metrics via Embedded Metric Format (EMF)** — AWS: *"Instead of making synchronous
  API calls to CloudWatch, use EMF to emit metrics through your function's logs,"* which
  *"reduces latency and improves performance."* Custom metrics emitted: {{custom_metrics}}
- **Platform metrics & alarms** — alarm on the signals that matter:

  | Metric | Why | Alarm for {{project_name}} |
  |---|---|---|
  | `Duration` / `Max Memory Used` | latency + right-sizing | {{alarm_duration}} |
  | `Errors` / `Throttles` | failure & capacity pressure | {{alarm_errors_throttles}} |
  | `ConcurrentExecutions` | approaching the concurrency cap | {{alarm_concurrency}} |
  | `IteratorAge` (streams) | consumer falling behind | {{alarm_iterator_age}} |
  | Cold-start / `InitDuration` | cold-start tax on latency | {{alarm_cold_start}} |

- **Distributed tracing** — {{tracing}} (e.g. AWS X-Ray / OpenTelemetry) to follow a request
  across functions and services; capture the cold-start segment explicitly.
- **Cost Anomaly Detection** — AWS recommends it to *"detect unusual activity on your account"*
  (ML-based; up to a 24h detection delay). Enabled for {{project_name}}: {{cost_anomaly_detection}}

## 🛡️ Security & Least Privilege

- **Most-restrictive IAM.** AWS: *"Understand the resources and operations your Lambda function
  needs, and limit the execution role to these permissions."* One execution role **per
  function**, scoped to exactly its actions/resources. Role model: {{iam_role_model}}
- **Secrets** — pulled at runtime from {{secret_source}} (e.g. Secrets Manager / Parameter
  Store / 1Password Connect); never baked into the package or plaintext env vars.
- **Posture monitoring** — AWS recommends **Security Hub CSPM** (evaluates Lambda configs
  against compliance controls) and **GuardDuty Lambda Protection** (flags suspicious network
  activity, e.g. a function *"queries an IP address… associated with cryptocurrency-related
  activity"*). Enabled: {{security_monitoring}}
- **Network placement** — {{network_placement}} (VPC-attached vs. public; VPC adds ENI cold-start
  cost and needs a NAT/endpoint for egress — weigh against the reachability requirement).

## ✅ Pre-Deploy Checklist

A gate to run before deploying {{project_name}} to each environment:

- [ ] Each function is single-purpose; unused functions deleted.
- [ ] SDK clients / connections / config initialized **outside** the handler; handler is lean.
- [ ] No user/session state stored in the warm execution environment; state is externalized.
- [ ] Idempotent code on all async + stream sources (dedupe key / Powertools Idempotency).
- [ ] No recursive self-invocation; reserved-concurrency-`0` break-glass understood.
- [ ] Memory right-sized from `Max Memory Used` (Power Tuning run); timeout load-tested.
- [ ] Provisioned concurrency justified by an SLO (not on by default — it's billed when idle).
- [ ] Reserved concurrency set where a downstream needs protection.
- [ ] Async sources have a DLQ / on-failure destination; stream sources use partial batch response.
- [ ] SQS visibility timeout ≥ function timeout (no duplicate invocations).
- [ ] `IteratorAge` alarm configured for every stream consumer.
- [ ] Structured JSON logs + EMF custom metrics; `Errors`/`Throttles`/`Duration` alarms live.
- [ ] Execution role is least-privilege, one per function; secrets pulled at runtime.
- [ ] Per-invocation cost cliff estimated; Cost Anomaly Detection enabled.
- [ ] `{{additional_checklist_item}}`

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
