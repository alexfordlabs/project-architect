---
template_name: RATE_LIMITING
generate_when: "conditional"
required_decisions:
  - api.enabled
  - scale
optional_decisions:
  - api.style
  - api.gateway
  - auth.enabled
  - infra.cdn
  - data.cache
revision_triggers:
  - api.enabled
  - scale
  - api.style
  - api.gateway
depends_on: []
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Rate Limiting: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This doc specifies how **{{project_name}}** throttles API traffic and how it advertises
> quota state to clients. The wire format follows the IETF HTTPAPI Working Group's
> *[RateLimit header fields for HTTP](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers/)*
> (draft-ietf-httpapi-ratelimit-headers, Standards-Track; current rev **-11**, May 2026).
> The draft defines two fields — `RateLimit-Policy` (the static quota policy) and `RateLimit`
> (the current service-limit state) — using HTTP Structured Field Values. Prefer these over
> the legacy, non-standard `X-RateLimit-*` headers, whose semantics were never agreed (the
> draft notes implementations disagree on whether the reset value is seconds-remaining,
> milliseconds, a UNIX timestamp, or an HTTP-date).

## Table of contents
- [🔐 Scope & Threat Model](#scope-threat-model)
- [⚖️ Quota Policies](#quota-policies)
- [🪟 Algorithm & Window Semantics](#algorithm-window-semantics)
- [🗝️ Partition Keys (Who Gets Counted)](#partition-keys-who-gets-counted)
- [📤 Response Headers (Wire Format)](#response-headers-wire-format)
- [🚫 429 & Retry-After Behavior](#429-retry-after-behavior)
- [🏗️ Enforcement Topology](#enforcement-topology)
- [🗄️ Counter Store](#counter-store)
- [🔧 Implementation](#implementation)
- [🔐 Security Considerations](#security-considerations)
- [🧪 Testing & Observability](#testing-observability)
- [↻ Revision Log](#revision-log)

## 🔐 Scope & Threat Model
What rate limiting is protecting **{{project_name}}** against, and what it explicitly is *not*:

- **Goals:** {{rate_limit_goals}} (fair sharing across clients, abuse/scraping resistance,
  cost control on metered downstreams, brownout protection of {{protected_resource}}).
- **Non-goals:** rate limiting is **not** an authentication or authorization mechanism.
  Per the draft's security guidance, *"this specification does not prevent clients from making
  requests; servers should always implement mechanisms to prevent resource exhaustion."*
  Treat advertised quota as advisory, never as a load-shedding substitute.
- **Endpoints in scope:** {{rate_limited_endpoints}}
- **Endpoints exempt:** {{exempt_endpoints}} (health checks, internal service-to-service, etc.)

## ⚖️ Quota Policies
Each policy is a named **Quota Policy Item**: a quota allocation (`q`) of some quota unit (`qu`)
over a time window (`w`). Multiple policies can apply simultaneously (e.g. a burst window plus a
daily cap); the most-constraining one governs. Define every policy here — these map 1:1 to the
items advertised in the `RateLimit-Policy` field.

| Policy name (`policyid`) | Quota `q` | Unit `qu` | Window `w` (s) | Applies to |
|---|---|---|---|---|
| `{{policy_1_name}}` | {{policy_1_quota}} | {{policy_1_unit}} | {{policy_1_window}} | {{policy_1_scope}} |
| `{{policy_2_name}}` | {{policy_2_quota}} | {{policy_2_unit}} | {{policy_2_window}} | {{policy_2_scope}} |
| `{{additional_policies}}` | … | … | … | … |

**Quota units (`qu`).** The draft defines three registered values — choose per policy:
- `requests` — the default; counts HTTP requests. Used when `qu` is omitted.
- `content-bytes` — counts bytes of payload; use for upload/bandwidth limits.
- `concurrent-requests` — counts in-flight requests; use for connection/concurrency caps.

**Tier mapping.** How a caller's plan/role selects a policy (e.g. anonymous → `{{tier_anon}}`,
authenticated → `{{tier_auth}}`, paid → `{{tier_paid}}`): {{tier_selection_rule}}

## 🪟 Algorithm & Window Semantics
**Counting algorithm:** `{{rate_limit_algorithm}}`
*(fixed window / sliding window log / sliding window counter / token bucket / leaky bucket /
GCRA. Token bucket is the common default for smoothing bursts; sliding-window-counter for
accurate per-window accounting at low storage cost.)*

**Window behavior:** the `w` parameter on each policy is the **nominal** window length. The
`RateLimit` field's `t` parameter reports the **effective window** — the time within which the
currently-available quota (`r`) can be consumed. Per the draft, these need not be identical:

- Clients **MUST NOT** consider the available quota `r` a service-level agreement — per the
  draft it is a best-effort hint, not a guarantee.
- Clients should **not** assume the full service limit is restored the instant the effective
  window `t` elapses (a sliding/continuous algorithm refills gradually, not all-at-once); only
  the literal `MUST NOT … SLA` rule above is normative in the draft.

**Burst handling:** {{burst_policy}} — whether short bursts above the steady rate are absorbed
(token-bucket capacity / leaky-bucket depth) and by how much.

## 🗝️ Partition Keys (Who Gets Counted)
A **partition key** divides server capacity so quota is allocated *per* client/resource rather
than globally. State the dimension(s) {{project_name}} partitions on, in priority order:

| Partition dimension | Source | Notes |
|---|---|---|
| {{partition_dim_1}} | {{partition_src_1}} | e.g. API-key/token subject claim — preferred for authenticated traffic |
| {{partition_dim_2}} | {{partition_src_2}} | e.g. client IP / IP+CIDR — fallback for anonymous traffic |
| {{partition_dim_3}} | {{partition_src_3}} | e.g. route group, tenant id, OAuth client_id |

**Advertising the key.** When a policy is partitioned, the optional `pk` parameter on
`RateLimit-Policy` / `RateLimit` carries the partition key as a Structured-Field **Byte
Sequence** (`:base64:`). Decide whether to expose `pk` (transparency) or omit it (avoid leaking
which bucket a caller falls into): {{expose_pk_decision}}

> ⚠️ Choosing IP as the sole partition is fragile behind NAT/CGNAT, mobile carriers, and shared
> egress; it both over-throttles legitimate shared clients and under-throttles distributed abuse.
> Prefer an authenticated subject where available; combine dimensions where not.

## 📤 Response Headers (Wire Format)
Emit both fields on responses for rate-limited endpoints. Syntax is HTTP Structured Fields.

**`RateLimit-Policy`** — a List of Quota Policy Items (the static contract). Each item is a
String `policyid` with parameters `q` (REQUIRED quota), `qu` (unit, default `requests`),
`w` (window seconds), and optionally `pk`:

```http
RateLimit-Policy: "{{policy_1_name}}";q={{policy_1_quota}};w={{policy_1_window}}, "{{policy_2_name}}";q={{policy_2_quota}};w={{policy_2_window}}
```

Spec examples for reference:
```http
RateLimit-Policy: "default";q=100;w=10
RateLimit-Policy: "permin";q=50;w=60, "perhr";q=1000;w=3600
RateLimit-Policy: "peruser";q=65535;qu="content-bytes";w=10;pk=:sdfjLJUOUH==:
```

**`RateLimit`** — a List of Service Limit Items (the live state). Each item references a
`policyid` with `r` (REQUIRED remaining quota units) and optionally `t` (effective window in
seconds) and `pk`:

```http
RateLimit: "{{governing_policy_name}}";r={{remaining_example}};t={{reset_seconds_example}}
```

Spec examples for reference:
```http
RateLimit: "default";r=50;t=30
RateLimit: "default";r=999;pk=:dHJpYWwxMjEzMjM=:
RateLimit: "day";r=100;t=36000
```

> A long List of Quota Policy Items MAY be split across multiple `RateLimit-Policy` header
> lines; receivers reassemble per Structured-Fields rules. **Casing matters:** the field names
> are `RateLimit-Policy` and `RateLimit` exactly.

**Legacy `X-RateLimit-*` emission:** {{emit_legacy_headers}} — whether {{project_name}} *also*
emits `X-RateLimit-Limit` / `-Remaining` / `-Reset` for older clients during a transition, and
the documented sunset date. Default: do not introduce them on greenfield surfaces.

## 🚫 429 & Retry-After Behavior
When a caller exceeds quota, respond:

- **Status:** `429 Too Many Requests` (RFC 9110). The draft does **not** mandate a correlation
  between `RateLimit` values and the status code — a `200` may still carry `r=0` near the edge —
  so don't rely on the header alone to detect throttling; check the status.
- **`Retry-After`:** {{retry_after_policy}}. Per the draft, if both `Retry-After` and `RateLimit`
  are present: `Retry-After` **MUST take precedence** and the effective window MAY be ignored by
  the client; and `Retry-After` **SHOULD NOT** reference a point in time earlier than the end of
  the effective window. Express as delta-seconds (recommended) or an HTTP-date.
- **Body:** {{error_body_shape}} — a machine-readable error (e.g. RFC 9457 `application/problem+json`
  with a `type`, `title`, and the limit that was hit). Avoid leaking the exact partition or
  another tenant's counts.
- **Idempotency:** rejected mutating requests must have produced no side effects; document the
  guarantee: {{idempotency_guarantee}}

## 🏗️ Enforcement Topology
Where the limit is decided and counted (closest-to-edge that has the needed identity wins):

```
{{enforcement_topology_diagram}}
  client → [CDN/WAF {{infra_cdn}}] → [API gateway {{api_gateway}}] → [app middleware] → origin
                  │                          │                            │
              coarse IP/edge            per-key policy            fine-grained per-route
```

**Decision point(s):** {{enforcement_layer}}
**Why here:** {{enforcement_rationale}} (edge sheds load cheaply but lacks app identity; the
gateway/app has the authenticated subject but pays more per request).
**Fail-open vs. fail-closed:** {{fail_mode}} — what happens to traffic if the counter store is
unreachable. Default to **fail-open** for availability unless the protected resource is more
precious than uptime.

## 🗄️ Counter Store
Shared, low-latency, atomic counters are required for correctness across N app instances.

| Aspect | Decision |
|---|---|
| Store | {{counter_store}} (e.g. Redis/Valkey, Memcached, gateway-native, DynamoDB) |
| Atomicity primitive | {{atomic_primitive}} (e.g. `INCR`+`EXPIRE`, Lua script, `GETEX`, token-bucket script) |
| Key schema | {{counter_key_schema}} (e.g. `rl:{policyid}:{partition}:{window_start}`) |
| TTL / eviction | {{counter_ttl}} — expire keys at window end to bound memory |
| Clock source | {{clock_source}} — single authoritative clock to avoid window skew across nodes |
| Consistency under failover | {{counter_consistency}} — bounded over-admission is usually acceptable |

## 🔧 Implementation
Concrete libraries, middleware, and gateway config (with versions):

- **Library/middleware:** {{rate_limit_library}}
- **Gateway config:** {{gateway_config}}
- **Header serialization:** {{sf_serializer}} — use a Structured-Fields-aware serializer so
  `pk` byte-sequences and quoted `policyid` strings encode correctly.
- **Config source of truth:** {{policy_config_location}} — where policy `q`/`w`/`qu` live so
  ops can tune limits without a code deploy.

## 🔐 Security Considerations
From the draft's Security Considerations plus operational hardening:

- **Resource exhaustion is the server's job.** Headers are advisory; keep hard backpressure
  (connection limits, request-size caps, timeouts) regardless of advertised quota.
- **Thundering herd.** A shared effective window `t` invites many throttled clients to retry at
  the same instant. Mitigate with **jitter** on `Retry-After` / `t` and exponential backoff
  guidance: {{thundering_herd_mitigation}}.
- **Information disclosure.** Exposing precise `r`/`pk` lets an attacker probe limits and infer
  other tenants' usage. Decide disclosure granularity: {{disclosure_granularity}}.
- **Quota-as-side-channel.** Error responses that still consume quota can be abused to map
  internal limits; ensure auth failures don't reveal whether a key exists via differential quota.
- **DoS via absurd values.** Don't echo client-supplied window/quota; clamp to sane server-side
  maxima: {{value_clamps}}.

## 🧪 Testing & Observability
- **Tests:** {{rate_limit_tests}} — assert the *exact* header strings (field casing, `q`/`w`/`r`/`t`/
  `pk` keys), boundary at `r=0`, the `429` + `Retry-After` precedence rule, and counter-store
  failure modes (fail-open/closed).
- **Metrics:** {{rate_limit_metrics}} — throttle rate per policy/partition, near-limit rate
  (`r` low), counter-store latency, fail-mode activations.
- **Alerts:** {{rate_limit_alerts}} — spikes in `429`s (abuse or a misconfigured client) and
  counter-store unavailability.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
