---
template_name: WELL_ARCHITECTED_CHECKLIST
generate_when: "conditional"
required_decisions:
  - project.name
  - project.type
  - scale
optional_decisions:
  - stack.hosting.provider
  - stack.backend.runtime
  - stack.database.engine
  - deployment.target
  - constraints.regulated
  - constraints.budget
  - constraints.compliance
  - ai.enabled
  - reliability.sla
depends_on: []
revision_triggers:
  - project.type
  - scale
  - stack.hosting.provider
  - deployment.target
  - constraints.regulated
  - reliability.sla
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Well-Architected Checklist: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the cross-cutting architecture self-assessment for **{{project_name}}**. It is structured around the **[AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)** (publication date November 6, 2024) — the six pillars of **Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability**. The Framework is *not an audit mechanism*; it is "a constructive conversation about architectural decisions." This checklist is that conversation, recorded. Each pillar below states the Framework's design principles, then captures THIS project's verdict and the concrete decision adopted. A principle marked _Not applicable_ or _Deferred_ must still carry a one-line justification — silence is not a verdict.
>
> The pillar-specific deep-dive docs (operations, security, reliability, performance, cost) are the source of detail; this checklist is the index that proves every pillar was considered. The framing was chosen to be **cloud/provider-agnostic** — substitute your stack ({{cloud_provider}} / {{deployment_target}}) for the AWS service examples.

## Table of contents
- [Scope & Workload Definition](#scope-workload-definition)
- [General Design Principles](#general-design-principles)
- [Pillar Scorecard](#pillar-scorecard)
- [🛠️ Pillar 1 — Operational Excellence](#pillar-1--operational-excellence)
- [🔐 Pillar 2 — Security](#pillar-2--security)
- [♻️ Pillar 3 — Reliability](#pillar-3--reliability)
- [⚡ Pillar 4 — Performance Efficiency](#pillar-4--performance-efficiency)
- [💰 Pillar 5 — Cost Optimization](#pillar-5--cost-optimization)
- [🌱 Pillar 6 — Sustainability](#pillar-6--sustainability)
- [📋 Trade-offs & Accepted Risks](#trade-offs-accepted-risks)
- [↻ Revision Log](#revision-log)

## Scope & Workload Definition
Define the *workload* being reviewed so every verdict below has a referent. State what {{project_name}} is (`{{project_type}}`), the operating scale (`{{scale}}` — e.g. solo / small-team / startup / enterprise), the deployment target (`{{deployment_target}}`) and cloud/provider (`{{cloud_provider}}`), and the business criticality (`{{business_criticality}}`). Note the governing constraints: regulated-data handling is **{{regulated_status}}**, the cost envelope is **{{budget_constraint}}**, and the availability target is **{{sla_target}}**. These constraints decide how aggressively each pillar is weighted — a solo side-project legitimately defers much of Reliability and Sustainability; a regulated multi-tenant SaaS does not.

## General Design Principles
The Framework's six cross-pillar principles. Record how {{project_name}} honors each (or why it is out of scope at this stage).

| General principle | How {{project_name}} applies it |
|---|---|
| **Stop guessing your capacity needs** — scale in/out automatically rather than provisioning for a peak guess | {{gdp_capacity}} |
| **Test systems at production scale** — spin up a production-scale test environment on demand, then decommission | {{gdp_prod_scale_test}} |
| **Automate with architectural experimentation in mind** — track, audit, and revert automation changes | {{gdp_automation}} |
| **Consider evolutionary architectures** — let the design change over its lifetime, not as static one-time decisions | {{gdp_evolutionary}} |
| **Drive architectures using data** — collect data on how architectural choices affect behavior and decide on facts | {{gdp_data_driven}} |
| **Improve through game days** — schedule simulations of production events to find improvement areas | {{gdp_game_days}} |

## Pillar Scorecard
A one-glance summary. For each pillar record the current maturity (`Strong` / `Adequate` / `Gap` / `Deferred`), the single highest-risk gap, and the owner.

| Pillar | Maturity | Highest-priority gap | Owner |
|---|---|---|---|
| Operational Excellence | {{oe_maturity}} | {{oe_top_gap}} | {{oe_owner}} |
| Security | {{sec_maturity}} | {{sec_top_gap}} | {{sec_owner}} |
| Reliability | {{rel_maturity}} | {{rel_top_gap}} | {{rel_owner}} |
| Performance Efficiency | {{perf_maturity}} | {{perf_top_gap}} | {{perf_owner}} |
| Cost Optimization | {{cost_maturity}} | {{cost_top_gap}} | {{cost_owner}} |
| Sustainability | {{sus_maturity}} | {{sus_top_gap}} | {{sus_owner}} |

## 🛠️ Pillar 1 — Operational Excellence
**Definition (AWS).** "A commitment to build software correctly while consistently delivering a great customer experience" — best practices for organizing your team, designing your workload, operating it at scale, and evolving it over time. Best-practice areas: **Organization · Prepare · Operate · Evolve**.

**Maturity for {{project_name}}:** {{oe_maturity}} — {{oe_summary}}

Check each design principle and record the decision (cross-reference the operations / runbook / CI-CD docs where they exist):

| OE design principle | Verdict | Decision / control adopted |
|---|---|---|
| **Organize teams around business outcomes** — operating model aligns people, process, tech to business goals & KPIs | {{oe1_verdict}} | {{oe1_decision}} |
| **Implement observability for actionable insights** — KPIs + telemetry across behavior, performance, reliability, cost, health | {{oe2_verdict}} | {{oe2_decision}} |
| **Safely automate where possible** — workload + operations as code, with guardrails (rate control, error thresholds, approvals) | {{oe3_verdict}} | {{oe3_decision}} |
| **Make frequent, small, reversible changes** — loosely-coupled design + incremental deploys to shrink blast radius | {{oe4_verdict}} | {{oe4_decision}} |
| **Refine operations procedures frequently** — review runbooks, keep them effective, communicate updates | {{oe5_verdict}} | {{oe5_decision}} |
| **Anticipate failure** — drive failure scenarios to understand the risk profile; test team response | {{oe6_verdict}} | {{oe6_decision}} |
| **Learn from all operational events and metrics** — share lessons learned across teams | {{oe7_verdict}} | {{oe7_decision}} |
| **Use managed services** — reduce operational burden via managed offerings | {{oe8_verdict}} | {{oe8_decision}} |

## 🔐 Pillar 2 — Security
**Definition (AWS).** "The ability to protect data, systems, and assets to take advantage of cloud technologies to improve your security." Best-practice areas: **Security foundations · Identity & access management · Detection · Infrastructure protection · Data protection · Incident response · Application security**.

**Maturity for {{project_name}}:** {{sec_maturity}} — {{sec_summary}}

> Reference the dedicated security / threat-model docs for detail. If the project ships an LLM feature (`ai.enabled` = {{ai_enabled}}), the AI-safety doc carries the LLM-specific threat model; this row only confirms it exists.

| Security design principle | Verdict | Decision / control adopted |
|---|---|---|
| **Implement a strong identity foundation** — least privilege, separation of duties, centralized identity, no long-term static credentials | {{sec1_verdict}} | {{sec1_decision}} |
| **Maintain traceability** — monitor, alert, and audit actions/changes in real time; integrate logs & metrics | {{sec2_verdict}} | {{sec2_decision}} |
| **Apply security at all layers** — defense in depth across edge, network, compute, OS, application, code | {{sec3_verdict}} | {{sec3_decision}} |
| **Automate security best practices** — controls defined and managed as code in version-controlled templates | {{sec4_verdict}} | {{sec4_decision}} |
| **Protect data in transit and at rest** — classify by sensitivity; use encryption, tokenization, access control | {{sec5_verdict}} | {{sec5_decision}} |
| **Keep people away from data** — reduce/eliminate direct access and manual processing of sensitive data | {{sec6_verdict}} | {{sec6_decision}} |
| **Prepare for security events** — incident management policy + processes; run response simulations | {{sec7_verdict}} | {{sec7_decision}} |

**Compliance posture.** Regulated data: {{regulated_status}}. Frameworks in scope: {{compliance_frameworks}}. Secrets management: {{secrets_management}}.

## ♻️ Pillar 3 — Reliability
**Definition (AWS).** "The ability of a workload to perform its intended function correctly and consistently when it's expected to" — including the ability to operate and test the workload through its total lifecycle. Best-practice areas: **Foundations · Workload architecture · Change management · Failure management**.

**Maturity for {{project_name}}:** {{rel_maturity}} — {{rel_summary}}

**Targets.** Availability SLA: {{sla_target}} · RTO (recovery time objective): {{rto_target}} · RPO (recovery point objective): {{rpo_target}}.

| Reliability design principle | Verdict | Decision / control adopted |
|---|---|---|
| **Automatically recover from failure** — monitor business-value KPIs; trigger automated notification & recovery on breach | {{rel1_verdict}} | {{rel1_decision}} |
| **Test recovery procedures** — validate how the workload fails and that recovery works (simulate/recreate failures) | {{rel2_verdict}} | {{rel2_decision}} |
| **Scale horizontally to increase aggregate availability** — many small resources, no shared single point of failure | {{rel3_verdict}} | {{rel3_decision}} |
| **Stop guessing capacity** — monitor demand & utilization; automate add/remove to avoid saturation & over-provisioning | {{rel4_verdict}} | {{rel4_decision}} |
| **Manage change through automation** — infrastructure changes via automation, tracked and reviewed | {{rel5_verdict}} | {{rel5_decision}} |

**Service quotas & limits to watch:** {{service_quotas}}.

## ⚡ Pillar 4 — Performance Efficiency
**Definition (AWS).** "The ability to use cloud resources efficiently to meet performance requirements, and to maintain that efficiency as demand changes and technologies evolve." Best-practice areas: **Architecture selection · Compute & hardware · Data management · Networking & content delivery · Process & culture**.

**Maturity for {{project_name}}:** {{perf_maturity}} — {{perf_summary}}

**Performance targets.** Key latency/throughput SLOs: {{performance_slos}}. Expected load profile: {{load_profile}}.

| Performance design principle | Verdict | Decision / control adopted |
|---|---|---|
| **Democratize advanced technologies** — consume specialist tech (NoSQL, transcoding, ML) as a service rather than self-host | {{perf1_verdict}} | {{perf1_decision}} |
| **Go global in minutes** — deploy across regions for lower latency where the audience warrants it | {{perf2_verdict}} | {{perf2_decision}} |
| **Use serverless architectures** — remove the burden of running/maintaining physical servers where it fits | {{perf3_verdict}} | {{perf3_decision}} |
| **Experiment more often** — comparative testing across instance types, storage, configurations | {{perf4_verdict}} | {{perf4_decision}} |
| **Consider mechanical sympathy** — pick the technology approach that matches the workload (e.g. data-access patterns drive DB/storage choice) | {{perf5_verdict}} | {{perf5_decision}} |

## 💰 Pillar 5 — Cost Optimization
**Definition (AWS).** "The ability to run systems to deliver business value at the lowest price point." Best-practice areas: **Practice Cloud Financial Management · Expenditure & usage awareness · Cost-effective resources · Manage demand & supply resources · Optimize over time**.

**Maturity for {{project_name}}:** {{cost_maturity}} — {{cost_summary}}

**Budget envelope.** Target run-rate: {{budget_constraint}}. Cross-reference the cost-model doc for the line-item estimate.

| Cost design principle | Verdict | Decision / control adopted |
|---|---|---|
| **Implement Cloud Financial Management** — build the organizational capability to operate cost-efficiently | {{cost1_verdict}} | {{cost1_decision}} |
| **Adopt a consumption model** — pay only for what you use; scale with real demand, not elaborate forecasts | {{cost2_verdict}} | {{cost2_decision}} |
| **Measure overall efficiency** — track business output vs. the cost of delivering it | {{cost3_verdict}} | {{cost3_decision}} |
| **Stop spending money on undifferentiated heavy lifting** — let the provider run the datacenter/OS/managed services | {{cost4_verdict}} | {{cost4_decision}} |
| **Analyze and attribute expenditure** — tag/identify usage so cost maps to workload owners and ROI is measurable | {{cost5_verdict}} | {{cost5_decision}} |

## 🌱 Pillar 6 — Sustainability
**Definition (AWS).** "Focuses on environmental impacts, especially energy consumption and efficiency, since they are important levers for architects to inform direct action to reduce resource usage." Best-practice areas: **Region selection · Alignment to demand · Software & architecture · Data · Hardware & services · Process & culture**.

**Maturity for {{project_name}}:** {{sus_maturity}} — {{sus_summary}}

> For a small or early-stage workload this pillar is often *Deferred* — record that explicitly rather than skipping it. Even then, "choose an efficient region" and "right-size, don't over-provision" cost nothing to honor.

| Sustainability design principle | Verdict | Decision / control adopted |
|---|---|---|
| **Understand your impact** — measure (and model the future) impact of the workload, incl. customer use & decommissioning | {{sus1_verdict}} | {{sus1_decision}} |
| **Establish sustainability goals** — long-term goals (e.g. resources per transaction); architect so growth reduces impact intensity | {{sus2_verdict}} | {{sus2_decision}} |
| **Maximize utilization** — right-size and raise utilization; minimize idle resources, processing, storage | {{sus3_verdict}} | {{sus3_decision}} |
| **Anticipate and adopt new, more efficient offerings** — design for flexibility to rapidly adopt efficient hardware/software | {{sus4_verdict}} | {{sus4_decision}} |
| **Use managed services** — share infrastructure across a broad base to maximize resource utilization | {{sus5_verdict}} | {{sus5_decision}} |
| **Reduce the downstream impact** — cut the energy/resources customers need to use your services | {{sus6_verdict}} | {{sus6_decision}} |

## 📋 Trade-offs & Accepted Risks
The pillars pull against each other — higher reliability often raises cost; aggressive cost optimization can erode performance or operational headroom. The Framework expects these tensions to be *made explicit and chosen deliberately*, not discovered in production. Record every trade-off where {{project_name}} consciously favored one pillar over another, and every gap accepted for now.

| Trade-off / accepted risk | Pillars in tension | Decision & rationale | Re-visit when |
|---|---|---|---|
| {{tradeoff_1}} | {{tradeoff_1_pillars}} | {{tradeoff_1_rationale}} | {{tradeoff_1_revisit}} |
| {{tradeoff_2}} | {{tradeoff_2_pillars}} | {{tradeoff_2_rationale}} | {{tradeoff_2_revisit}} |
| {{additional_tradeoffs}} | … | … | … |

**Next review trigger.** This checklist should be re-run when: {{review_triggers}} (e.g. scale tier changes, a new pillar gap is reported in production, a regulated-data requirement is added, or at a fixed cadence — {{review_cadence}}).

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
