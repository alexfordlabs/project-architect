---
template_name: BILLING_AND_PAYMENTS
generate_when: "decisions.monetization.enabled == true"
required_decisions:
  - payments.provider
  - payments.model
optional_decisions:
  - payments.pricing_tiers
  - payments.taxation
  - payments.fraud_prevention
depends_on: []
revision_triggers:
  - payments.provider
  - payments.model
  - payments.pricing_tiers
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Billing & Payments: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Provider & Rationale](#provider-rationale)
- [💰 Pricing Model](#pricing-model)
- [💰 Pricing Tiers Table](#pricing-tiers-table)
- [Checkout Flow](#checkout-flow)
- [🌐 Webhook Handling](#webhook-handling)
- [💰 Refunds & Disputes](#refunds-disputes)
- [💰 Taxation Strategy](#taxation-strategy)
- [Fraud Prevention](#fraud-prevention)
- [Reporting & Reconciliation](#reporting-reconciliation)
- [↻ Revision Log](#revision-log)

## Provider & Rationale
Chosen provider (Stripe, Lemon Squeezy, Paddle, Mollie, etc.) with rationale, citing the ADR. Cover region coverage, supported payment methods, payout speed, and merchant-of-record vs direct-merchant trade-offs.

## 💰 Pricing Model
Which billing model applies (one-time, subscription, usage-based, tiered, hybrid) and how it maps to the product surface. Note any plan migrations or grandfathering rules.

## 💰 Pricing Tiers Table
Table: tier name | included quotas | overage rules | price (monthly/annual) | target persona. Pulled from `payments.pricing_tiers`.

## Checkout Flow
Step-by-step user journey from price selection to confirmation: hosted vs embedded checkout, supported wallets/cards, address & tax collection, abandonment recovery.

## 🌐 Webhook Handling
Provider → app webhook contract: events consumed, signing verification, idempotency keys, retry behaviour. Link to `THIRD_PARTY_INTEGRATIONS.md`.

## 💰 Refunds & Disputes
Refund policy windows, partial vs full refunds, dispute/chargeback workflow, evidence collection, escalation paths.

## 💰 Taxation Strategy
Sales tax / VAT / GST handling: provider-managed (Stripe Tax, Paddle MoR) vs in-house TaxJar/Avalara, reverse-charge rules, invoice/receipt compliance.

## Fraud Prevention
Risk tooling (Stripe Radar, Sift, Signifyd), velocity rules, 3DS enforcement, manual review queues, blocklists.

## Reporting & Reconciliation
MRR/ARR dashboards, revenue recognition, accounting export (Stripe → QuickBooks/NetSuite), reconciliation cadence.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
