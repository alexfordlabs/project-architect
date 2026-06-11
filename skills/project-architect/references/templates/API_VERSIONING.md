---
template_name: API_VERSIONING
generate_when: "conditional"
required_decisions: [api.enabled, api.public]
optional_decisions:
  - api.protocol
  - api.style
  - api.sdks
  - api.consumers
  - api.deprecation_policy
depends_on: []
revision_triggers:
  - api.enabled
  - api.public
  - api.protocol
  - api.style
  - api.deprecation_policy
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# API Versioning Strategy: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document defines how the **public** API of {{project_name}} evolves without breaking the integrations that depend on it. It is modelled on **[Stripe's API versioning approach](https://docs.stripe.com/api/versioning)** — the industry reference for shipping breaking changes to a large, long-lived consumer base while keeping every existing integration working. The central commitment Stripe makes, and the one this document adapts for {{project_name}}, is: **a pinned version never changes behavior under a consumer's feet.** New behavior (including breaking changes) is opt-in; consumers upgrade on their own schedule. If {{project_name}} adopts a different model (semantic-version path prefixes, header-negotiated content types, or no versioning at all), state that in [Versioning Model](#versioning-model) and adapt the rest of this document accordingly.

## Table of contents
- [Versioning Model](#versioning-model)
- [Version Identifier Format](#version-identifier-format)
- [Version Selection — Pinning & Override](#version-selection--pinning--override)
- [Compatibility Contract](#compatibility-contract)
- [Backward-Compatible vs Breaking Changes](#backward-compatible-vs-breaking-changes)
- [Release Trains & Cadence](#release-trains--cadence)
- [SDK Pinning](#sdk-pinning)
- [Webhook / Event Versioning](#webhook--event-versioning)
- [🔐 Deprecation & Sunset Policy](#deprecation--sunset-policy)
- [Upgrade Path for Consumers](#upgrade-path-for-consumers)
- [Internal Implementation](#internal-implementation)
- [Documentation & Changelog](#documentation--changelog)
- [↻ Revision Log](#revision-log)

## Versioning Model
The versioning strategy {{project_name}} commits to, and *why*. Choose one and justify it against the cited ADR:

- **Date-based version pinning (Stripe model)** — a single rolling API surface; each consumer is pinned to a dated version; breaking changes ship as a new dated version that nobody is auto-migrated onto. Best for a public API with many long-lived external integrations.
- **URI / path versioning** (`/v1/`, `/v2/`) — coarse-grained major versions in the path. Simple and cache-friendly, but every breaking change forces a whole new major.
- **Header / media-type negotiation** (`Accept: application/vnd.{{api_media_type}}.v2+json`) — version negotiated per request via content type.
- **No versioning** — only valid for an internal or private API. If `api.public` is false this document should not have been generated; confirm the decision.

{{project_name}} uses **{{versioning_model}}**. The rest of this document assumes the date-based pinning model unless that field says otherwise; rewrite the affected sections if a different model was chosen.

## Version Identifier Format
Stripe identifies versions as `YYYY-MM-DD.releasename` — for example the current `2026-05-27.dahlia`: a release date plus the name of the major release train it belongs to. The date makes ordering unambiguous; the suffix groups every backward-compatible monthly release under the major train that introduced it.

For {{project_name}}, the version identifier format is **{{version_identifier_format}}** (e.g. `{{version_identifier_example}}`). Define precisely:

- The canonical string format and an example.
- Whether the suffix names a release train (recommended) or is omitted.
- The collation/ordering rule used to compare two versions.
- The reserved name of the very first published version: **{{initial_version}}**.

## Version Selection — Pinning & Override
Following Stripe, a request resolves its version from two layers, request-level winning over account-level:

1. **Account / API-key default.** Each consumer (API key, account, or token) has a pinned default version, set once and applied to every request and event unless overridden. New keys default to the version current **at the time the key was first used** — never silently advanced. For {{project_name}}, the default is configured via **{{version_config_surface}}** (e.g. a dashboard/Workbench-equivalent, an account setting, or first-request capture).
2. **Per-request override.** A consumer overrides the account default on a single call by sending the **`{{version_header_name}}`** request header (Stripe's is `Stripe-Version`), value `{{version_identifier_example}}`. Per Stripe's semantics, objects returned by an overridden request reuse that same version for any follow-on method calls.

Document for {{project_name}}:

- Exact request header name and accepted value(s): **`{{version_header_name}}: {{version_identifier_example}}`**.
- How the CLI / tooling overrides the default (Stripe uses a `stripe-version` argument).
- The resolution precedence (request header → account default → server-rejects-or-falls-back-to-{{fallback_version}}).
- Whether an unknown/unsupported requested version is **rejected with `{{unknown_version_status}}`** (recommended) or silently coerced.

## Compatibility Contract
The promise that makes pinning safe. State it explicitly:

> A request pinned to version **V** receives **V's** behavior — request parsing, response shape, field semantics, enum values, error codes, and event payloads — for as long as **V** is supported. New behavior is delivered only by pinning to a newer version.

Capture the supported-version window: {{project_name}} supports **{{supported_version_window}}** (e.g. "every version since {{oldest_supported_version}}", or "the latest N major trains"). List any exceptions where behavior *does* change under a pinned version (security fixes, legally-mandated changes, abuse mitigation) — keep this list short and auditable.

## Backward-Compatible vs Breaking Changes
The line between a change that can ship to *every* pinned version and one that requires a *new* version. Per Stripe's [upgrade guide](https://docs.stripe.com/upgrades), the following are **backward-compatible** and ship without a version bump — consumers must tolerate them:

| Backward-compatible change | Consumer obligation |
|---|---|
| Adding a new API resource / endpoint | Ignore unrecognized resources |
| Adding a new **optional** request parameter | n/a |
| Adding a new property to an existing response | Ignore unknown response fields (do not fail on extra keys) |
| Changing the **order** of properties in a response | Do not depend on field order |
| Changing the length or format of opaque strings (object IDs, error messages) — including adding/removing fixed prefixes like `{{id_prefix_example}}` | Store IDs as variable-length strings; **do not parse** them. Stripe IDs can be up to **255 characters** — size columns accordingly (e.g. `VARCHAR(255)`) |
| Adding a new event type | Webhook handlers must gracefully ignore unfamiliar event types |
| Adding a new value to an existing enum *(declare your policy — Stripe's enumerated list does not cover this case; if you treat it as compatible, consumers must default-case unknown enum values)* | Handle unknown enum values via a default branch |

A change is **breaking** — and therefore requires a new version / release train — when it is the inverse of the above, for example:

- Removing or renaming a resource, endpoint, parameter, or response property.
- Making a previously optional parameter **required**.
- Changing the type, semantics, units, or default of an existing field.
- Removing or repurposing an enum value or error code.
- Changing pagination, authentication, or error-envelope structure.

{{project_name}}'s authoritative classification rules: **{{breaking_change_policy}}**. When in doubt, treat it as breaking.

## Release Trains & Cadence
Stripe ships **major** releases (named trains, e.g. *Acacia*, *Dahlia*) that may contain breaking changes, and **monthly** releases that reuse the current major's name and contain **only** backward-compatible changes. A consumer never lands on a new major automatically.

For {{project_name}}:

- Major-release cadence and naming scheme: **{{major_release_cadence}}** (trains named {{release_train_scheme}}).
- Minor/monthly cadence (backward-compatible only): **{{minor_release_cadence}}**.
- Who approves promoting a change set into a new major train, and the freeze/QA gate before it ships: {{release_governance}}.
- Where the canonical "current version" is published: {{current_version_publish_location}}.

## SDK Pinning
Stripe's modern SDKs are pinned to the API version that was current **at the SDK's release time** — upgrading the SDK is how you move the version, and the SDK exposes an override property (`Stripe.api_version` / `apiVersion` init option / `StripeConfiguration.ApiVersion`, etc.). Strongly-typed SDKs (Java, Go, .NET) are fixed to one version per release so the generated types always match the wire format.

Document {{project_name}}'s SDK story:

- Languages with first-party SDKs: {{sdk_languages}}.
- How each SDK pins its version (compiled-in constant vs runtime override): {{sdk_pinning_mechanism}}.
- The override surface consumers use to test a newer version without changing their account default: {{sdk_version_override}}.
- Type-safety guarantee: whether typed SDKs are locked to exactly one version (recommended for {{api_style}}).

## Webhook / Event Versioning
Stripe versions event payloads independently: each webhook endpoint is stamped with the API version chosen **at endpoint-creation time** (falling back to the account default), so the event JSON a consumer receives matches the shape they integrated against. SDK-pinned consumers are advised to **match the endpoint's API version to the version their SDK targets**.

For {{project_name}} (omit if no async/event/webhook surface — `{{has_webhooks}}`):

- How an endpoint's payload version is chosen and stored: {{webhook_version_binding}}.
- The header/field that stamps the delivered version onto each event: {{event_version_field}}.
- The rule that handlers must ignore unknown event types (per the compatibility contract).
- How a consumer upgrades an endpoint's payload version safely (parallel endpoint → cut over).

## 🔐 Deprecation & Sunset Policy
A version cannot be supported forever; the policy makes retirement predictable and non-hostile.

- **Minimum support window** for any published version before it can be sunset: **{{min_support_window}}**.
- **Advance-notice period** before a sunset takes effect: **{{deprecation_notice_period}}**.
- **In-band signalling**: deprecated versions return a **`{{deprecation_header}}`** header (consider the RFC 8594 `Sunset` header and a `Deprecation` header with the cutoff date) so consumers detect impending retirement programmatically.
- **Communication channels**: {{deprecation_channels}} (dashboard banner, email to integration owners, changelog, status page).
- **Sunset behavior**: what a request pinned to a retired version receives — hard `{{sunset_status}}` error vs forced-upgrade to {{forced_upgrade_target}}.
- **Security exception**: a version may be patched-in-place or sunset early for an active vulnerability ({{security_sunset_policy}}).

## Upgrade Path for Consumers
The Stripe-style upgrade is **test-then-commit**: a consumer pins a single test request to the new version (via the override header / SDK property), validates their integration against the new shape, then changes their account default. Document the {{project_name}} equivalent:

1. Read the version-changelog entry for the target version (what broke).
2. Override a non-production request to the target version using `{{version_header_name}}`.
3. Run the integration's test suite against the new shape.
4. Promote the account default via {{version_config_surface}}.
5. Re-version any webhook endpoints to match.

Provide the migration-guide location: {{migration_guide_location}}.

## Internal Implementation
How the server actually serves multiple versions from one codebase. Recommended pattern (Stripe's): keep the data model and core logic at **head**, and apply ordered, composable **request/response transformers** that translate between the head shape and each historical version. Document:

- The version-resolution middleware (where `{{version_header_name}}` is parsed and the effective version bound to the request context): {{version_middleware}}.
- The transformer/shim registry — one transform per breaking change, chained from the requested version up to head: {{transform_strategy}}.
- How transforms are tested (a fixture per version × endpoint is recommended): {{version_test_strategy}}.
- The single source of truth for the version list and ordering: {{version_registry_location}}.
- How a new breaking change is added: write the head change + the inverse transform + the new version registry entry + the changelog, in one change.

## Documentation & Changelog
Per-version transparency is part of the contract:

- A machine- and human-readable **version changelog** that lists, for each version, every backward-compatible and breaking change: {{changelog_location}}.
- Versioned API reference docs (the published reference reflects {{docs_default_version}} with a version switcher).
- The OpenAPI / schema artifact per version (if `{{has_openapi}}`): {{openapi_location}}.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
