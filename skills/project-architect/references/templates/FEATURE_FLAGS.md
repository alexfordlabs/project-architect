---
template_name: FEATURE_FLAGS
generate_when: "conditional"
required_decisions: [feature_flags.enabled]
optional_decisions:
  - feature_flags.provider
  - feature_flags.sdk
  - feature_flags.context_paradigm
  - feature_flags.experimentation
  - feature_flags.flag_types
  - feature_flags.local_dev
  - feature_flags.governance
  - project.type
depends_on: []
revision_triggers:
  - feature_flags.provider
  - feature_flags.sdk
  - feature_flags.context_paradigm
  - feature_flags.experimentation
  - feature_flags.flag_types
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Feature Flags: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the feature-flagging design doc for **{{project_name}}**. Its structure and
> terminology follow the **[OpenFeature Specification](https://openfeature.dev/specification/)** —
> the CNCF vendor-neutral standard for feature-flag evaluation. OpenFeature decouples your
> application code (which calls a stable **Evaluation API**) from the flag-management system
> behind it (the **Provider**), so you can swap vendors without rewriting evaluation call sites.
> Requirements in the spec use RFC 2119 keywords (MUST / SHOULD / MAY); the choices recorded
> below state how {{project_name}} satisfies them.

## Table of contents
- [🎯 Why Feature Flags Here](#why-feature-flags-here)
- [🧱 OpenFeature Architecture](#openfeature-architecture)
- [🔌 Provider & SDK Choice](#provider-sdk-choice)
- [🚦 Flag Value Types](#flag-value-types)
- [📞 Evaluation API](#evaluation-api)
- [🧭 Evaluation Context & Targeting](#evaluation-context-targeting)
- [🪝 Hooks](#hooks)
- [📡 Provider Lifecycle & Events](#provider-lifecycle-events)
- [📊 Tracking & Experimentation](#tracking-experimentation)
- [🗂️ Flag Catalog & Naming](#flag-catalog-naming)
- [♻️ Flag Lifecycle & Cleanup](#flag-lifecycle-cleanup)
- [🛡️ Failure Modes & Defaults](#failure-modes-defaults)
- [🧪 Local Development & Testing](#local-development-testing)
- [↻ Revision Log](#revision-log)

## 🎯 Why Feature Flags Here

Feature flags decouple *deploy* from *release*: code ships dark, then a flag turns it on for
a cohort. State the concrete jobs flags do for {{project_name}} so the abstraction earns its
place — not every flag use case is the same:

| Use case | In scope for {{project_name}}? | Notes |
|---|---|---|
| Release toggles (deploy-dark, gradual rollout, kill switch) | {{uses_release_toggles}} | {{release_toggle_notes}} |
| Experimentation / A-B testing (see Tracking) | {{uses_experimentation}} | {{experimentation_notes}} |
| Operational toggles (circuit breakers, feature gating under load) | {{uses_operational_toggles}} | {{operational_notes}} |
| Permission / entitlement flags (plan tier, beta access) | {{uses_permission_flags}} | {{permission_notes}} |

**Governing decision:** {{flag_strategy_summary}}

## 🧱 OpenFeature Architecture

OpenFeature's core building blocks (spec §Glossary, §Flag Evaluation API, §Provider):

- **API (global singleton)** — where you register the default **Provider** and global hooks /
  evaluation context. There is one global API instance per process.
- **Client** — obtained via `getClient([domain])`. The client is the object application code
  calls to evaluate flags. Per spec Requirement 1.1.7, *the client creation function MUST NOT
  throw, or otherwise abnormally terminate.* {{project_name}} uses the domain(s): {{client_domains}}.
- **Provider** — the pluggable adapter that actually resolves flag values against a backend
  (LaunchDarkly, flagd, Flagsmith, GrowthBook, Unleash, a static file, etc.). When a provider
  is registered, the API *MUST invoke the `initialize` function on the newly registered
  provider* (Requirement 1.1.2.2).
- **Evaluation Context** — the data (targeting key + custom attributes) used to target a flag.
- **Hooks** — extension points around evaluation (logging, telemetry, validation).
- **Events** — provider state-change notifications (ready / error / config-changed / stale).
- **Tracking** — associates a flag exposure with a downstream business/experiment metric.

```
{{architecture_diagram}}

  application code
        │  client.getBooleanValue("flag-key", false, ctx)
        ▼
  OpenFeature Client ──(hooks: before → after/error/finally)──┐
        │                                                       │
        ▼                                                       ▼
  Provider (initialize/shutdown, resolve* methods) ───────►  emits Events
        │
        ▼
  flag-management backend: {{flag_backend}}
```

## 🔌 Provider & SDK Choice

| Aspect | Decision for {{project_name}} |
|---|---|
| OpenFeature SDK / language | `{{openfeature_sdk}}` (e.g. `@openfeature/server-sdk`, `@openfeature/web-sdk`, `openfeature` Python) |
| Provider | `{{flag_provider}}` (`feature_flags.provider`) |
| Provider package | `{{provider_package}}` (with pinned version) |
| Self-hosted vs. SaaS | {{provider_hosting}} |
| Why this provider | {{provider_rationale}} |
| Migration / exit path | {{provider_exit_path}} — the OpenFeature API is the seam that lets you swap providers |

> **Context paradigm matters.** OpenFeature distinguishes two paradigms: **dynamic-context**
> (server-side — context is passed per evaluation) and **static-context** (client/mobile —
> context is set once and reconciled on change, with `PROVIDER_RECONCILING` /
> `PROVIDER_CONTEXT_CHANGED` events). {{project_name}} uses the **{{context_paradigm}}** paradigm
> because {{paradigm_rationale}}.

## 🚦 Flag Value Types

OpenFeature supports exactly four flag value types (spec §Types and Data Structures). Each has
a typed evaluation method; calling the wrong-typed method yields a `TYPE_MISMATCH` error code.

| Type | Use for | Example flag in {{project_name}} |
|---|---|---|
| **Boolean** | on/off toggles, kill switches | {{boolean_flag_example}} |
| **String** | variant selection, enum-like config | {{string_flag_example}} |
| **Number** | thresholds, percentages, limits (integers/floats where the language differentiates) | {{number_flag_example}} |
| **Object / Structure** | grouped config payloads | {{object_flag_example}} |

**Default-value discipline:** every evaluation call passes a hardcoded, type-correct *default
value* that is returned on any abnormal execution (Requirement 1.4.10). Defaults for
{{project_name}} are chosen so the safe/off path is the fallback: {{default_value_policy}}.

## 📞 Evaluation API

Application code evaluates flags through the client's typed methods. **Value methods** return
the resolved value directly; **detail methods** return a `FlagEvaluationDetails` structure with
the evaluation metadata. Per Requirement 1.4.10, *flag evaluation calls MUST always return the
`default value` in the event of abnormal execution* — evaluation never throws.

| Value method | Detail method |
|---|---|
| `getBooleanValue(flagKey, defaultValue, [context], [options])` | `getBooleanDetails(...)` |
| `getStringValue(flagKey, defaultValue, [context], [options])` | `getStringDetails(...)` |
| `getNumberValue(flagKey, defaultValue, [context], [options])` | `getNumberDetails(...)` |
| `getObjectValue(flagKey, defaultValue, [context], [options])` | `getObjectDetails(...)` |

**`FlagEvaluationDetails` fields** (returned by the detail methods):
`value`, `flagKey`, `variant`, `reason`, `errorCode`, `errorMessage`, `flagMetadata`.

**Standard `reason` values** {{project_name}} relies on for decision logic / observability
(spec §Flag Evaluation):

| Reason | Meaning |
|---|---|
| `STATIC` | resolved from a static, context-free configuration |
| `DEFAULT` | the flag's configured default rule applied (no targeting matched) |
| `TARGETING_MATCH` | a targeting rule matched the evaluation context |
| `SPLIT` | resolved via a pseudorandom/percentage split |
| `CACHED` | served from the provider's cache |
| `DISABLED` | the flag is disabled in the management system |
| `STALE` | the value may be outdated (provider is in STALE state) |
| `UNKNOWN` | reason unknown |
| `ERROR` | abnormal execution; see `errorCode` |

**Standard `errorCode` values** the code handles (spec §Flag Evaluation):
`PROVIDER_NOT_READY`, `PROVIDER_FATAL`, `FLAG_NOT_FOUND`, `PARSE_ERROR`, `TYPE_MISMATCH`,
`TARGETING_KEY_MISSING`, `INVALID_CONTEXT`, `GENERAL`.

**Detail-vs-value usage rule for {{project_name}}:** {{detail_method_policy}}
*(e.g. "use `*Details` wherever the `reason`/`variant` feeds analytics or branching; use the
plain value method for simple on/off gates.")*

## 🧭 Evaluation Context & Targeting

The **evaluation context** carries the data targeting rules evaluate against. Per the spec, it
*MUST define an optional `targeting key` field of type string, identifying the subject of the
flag evaluation*, and *MUST support custom fields* with values of type
`boolean | string | number | datetime | structure`.

| Field | Value for {{project_name}} |
|---|---|
| `targetingKey` | {{targeting_key}} (the subject — e.g. user id, org id, device id) |
| Custom attributes used for targeting | {{targeting_attributes}} |
| Where context is assembled | {{context_assembly}} |

**Context-level merge order.** OpenFeature merges context from up to five levels, *with
duplicate values being overwritten* in this precedence (lowest → highest):

```
API (global) → transaction → client → invocation → before-hooks
```

For {{project_name}}: {{context_level_mapping}}
*(state what lives at each level — e.g. "static service attributes at API/global; the
per-request user at transaction level via a transaction-context propagator; ad-hoc overrides
at invocation level.")*

> **Privacy note.** The evaluation context often contains user identifiers and attributes that
> reach the provider. Send only what targeting requires ({{context_data_minimization}}), and
> confirm the provider's data-handling terms align with this project's privacy obligations.

## 🪝 Hooks

Hooks add cross-cutting behavior around evaluation without touching call sites. OpenFeature
defines four stages (spec §Hooks):

| Stage | When it runs | Typical use in {{project_name}} |
|---|---|---|
| **before** | before flag resolution; *MAY* mutate/augment the evaluation context | {{before_hook_use}} |
| **after** | after a successful resolution; receives the evaluation details | {{after_hook_use}} |
| **error** | when the before stage, after stage, or resolution errors | {{error_hook_use}} |
| **finally** | unconditionally, after before/after/error | {{finally_hook_use}} |

**Execution order:** `before` hooks run **API → Client → Invocation → Provider**;
`after` / `error` / `finally` run in **reverse** (Provider → Invocation → Client → API).
The **hook context** exposes the flag key, flag value type, evaluation context, default value,
and mutable hook data (flag key, flag type, and default value are immutable). **Hook hints** may
pass arbitrary read-only data into hooks.

**Hooks registered for {{project_name}}** (and at which level — API / client / invocation / provider):

| Hook | Level | Purpose |
|---|---|---|
| {{hook_1_name}} | {{hook_1_level}} | {{hook_1_purpose}} |
| {{hook_2_name}} | {{hook_2_level}} | {{hook_2_purpose}} |
| {{additional_hooks}} | … | … |

## 📡 Provider Lifecycle & Events

The provider exposes `initialize` (called on registration, accepts the global evaluation
context) and `shutdown` (graceful resource disposal). Its status moves through lifecycle states
surfaced as **provider events** (spec §Events):

| Event | Provider status | What {{project_name}} does on it |
|---|---|---|
| `PROVIDER_READY` | `READY` | {{on_ready}} |
| `PROVIDER_ERROR` | `ERROR` or `FATAL` | {{on_error}} |
| `PROVIDER_CONFIGURATION_CHANGED` | (no state change) | {{on_config_changed}} |
| `PROVIDER_STALE` | `STALE` | {{on_stale}} |
| `PROVIDER_RECONCILING` / `PROVIDER_CONTEXT_CHANGED` | (static-context only) | {{on_reconciling}} |

`NOT_READY` is the status before `initialize` completes (evaluations during it return
`PROVIDER_NOT_READY` → the default value). `FATAL` is unrecoverable. The `provider event details`
payload carries the `provider name` (required), an optional `error message`, `error code`, and a
list of changed `flag keys`. Readiness-gating strategy for {{project_name}}: {{readiness_policy}}.

## 📊 Tracking & Experimentation

> Include this section only when `feature_flags.experimentation` is set. Tracking *associates
> feature flag evaluations with subsequent actions or application states, to facilitate
> experimentation and analysis of the impact of feature flags on business objectives.*

OpenFeature's **Tracking API** records business/conversion events that can be correlated with
flag exposures:

- **Signature:** `client.track(eventName, evaluationContext, trackingEventDetails)` (dynamic-context)
  or `client.track(eventName, trackingEventDetails)` (static-context). All parameters except the
  event name are optional; `track` returns nothing.
- **`trackingEventDetails`** defines an optional numeric **`value`** (a scalar associated with the
  event) plus custom fields (`boolean | string | number | structure`).

| Experimentation aspect | Decision for {{project_name}} |
|---|---|
| Experiment platform | {{experiment_platform}} |
| Exposure logging | {{exposure_logging}} — how a flag evaluation is recorded as an exposure (often an `after` hook) |
| Tracked conversion events | {{tracked_events}} |
| Metric ↔ flag attribution | {{metric_attribution}} |
| Statistical / rollout decision rule | {{rollout_decision_rule}} |

## 🗂️ Flag Catalog & Naming

| Convention | Decision |
|---|---|
| Naming scheme | {{flag_naming_convention}} (e.g. `kebab-case`, dot-namespaced by domain) |
| Source of truth for flag definitions | {{flag_source_of_truth}} |
| Required metadata per flag (owner, type, expiry, jira/ADR) | {{flag_metadata_policy}} |

**Initial flag catalog** (seed; keep current as flags are added/retired):

| Flag key | Type | Purpose | Owner | Default | Expiry / cleanup date |
|---|---|---|---|---|---|
| {{flag_1_key}} | {{flag_1_type}} | {{flag_1_purpose}} | {{flag_1_owner}} | {{flag_1_default}} | {{flag_1_expiry}} |
| {{flag_2_key}} | {{flag_2_type}} | {{flag_2_purpose}} | {{flag_2_owner}} | {{flag_2_default}} | {{flag_2_expiry}} |
| {{additional_flags}} | … | … | … | … | … |

## ♻️ Flag Lifecycle & Cleanup

Flags are debt. A release/experiment flag that outlives its purpose becomes a permanent
branch in the code and a stale targeting rule in the backend. Define the discipline:

- **Flag classification:** {{flag_classification}} — short-lived (release/experiment) vs.
  long-lived (operational/permission). Short-lived flags get an expiry date at creation.
- **Cleanup trigger:** {{cleanup_trigger}} — what marks a flag for removal (experiment concluded,
  100% rollout reached, expiry date passed) and who is alerted.
- **Removal procedure:** {{removal_procedure}} — remove the call site + the dead branch, then
  archive the flag in the backend. Order matters: retire code before the flag definition.
- **Stale-flag audit:** {{stale_flag_audit}} — cadence and tooling (linter, provider report) that
  surfaces flags past expiry or stuck at 0%/100%.

## 🛡️ Failure Modes & Defaults

Because evaluation never throws and always falls back to the supplied default, the *default
value* is your last line of defense. Specify the resilient behavior:

- **Default-value safety:** {{default_safety}} — every default routes to the safe/off path so a
  provider outage degrades to known-good behavior.
- **Provider-down behavior:** {{provider_down_behavior}} — what happens when the provider is
  `NOT_READY` / `ERROR` / `FATAL` (serve defaults; alarm; optionally serve a cached snapshot).
- **Caching / offline mode:** {{caching_policy}} — local cache, bootstrap file, or last-known-good
  snapshot so the app starts even if the backend is unreachable (and how `CACHED`/`STALE` reasons
  are treated).
- **Timeout & latency budget:** {{eval_timeout}} — initialization and evaluation timeouts so a
  slow provider can't block the request path.
- **Observability:** {{flag_observability}} — what gets logged/metered per evaluation (`reason`,
  `errorCode`, latency), wired via an `after`/`error`/`finally` hook.

## 🧪 Local Development & Testing

- **Local provider:** {{local_dev_provider}} — how flags resolve in dev/test (in-memory provider,
  flagd in a container, a static JSON file). OpenFeature ships an in-memory provider ideal for
  deterministic tests.
- **Test strategy:** {{flag_test_strategy}} — override flag values per test, assert both branches
  of every gate, and verify the default-on-error path.
- **CI / preview environments:** {{ci_flag_config}} — how flag state is seeded for CI and preview
  deployments so behavior is reproducible.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
