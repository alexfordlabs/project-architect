---
template_name: EDGE_COMPUTE_DESIGN
generate_when: "conditional"
required_decisions:
  - deployment.edge
  - deployment.target
optional_decisions:
  - deployment.edge_platform
  - deployment.edge_state
  - deployment.edge_runtime
  - architecture.style
  - data.store
  - observability.stack
  - deployment.iac
depends_on: []
revision_triggers:
  - deployment.edge
  - deployment.edge_platform
  - deployment.edge_state
  - deployment.edge_runtime
  - deployment.target
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Edge-Compute Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This design is grounded in the **[Cloudflare Workers](https://developers.cloudflare.com/workers/)**
> platform model — the canonical edge-FaaS reference — and in
> *[How Workers works](https://developers.cloudflare.com/workers/reference/how-workers-works/)*
> + the *[Platform limits](https://developers.cloudflare.com/workers/platform/limits/)*. The
> governing constraint of edge compute: code runs in lightweight **V8 isolates** distributed
> across a global network, not in per-request VMs/containers — which buys near-zero cold starts
> but imposes a small, sandboxed execution envelope (CPU-time budgets, no persistent local disk,
> no guaranteed instance affinity). Every choice below is justified against that envelope. Where
> {{project_name}} targets a different provider (Vercel Edge Functions, Deno Deploy, Fastly
> Compute, AWS Lambda@Edge / CloudFront Functions), the concepts map but the **exact limits and
> product names differ** — record the provider's actual figures in each table.

## Table of contents
- [🌍 Platform & Execution Model](#platform-execution-model)
- [🧩 Edge vs Origin Split](#edge-vs-origin-split)
- [🗺️ Regional vs Global Placement](#regional-vs-global-placement)
- [💾 Edge State & Storage Bindings](#edge-state-storage-bindings)
- [🔄 Request Lifecycle](#request-lifecycle)
- [📏 Limits & Budgets](#limits-budgets)
- [🔌 Bindings, Config & Secrets](#bindings-config-secrets)
- [👁️ Observability at the Edge](#observability-at-the-edge)
- [🧪 Local Dev & Deployment](#local-dev-deployment)
- [✅ Pre-Deploy Checklist](#pre-deploy-checklist)
- [↻ Revision Log](#revision-log)

## 🌍 Platform & Execution Model

| Property | Decision for {{project_name}} |
|---|---|
| Edge platform | `{{deployment_edge_platform}}` (Cloudflare Workers / Vercel Edge / Deno Deploy / Fastly Compute / Lambda@Edge) |
| Runtime | `{{deployment_edge_runtime}}` (V8 isolate JS/TS / WASM / WASI) |
| Language(s) | {{edge_languages}} |
| Isolation unit | {{isolation_unit}} (e.g. V8 isolate — *not* a per-request container) |

**Isolates, not containers.** On Cloudflare Workers, code runs inside a **V8 isolate** — "a
lightweight context that provides your code with variables it can access and a safe environment
to be executed within." A single runtime process hosts hundreds-to-thousands of isolates, each
memory-separated from the rest. The JavaScript-runtime overhead is paid **once on container
start**, not per request, so an isolate "can start around a hundred times faster than a Node
process on a container or virtual machine." This is what eliminates the cold-start tax that
container-per-function FaaS (e.g. classic AWS Lambda) pays.

> **Cold-start posture for {{project_name}}:** {{cold_start_posture}} — for isolate platforms this
> is effectively near-zero; if WASM modules or large dependency graphs inflate first-load, note
> the mitigation. If the target platform is container-based (AWS Lambda@Edge, Fastly Compute), state
> the real cold-start budget and any provisioned-concurrency / warm-pool strategy instead.

> **No instance affinity.** Per the docs, "there is no guarantee that any two user requests will
> be routed to the same or a different instance." Treat module-global variables as a **best-effort
> per-isolate cache, never as durable or shared state** — anything that must survive a request or
> be shared across isolates lives in a [storage binding](#edge-state-storage-bindings).

## 🧩 Edge vs Origin Split

Decide, function by function, what genuinely belongs at the edge versus what should defer to an
origin / region-locked service. The edge wins for latency-sensitive, stateless-ish, fan-out-light
work; the origin wins for heavy compute, large stateful transactions, and data with residency or
proximity requirements.

| Concern | Runs at edge | Runs at origin | Rationale for {{project_name}} |
|---|---|---|---|
| {{concern_1}} | {{concern_1_edge}} | {{concern_1_origin}} | {{concern_1_rationale}} |
| {{concern_2}} | {{concern_2_edge}} | {{concern_2_origin}} | {{concern_2_rationale}} |
| {{additional_concerns}} | … | … | … |

**Good edge candidates:** request routing/rewriting, auth/JWT verification, A/B + feature flags,
personalization, caching & cache-key shaping, lightweight API aggregation, header/security
manipulation, rate-limiting at the door. **Keep at origin (or proximate region):** long CPU-bound
jobs that exceed the edge CPU budget, large analytical queries, write-heavy transactions against a
single primary DB, and anything bound by data-residency law. Strategy: {{edge_origin_strategy}}.

## 🗺️ Regional vs Global Placement

By default an edge Worker executes in the data center **closest to the requesting user**, across
"a growing global network of thousands of machines distributed across hundreds of locations." That
is ideal when the work is self-contained — but it can be *slower* when the Worker makes several
round-trips to a database that lives in one region, because each hop crosses the long user→origin leg.

| Property | Decision |
|---|---|
| Placement mode | {{placement_mode}} (default: closest-to-user) |
| Smart Placement | {{smart_placement}} — Cloudflare can relocate a Worker closer to back-end services it talks to repeatedly, to cut total latency |
| Region pinning / jurisdiction | {{region_pinning}} (e.g. Durable Objects `jurisdiction`, EU/FedRAMP data locality) |
| Data residency requirements | {{data_residency}} |

> Rule of thumb: if a Worker chats with one back-end **N times per request**, enabling Smart
> Placement (or pinning compute near that back-end) usually beats running at the user's edge.
> If it mostly reads edge-cached data and rarely calls origin, keep it at the user's edge.

## 💾 Edge State & Storage Bindings

The edge has **no persistent local disk** and no shared process memory. All durable or
cross-request state goes through a managed storage product, accessed via a **binding** (a typed
handle injected on `env`). Map each storage need to the right primitive:

| Need | Cloudflare product | What it is | {{project_name}} usage |
|---|---|---|---|
| Low-latency cached reads, config, sessions | **Workers KV** | Eventually-consistent, edge-cached key-value store; fast global reads, slower global write propagation | {{kv_usage}} |
| Strongly-consistent coordination, per-entity state, WebSockets | **Durable Objects** | Single-threaded stateful objects with a unique global address + transactional storage; serializes access per object | {{do_usage}} |
| Relational queries | **D1** | Serverless SQLite-based SQL database for fast global queries | {{d1_usage}} |
| Large blobs / media / backups | **R2** | S3-compatible object storage with **zero egress fees** | {{r2_usage}} |
| Async work / decoupling | **Queues** | Guaranteed-delivery message queue with no egress charges | {{queue_usage}} |
| Accelerating an external SQL DB | **Hyperdrive** | Connection pooling + edge query caching in front of your existing Postgres/MySQL | {{hyperdrive_usage}} |
| Embeddings / semantic search | **Vectorize** | Vector database for AI-powered retrieval | {{vectorize_usage}} |
| Model inference | **Workers AI** | Serverless-GPU model inference at the edge | {{workers_ai_usage}} |

**Consistency model is the load-bearing decision.** KV is **eventually consistent** — perfect for
read-mostly config and cache, wrong for a counter or a lock. Durable Objects give **strong
consistency and serialized access** for exactly one logical entity — use them for coordination,
real-time presence, and per-user/per-room state. State the model {{project_name}} relies on and
why: {{consistency_decision}}.

> For non-Cloudflare targets, substitute the equivalent: Vercel KV/Blob/Postgres, Deno KV,
> Fastly KV/Config Store, DynamoDB Global Tables + Lambda@Edge. Keep the *need → primitive →
> consistency model* mapping; only the brand names change.

## 🔄 Request Lifecycle

The Workers handler signature is `fetch(request, env, ctx)` returning a `Response`. Map
{{project_name}}'s request flow onto it:

1. **Ingress** — request hits the nearest data center; routing/rewrites/auth happen first: {{ingress_logic}}
2. **Read/compute** — edge state reads + business logic within the CPU budget: {{compute_logic}}
3. **Origin/subrequest** — calls to APIs, DB bindings, or origin (`fetch()`), counted against the subrequest limit: {{subrequest_logic}}
4. **Response shaping** — caching headers, cache key, streaming the `Response`: {{response_logic}}
5. **Deferred work** — `ctx.waitUntil()` to extend lifetime for logging/cache-fill *after* the response is sent: {{waituntil_logic}}

> Use **`ctx.waitUntil(promise)`** to keep the isolate alive for fire-and-forget work (cache
> population, analytics) without delaying the user's response. Use **streaming responses** to start
> sending bytes before the full body is computed. Triggers beyond HTTP — **Cron Triggers**, **Queue
> consumers**, **Durable Object Alarms** — each have their own lifecycle and limits.

## 📏 Limits & Budgets

> Values below are **Cloudflare Workers** figures (verified against the Platform limits page).
> If targeting another provider, **replace every cell** with that provider's documented limit —
> these numbers do not transfer.

| Limit | Workers Free | Workers Paid | Budget for {{project_name}} |
|---|---|---|---|
| **CPU time** / HTTP request | 10 ms | 5 min (default 30 s) | {{cpu_budget}} |
| **Wall time** (duration) / HTTP request | No limit | No limit | {{wall_budget}} |
| **Memory** per isolate | 128 MB | 128 MB | {{memory_budget}} |
| **Subrequests** / request | 50 | 10,000 (configurable up to 10M) | {{subrequest_budget}} |
| Simultaneous open connections | 6 | 6 | {{connection_budget}} |
| Environment variables (count / size) | 64 / 5 KB | 128 / 5 KB | {{env_var_budget}} |
| Worker size (gzip / uncompressed) | 3 MB / 64 MB | 10 MB / 64 MB | {{bundle_budget}} |
| Cron / Queue / DO-Alarm duration | 15 min | 15 min | {{background_budget}} |

**CPU time ≠ wall time.** CPU time measures only how long the CPU spends *executing your code*;
time spent awaiting network/`fetch()`/I/O does **not** count against it. The default CPU cap is
generous for I/O-bound edge logic but unforgiving for CPU-bound loops (crypto, image processing,
large parsing). If {{project_name}} has a CPU-heavy path, document how it stays inside the budget
(stream, chunk, offload to a Queue consumer / Durable Object / origin): {{cpu_strategy}}.

> The **6-concurrent-connections** ceiling (connections awaiting response headers) is a common
> trip-wire for fan-out aggregators — connections release as headers arrive, so batch/sequence wide
> fan-outs accordingly. Note the fan-out handling for {{project_name}}: {{fanout_strategy}}.

## 🔌 Bindings, Config & Secrets

Bindings connect a Worker to platform resources (KV, DO, D1, R2, Queues, AI, service bindings,
other Workers) and are declared in configuration, then surfaced on `env` at runtime.

| Concern | Mechanism for {{project_name}} |
|---|---|
| Config file | `{{config_file}}` (e.g. `wrangler.jsonc` / `wrangler.toml`) |
| Resource bindings | {{resource_bindings}} (KV namespaces, DO classes, D1 DBs, R2 buckets, Queues, service bindings) |
| Non-secret vars | {{plain_vars}} — `[vars]` / env (≤ 64–128 entries, ≤ 5 KB each) |
| Secrets | `{{secrets_mechanism}}` (`wrangler secret put` / dashboard — **never** committed plaintext) |
| Multi-environment | {{environments}} (preview / staging / production via named environments) |

> Per the workspace secret-distribution canon, runtime secrets resolve through 1Password Connect
> where applicable — only the Connect token (or platform secret bindings) lives on the platform,
> never raw API keys in `{{config_file}}` or the repo.

## 👁️ Observability at the Edge

Distributed edge execution means logs come from many data centers and a request may touch several
bound services — observability must be wired in from the start, not bolted on.

| Capability | Cloudflare product | Decision for {{project_name}} |
|---|---|---|
| Stored, queryable logs | **Workers Logs** (auto-collect, filter, analyze in dashboard) | {{workers_logs_decision}} |
| Live tail during dev/deploy | **Real-time logs** (`wrangler tail`) | {{realtime_logs_decision}} |
| Custom filter/sample/transform of telemetry | **Tail Workers** | {{tail_workers_decision}} |
| Export to R2 / S3 / SIEM | **Workers Logpush** (Trace Event Logs) | {{logpush_decision}} |
| Distributed tracing | **Tracing** (end-to-end request visibility) | {{tracing_decision}} |
| Readable errors | **Source maps & stack traces** | {{sourcemaps_decision}} |
| Health metrics | **Metrics & analytics** (requests, error rate, CPU time, wall time, duration) | {{metrics_decision}} |

- **SLIs / alerts:** {{slis_alerts}} — what pages on-call and the thresholds (error rate, CPU-time
  approaching the cap, subrequest-limit hits).
- **Structured logging:** {{structured_logging}} — log JSON, include a request/trace ID, sample in
  high-traffic paths to control volume.
- **Provider-neutral note:** map these onto the target platform's equivalents (Vercel Logs/OTel,
  Deno Deploy logs, Fastly real-time log streaming, CloudWatch for Lambda@Edge).

## 🧪 Local Dev & Deployment

| Property | Decision |
|---|---|
| Local dev | {{local_dev}} (e.g. `wrangler dev` running the real `workerd` runtime locally) |
| Build / bundle | {{build_tool}} (esbuild via Wrangler / custom) |
| Deploy | {{deploy_command}} (e.g. `wrangler deploy`) |
| IaC / config-as-code | `{{deployment_iac}}` (config file committed; Terraform / API for account-level resources) |
| Rollout & rollback | {{rollout_strategy}} (versioned deploys, gradual rollout, instant rollback to a prior version) |
| Preview environments | {{preview_envs}} (per-PR preview deploys / versioned URLs) |

> Develop against the **same runtime** that runs in production (`wrangler dev` uses `workerd`) so
> behavioral surprises don't appear only after deploy. Keep `{{config_file}}` in version control as
> the source of truth for bindings and limits.

## ✅ Pre-Deploy Checklist

Confirm each item for {{project_name}} before promoting to production:

- [ ] No reliance on instance affinity — module globals treated as best-effort cache only.
- [ ] All durable/shared state goes through a binding with the **right consistency model** (KV eventual vs DO strong).
- [ ] CPU-heavy paths verified to stay within the CPU-time budget (`{{cpu_budget}}`); offload documented if not.
- [ ] Subrequest count per request is under the plan limit; wide fan-outs respect the 6-connection ceiling.
- [ ] Worker bundle is under the size limit (gzip & uncompressed).
- [ ] Secrets flow through `{{secrets_mechanism}}` / 1Password Connect — no plaintext in `{{config_file}}` or repo.
- [ ] Edge-vs-origin split reviewed; latency-critical work is at the edge, residency-bound data is region-pinned.
- [ ] Observability wired: logs, tracing, and at least one alert on error rate + CPU-time saturation.
- [ ] Deploys are versioned with a tested rollback path.
- [ ] `{{additional_checklist_item}}`

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
