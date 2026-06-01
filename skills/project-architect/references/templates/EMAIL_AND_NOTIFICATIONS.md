---
template_name: EMAIL_AND_NOTIFICATIONS
generate_when: "decisions.notifications.enabled == true"
required_decisions:
  - notifications.email_provider
optional_decisions:
  - notifications.push_provider
  - notifications.sms_provider
  - notifications.multi_channel_provider
  - notifications.templates_location
depends_on: []
revision_triggers:
  - notifications.email_provider
  - notifications.push_provider
  - notifications.multi_channel_provider
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Email & Notifications: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🎯 Channels Overview](#channels-overview)
- [Transactional Email](#transactional-email)
- [Marketing Email](#marketing-email)
- [Push Notifications](#push-notifications)
- [SMS](#sms)
- [Multi-Channel Orchestration](#multi-channel-orchestration)
- [Templates & Localization](#templates-localization)
- [User Preferences & Unsubscribe](#user-preferences-unsubscribe)
- [Deliverability Strategy](#deliverability-strategy)
- [↻ Revision Log](#revision-log)

## 🎯 Channels Overview
Summary table of every channel in use (email, push, SMS, in-app, webhooks) with provider, primary use case, and ownership.

## Transactional Email
Email provider (Resend, Postmark, SendGrid, SES) plus template strategy: code-defined (React Email, MJML) vs provider-hosted templates, preview/test workflow, sandbox vs live keys.

## Marketing Email
If applicable: marketing-class provider (Customer.io, Loops, Brevo), audience sync from source-of-truth, suppression/list hygiene, separation of marketing and transactional reputations.

## Push Notifications
Per platform: iOS (APNs token strategy, key vs certificate), Android (FCM), Web Push (VAPID), provider abstraction (OneSignal/Knock/Novu) vs direct integration.

## SMS
If applicable: provider (Twilio, MessageBird, Vonage), sender ID/short code/long code strategy, A2P 10DLC registration, opt-in compliance.

## Multi-Channel Orchestration
If applicable: Knock/Novu/Courier as the routing layer, channel priority and fallback, batching/digesting, per-channel rate limits.

## Templates & Localization
Where source templates live (in-repo vs provider), variable conventions, localization pipeline, brand tokens, render testing.

## User Preferences & Unsubscribe
Preferences model (per-channel × per-category), unsubscribe links/list-unsubscribe headers, double opt-in (where required), CAN-SPAM/CASL/GDPR compliance.

## Deliverability Strategy
SPF/DKIM/DMARC records, dedicated IPs vs shared, warm-up plan, bounce/complaint handling, monitoring (Postmaster Tools, Google Postmaster, Bounce/Complaint webhooks).

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
