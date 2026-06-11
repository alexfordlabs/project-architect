---
template_name: IDEMPOTENCY_DESIGN
generate_when: "conditional"
required_decisions:
  - api.enabled
  - monetization.enabled
  - api.idempotency_required
optional_decisions:
  - api.style
  - api.payment_provider
  - api.retry_policy
  - data.store
  - data.cache
  - infra.queue
depends_on: []
revision_triggers:
  - api.idempotency_required
  - api.payment_provider
  - api.retry_policy
  - data.store
  - data.cache
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Idempotency Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This doc specifies how **{{project_name}}** makes mutating API operations safe to retry.
> Its structure and concrete values follow Stripe's *[Idempotent Requests](https://docs.stripe.com/api/idempotent_requests)*
> reference — the de-facto industry pattern for idempotent payment-grade APIs. The governing
> guarantee: **a client may safely retry a request as many times as it likes; the operation
> happens at most once, and every retry returns the same recorded outcome.** Every choice below
> is justified against that bar, with deltas from Stripe's behavior called out explicitly.

## Table of contents
- [💳 Why Idempotency Here](#why-idempotency-here)
- [💳 The Idempotency Key](#the-idempotency-key)
- [💳 Which Operations Are Idempotent](#which-operations-are-idempotent)
- [💳 Request Lifecycle](#request-lifecycle)
- [Replay Semantics](#replay-semantics)
- [💳 Parameter-Mismatch & Conflict Handling](#parameter-mismatch-conflict-handling)
- [Storage & Retention](#storage-retention)
- [Concurrency Control](#concurrency-control)
- [Client Retry Contract](#client-retry-contract)
- [💳 Payment-Provider Pass-Through](#payment-provider-pass-through)
- [🔧 Implementation Packages](#implementation-packages)
- [Testing & Verification](#testing-verification)
- [↻ Revision Log](#revision-log)

## 💳 Why Idempotency Here

State *what* forces idempotency in {{project_name}} and the failure it prevents. Stripe's
motivating case: "to perform a request safely without the risk of duplicating an object or
processing the same operation twice." Network timeouts, client retries, at-least-once queue
delivery (`{{infra_queue}}`), and double-clicks all replay the same intent.

| Driver | Present here? | Operation(s) at risk |
|---|---|---|
| Money movement / charges | {{has_payments}} | {{payment_operations}} |
| At-least-once event/queue delivery | {{has_queue_redelivery}} | {{queue_operations}} |
| Client auto-retry on 5xx / timeout | {{has_client_retries}} | {{retried_operations}} |
| User-facing double-submit | {{has_double_submit}} | {{double_submit_operations}} |

**Scope decision:** `{{idempotency_required}}` — idempotency is **required** on every mutating
endpoint listed below, **opt-in** per endpoint, or **provider-only** (delegated entirely to
`{{payment_provider}}`). Cite the ADR that recorded this.

## 💳 The Idempotency Key

Following Stripe exactly unless noted:

| Property | Stripe baseline | Decision for {{project_name}} |
|---|---|---|
| Transport | HTTP request **header** `Idempotency-Key` | `{{key_transport}}` (header `{{key_header_name}}`) |
| Recommended value | V4 UUID or a random string with **sufficient entropy to avoid collisions** | {{key_format}} |
| Max length | **255 characters** | {{key_max_length}} |
| Who generates it | The **client**, once per logical operation; reused verbatim on every retry of that operation | {{key_generator}} |
| Sensitive data | **Never** embed emails/personal identifiers in the key | {{key_sensitive_rule}} |

> Default to Stripe's canonical header name `Idempotency-Key` and value format unless there's a
> concrete reason to diverge. A key uniquely identifies one *logical* operation — a new key per
> retry defeats the entire mechanism. Document the client convention in
> [Client Retry Contract](#client-retry-contract).

## 💳 Which Operations Are Idempotent

Stripe's rule: idempotency keys apply to **`POST`** requests; **`GET`** and **`DELETE`** are
idempotent *by definition* and ignore the key. Mirror that and enumerate this project's surface.

| Method | Stripe behavior | This project |
|---|---|---|
| `POST` (create/mutate) | Accepts `Idempotency-Key`; result recorded | {{post_policy}} |
| `PUT` / `PATCH` | (not in Stripe scope) — decide here | {{put_patch_policy}} |
| `GET` | Naturally idempotent; key ignored | {{get_policy}} |
| `DELETE` | Naturally idempotent; key ignored | {{delete_policy}} |

**Endpoints requiring a key:**
{{idempotent_endpoint_list}}
*(e.g. `POST /v1/charges`, `POST /orders`, `POST /transfers` — list each mutating endpoint and
whether the key is required, optional, or ignored.)*

## 💳 Request Lifecycle

The server-side state machine for one keyed request. Stripe's critical nuance: **a result is
only saved once endpoint execution begins** — requests that fail parameter validation, or that
conflict with a concurrent in-flight request on the same key, are **not** saved and are safe to
retry.

```
{{idempotency_flow_diagram}}

  1. RECEIVE        — read Idempotency-Key from request
  2. LOOKUP         — query the idempotency store for (key, endpoint, account/tenant)
       ├─ MISS  → 3a. ACQUIRE LOCK on the key (mark in-flight)
       │           3b. VALIDATE params → on failure: release, do NOT save (retryable)
       │           3c. EXECUTE the operation exactly once
       │           3d. PERSIST {status, headers, body} keyed by the request fingerprint
       │           3e. RELEASE lock → return fresh response
       └─ HIT   → 4a. COMPARE incoming params to the stored fingerprint
                   4b. MATCH      → return the stored response (replay)
                   4c. MISMATCH   → 409 Conflict (see Parameter-Mismatch)
                   4d. IN-FLIGHT  → 409 Conflict / "key in use" (concurrent; retryable)
```

| Lifecycle element | Decision |
|---|---|
| Store keyed by | {{store_key_composition}} *(key alone vs. key + endpoint + tenant — namespace to prevent cross-endpoint collisions)* |
| Request fingerprint | {{request_fingerprint}} *(hash of method + path + canonicalized body used for the mismatch check)* |
| "Begins execution" boundary | {{execution_boundary}} *(exactly where the result becomes recorded vs. retryable)* |

## Replay Semantics

What a replay (same key, same params) returns. Stripe replays the **exact same result as the
original request**: same status code and same response body — **including `5xx` errors, which are
also cached and replayed.**

| Aspect | Stripe baseline | Decision for {{project_name}} |
|---|---|---|
| Status code on replay | Identical to original | {{replay_status}} |
| Body on replay | Byte-identical recorded body | {{replay_body}} |
| Are cached `5xx`/errors replayed? | **Yes** — errors are recorded and returned on replay | {{replay_errors}} |
| Replay signalling header | Not specified by Stripe — a custom header such as `Idempotency-Replayed: true` is a recommended optional signal | {{replay_header}} |
| Stored fields | status + headers + body | {{stored_fields}} |

> If you choose **not** to cache failed responses (so a transient `5xx` can be genuinely retried
> rather than replayed forever), that is a deliberate divergence from Stripe — record it here and
> in the ADR, and reconcile it with the [Client Retry Contract](#client-retry-contract).

## 💳 Parameter-Mismatch & Conflict Handling

Stripe's safety check: "The idempotency layer compares incoming parameters to those of the
original request and **errors if they're not the same** to prevent accidental misuse." Stripe
does not document a specific HTTP status for this; **`409 Conflict`** is the recommended choice
here (record the divergence if you pick another). Define the exact response.

| Scenario | Status | Error shape | This project |
|---|---|---|---|
| Same key, different params | **`409 Conflict`** *(recommended; Stripe documents only "errors")* | error indicating params didn't match the original | {{mismatch_response}} |
| Same key, request still in-flight (concurrent) | `409 Conflict` *(recommended)* — Stripe error code `idempotency_key_in_use` | "key currently in use; retry shortly" | {{concurrent_response}} |
| Key length > {{key_max_length}} chars | {{oversize_status}} | {{oversize_error}} | {{oversize_response}} |

**Error body schema** clients can rely on:
```json
{{error_body_schema}}
```
*(e.g. `{ "type": "idempotency_error", "code": "idempotency_key_in_use", "message": "..." }` —
keep it stable so retry middleware can branch on it.)*

## Storage & Retention

Where keyed results live and for how long. Stripe stores keys for **at least 24 hours** and may
prune them after that; **a key reused after its original record is pruned generates a brand-new
request** (no longer a replay).

| Property | Stripe baseline | Decision for {{project_name}} |
|---|---|---|
| Backing store | (managed) | `{{idempotency_store}}` *(e.g. Postgres table, Redis, DynamoDB — `{{data_store}}` / `{{data_cache}}`)* |
| Retention / TTL | **≥ 24 hours**, then prunable | {{retention_window}} |
| Behavior after prune | Same key → **new** request (not a replay) | {{post_prune_behavior}} |
| Eviction mechanism | — | {{eviction_mechanism}} *(TTL index / cron sweep / Redis EXPIRE)* |
| Schema | — | {{store_schema}} *(columns: key, fingerprint, status, response_body, locked_at, created_at, expires_at)* |

> Set retention **≥** the maximum client retry horizon. If a client may retry for up to N hours,
> a key pruned before then silently double-executes. Reconcile {{retention_window}} against
> {{client_retry_horizon}} below.

## Concurrency Control

How two simultaneous requests with the same key are serialized so the operation runs **once**.
Stripe's guarantee: a request that "conflicts with another concurrent request using the same key"
is **not saved** and is safely retryable.

- **Lock acquisition:** {{lock_mechanism}} *(e.g. `INSERT ... ON CONFLICT DO NOTHING` row-lock,
  Redis `SET key NX EX`, advisory lock) — atomic; only one writer proceeds.*
- **Loser behavior:** {{concurrent_loser_behavior}} *(immediate `409` with `idempotency_key_in_use`
  so the client backs off and retries, vs. block-and-wait for the winner's result.)*
- **Crash recovery:** {{stale_lock_recovery}} *(a holder that dies mid-flight must not wedge the
  key forever — lock TTL / `locked_at` staleness check.)*
- **Atomicity boundary:** {{atomicity_boundary}} *(the side-effect + the result-persist must be in
  one transaction, or use the outbox/two-phase pattern, so a result is never recorded without its
  effect — or vice versa.)*

## Client Retry Contract

The reciprocal obligations clients must honor for the guarantee to hold. Document this so SDK and
caller code is consistent.

- **One key per logical operation:** {{client_key_rule}} — generate the key *before* the first
  attempt; reuse it **verbatim** on every retry of that same intent.
- **Retry triggers:** {{retry_triggers}} — which responses are retryable (network error, timeout,
  `409` in-use, `5xx` if not cached) vs. terminal (`4xx` validation, replayed cached error).
- **Backoff strategy:** {{backoff_strategy}} — exponential backoff + jitter; max attempts
  {{max_retry_attempts}}; total retry horizon {{client_retry_horizon}}.
- **New-key conditions:** {{new_key_conditions}} — when a *new* key is required (genuinely new
  operation; never for a retry).

## 💳 Payment-Provider Pass-Through

> Include only if `{{payment_provider}}` is set (Stripe, Adyen, Braintree, etc.).

When {{project_name}} fronts a payment provider, decide whether your idempotency key is your own,
the provider's, or both. With Stripe specifically, forward an `idempotency_key` on the
**provider** call too, so a retry of *your* operation deterministically retries the *same*
provider operation rather than creating a second charge.

| Layer | Key source | Notes |
|---|---|---|
| {{project_name}} API edge | {{edge_key_source}} | client-supplied `Idempotency-Key` |
| → Provider call (`{{payment_provider}}`) | {{provider_key_source}} | {{provider_key_derivation}} *(derive deterministically from the inbound key so the provider also dedupes)* |

## 🔧 Implementation Packages

Specific libraries, middleware, and store clients (with versions) implementing the above —
API-edge middleware, the idempotency store driver, and any provider SDK.

{{implementation_packages}}

## Testing & Verification

How the guarantee is proven, not assumed:

- **Replay test:** {{test_replay}} — same key + same params twice ⇒ identical status/body, one
  side-effect.
- **Mismatch test:** {{test_mismatch}} — same key + different params ⇒ `409`.
- **Concurrency test:** {{test_concurrency}} — N parallel requests, same key ⇒ exactly one
  execution; losers get `409`/in-use.
- **Retention/prune test:** {{test_retention}} — key reused after TTL ⇒ new request.
- **Crash-recovery test:** {{test_crash}} — process dies mid-flight ⇒ key not wedged; safe retry.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
