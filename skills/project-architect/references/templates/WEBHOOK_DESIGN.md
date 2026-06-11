---
template_name: WEBHOOK_DESIGN
generate_when: "conditional"
required_decisions: [api.enabled, webhooks.outbound]
optional_decisions: [stack.api.protocol, api.public, api.idempotency_required, stack.backend.language, stack.backend.framework, stack.cache.engine, background_jobs.enabled]
depends_on: []
revision_triggers: [webhooks.outbound, api.idempotency_required, stack.api.protocol]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Webhook Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> **Standard:** This design conforms to the [Standard Webhooks specification](https://github.com/standard-webhooks/standard-webhooks) — the open, vendor-neutral spec for sending webhooks securely and reliably (adopted by OpenAI, Anthropic, Twilio, Kong, Svix, Resend, and others). Where this document deviates from the spec, the deviation is called out explicitly with a rationale.

## Table of contents
- [🌐 Overview & Scope](#overview-scope)
- [🌐 Event Catalog](#event-catalog)
- [🌐 Payload Shape & Versioning](#payload-shape-versioning)
- [🔐 Signing & Verification](#signing-verification)
- [🔐 Timestamp & Replay Protection](#timestamp-replay-protection)
- [🔐 Secret Strategy & Rotation](#secret-strategy-rotation)
- [🌐 Delivery Semantics & Idempotency](#delivery-semantics-idempotency)
- [🌐 Retries, Backoff & Dead-Lettering](#retries-backoff-dead-lettering)
- [🌐 Consumer-Side Verification Guide](#consumer-side-verification-guide)
- [🔐 Security Considerations](#security-considerations)
- [🔧 Implementation Notes](#implementation-notes)
- [🌐 Observability & Operations](#observability-operations)
- [↻ Revision Log](#revision-log)

## 🌐 Overview & Scope
What outbound webhooks {{project_name}} emits and why a consumer would subscribe. State the transport (HTTPS POST to a consumer-registered endpoint URL), the content type (`application/json`), and the directionality (this document covers **outbound** delivery — {{project_name}} as the sender; inbound/received webhooks from third parties belong in `THIRD_PARTY_INTEGRATIONS.md`). Name the endpoint-registration surface ({{endpoint_registration_surface}} — e.g. dashboard UI, REST `POST /webhook-endpoints`, IaC) and the per-endpoint configuration consumers control (subscribed event types, secret, target URL, enabled/disabled).

## 🌐 Event Catalog
The authoritative list of event types. Per the Standard Webhooks spec, the `type` field is a **full-stop-delimited identifier** (e.g. `user.created`, `invoice.payment_succeeded`). One row per event:

| Event type | Trigger | `data` payload summary | First shipped | Stability |
|---|---|---|---|---|
| `{{event_type_1}}` | {{trigger_1}} | {{data_summary_1}} | v{{event_version_1}} | stable / beta |
| `{{event_type_2}}` | {{trigger_2}} | {{data_summary_2}} | v{{event_version_2}} | stable / beta |

State the naming convention ({{event_naming_convention}} — `resource.action`, lowercase, dots as separators) and how new event types are added without breaking existing subscribers (additive only). Document whether consumers subscribe to specific types or receive all events for an endpoint.

## 🌐 Payload Shape & Versioning
Every webhook body MUST follow the Standard Webhooks envelope — three recommended top-level fields:

```json
{
  "type": "{{event_type_1}}",
  "timestamp": "2022-11-03T20:26:10.344522Z",
  "data": {
    "id": "{{example_resource_id}}"
  }
}
```

- `type` — the full-stop-delimited event type (matches a row in the Event Catalog).
- `timestamp` — ISO 8601 timestamp of when the event **occurred** (distinct from the `webhook-timestamp` header, which marks send time).
- `data` — the event-specific payload. Define the shape per event type and keep it stable.

**Message identity:** each delivery attempt carries a unique message id ({{message_id_format}} — e.g. `msg_2KWPBgLlAfxdpx2AI54pPJ85f4W`) that is **constant across retries of the same event** and surfaced in the `webhook-id` header (see Signing).

**Versioning strategy:** {{payload_versioning_strategy}}. Recommended: treat the payload as an evolving contract — additive changes (new optional `data` fields, new event types) are non-breaking; removing/renaming fields or changing semantics is breaking and requires a new event type or an endpoint-level API version. Document how a consumer pins a version and how deprecations are announced.

## 🔐 Signing & Verification
{{project_name}} signs every webhook so consumers can verify authenticity and integrity. This follows the Standard Webhooks signature scheme exactly.

**Headers sent on every delivery** (all prefixed `webhook-`, exact casing per spec):

| Header | Contents |
|---|---|
| `webhook-id` | The unique message id (constant across retries) |
| `webhook-timestamp` | Integer Unix timestamp (seconds since epoch) of the send |
| `webhook-signature` | Space-delimited list of one or more signatures (supports rotation) |

**Signed content** — the id, timestamp, and raw body are concatenated, delimited by full-stops, then signed:

```
signed_content = `${webhook_id}.${webhook_timestamp}.${raw_request_body}`
```

Example (line wrapped for readability — there are no newlines in the real value):

```
msg_2KWPBgLlAfxdpx2AI54pPJ85f4W.1674087231.{"type":"contact.created","timestamp":"2022-11-03T20:26:10.344522Z","data":{"id":"1f81eb52-5198-4599-803e-771906343485"}}
```

> ⚠️ The signed bytes MUST be the **exact bytes sent** — cryptographic signatures are sensitive to any change (re-serialization, key reordering, whitespace). Sign the serialized body, not a re-parsed object.

**Signature algorithm:** {{signature_algorithm}}.
- **Symmetric (default):** HMAC-SHA256 over `signed_content` with the endpoint's secret key; the result is base64-encoded and prefixed with the version identifier `v1`. So one entry in the header is `v1,<base64-hmac>`.
- **Asymmetric (optional):** ed25519 signature, prefixed `v1a`. Use this when consumers must verify without holding a shared secret (the public key is distributed; {{project_name}} holds the private key).

**`webhook-signature` header format** — a space-delimited list, enabling multiple valid signatures simultaneously (for rotation):

```
webhook-signature: v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE= v1,bm9ldHQ4dGhpc2lzYW5vdGhlcnNpZ25hdHVyZQ==
```

Consumers MUST accept the delivery if **any** listed signature verifies.

## 🔐 Timestamp & Replay Protection
The `webhook-timestamp` header defends against replay attacks. {{project_name}} sends the current send-time; consumers compare it against their clock and reject deliveries outside a tolerance window.

- **Recommended tolerance:** {{replay_tolerance}} (the Standard Webhooks reference implementations default to **5 minutes** in each direction; the spec recommends verifying within a tolerance window but leaves the exact value to the implementation).
- Reject timestamps **too far in the past** (replayed capture) and **too far in the future** (clock-skew or forged value).
- The timestamp is part of the signed content, so it cannot be tampered with independently of the signature.

## 🔐 Secret Strategy & Rotation
**Secret format:** signing secrets follow the spec's prefixed-base64 convention:
- Symmetric HMAC secret: `whsec_` prefix + base64-encoded random key (between 24 bytes / 192 bits and 64 bytes / 512 bits).
- Asymmetric ed25519 (if used): secret key `whsk_`, public key `whpk_`.

**Per-endpoint uniqueness:** {{secret_scope}}. The spec requires a **unique secret per endpoint** for symmetric signatures (per endpoint, or per customer, for asymmetric). Never reuse a secret across endpoints or customers — reuse lets one compromised consumer forge messages to another.

**Storage:** secrets live in {{secret_storage}} (e.g. 1Password Connect at runtime, never in source / env files as primary storage; see the project's secret-distribution pattern). Secrets are shown to the consumer once at creation; {{project_name}} stores them hashed/encrypted at rest where the implementation permits.

**Zero-downtime rotation:** when rotating an endpoint's secret, sign each delivery with **both** the new and old keys for the rotation window, emitting both signatures space-delimited in `webhook-signature`. Consumers validate against each until one matches, so no message is lost during the cutover. Signing with multiple keys (even a compromised one) does not weaken the scheme — a valid signature is still required. Rotation cadence: {{rotation_cadence}}.

## 🌐 Delivery Semantics & Idempotency
**Guarantee:** {{delivery_guarantee}} — webhooks are **at-least-once**. A consumer may receive the same event more than once (retry after a slow/failed-but-actually-succeeded response, network partition, etc.). Consumers MUST be idempotent.

**Idempotency key:** the `webhook-id` header is the idempotency key — it is constant across all retries of one event. Consumers de-duplicate by recording processed ids (the spec suggests retaining ids for at least {{idempotency_retention}}, e.g. 5 minutes, to cover the retry window). {{idempotency_note}}

**Ordering:** {{ordering_guarantee}} — by default ordering is **not guaranteed** (retries and parallel delivery can reorder events). If consumers need ordering, rely on the in-payload `timestamp` and/or a monotonic sequence field rather than arrival order. State here whether {{project_name}} offers any ordering guarantee and at what granularity (per-endpoint, per-resource).

## 🌐 Retries, Backoff & Dead-Lettering
**Success criterion:** a delivery succeeds when the consumer returns a {{success_status_codes}} (e.g. 2xx) within the {{delivery_timeout}} timeout. Any other status, a timeout, or a connection failure counts as a failure and triggers a retry.

**Retry policy:** {{retry_policy}} — retries use **exponential backoff** (optionally with jitter) over a schedule such as: immediately, then {{backoff_schedule}} (e.g. 5s, 5m, 30m, 2h, 5h, 10h), up to {{max_retries}} attempts spanning {{max_retry_window}}.

| Attempt | Delay after previous |
|---|---|
| 1 | immediate |
| 2 | {{retry_delay_2}} |
| 3 | {{retry_delay_3}} |
| … | … (exponential) |

**Dead-lettering / disablement:** after the retry budget is exhausted, the delivery is marked failed and {{dead_letter_behavior}} — typically: record it for manual replay, surface it in the endpoint's delivery log, and, if an endpoint fails persistently for {{disable_threshold}}, auto-disable the endpoint and notify the owner. Document the **manual replay** mechanism ({{replay_mechanism}}) consumers/operators use to re-trigger a failed delivery.

**Engine:** delivery + retries run on {{delivery_engine}} (e.g. a durable queue / background-job system — note whether `background_jobs.enabled`). Retries must be durable across restarts.

## 🌐 Consumer-Side Verification Guide
Verification steps a consumer implements (publish this in the public docs). Per the Standard Webhooks spec:

1. Read the raw request **body bytes** (do not parse-then-reserialize) plus the `webhook-id`, `webhook-timestamp`, and `webhook-signature` headers.
2. Reconstruct `signed_content = id.timestamp.body`.
3. Compute the expected signature: base64( HMAC-SHA256( base64decode(secret-without-`whsec_`-prefix), signed_content ) ).
4. Compare against **each** `v1,...` entry in `webhook-signature` using a **constant-time comparison**. Accept if any matches. (For `v1a` entries, verify with a battle-tested ed25519 library using the public key.)
5. Validate `webhook-timestamp` is within the {{replay_tolerance}} tolerance.
6. Use `webhook-id` as an idempotency key — skip if already processed.
7. Respond {{success_status_codes}} **fast**; do heavy work asynchronously so the connection doesn't time out and trigger spurious retries.

Recommend consumers use an official Standard Webhooks library (available for Python, JavaScript/TypeScript, Java, Rust, Go, Ruby, PHP, C#, Elixir) rather than hand-rolling verification. Provide the verification snippet in {{consumer_languages}}.

## 🔐 Security Considerations
- **HTTPS only** — refuse `http://` endpoint URLs; webhook bodies may contain sensitive data.
- **Constant-time signature comparison** — prevents timing attacks (never `==` on the signature).
- **SSRF defense** — validate consumer-registered URLs at registration and at send time; block private/internal/link-local IP ranges ({{ssrf_blocklist}}) and metadata endpoints so an attacker can't point an endpoint at internal services.
- **Sign before encrypting / never log secrets** — signing secrets, raw signatures, and full payloads must never appear in logs at info level.
- **Minimal payloads / thin events (optional):** {{thin_payload_policy}} — consider sending only an id + type and letting the consumer fetch the resource via the API, so a leaked webhook body discloses less and stays authoritative.
- **No secrets in the payload** — the `data` field should reference resources, not embed credentials/PII beyond what the event requires.
- **Rate / volume controls** — cap per-endpoint throughput to avoid being a DoS amplifier; document {{volume_controls}}.

## 🔧 Implementation Notes
Concrete stack choices: signing implemented in {{stack.backend.language}} ({{signing_library}}); delivery on {{delivery_engine}}; secret storage in {{secret_storage}}; de-dup/idempotency store in {{idempotency_store}} (e.g. `{{stack.cache.engine}}` or a DB table). Note the exact serialization library used to produce the signed body and the guarantee that the bytes signed == bytes sent. List the official Standard Webhooks SDK or the verification primitives shipped for consumers.

## 🌐 Observability & Operations
Per-endpoint delivery log (attempts, status codes, latency, signature version used), metrics ({{webhook_metrics}} — delivery success rate, p95 latency, retry rate, dead-letter count), alerting thresholds, and the operator runbook for a stuck/disabled endpoint. Document where consumers see their own delivery history and how they self-serve a replay.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
