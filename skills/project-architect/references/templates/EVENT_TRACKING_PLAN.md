---
template_name: EVENT_TRACKING_PLAN
generate_when: "conditional"
required_decisions:
  - analytics.enabled
optional_decisions:
  - analytics.provider
  - analytics.casing_convention
  - analytics.governance_owner
  - analytics.enforcement
  - analytics.id_strategy
  - analytics.consent
depends_on: []
revision_triggers:
  - analytics.enabled
  - analytics.provider
  - analytics.casing_convention
  - analytics.enforcement
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Event Tracking Plan: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the central, source-of-truth tracking plan for **{{project_name}}**. Its naming
> conventions follow Twilio Segment's
> *[Naming conventions for clean data](https://www.twilio.com/en-us/resource-center/naming-conventions-for-clean-data)*;
> the call-type, identity-envelope, and reserved-event sections below draw on the broader
> [Segment Spec](https://segment.com/docs/connections/spec/) that that guidance assumes.
> The governing principle from the conventions guidance: **"The only thing that really matters
> is that you keep it consistent!"** — pick one framework, document it here, and enforce it
> everywhere. Document conventions "in a centralized tracking plan that defines every event,
> property, and data type your organization uses," shared across engineering, product, and
> analytics teams so everyone implements tracking the same way.

## Table of contents
- [📐 Conventions (the rules, agreed once)](#conventions-the-rules-agreed-once)
- [🧱 Object-Action Framework](#object-action-framework)
- [📞 API Call Types Used](#api-call-types-used)
- [🆔 Identity & Common Fields](#identity-common-fields)
- [📊 Event Catalog](#event-catalog)
- [🧩 Shared Property Dictionary](#shared-property-dictionary)
- [🛒 Semantic / Reserved Events](#semantic-reserved-events)
- [🚫 Anti-Patterns to Avoid](#anti-patterns-to-avoid)
- [🛡️ Governance & Enforcement](#governance-enforcement)
- [🔒 Consent & PII](#consent-pii)
- [↻ Revision Log](#revision-log)

## 📐 Conventions (the rules, agreed once)

Per Segment, the one-time decisions below bind the entire organization. Record the choice and
*never deviate* — duplicate variations (`Sign Up`, `signup`, `signed up`, `User Signed Up` for
the same action) are the single most common cause of dirty data.

| Convention | Decision for {{project_name}} | Segment recommendation |
|---|---|---|
| Analytics provider / CDP | `{{analytics_provider}}` | (e.g. Segment, RudderStack, PostHog, Amplitude, GA4) |
| Event-name casing | `{{event_casing}}` | **Proper Case** (e.g. `Product Viewed`) |
| Property-name casing | `{{property_casing}}` | **snake_case** (e.g. `product_id`) |
| Tense | `{{event_tense}}` | either past or present tense (e.g. `Viewed`, `Played`) — Segment allows both *as long as it's consistent* |
| Casing rule | Pick ONE and apply uniformly | "keep it consistent!" |

## 🧱 Object-Action Framework

Segment's recommended naming framework names every event as an **Object** followed by an
**Action**, in the chosen casing.

- **Object** — a key "piece" of the app users interact with (e.g. `Product`, `Cart`,
  `Account`, `Application`, `Subscription`).
- **Action** — how the user interacted with that object, as a verb (e.g. `Viewed`, `Clicked`,
  `Created`, `Favorited`, `Completed`).

**Format:** `Object Action` → e.g. **`Product Viewed`**, **`Account Created`**,
**`Application Installed`**.

**Objects in {{project_name}}:** {{tracked_objects}}
**Actions in {{project_name}}:** {{tracked_actions}}

> A good event name is *specific*: prefer `{{specific_event_example}}` over a vague `Click`
> (which button? which link?). Specificity moves variable data into properties, not the name.

## 📞 API Call Types Used

The Segment Spec defines a small fixed set of call types. State which {{project_name}} uses and
how each is invoked.

| Call type | Captures | Used here? | Notes |
|---|---|---|---|
| `identify` | Who the user is — ties a `userId` to user `traits`. | {{uses_identify}} | Call on sign-in / when traits change. |
| `track` | What the user did — a single discrete action + `properties`. | {{uses_track}} | The workhorse; carries the Object-Action event name. |
| `page` | A web page was viewed (`name`, `category`, `url`). | {{uses_page}} | Web only. |
| `screen` | A mobile screen was viewed (`name`, `category`). | {{uses_screen}} | Mobile only. |
| `group` | Associates a user with an account/org and its `traits`. | {{uses_group}} | B2B / multi-tenant. |
| `alias` | Merges two identities (anonymous → known). | {{uses_alias}} | Rarely needed; provider-specific. |

**Canonical `track` shape** (move variable data out of the name into `properties`):

```js
analytics.track('{{example_event_name}}', {
  {{example_property_key}}: '{{example_property_value}}'
});
// GOOD: analytics.track('Sign Up', { email: 'jake@example.com' })
// BAD : analytics.track('Sign Up - jake@example.com')  // never bake variable data into the name
```

## 🆔 Identity & Common Fields

Every call carries a shared envelope regardless of type. Document the identity strategy and the
common fields {{project_name}} populates.

| Field | Meaning | Decision |
|---|---|---|
| `userId` | Stable, unique known-user id (DB id / UUID — never PII like email). | {{user_id_source}} |
| `anonymousId` | Pre-auth visitor id (auto-generated by the SDK). | {{anonymous_id_strategy}} |
| `timestamp` | When the event occurred (ISO-8601 / UTC). | {{timestamp_policy}} |
| `messageId` | De-dup key for the call. | {{message_id_policy}} |
| `context` | Env metadata: `context.app`, `context.library`, `context.page`, `context.ip`, `context.userAgent`, `context.locale`. | {{context_fields}} |
| `type` | The call type (`track` / `identify` / …). | auto-set by SDK |

**Identity resolution:** {{identity_resolution}} — how anonymous → known is stitched
(`{{anonymous_to_known}}`), and the canonical `userId` source of truth.

## 📊 Event Catalog

The heart of the tracking plan: every event {{project_name}} fires, its trigger, its
properties (with types + required flag). Keep this exhaustive — an undocumented event is an
unenforceable event.

| Event name (`Object Action`) | Fires when | Properties (type · required?) | Owner |
|---|---|---|---|
| `{{event_1_name}}` | {{event_1_trigger}} | {{event_1_properties}} | {{event_1_owner}} |
| `{{event_2_name}}` | {{event_2_trigger}} | {{event_2_properties}} | {{event_2_owner}} |
| `{{event_3_name}}` | {{event_3_trigger}} | {{event_3_properties}} | {{event_3_owner}} |
| {{additional_events}} | … | … | … |

> Per the Object-Action rule, the **same object collects a consistent property set across its
> related events.** Example from Segment: `Product Viewed`, `Product Clicked`, and
> `Product Shared` all carry `category`, `product_id`, `price`, `brand`, `name`, `quantity`,
> `sku`, `size`. Define each object's shared property set in the dictionary below.

## 🧩 Shared Property Dictionary

Properties reused across events — defined ONCE here so the type and casing never drift.
snake_case, one canonical meaning per key.

| Property | Type | Example | Notes / allowed values | Appears on |
|---|---|---|---|---|
| `{{prop_1_key}}` | {{prop_1_type}} | {{prop_1_example}} | {{prop_1_notes}} | {{prop_1_events}} |
| `{{prop_2_key}}` | {{prop_2_type}} | {{prop_2_example}} | {{prop_2_notes}} | {{prop_2_events}} |
| `{{prop_3_key}}` | {{prop_3_type}} | {{prop_3_example}} | {{prop_3_notes}} | {{prop_3_events}} |
| {{additional_properties}} | … | … | … | … |

**Per-object property sets** (the consistent bundle each object carries):

- **{{object_a}}** → {{object_a_properties}}
- **{{object_b}}** → {{object_b_properties}}

## 🛒 Semantic / Reserved Events

If {{project_name}} fits a domain Segment has *specced* (E-Commerce, Video, Mobile, B2B SaaS,
Live Chat), adopt the reserved Object-Action names verbatim — downstream tools (warehouses,
ad destinations) recognise them and pre-build funnels. Do NOT invent synonyms for these.

| Domain spec | Reserved events to reuse | Used by {{project_name}}? |
|---|---|---|
| E-Commerce | `Product Viewed`, `Product Added`, `Cart Viewed`, `Checkout Started`, `Order Completed`, `Order Refunded` | {{uses_ecommerce_spec}} |
| Video | `Video Playback Started`, `Video Content Started`, `Video Playback Completed` | {{uses_video_spec}} |
| Mobile lifecycle | `Application Installed`, `Application Opened`, `Application Updated` | {{uses_mobile_spec}} |
| B2B SaaS | `Account Created`, `Trial Started`, `Subscription Started` | {{uses_saas_spec}} |

**Custom events not covered by a spec:** {{custom_events_rationale}} — name them with the same
Object-Action framework as everything else.

## 🚫 Anti-Patterns to Avoid

Segment's catalogue of mistakes that produce dirty, un-analyzable data. Each maps to a check the
[enforcement layer](#governance-enforcement) should block.

- ❌ **Duplicate variations** of one action — `Sign Up` / `signup` / `signed up` / `User Signed Up`. Choose ONE: `{{canonical_signup_event}}`.
- ❌ **Vague names** — `Click`, `Submit`, `View` with no object. Always name the object.
- ❌ **Inconsistent casing** — mixing `snake_case`, `camelCase`, and `Proper Case` for events.
- ❌ **Dynamic event names** — baking variable data into the name (`Sign Up - jake@example.com`). Move it to a property.
- ❌ **Undocumented events** — an event not in the [Event Catalog](#event-catalog) ships to production.
- ❌ **Re-purposing a property** — the same key meaning two things on different events.

## 🛡️ Governance & Enforcement

A tracking plan is only as clean as its enforcement. Record who owns it and how violations are
caught.

- **Plan owner / approver:** {{governance_owner}} — the single party who approves new events
  before they ship (Segment: share the plan across "engineering, product, and analytics teams").
- **Change process:** {{change_process}} — how a new event is proposed → reviewed → added here →
  implemented (this doc is updated in the *same* change as the code).
- **Enforcement mechanism:** {{enforcement_mechanism}} — e.g. Segment **Protocols** (real-time
  validation against this plan, automated blocking/flagging of non-compliant events, schema
  enforcement of required properties / allowed values / data types, and a violations dashboard),
  or a typed analytics wrapper / Typewriter-style codegen, or CI schema linting.
- **Violation handling:** {{violation_policy}} — block, flag, or route to a dead-letter stream.
- **Source of truth:** this file (committed) + {{plan_storage}} (the live plan in the CDP UI, if
  any) — they must agree; this doc is authoritative when they drift.

## 🔒 Consent & PII

- **Consent gating:** {{consent_policy}} — which calls fire only after consent (GDPR/CCPA),
  and how consent state is read.
- **PII in events:** {{pii_policy}} — never put PII (email, name) in the *event name*; minimize
  PII in properties; record which properties are classified sensitive and their retention.
- **Identifier hygiene:** `userId` is a stable internal id, **not** an email or other PII.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
