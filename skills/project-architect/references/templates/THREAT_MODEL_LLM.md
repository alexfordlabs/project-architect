---
template_name: THREAT_MODEL_LLM
generate_when: "conditional"
required_decisions:
  - ai.agent
  - constraints.regulated
optional_decisions:
  - ai.enabled
  - ai.framework
  - ai.persistent_memory
  - agent.autonomy
  - agent.tools.sandbox
  - agent.hitl
  - data.classification
  - constraints.compliance
depends_on: []
revision_triggers:
  - ai.agent
  - ai.framework
  - agent.autonomy
  - agent.tools.sandbox
  - agent.hitl
  - data.classification
  - constraints.regulated
  - constraints.compliance
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# LLM Threat Model: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the adversarial threat model for the LLM/agentic surface of **{{project_name}}**, a
> regulated/audit-bound project (`constraints.regulated`). It applies **STRIDE** (Microsoft's
> threat-classification mnemonic) to the LLM attack surface, maps each threat onto the
> **[MITRE ATLAS](https://atlas.mitre.org/)** matrix — *Adversarial Threat Landscape for
> Artificial-Intelligence Systems*, the ATT&CK-styled knowledge base of real-world adversarial-ML
> tactics & techniques — and grounds concrete risks in the
> **[OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)**. It
> **complements `AI_SAFETY.md`** (alignment, harmful-output, eval safety) and does **not**
> duplicate it: this doc is about a *deliberate adversary*, not unintended model behaviour.

## Table of contents
- [🎯 Scope, Assets & Audit Mandate](#scope-assets-audit-mandate)
- [🧭 Trust Boundaries & Data-Flow](#trust-boundaries-data-flow)
- [🔡 The LLM Attack Surface](#the-llm-attack-surface)
- [🧱 STRIDE Applied to the LLM](#stride-applied-to-the-llm)
- [🗺️ MITRE ATLAS Tactics & Techniques](#mitre-atlas-tactics-techniques)
- [🔟 OWASP LLM Top-10 as Concrete Threats](#owasp-llm-top-10-as-concrete-threats)
- [🛡️ Per-Threat Mitigations](#per-threat-mitigations)
- [🧾 Audit Trail & Evidence (Regulated)](#audit-trail-evidence-regulated)
- [📉 Residual Risk Register](#residual-risk-register)
- [↻ Revision Log](#revision-log)

## 🎯 Scope, Assets & Audit Mandate

| Property | Decision for {{project_name}} |
|---|---|
| LLM surface in scope | {{llm_surface_scope}} — chat / RAG / autonomous agent / batch inference |
| Agentic? | `{{ai_agent}}` (`ai.agent`) — agents widen the surface to **tool invocation** |
| Autonomy level | `{{agent_autonomy}}` (`agent.autonomy`) — higher autonomy ⇒ larger blast radius |
| Base model(s) | `{{models_in_scope}}` (hosted API / self-hosted / fine-tuned) |
| Data sensitivity | `{{data_classification}}` (`data.classification`) — PII / PHI / PCI / regulated |
| Regulatory regime | `{{compliance_regime}}` (`constraints.compliance`) — e.g. EU AI Act, GDPR, HIPAA, SOC 2, NIST AI RMF |
| Audit obligation | {{audit_obligation}} — who consumes the trail, retention period, attestation cadence |

**Crown-jewel assets** (what an adversary is after — rank them):

1. {{asset_1}} — {{asset_1_impact}}
2. {{asset_2}} — {{asset_2_impact}}
3. {{asset_3}} — {{asset_3_impact}}

> **Why a regulated project needs this doc.** ATLAS exists because the supply chains, opaque
> behaviours, and novel inference-time attacks of AI systems are *not* covered by classic appsec
> threat models. For an audit-bound system, "we ran a generic pentest" is insufficient — auditors
> increasingly expect an AI-specific threat model that names the adversarial-ML techniques in
> scope and shows each is mitigated *and evidenced*.

## 🧭 Trust Boundaries & Data-Flow

Threats cross **trust boundaries**. Draw the boundary diagram and enumerate every crossing — each
arrow that crosses a boundary is a candidate threat. Reference the C4/component diagram if one exists.

```
{{trust_boundary_diagram}}

  [ untrusted: end user / public input ]
        │  (boundary 1: ingress — prompt + uploads)
        ▼
  [ semi-trusted: app / orchestrator ]  ──(boundary 2)──▶ [ LLM (hosted API or self-hosted) ]
        │  (boundary 3: tool/agent action)                        │ (boundary 5: training/fine-tune)
        ▼                                                         ▼
  [ tools · MCP servers · code exec · DB · email · web ]   [ model weights / fine-tune pipeline ]
        │  (boundary 4: RAG retrieval)
        ▼
  [ RAG corpus / vector store / external content ]  ← INDIRECT-INJECTION VECTOR
```

| # | Boundary crossing | Trusted? | Primary threat at this crossing |
|---|---|---|---|
| 1 | User → app (the prompt itself) | untrusted | Direct prompt injection / jailbreak |
| 2 | App → LLM (assembled context) | semi | System-prompt leakage; over-trusted instructions |
| 3 | LLM → tools/agent action | **least-privilege** | Excessive Agency; destructive/unauthorized tool calls |
| 4 | Retrieval → context | untrusted-content | **Indirect** prompt injection via poisoned RAG/web |
| 5 | Data → training/fine-tune | supply chain | Data & model poisoning |

> **Treat all model output and all retrieved content as untrusted.** OWASP **LLM05: Improper
> Output Handling** is exactly the failure to do so — model output flowing unescaped into a shell,
> SQL, browser DOM, or a downstream tool. The boundary between "LLM said it" and "the system acted
> on it" (boundary 3) is the single highest-value control point in an agentic system.

## 🔡 The LLM Attack Surface

Enumerate every place adversary-controlled bytes can reach the model or its actions:

| Surface | In scope? | Notes for {{project_name}} |
|---|---|---|
| Direct user prompt | {{surface_direct_prompt}} | The obvious one; includes multimodal (image/audio) prompts |
| Retrieved/RAG content (indirect) | {{surface_rag}} | Web pages, docs, emails, tickets — content the *user* didn't write |
| Tool/function results fed back into context | {{surface_tool_results}} | A poisoned tool/MCP server can inject instructions |
| Conversation history / persistent memory | {{surface_memory}} (`ai.persistent_memory`) | Poisoned memory persists across sessions |
| Uploaded files / documents | {{surface_uploads}} | Hidden text, metadata, steganographic instructions |
| Training / fine-tuning data | {{surface_training_data}} | Supply-chain & poisoning vector (boundary 5) |
| Model + dependency supply chain | {{surface_supply_chain}} | Weights, tokenizer, plugins, MCP servers, libraries |

## 🧱 STRIDE Applied to the LLM

STRIDE classifies threats into six categories. Below each is mapped to its LLM-specific form,
the property it violates, and the ATLAS/OWASP anchor. Fill the *risk* and *owner* columns.

| STRIDE | Violates | LLM-specific manifestation | ATLAS / OWASP anchor | Risk (L/M/H) · Owner |
|---|---|---|---|---|
| **S — Spoofing** | Authentication | Impersonated user/system role in the prompt; forged tool identity; deepfake input bypassing identity checks | ATLAS *Initial Access* → **Prompt Infiltration via Public-Facing Application**; **Spearphishing via Social Engineering LLM** | {{stride_s_risk}} · {{stride_s_owner}} |
| **T — Tampering** | Integrity | Prompt injection altering instructions; **RAG Poisoning**; **Poison Training Data**; manipulating tool inputs | ATLAS **LLM Prompt Injection**, **RAG Poisoning**, **Erode AI Model Integrity** · OWASP **LLM01**, **LLM04** | {{stride_t_risk}} · {{stride_t_owner}} |
| **R — Repudiation** | Non-repudiation | No trace linking a prompt → model decision → tool action → effect; user denies an action the agent took on their behalf | (audit-trail gap — see [Audit Trail](#audit-trail-evidence-regulated)) | {{stride_r_risk}} · {{stride_r_owner}} |
| **I — Information Disclosure** | Confidentiality | **Extract LLM System Prompt**; training-data / memory leakage; secrets in context exfiltrated via tool calls or rendered links | ATLAS **Extract LLM System Prompt**, **LLM Data Leakage**, **Exfiltration via AI Agent Tool Invocation** · OWASP **LLM02**, **LLM07** | {{stride_i_risk}} · {{stride_i_owner}} |
| **D — Denial of Service** | Availability | **Denial of AI Service**; **Cost Harvesting** (token/$ exhaustion); context-window flooding; recursive/self-replicating prompts | ATLAS **Denial of AI Service**, **Cost Harvesting**, **LLM Prompt Self-Replication** · OWASP **LLM10** | {{stride_d_risk}} · {{stride_d_owner}} |
| **E — Elevation of Privilege** | Authorization | **Excessive Agency** — agent invokes a tool/permission beyond intent; injection escalates from "answer" to "act"; jailbreak removes guardrails | ATLAS **LLM Jailbreak** (Privilege Escalation tactic) · OWASP **LLM06** | {{stride_e_risk}} · {{stride_e_owner}} |

## 🗺️ MITRE ATLAS Tactics & Techniques

ATLAS adapts the ATT&CK structure to AI systems. The matrix runs left-to-right across **16
tactics** (the adversary's *goals*), each containing *techniques* (the *how*). Mark which tactics
are in scope for {{project_name}} and name the specific technique(s) you defend against.

| # | ATLAS Tactic | Adversary goal | In scope? | Relevant technique(s) for {{project_name}} |
|---|---|---|---|---|
| 1 | **Reconnaissance** | Gather info to plan an attack | {{atlas_recon}} | Search Open AI Vulnerability Analysis; Search Victim-Owned Websites |
| 2 | **Resource Development** | Build/buy attack capability | {{atlas_resource_dev}} | Develop/Obtain Adversarial AI Attacks; **Publish Poisoned Datasets** |
| 3 | **Initial Access** | Get into the AI system | {{atlas_initial_access}} | **AI Supply Chain Compromise**; **LLM Prompt Injection**; Prompt Infiltration via Public-Facing Application |
| 4 | **AI Model Access** | Reach the model itself | {{atlas_model_access}} | AI Model Inference API Access; AI-Enabled Product or Service; Full AI Model Access |
| 5 | **Execution** | Run adversary code/instructions | {{atlas_execution}} | **LLM Prompt Injection** (direct/indirect); LLM Prompt Self-Replication |
| 6 | **Persistence** | Maintain foothold | {{atlas_persistence}} | **Poison Training Data**; **Manipulate AI Model** (memory/fine-tune) |
| 7 | **Privilege Escalation** | Gain higher permissions | {{atlas_privesc}} | **LLM Jailbreak**; LLM Prompt Injection escalating to tool action |
| 8 | **Defense Evasion** | Avoid detection/guardrails | {{atlas_defense_evasion}} | **Evade AI Model**; **LLM Prompt Obfuscation**; Craft Adversarial Data |
| 9 | **Credential Access** | Steal credentials | {{atlas_cred_access}} | **RAG Credential Harvesting**; Unsecured Credentials in context |
| 10 | **Discovery** | Learn the environment | {{atlas_discovery}} | **Discover LLM System Information**; Discover AI Model Family; **Discover LLM Hallucinations** |
| 11 | **Lateral Movement** | Pivot to other systems/agents | {{atlas_lateral_movement}} | Spread across agents/tools via injected instructions; pivot from a compromised tool to connected services |
| 12 | **Collection** | Stage data of interest | {{atlas_collection}} | RAG Databases; Data from Information Repositories |
| 13 | **AI Attack Staging** | Prepare the model attack | {{atlas_attack_staging}} | **Craft Adversarial Data**; **Verify Attack**; **Erode AI Model Integrity** |
| 14 | **Command and Control** | Operate the foothold remotely | {{atlas_command_and_control}} | Reverse Shell; channel instructions/exfil through model or tool traffic |
| 15 | **Exfiltration** | Get data out | {{atlas_exfiltration}} | **Exfiltration via AI Agent Tool Invocation**; **Exfiltration via AI Inference API**; **Extract AI Model** |
| 16 | **Impact** | Cause damage/loss | {{atlas_impact}} | **Denial of AI Service**; **Cost Harvesting**; **External Harms**; **Erode AI Model Integrity** |

> ATLAS also catalogs real-world **case studies** (e.g. *Morris II* RAG worm, *Bing Chat Data
> Pirate* indirect injection, *ChatGPT Conversation Exfiltration*). Cite the closest case study to
> each in-scope tactic so reviewers can see the attack is *real*, not theoretical:
> **{{relevant_atlas_case_studies}}**.

## 🔟 OWASP LLM Top-10 as Concrete Threats

The 2025 list, mapped to whether it applies here and to the owning mitigation. (Names are exact
from the OWASP GenAI project.)

| ID | Risk | Applies? | Concrete scenario for {{project_name}} |
|---|---|---|---|
| **LLM01** | Prompt Injection | {{owasp_llm01}} | {{owasp_llm01_scenario}} |
| **LLM02** | Sensitive Information Disclosure | {{owasp_llm02}} | {{owasp_llm02_scenario}} |
| **LLM03** | Supply Chain | {{owasp_llm03}} | {{owasp_llm03_scenario}} |
| **LLM04** | Data and Model Poisoning | {{owasp_llm04}} | {{owasp_llm04_scenario}} |
| **LLM05** | Improper Output Handling | {{owasp_llm05}} | {{owasp_llm05_scenario}} |
| **LLM06** | Excessive Agency | {{owasp_llm06}} | {{owasp_llm06_scenario}} |
| **LLM07** | System Prompt Leakage | {{owasp_llm07}} | {{owasp_llm07_scenario}} |
| **LLM08** | Vector and Embedding Weaknesses | {{owasp_llm08}} | {{owasp_llm08_scenario}} |
| **LLM09** | Misinformation | {{owasp_llm09}} | {{owasp_llm09_scenario}} |
| **LLM10** | Unbounded Consumption | {{owasp_llm10}} | {{owasp_llm10_scenario}} |

## 🛡️ Per-Threat Mitigations

For every in-scope threat above, name the **control**, where it sits in the data-flow, whether it
is preventive/detective/responsive, and how it is **tested**. Layer controls — no single defense
(not even a good system prompt) stops prompt injection on its own.

| Threat (STRIDE / ATLAS / OWASP ref) | Control | Boundary | Type | Verified by |
|---|---|---|---|---|
| Direct injection / jailbreak (LLM01, LLM Jailbreak) | {{ctrl_injection}} — input screening, instruction/data separation, injection-detection classifier | 1, 2 | Preventive + detective | {{verify_injection}} |
| Indirect injection via RAG/tools (LLM01, RAG Poisoning) | {{ctrl_indirect}} — sanitize & label retrieved content as untrusted data, never instructions; provenance on RAG docs | 4, 3 | Preventive | {{verify_indirect}} |
| Excessive Agency (LLM06) | {{ctrl_agency}} — **least-privilege tools**, allow-listed actions, human-in-the-loop (`agent.hitl` = `{{agent_hitl}}`) on destructive/irreversible calls | 3 | Preventive | {{verify_agency}} |
| Improper output handling (LLM05) | {{ctrl_output}} — encode/escape model output before any sink (shell/SQL/DOM/tool arg); treat output as untrusted | 3 | Preventive | {{verify_output}} |
| Sensitive disclosure / system-prompt leak (LLM02, LLM07) | {{ctrl_disclosure}} — keep secrets out of context, no secrets in system prompt, output DLP/redaction, egress controls on tool/link rendering | 2, I | Preventive + detective | {{verify_disclosure}} |
| Data/model poisoning & supply chain (LLM03, LLM04) | {{ctrl_supply_chain}} — vetted datasets, signed model artifacts, SBOM, pinned/verified deps & MCP servers | 5, supply | Preventive | {{verify_supply_chain}} |
| Unbounded consumption / DoS (LLM10, Cost Harvesting) | {{ctrl_dos}} — rate limits, per-user token & $ budgets, input-size caps, loop/iteration ceilings | 1, 3 | Preventive + detective | {{verify_dos}} |
| Sandboxing (all tool execution) | {{ctrl_sandbox}} (`agent.tools.sandbox` = `{{agent_tools_sandbox}}`) — isolate tool/code execution; cap blast radius | 3 | Preventive | {{verify_sandbox}} |

> **Defense in depth is mandatory for prompt injection.** There is no known complete prevention.
> Combine: (1) a constrained system prompt, (2) input/output filtering, (3) clear data↔instruction
> separation, (4) least-privilege tool scopes, and (5) human approval for high-impact actions. Each
> layer reduces likelihood; the *least-privilege + HITL* combination caps the *impact* when a layer fails.

## 🧾 Audit Trail & Evidence (Regulated)

Because `constraints.regulated` is true, every threat above must have **evidence** an auditor can
inspect. This is the **Repudiation** control made concrete: a tamper-evident record linking
*prompt → retrieved context → model decision → tool action → effect*.

| Audit requirement | Implementation for {{project_name}} |
|---|---|
| Per-interaction trace | {{audit_trace}} — request ID correlating prompt, full assembled context (or hash), model+version, tool calls, outputs |
| Tamper-evidence | {{audit_tamper_evidence}} — append-only / hash-chained / WORM store so logs can't be silently altered |
| Identity & attribution | {{audit_identity}} — authenticated user bound to every agent action (closes Spoofing/Repudiation) |
| PII/secret handling in logs | {{audit_pii}} — redaction before persistence; logs are an exfiltration target too |
| Retention & access | {{audit_retention}} — retention window per `{{compliance_regime}}`; who may read the trail |
| Detection & alerting | {{audit_detection}} — anomaly alerts on injection signatures, cost spikes, denied-tool attempts |
| Incident response | {{audit_incident_response}} — runbook for a confirmed injection/exfiltration; revoke, rotate, notify |
| Control evidence for auditors | {{audit_control_evidence}} — map each in-scope ATLAS/OWASP item → control → test result → owner |

> **Regulatory mapping.** Tie controls to the governing framework(s): {{regulatory_control_map}}
> (e.g. NIST AI RMF *Map/Measure/Manage*, EU AI Act risk-management Art. 9, SOC 2 CC-series,
> ISO/IEC 42001). An auditor reads *this table* to confirm the AI-specific risks are governed, not
> just the classic CIA triad.

## 📉 Residual Risk Register

Threats that remain after mitigation — accepted, transferred, or deferred — with sign-off.

| Threat | Residual risk | Treatment | Accepted by | Review date |
|---|---|---|---|---|
| {{residual_1}} | {{residual_1_level}} | {{residual_1_treatment}} | {{residual_1_owner}} | {{residual_1_review}} |
| {{residual_2}} | {{residual_2_level}} | {{residual_2_treatment}} | {{residual_2_owner}} | {{residual_2_review}} |

**Open questions / deferred analysis:** {{open_questions}}

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
