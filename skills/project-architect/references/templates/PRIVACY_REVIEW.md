---
template_name: PRIVACY_REVIEW
generate_when: "conditional"
required_decisions:
  - constraints.gdpr
  - constraints.ccpa
  - constraints.hipaa
  - personal_data
optional_decisions:
  - data.categories
  - data.special_categories
  - data.subjects
  - data.retention
  - data.residency
  - ai.enabled
  - agent.autonomy
  - scale
  - constraints.regulated
depends_on: []
revision_triggers:
  - constraints.gdpr
  - constraints.ccpa
  - constraints.hipaa
  - personal_data
  - data.categories
  - data.special_categories
  - data.subjects
  - data.retention
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Privacy Review & Data Protection Impact Assessment: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document is the privacy review for {{project_name}}, structured as a **Data Protection Impact Assessment (DPIA)** per **[GDPR Article 35](https://gdpr-info.eu/art-35-gdpr/)** — the authoritative reference for assessing processing that "is likely to result in a high risk to the rights and freedoms of natural persons." Article 35(7) fixes the four-part minimum content of a DPIA; this document follows that structure verbatim, then adds a CCPA/CPRA and HIPAA overlay where those regimes also apply. Even where a full DPIA is **not** legally mandated, this review records the threshold analysis (Art. 35(1) + the [WP248 nine-criteria test](https://ec.europa.eu/newsroom/article29/items/611236)) so the "no DPIA required" verdict is itself documented, not assumed.

## Table of contents
- [⚖️ Applicable Regimes & Scope](#applicable-regimes-scope)
- [🚦 DPIA Threshold Assessment (Art. 35(1), (3))](#dpia-threshold-assessment-art-351-3)
- [🗂️ §1 — Systematic Description of Processing (Art. 35(7)(a))](#1--systematic-description-of-processing-art-357a)
- [🎯 §2 — Necessity & Proportionality (Art. 35(7)(b))](#2--necessity-proportionality-art-357b)
- [⚠️ §3 — Risks to Rights & Freedoms (Art. 35(7)(c))](#3--risks-to-rights-freedoms-art-357c)
- [🛡️ §4 — Measures & Safeguards (Art. 35(7)(d))](#4--measures-safeguards-art-357d)
- [👥 DPO Advice & Data-Subject Views (Art. 35(2), (9))](#dpo-advice-data-subject-views-art-352-9)
- [📞 Prior Consultation (Art. 36)](#prior-consultation-art-36)
- [🇺🇸 CCPA / CPRA Overlay](#ccpa--cpra-overlay)
- [🏥 HIPAA Overlay](#hipaa-overlay)
- [✅ Verdict, Residual Risk & Review Cadence (Art. 35(11))](#verdict-residual-risk-review-cadence-art-3511)
- [↻ Revision Log](#revision-log)

## ⚖️ Applicable Regimes & Scope
State which privacy regimes bind {{project_name}} and why. This frames every section below.

| Regime | Applies? | Basis for applicability |
|---|---|---|
| GDPR (EU/EEA) | {{gdpr_applies}} | EU/EEA data subjects, EU establishment, or offering goods/services to / monitoring EU residents (Art. 3) |
| UK GDPR / DPA 2018 | {{uk_gdpr_applies}} | {{uk_gdpr_basis}} |
| CCPA / CPRA (California) | {{ccpa_applies}} | For-profit business meeting a CPRA threshold (≥ $25M revenue, ≥ 100k consumers/households, or ≥ 50% revenue from selling/sharing PI) |
| HIPAA (US health) | {{hipaa_applies}} | Covered entity or business associate handling Protected Health Information (PHI) |
| Other ({{other_regime}}) | {{other_applies}} | {{other_basis}} |

- **Personal data processed at all?** {{processes_personal_data}} (`personal_data`)
- **Controller / processor / joint-controller role:** {{controller_role}} — and named for each regime where the term differs.
- **Territorial reach:** {{territorial_reach}} — where subjects are and where data is stored/processed (`data.residency`).
- **Data Protection Officer:** {{dpo_designated}} — designated where Art. 37 triggers apply (core-activity large-scale monitoring or special-category processing, or a public authority).

## 🚦 DPIA Threshold Assessment (Art. 35(1), (3))
A DPIA is **mandatory** when processing is likely to result in high risk. Article 35(3) names three per-se triggers; WP248 supplies nine criteria where meeting **two or more** indicates a DPIA should be done. Record the verdict for each before deciding whether a full DPIA is required.

**Art. 35(3) per-se mandatory triggers:**

| Trigger | Present? | Detail |
|---|---|---|
| (a) Systematic & extensive **automated** evaluation/profiling producing legal or similarly significant effects | {{trigger_3a}} | {{trigger_3a_detail}} (cross-ref AI/ML or Agent design if `ai.enabled` / `agent.autonomy`) |
| (b) Large-scale processing of **special categories** (Art. 9) or criminal-offence data (Art. 10) | {{trigger_3b}} | {{trigger_3b_detail}} (`data.special_categories`) |
| (c) **Systematic monitoring** of a publicly accessible area on a large scale | {{trigger_3c}} | {{trigger_3c_detail}} |

**WP248 nine-criteria screen** (two or more ⇒ DPIA expected):

| # | Criterion | Met? |
|---|---|---|
| 1 | Evaluation or scoring (incl. profiling/predicting) | {{wp248_1}} |
| 2 | Automated decision-making with legal/significant effect | {{wp248_2}} |
| 3 | Systematic monitoring | {{wp248_3}} |
| 4 | Sensitive data or data of a highly personal nature | {{wp248_4}} |
| 5 | Data processed on a large scale | {{wp248_5}} |
| 6 | Matching or combining datasets | {{wp248_6}} |
| 7 | Data concerning vulnerable subjects (children, employees, patients) | {{wp248_7}} |
| 8 | Innovative use / new technological or organisational solutions | {{wp248_8}} |
| 9 | Processing that prevents subjects from exercising a right or using a service/contract | {{wp248_9}} |

**Threshold verdict:** {{dpia_required}} — *(Full DPIA required / not required — with the supervisory authority's Art. 35(4)/(5) published list checked: {{authority_list_check}}.)* If a full DPIA is not required, the remainder of this document is completed as a lightweight privacy review; the threshold analysis above remains the record of why.

## 🗂️ §1 — Systematic Description of Processing (Art. 35(7)(a))
A "systematic description of the envisaged processing operations and the purposes of the processing, including, where applicable, the legitimate interest pursued by the controller."

- **Processing purposes:** {{processing_purposes}} — each distinct purpose stated plainly.
- **Lawful basis per purpose (Art. 6):** {{lawful_basis}} — consent / contract / legal obligation / vital interests / public task / legitimate interests. For special categories, the additional Art. 9(2) condition: {{art9_condition}}.
- **Legitimate-interests balancing test** (if relied on): {{lia_summary}}.

**Data inventory (data map):**

| Data category | Examples | Special category? (Art. 9/10) | Source | Subjects | Recipients / processors | Retention |
|---|---|---|---|---|---|---|
| {{cat_1}} | {{cat_1_examples}} | {{cat_1_special}} | {{cat_1_source}} | {{cat_1_subjects}} | {{cat_1_recipients}} | {{cat_1_retention}} |
| {{cat_2}} | {{cat_2_examples}} | {{cat_2_special}} | {{cat_2_source}} | {{cat_2_subjects}} | {{cat_2_recipients}} | {{cat_2_retention}} |
| {{additional_categories}} | … | … | … | … | … | … |

- **Data subjects:** {{data_subjects}} (`data.subjects`) — including any vulnerable groups (children, employees, patients).
- **Data flows:** {{data_flow_summary}} — collection → processing → storage → sharing → deletion (reference the architecture/C4 diagram).
- **International transfers (Ch. V):** {{international_transfers}} — third countries involved and the transfer mechanism (adequacy decision / SCCs + transfer-impact assessment / BCRs / derogation).
- **Retention & deletion (`data.retention`):** {{retention_policy}} — per category, with the trigger and method for erasure.

## 🎯 §2 — Necessity & Proportionality (Art. 35(7)(b))
An "assessment of the necessity and proportionality of the processing operations in relation to the purposes."

- **Necessity:** {{necessity_assessment}} — is each data element actually required to achieve the stated purpose? Could the purpose be met with less data or anonymised/pseudonymised data?
- **Proportionality:** {{proportionality_assessment}} — is the privacy intrusion proportionate to the benefit?
- **Data minimisation (Art. 5(1)(c)):** {{minimisation_measures}} — fields collected vs. fields strictly needed; what was dropped.
- **Storage limitation (Art. 5(1)(e)):** {{storage_limitation}} — retention tied to purpose; no indefinite retention.
- **Accuracy (Art. 5(1)(d)) & purpose limitation (Art. 5(1)(b)):** {{accuracy_purpose}} — no incompatible secondary use without a fresh basis.
- **Data-subject rights enablement (Arts. 12–22):** how each right is technically served:

| Right | Article | How served |
|---|---|---|
| Information / transparency | 13–14 | {{right_information}} |
| Access | 15 | {{right_access}} |
| Rectification | 16 | {{right_rectification}} |
| Erasure ("right to be forgotten") | 17 | {{right_erasure}} |
| Restriction | 18 | {{right_restriction}} |
| Portability | 20 | {{right_portability}} |
| Objection | 21 | {{right_objection}} |
| Not subject to solely-automated decisions | 22 | {{right_automated}} |

## ⚠️ §3 — Risks to Rights & Freedoms (Art. 35(7)(c))
An "assessment of the risks to the rights and freedoms of data subjects" — assessed from the **subject's** perspective, not just the organisation's. Score each risk by likelihood × severity, considering the source, nature, particularity, and gravity of harm.

| # | Risk to subjects | Source / threat | Likelihood | Severity | Inherent risk |
|---|---|---|---|---|---|
| R1 | Unauthorised access / data breach (confidentiality) | {{r1_source}} | {{r1_likelihood}} | {{r1_severity}} | {{r1_inherent}} |
| R2 | Unwanted modification (integrity) | {{r2_source}} | {{r2_likelihood}} | {{r2_severity}} | {{r2_inherent}} |
| R3 | Loss / unavailability of data | {{r3_source}} | {{r3_likelihood}} | {{r3_severity}} | {{r3_inherent}} |
| R4 | Function creep / unlawful secondary use | {{r4_source}} | {{r4_likelihood}} | {{r4_severity}} | {{r4_inherent}} |
| R5 | Re-identification of pseudonymised data | {{r5_source}} | {{r5_likelihood}} | {{r5_severity}} | {{r5_inherent}} |
| R6 | Discrimination / unfair profiling outcomes | {{r6_source}} | {{r6_likelihood}} | {{r6_severity}} | {{r6_inherent}} |
| R7 | {{r7_risk}} | {{r7_source}} | {{r7_likelihood}} | {{r7_severity}} | {{r7_inherent}} |

**Potential harms to subjects:** {{potential_harms}} — physical, material (financial loss, identity theft), and non-material (discrimination, reputational damage, loss of confidentiality, loss of control over personal data).

## 🛡️ §4 — Measures & Safeguards (Art. 35(7)(d))
The "measures envisaged to address the risks, including safeguards, security measures and mechanisms to ensure the protection of personal data and to demonstrate compliance with this Regulation." Map each measure back to the risks it reduces.

| Measure | Addresses | Type | Residual risk after measure |
|---|---|---|---|
| Encryption in transit (TLS) & at rest | R1, R5 | Technical | {{m_encryption_residual}} |
| Pseudonymisation / anonymisation | R1, R5, R6 | Technical | {{m_pseudonym_residual}} |
| Access control & least privilege | R1, R4 | Technical/org | {{m_access_residual}} |
| Audit logging & monitoring | R1, R4 | Technical | {{m_logging_residual}} |
| Data minimisation by design | R1, R4 | Org | {{m_minimisation_residual}} |
| Retention/erasure automation | R3, R4 | Technical | {{m_retention_residual}} |
| Breach detection & 72-hour notification (Art. 33/34) | R1 | Org | {{m_breach_residual}} |
| Processor agreements / DPAs (Art. 28) | R1, R4 | Legal | {{m_dpa_residual}} |
| {{additional_measure}} | … | … | … |

- **Privacy by Design & by Default (Art. 25):** {{pbd_measures}} — privacy controls baked into defaults (e.g. opt-in, minimal exposure, off-by-default sharing).
- **Records of Processing Activities (Art. 30):** {{ropa_reference}} — where the RoPA entry for {{project_name}} lives.
- **Security of processing (Art. 32):** {{security_measures}} — cross-reference the security/threat-model doc and (if `ai.enabled`) the AI-safety doc for model-mediated PII exposure.

## 👥 DPO Advice & Data-Subject Views (Art. 35(2), (9))
- **DPO advice (Art. 35(2)):** "The controller shall seek the advice of the data protection officer, where designated." {{dpo_advice}} — record the DPO's input and sign-off, or note no DPO is designated and why.
- **Data-subject views (Art. 35(9)):** "The controller shall seek the views of data subjects or their representatives on the intended processing." {{data_subject_views}} — how views were sought (survey, consultation, representative bodies) or the documented justification for not seeking them (e.g. commercial confidentiality, security of operations).

## 📞 Prior Consultation (Art. 36)
Where the DPIA indicates the processing would result in a **high residual risk** that the controller cannot mitigate, the controller must consult the supervisory authority **before** processing begins.

- **High residual risk remaining after measures?** {{high_residual_remaining}}
- **Prior consultation required?** {{prior_consultation_required}} — if yes, the authority and the submission package (the DPIA, responsibilities of controller/processors, purposes/means, safeguards, DPO contact) per Art. 36(3): {{prior_consultation_plan}}.

## 🇺🇸 CCPA / CPRA Overlay
> Complete only if `constraints.ccpa` is true. Skip with a one-line note otherwise.

- **Categories of PI collected (CCPA §1798.140(v)) & sensitive PI (CPRA):** {{ccpa_pi_categories}}.
- **Business / commercial purposes for collection:** {{ccpa_purposes}}.
- **Sale or "sharing" (cross-context behavioural advertising) of PI?** {{ccpa_sale_sharing}} — if yes, the "Do Not Sell or Share My Personal Information" + "Limit the Use of My Sensitive PI" links and GPC (Global Privacy Control) signal honoring: {{ccpa_optout}}.
- **Consumer rights served:** know/access, delete, correct, opt-out of sale/share, limit sensitive-PI use, non-discrimination — {{ccpa_rights}}.
- **Notice at collection + privacy policy:** {{ccpa_notice}}.
- **CPRA risk assessment / cybersecurity audit obligations** (for high-risk processing): {{cpra_risk_assessment}}.
- **Service-provider / contractor contract terms:** {{ccpa_contracts}}.

## 🏥 HIPAA Overlay
> Complete only if `constraints.hipaa` is true. Skip with a one-line note otherwise.

- **Role:** {{hipaa_role}} — Covered Entity or Business Associate.
- **PHI handled & the 18 identifiers in scope:** {{phi_inventory}}.
- **Business Associate Agreement(s) (BAA):** {{baa_status}} — required before any vendor (cloud, AI provider, analytics) touches PHI.
- **Privacy Rule — minimum necessary & permitted uses/disclosures:** {{hipaa_privacy_rule}}.
- **Security Rule safeguards (administrative / physical / technical):** {{hipaa_security_rule}} — including access controls, audit controls, encryption, and transmission security.
- **Breach Notification Rule:** {{hipaa_breach}} — notification thresholds and timelines (individuals, HHS, and media for breaches ≥ 500).
- **De-identification approach (Safe Harbor or Expert Determination):** {{hipaa_deidentification}}.

## ✅ Verdict, Residual Risk & Review Cadence (Art. 35(11))
- **Overall verdict:** {{overall_verdict}} — proceed / proceed-with-conditions / consult-authority / do-not-proceed.
- **Conditions / outstanding actions before go-live:** {{outstanding_actions}}.
- **Accepted residual risk & owner:** {{accepted_residual_risk}} — signed off by {{risk_owner}}.
- **Review cadence (Art. 35(11)):** the controller must "carry out a review to assess if processing is performed in accordance with the [DPIA] at least when there is a change of the risk." Trigger this review on: {{review_triggers_prose}} — and at minimum {{review_interval}}. The `revision_triggers` decision keys above drive regeneration of this document.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
