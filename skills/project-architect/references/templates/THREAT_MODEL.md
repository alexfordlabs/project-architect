---
template_name: THREAT_MODEL
generate_when: "decisions.constraints.includes('regulated') OR decisions.security.formal_threat_model == true OR decisions.project.type == 'web3'"
required_decisions: []
optional_decisions: [threat_model.framework]
depends_on: [SECURITY_AND_COMPLIANCE]
revision_triggers: [project.type, security.*, regulatory.*]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Threat Model: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Assets](#assets)
- [🔐 Adversary Model](#adversary-model)
- [🔐 Trust Boundaries](#trust-boundaries)
- [🔐 STRIDE / PASTA Walkthrough](#stride-pasta-walkthrough)
- [🔐 Top Threats](#top-threats)
- [🔐 Mitigations](#mitigations)
- [🔐 Residual Risk](#residual-risk)
- [↻ Revision Log](#revision-log)

## Assets
What we're protecting, ranked by impact: user PII, payment data, credentials, intellectual property, availability of the service itself, brand / trust, regulatory standing. Each asset gets a CIA rating (Confidentiality / Integrity / Availability) so trade-offs are explicit.

## 🔐 Adversary Model
Subsections per adversary class: opportunistic attacker, motivated attacker (financial), insider (malicious or compromised), state actor (only if applicable), supply-chain attacker, and accidental misuse by trusted users. For each: capabilities, motivations, resources, and whether they're in scope.

## 🔐 Trust Boundaries
Diagram (Mermaid or external) showing every component, the data flowing between them, and a labeled boundary wherever data crosses a trust zone (browser ↔ edge, edge ↔ origin, app ↔ database, app ↔ third-party). Each boundary is later enumerated in the STRIDE walkthrough.

## 🔐 STRIDE / PASTA Walkthrough
Per component, walk through the chosen framework (default STRIDE: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege). Document threats found, even those rated low, so future revisions can re-evaluate.

## 🔐 Top Threats
Ranked list of the most material threats discovered, scored by likelihood × impact (or DREAD / CVSS if a quantitative model is preferred). The top N drive the mitigation roadmap.

## 🔐 Mitigations
Table: threat ID | mitigation | control type (preventive / detective / responsive) | owner | status (planned / shipped / verified). Every top threat must map to at least one control.

## 🔐 Residual Risk
Threats that cannot be fully mitigated and the explicit risk-acceptance decision (who, when, expiry). Included so auditors and future maintainers can challenge / revisit instead of rediscovering.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
