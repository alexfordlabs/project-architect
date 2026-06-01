---
template_name: API_GATEWAY
generate_when: "decisions.api.enabled == true"
required_decisions: [backend.framework, backend.api_style]
optional_decisions: [backend.versioning, backend.rate_limiting, backend.realtime_protocol, backend.webhooks]
depends_on: [AUTHENTICATION_SYSTEM, DATABASE_DESIGN]
revision_triggers: [backend.framework, backend.api_style, backend.versioning, backend.realtime_protocol]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# API Gateway: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🌐 API Style](#api-style)
- [🌐 Base URL & Versioning](#base-url-versioning)
- [🔐 Authentication & Authorization](#authentication-authorization)
- [🌐 Endpoints / Operations](#endpoints-operations)
- [🔧 Common Patterns](#common-patterns)
- [🌐 Real-Time](#real-time)
- [🌐 API Documentation](#api-documentation)
- [🌐 Webhooks](#webhooks)
- [↻ Revision Log](#revision-log)

## 🌐 API Style
REST / GraphQL / tRPC / RPC choice with one-paragraph rationale and a link to the ADR.

## 🌐 Base URL & Versioning
Base URL pattern (e.g. `api.{{project_name}}.com/v1`), versioning scheme (URL / header / never-break), and deprecation policy.

## 🔐 Authentication & Authorization
How requests are authenticated (bearer token / cookie / mTLS) and authorized. Link to AUTHENTICATION_SYSTEM.md for the full identity model.

## 🌐 Endpoints / Operations
One subsection per resource (or GraphQL type / tRPC router). Each subsection lists operations with: method, path, purpose, request shape, response shape, error codes.

## 🔧 Common Patterns
Pagination (cursor / offset), filtering, sorting, error format (RFC 7807 / custom), rate limiting tiers, and idempotency-key conventions.

## 🌐 Real-Time
Transport (WebSocket / SSE / WebTransport), event schema, and subscription model. Skip this section if no real-time surface.

## 🌐 API Documentation
Source of truth (OpenAPI / GraphQL SDL / tRPC types), where the rendered docs live (Scalar / Redoc / GraphiQL), and how docs stay in sync with code.

## 🌐 Webhooks
Outbound webhook events, payload schema, signing strategy, retry policy. Skip if no outbound webhooks.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
