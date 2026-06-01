---
template_name: AUTHENTICATION_SYSTEM
generate_when: "decisions.auth.enabled == true"
required_decisions: [auth.provider, auth.methods, auth.session_strategy]
optional_decisions: [auth.oauth_providers, auth.multi_tenancy, auth.mfa, auth.password_policy]
depends_on: []
revision_triggers: [auth.provider, auth.methods, auth.session_strategy, auth.multi_tenancy, auth.mfa]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Authentication System: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🔐 Auth Provider](#auth-provider)
- [🔐 Authentication Methods](#authentication-methods)
- [🔐 Auth Flow Diagrams](#auth-flow-diagrams)
- [Session Management](#session-management)
- [🔐 Authorization Model](#authorization-model)
- [Multi-Tenancy](#multi-tenancy)
- [🔐 OAuth Providers](#oauth-providers)
- [MFA](#mfa)
- [🔐 Security Considerations](#security-considerations)
- [🔧 Implementation Packages](#implementation-packages)
- [↻ Revision Log](#revision-log)

## 🔐 Auth Provider
Chosen provider (e.g. Clerk, Auth0, Supabase Auth, custom) and one-paragraph rationale. Cite the ADR that recorded this decision.

## 🔐 Authentication Methods
List of methods enabled (email/password, OAuth providers, magic links, passkeys, MFA), with one-line description each.

## 🔐 Auth Flow Diagrams
Sign-up, sign-in, and password-reset flows. Mermaid sequence diagrams or ASCII art showing the actors (browser, app, auth provider, DB) and message order.

## Session Management
Strategy (JWT / opaque session / cookie), token storage (httpOnly cookie / localStorage / native keychain), session duration, refresh policy, concurrent-session rules.

## 🔐 Authorization Model
Pattern used (RBAC / ABAC / simple boolean roles), the canonical role list, and the permissions each role grants. Reference the source-of-truth location (DB table, policy file, IdP rules).

## Multi-Tenancy
Tenant isolation model (per-row / per-schema / per-DB), how tenants are identified (subdomain / header / JWT claim), and tenant-switching rules. Omit this section if `auth.multi_tenancy` is not set.

## 🔐 OAuth Providers
List of OAuth/OIDC providers wired in, the scopes requested from each, and the redirect-URI conventions.

## MFA
Second-factor methods enabled (TOTP / passkeys / SMS / email codes), the enrollment flow, and the recovery-code policy.

## 🔐 Security Considerations
Password hashing algorithm and parameters, rate limits and lockout thresholds, CSRF defenses, token-rotation policy, and session-fixation protections.

## 🔧 Implementation Packages
Specific SDKs, libraries, and middleware (with versions) used to implement the above — frontend, backend, and edge.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
