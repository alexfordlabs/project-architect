---
template_name: ENGINEERING_PRINCIPLES
generate_when: "conditional"
required_decisions: [scale, team_size]
optional_decisions:
  - project.type
  - stack.primary_language
  - team.code_review
  - team.ci_cd
  - constraints.regulated
  - quality.priorities
depends_on: []
revision_triggers:
  - scale
  - team_size
  - quality.priorities
  - constraints.regulated
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Engineering Principles & Quality Goals: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document is the **shared engineering charter** for {{project_name}} — the durable, team-wide
> principles plus the prioritized, *measurable* quality goals that justify the architecture. Its
> structure follows **[arc42 §10 — Quality Requirements](https://docs.arc42.org/section-10/)**,
> which itself is grounded in **ISO/IEC 25010:2023** (the product-quality model) and the pragmatic
> **[Q42 quality model](https://quality.arc42.org/)**. arc42's core demand: quality requirements
> "significantly influence architectural decisions and must be **specific and measurable**" — a goal
> like "the system shall be fast" is worthless until expressed as a scenario whose fulfilment can be
> decided. Everything below turns adjectives into acceptance criteria.

## Table of contents
- [Why This Document Exists](#why-this-document-exists)
- [Engineering Principles](#engineering-principles)
- [📊 10.1 Quality Requirements Overview](#101-quality-requirements-overview)
- [🌳 Quality Attribute Utility Tree](#quality-attribute-utility-tree)
- [🎯 10.2 Quality Scenarios](#102-quality-scenarios)
- [Trade-offs Between Quality Goals](#trade-offs-between-quality-goals)
- [How Principles Are Enforced](#how-principles-are-enforced)
- [↻ Revision Log](#revision-log)

## Why This Document Exists

This document is generated because **`scale` is `{{scale}}`** and/or **`team_size` is `{{team_size}}`** —
i.e. {{project_name}} is past the point where a single developer can hold the standards in their head.
With {{team_size}} contributors at {{scale}} scale, shared engineering principles and explicit,
testable quality goals are the mechanism that keeps independent decisions coherent. arc42's framing:
quality requirements are *the* primary driver of architecture, so they belong in a first-class,
reviewed artifact — not scattered in tickets and tribal knowledge.

This charter is **normative**. When a code review, design proposal, or ADR conflicts with a principle
or quality goal here, the conflict is resolved here (revise the principle with an ADR) or there (reject
the change) — never silently.

## Engineering Principles

The durable "how we build" rules. These are stable across releases; changing one is an architectural
decision (file an ADR). State each as an imperative the team can be held to. Replace the examples below
with the principles {{team_name}} actually commits to — keep the list short enough to remember (5–9 items).

| # | Principle | What it means in practice | Rationale |
|---|---|---|---|
| 1 | {{principle_1}} | {{principle_1_practice}} | {{principle_1_rationale}} |
| 2 | {{principle_2}} | {{principle_2_practice}} | {{principle_2_rationale}} |
| 3 | {{principle_3}} | {{principle_3_practice}} | {{principle_3_rationale}} |
| 4 | {{principle_4}} | {{principle_4_practice}} | {{principle_4_rationale}} |
| 5 | {{principle_5}} | {{principle_5_practice}} | {{principle_5_rationale}} |

> Starter set to adapt (delete what doesn't fit): *Simplicity first — add complexity only when a quality
> goal demands it. · No untested change reaches `main`. · Every architectural decision is an ADR. · Code
> review is mandatory for every merge ({{code_review_policy}}). · Prefer boring, well-understood technology
> over novelty. · Make illegal states unrepresentable. · Optimise for the reader, not the writer.*

## 📊 10.1 Quality Requirements Overview

Per arc42 §10.1, summarise the quality requirements by category. We use the **ISO/IEC 25010:2023**
product-quality model — its nine top-level characteristics are the canonical category set. For each,
state whether it is a **priority** for {{project_name}} and a one-line target. arc42's advice: not every
characteristic is equally important; pick the few that drive architecture and say so. (Cross-reference
the Q42 hashtag labels `#flexible #efficient #usable #operable #testable #secure #safe #reliable` where
your team prefers that vocabulary.)

| ISO 25010:2023 characteristic | Priority for {{project_name}} | One-line target | Owner |
|---|---|---|---|
| **Functional Suitability** (completeness, correctness, appropriateness) | {{q_functional_priority}} | {{q_functional_target}} | {{q_functional_owner}} |
| **Performance Efficiency** (time-behaviour, resource use, capacity) | {{q_performance_priority}} | {{q_performance_target}} | {{q_performance_owner}} |
| **Compatibility** (co-existence, interoperability) | {{q_compatibility_priority}} | {{q_compatibility_target}} | {{q_compatibility_owner}} |
| **Interaction Capability** *(was "Usability"; renamed in 25010:2023)* | {{q_usability_priority}} | {{q_usability_target}} | {{q_usability_owner}} |
| **Reliability** (availability, fault tolerance, recoverability, maturity) | {{q_reliability_priority}} | {{q_reliability_target}} | {{q_reliability_owner}} |
| **Security** (confidentiality, integrity, non-repudiation, accountability, authenticity, **resistance** — new in 25010:2023) | {{q_security_priority}} | {{q_security_target}} | {{q_security_owner}} |
| **Maintainability** (modularity, reusability, analysability, modifiability, testability) | {{q_maintainability_priority}} | {{q_maintainability_target}} | {{q_maintainability_owner}} |
| **Flexibility** *(new top-level char in 25010:2023 — adaptability, scalability, installability, replaceability)* | {{q_flexibility_priority}} | {{q_flexibility_target}} | {{q_flexibility_owner}} |
| **Safety** *(new top-level char in 25010:2023 — operational constraint, risk identification, fail-safe, hazard warning)* | {{q_safety_priority}} | {{q_safety_target}} | {{q_safety_owner}} |

> **Note on 25010:2023 vs the older 25010:2011** that many teams still quote: the 2023 revision elevated
> **Safety** and **Flexibility** to top-level characteristics, renamed *Usability* → *Interaction
> Capability* and *Portability* → *Flexibility* (whose sub-characteristics now include adaptability,
> scalability, installability, and replaceability), and added **Resistance** under Security.
> Use the 2023 names above so this doc stays current.

## 🌳 Quality Attribute Utility Tree

arc42 (citing Bass et al., *Software Architecture in Practice*, who introduced the **"Quality Attribute
Utility Tree"**) recommends refining the abstract characteristics above into a tree whose leaves are
concrete scenarios. Each leaf carries a two-part priority: **(Business importance, Architectural
difficulty/risk)** — typically rated H/M/L. The (H, H) leaves are the architecturally significant ones
that the scenarios in §10.2 and the architecture itself must explicitly address.

```
{{project_name}} — Utility
├── {{priority_quality_1}}            (e.g. Performance Efficiency)
│   ├── {{scenario_ref_1a}}           (B: {{importance_1a}}, A: {{difficulty_1a}})
│   └── {{scenario_ref_1b}}           (B: {{importance_1b}}, A: {{difficulty_1b}})
├── {{priority_quality_2}}            (e.g. Reliability)
│   ├── {{scenario_ref_2a}}           (B: {{importance_2a}}, A: {{difficulty_2a}})
│   └── {{scenario_ref_2b}}           (B: {{importance_2b}}, A: {{difficulty_2b}})
└── {{priority_quality_3}}            (e.g. Maintainability)
    └── {{scenario_ref_3a}}           (B: {{importance_3a}}, A: {{difficulty_3a}})
```

**Architecturally significant scenarios (rated H,H):** {{architecturally_significant_scenarios}}
*(These are the ones the architecture is obligated to satisfy and that the team re-validates each release.)*

## 🎯 10.2 Quality Scenarios

arc42 §10.2: "Quality scenarios make quality requirements concrete and allow to decide whether they are
fulfilled." A scenario must be *measurable* — its response measure is the acceptance criterion. arc42
distinguishes two kinds:

- **Usage (runtime) scenarios** — "the system's runtime reaction to a certain stimulus" (latency,
  throughput, availability, security response). Example from the standard: *"The system reacts to a
  user's request within one second."*
- **Change scenarios** — "the desired effect of a modification or extension of the system," measured by
  the **effort or duration** needed (e.g. how long a new developer needs to ship a change, how long to
  add a payment provider). These drive Maintainability / Flexibility.

Use the **long form** (SEI / Bass et al.) for the (H,H) leaves and the short form for the rest.

### Long-form scenario template (one block per architecturally significant scenario)

| Field | Value |
|---|---|
| **ID** | {{scenario_id}} (e.g. QS-PERF-01) |
| **Name** | {{scenario_name}} |
| **Quality category** | {{scenario_category}} (an ISO 25010:2023 characteristic above) |
| **Type** | {{scenario_type}} (usage / change) |
| **Source** | {{scenario_source}} — who/what generates the stimulus (end user, batch job, attacker, developer) |
| **Stimulus** | {{scenario_stimulus}} — the condition that arrives (a request burst, a fault, a feature request) |
| **Artifact** | {{scenario_artifact}} — the part of the system stimulated (API, datastore, whole system) |
| **Environment** | {{scenario_environment}} — operating state (normal load, peak, degraded, under attack) |
| **Response** | {{scenario_response}} — what the system does in reaction |
| **Response measure** | {{scenario_response_measure}} — the **measurable** acceptance criterion (e.g. p95 < 200 ms, 99.9% availability, ≤ 2 dev-days) |
| **Priority** | (B: {{scenario_business_priority}}, A: {{scenario_arch_priority}}) |
| **Verified by** | {{scenario_verification}} — the test / SLO monitor / benchmark that proves it (links §How Principles Are Enforced) |

> Worked examples to imitate:
> - **Usage / Performance:** *Under {{peak_load}} concurrent users (Environment: peak), a read request
>   (Stimulus, Source: end user) to the API (Artifact) returns successfully (Response) with **p95 latency
>   below {{p95_target}} ms** (Response measure).*
> - **Usage / Reliability:** *When a downstream dependency fails (Stimulus) during normal operation
>   (Environment), the system degrades gracefully (Response) and maintains **{{availability_target}}
>   monthly availability** (Response measure).*
> - **Change / Maintainability:** *A developer (Source) is asked to add a new {{change_unit}}
>   (Stimulus) to the codebase (Artifact) in the development environment; the change is implemented,
>   reviewed, and merged (Response) in **≤ {{change_effort_target}} developer-days** (Response measure).*

### Short-form scenario register (everything else)

| ID | Quality category | Scenario (context · stimulus · acceptance criterion) | Measure |
|---|---|---|---|
| {{short_scenario_1_id}} | {{short_scenario_1_cat}} | {{short_scenario_1_desc}} | {{short_scenario_1_measure}} |
| {{short_scenario_2_id}} | {{short_scenario_2_cat}} | {{short_scenario_2_desc}} | {{short_scenario_2_measure}} |
| {{short_scenario_3_id}} | {{short_scenario_3_cat}} | {{short_scenario_3_desc}} | {{short_scenario_3_measure}} |

## Trade-offs Between Quality Goals

Quality goals conflict; the architecture is the resolution of those conflicts. arc42 expects the
priority ordering to be explicit so that, when two goals collide, the team knows which wins. Record the
deliberate trade-offs {{project_name}} has accepted.

| Tension | Resolution for {{project_name}} | Recorded in |
|---|---|---|
| {{tradeoff_1_pair}} (e.g. Performance vs. Maintainability) | {{tradeoff_1_resolution}} | {{tradeoff_1_adr}} |
| {{tradeoff_2_pair}} (e.g. Security vs. Interaction Capability) | {{tradeoff_2_resolution}} | {{tradeoff_2_adr}} |
| {{tradeoff_3_pair}} (e.g. Flexibility vs. Simplicity / time-to-market) | {{tradeoff_3_resolution}} | {{tradeoff_3_adr}} |

**Priority order when goals conflict (highest first):** {{quality_priority_order}}

## How Principles Are Enforced

A principle nobody checks is decoration. For {{scale}} scale with {{team_size}} contributors, wire each
principle and quality scenario to an automated or process gate so adherence is the default, not a virtue.

| Principle / quality goal | Enforcement mechanism | Gate type |
|---|---|---|
| Code review on every merge | {{code_review_mechanism}} (e.g. required PR review, CODEOWNERS) | process |
| No untested change | {{test_gate}} (CI required check, coverage threshold) | automated |
| Performance scenarios hold | {{perf_gate}} (load test / SLO monitor / benchmark in CI) | automated |
| Reliability scenarios hold | {{reliability_gate}} (SLOs + error budgets, chaos tests) | automated |
| Security scenarios hold | {{security_gate}} (SAST/dependency scan, threat-model review) | automated |
| Style / static analysis | {{lint_gate}} (linter + formatter + type checker in CI) | automated |
| Every architectural decision is an ADR | {{adr_gate}} (ADR-required check in review) | process |

- **CI/CD pipeline:** {{ci_cd_pipeline}} — the single place the automated gates run.
- **Definition of Done:** {{definition_of_done}} — what every change satisfies before it is "done".
- **Regulated-data controls:** {{regulated_controls}} *(only if `constraints.regulated` is true — name
  the compliance regime and the additional gates it imposes; otherwise "N/A — not a regulated system").*
- **Review cadence:** these principles and quality goals are revisited {{review_cadence}} and whenever a
  `revision_trigger` decision (`scale`, `team_size`, `quality.priorities`, `constraints.regulated`) changes.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
