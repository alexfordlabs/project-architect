---
template_name: SECURITY_AND_COMPLIANCE
generate_when: "decisions.auth.enabled == true OR decisions.constraints.includes('regulated')"
required_decisions: []
optional_decisions: [security.*, regulatory.*, project.constraints]
depends_on: [AUTHENTICATION_SYSTEM, DATABASE_DESIGN]
revision_triggers: [security.*, regulatory.*, auth.provider, database.engine]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Security and Compliance: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🔐 Threat Model](#threat-model)
- [Regulatory Requirements](#regulatory-requirements)
- [🗄️ Data Classification](#data-classification)
- [Encryption](#encryption)
- [Secret Management](#secret-management)
- [Input Validation & Sanitization](#input-validation-sanitization)
- [🔐 Dependency Security](#dependency-security)
- [Access Control](#access-control)
- [Privacy](#privacy)
- [Incident Response](#incident-response)
- [🔐 Compliance Checklist](#compliance-checklist)
- [↻ Revision Log](#revision-log)

## 🔐 Threat Model
High-level summary: what we protect, who the adversaries are, and what trust boundaries exist. Defer formal STRIDE/PASTA work to THREAT_MODEL.md when generated.

## Regulatory Requirements
Specific obligations per regulation that applies (GDPR / HIPAA / PCI-DSS / SOC2 / CCPA / DPDP). One bullet block per regulation listing concrete controls demanded.

## 🗄️ Data Classification
Table: data category | sensitivity | examples | handling rules. Drives encryption, retention, and access decisions downstream.

## Encryption
In-transit (TLS version, HSTS, cipher policy), at-rest (algorithm, KMS provider, key-rotation cadence), end-to-end if applicable, and post-quantum readiness if applicable.

## Secret Management
Where secrets live (Vercel env, AWS Secrets Manager, Infisical, Doppler, 1Password), rotation policy, and the developer access model.

## Input Validation & Sanitization
Validation library (Zod / Valibot / Pydantic / class-validator), where validation runs (edge / app / DB), and the policy for untrusted input (file uploads, URLs, HTML rendering).

## 🔐 Dependency Security
Automated scanning tooling (Dependabot / Renovate / Snyk / Socket / npm audit), vulnerability SLA, and the policy for accepting/blocking advisories.

## Access Control
How access is granted, reviewed, and revoked for production systems. Reference AUTHENTICATION_SYSTEM.md for the end-user model; this section is about operator access.

## Privacy
Data collected, retention windows per category, deletion/export workflows (GDPR Art. 15/17 equivalents), cookie/consent policy, and analytics scope.

## Incident Response
High-level outline: detection, triage, containment, notification. Link to RUNBOOK.md and INCIDENT_RESPONSE.md for the operational detail.

## 🔐 Compliance Checklist
Concrete checklist mapping each applicable regulation/standard to implemented controls. Used during audits.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
