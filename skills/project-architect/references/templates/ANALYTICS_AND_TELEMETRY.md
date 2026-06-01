---
template_name: ANALYTICS_AND_TELEMETRY
generate_when: "decisions.analytics.enabled == true"
required_decisions: [analytics.product]
optional_decisions: [analytics.event_schema, analytics.privacy_policy, analytics.consent_management]
depends_on: []
revision_triggers: [analytics.product, analytics.event_schema, analytics.consent_management]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Analytics and Telemetry: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [📊 Product Analytics Provider](#product-analytics-provider)
- [Event Taxonomy](#event-taxonomy)
- [🗄️ Event Schema Conventions](#event-schema-conventions)
- [Identification Strategy](#identification-strategy)
- [Privacy & Consent](#privacy-consent)
- [Funnels & Cohorts of Interest](#funnels-cohorts-of-interest)
- [📊 Dashboards](#dashboards)
- [↻ Revision Log](#revision-log)

## 📊 Product Analytics Provider
Provider chosen (PostHog / Amplitude / Mixpanel / Segment + warehouse / Snowplow) with one-paragraph rationale, ADR link, data-residency choice, retention defaults, and the SDKs in use (web / mobile / server). Note any second tool used in parallel (e.g., a warehouse-first pipeline alongside a product-analytics tool) and why.

## Event Taxonomy
The canonical event list grouped by domain (auth, onboarding, core action, billing, retention). For each event note: name, when it fires, who fires it (client / server), and its lifecycle stage (active / deprecated). Reference the source of truth (tracking plan doc, Avo / Iteratively schema, or a versioned JSON file in the repo).

## 🗄️ Event Schema Conventions
Naming convention (e.g., `domain.object_action`, snake_case vs camelCase), the required property set for every event (timestamp, user_id, session_id, app_version, environment), allowed property types, and the deprecation flow for renaming or removing a property. Include an example event payload.

## Identification Strategy
Anonymous-id vs identified-user lifecycle: when an anonymous id is generated, the alias/identify step on login, how multi-device users are unified, the policy on identifying minors, and the rule for not sending PII as event properties. Reference AUTHENTICATION_SYSTEM.md for the identity primitives.

## Privacy & Consent
Lawful basis (consent / legitimate interest), the consent-management implementation (banner, preferences, server-side enforcement), per-jurisdiction differences (GDPR / CCPA / LGPD), the do-not-track behavior, and the data-subject-request flow. Link to SECURITY_AND_COMPLIANCE.md for the broader policy.

## Funnels & Cohorts of Interest
The canonical funnels (signup -> activation -> retention -> referral, plus product-specific funnels) and the cohorts the team monitors (paid plan, weekly-active, churned, expansion candidates). Each entry names the owning team and the review cadence.

## 📊 Dashboards
The set of canonical dashboards (executive, growth, product, reliability, billing) with their owning team, refresh cadence, and the URL/link. Note which dashboards are watched in incident response and which feed business reviews.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
