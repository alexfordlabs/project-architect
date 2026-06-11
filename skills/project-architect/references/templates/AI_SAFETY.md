---
template_name: AI_SAFETY
generate_when: "conditional"
required_decisions: [ai.enabled, scale, constraints.regulated]
optional_decisions:
  - ai.agent
  - ai.provider
  - ai.model
  - ai.framework
  - ai.rag.enabled
  - agent.autonomy
  - agent.tools.sandbox
  - constraints.supply_chain_security
depends_on: []
revision_triggers:
  - ai.enabled
  - ai.agent
  - ai.framework
  - ai.rag.enabled
  - agent.autonomy
  - agent.tools.sandbox
  - constraints.regulated
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# AI Safety & LLM Security: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document is the LLM-application threat model for {{project_name}}. It is structured around the **[OWASP Top 10 for Large Language Model Applications 2025](https://genai.owasp.org/llm-top-10/)** (LLM01:2025 – LLM10:2025), the current authoritative reference for generative-AI application security. Each risk below states OWASP's threat, then records THIS project's applicability verdict and the concrete mitigation adopted. Risks marked _Not applicable_ must still carry a one-line justification — silence is not a verdict.

## Table of contents
- [Scope & Threat Surface](#scope-threat-surface)
- [Risk Applicability Matrix](#risk-applicability-matrix)
- [🔐 LLM01:2025 — Prompt Injection](#llm012025--prompt-injection)
- [🔐 LLM02:2025 — Sensitive Information Disclosure](#llm022025--sensitive-information-disclosure)
- [🔐 LLM03:2025 — Supply Chain](#llm032025--supply-chain)
- [🔐 LLM04:2025 — Data and Model Poisoning](#llm042025--data-and-model-poisoning)
- [🔐 LLM05:2025 — Improper Output Handling](#llm052025--improper-output-handling)
- [🔐 LLM06:2025 — Excessive Agency](#llm062025--excessive-agency)
- [🔐 LLM07:2025 — System Prompt Leakage](#llm072025--system-prompt-leakage)
- [🔐 LLM08:2025 — Vector and Embedding Weaknesses](#llm082025--vector-and-embedding-weaknesses)
- [🔐 LLM09:2025 — Misinformation](#llm092025--misinformation)
- [🔐 LLM10:2025 — Unbounded Consumption](#llm102025--unbounded-consumption)
- [🛡️ Input Guardrails](#input-guardrails)
- [🛡️ Output Guardrails](#output-guardrails)
- [🚦 Red-Teaming & Continuous Assurance](#red-teaming-continuous-assurance)
- [↻ Revision Log](#revision-log)

## Scope & Threat Surface
What AI capability {{project_name}} ships and therefore what the attack surface actually is. State the model(s) in play ({{primary_model}} via {{ai_provider}}), whether the system is a single-shot generation feature or an **{{agentic_or_assistant}}** system, what untrusted inputs reach the model (end-user prompts, retrieved documents, tool outputs, uploaded files), what trusted assets the model can touch (databases, tools, payment rails, customer PII), and who the threat actors are. Note the governing constraints: regulated-data handling is **{{regulated_status}}** and supply-chain hardening is **{{supply_chain_status}}**. This section sets the lens for every applicability verdict below.

## Risk Applicability Matrix
A one-glance summary. Fill `Yes` / `No` / `Partial` for each OWASP 2025 risk, the owner, and the residual-risk rating after mitigation.

| OWASP 2025 Risk | Applies? | Severity (pre-mitigation) | Residual risk | Owner |
|---|---|---|---|---|
| LLM01 Prompt Injection | {{llm01_applies}} | {{llm01_severity}} | {{llm01_residual}} | {{llm01_owner}} |
| LLM02 Sensitive Information Disclosure | {{llm02_applies}} | {{llm02_severity}} | {{llm02_residual}} | {{llm02_owner}} |
| LLM03 Supply Chain | {{llm03_applies}} | {{llm03_severity}} | {{llm03_residual}} | {{llm03_owner}} |
| LLM04 Data and Model Poisoning | {{llm04_applies}} | {{llm04_severity}} | {{llm04_residual}} | {{llm04_owner}} |
| LLM05 Improper Output Handling | {{llm05_applies}} | {{llm05_severity}} | {{llm05_residual}} | {{llm05_owner}} |
| LLM06 Excessive Agency | {{llm06_applies}} | {{llm06_severity}} | {{llm06_residual}} | {{llm06_owner}} |
| LLM07 System Prompt Leakage | {{llm07_applies}} | {{llm07_severity}} | {{llm07_residual}} | {{llm07_owner}} |
| LLM08 Vector and Embedding Weaknesses | {{llm08_applies}} | {{llm08_severity}} | {{llm08_residual}} | {{llm08_owner}} |
| LLM09 Misinformation | {{llm09_applies}} | {{llm09_severity}} | {{llm09_residual}} | {{llm09_owner}} |
| LLM10 Unbounded Consumption | {{llm10_applies}} | {{llm10_severity}} | {{llm10_residual}} | {{llm10_owner}} |

## 🔐 LLM01:2025 — Prompt Injection
**OWASP threat.** User or third-party content alters the model's behavior or output in unintended ways — directly (a crafted user prompt) or indirectly (injected instructions inside a retrieved document, web page, tool result, or uploaded file). This can produce unauthorized actions, data exfiltration, or bypassed safety controls.

**Applies to {{project_name}}?** {{llm01_applies}} — {{llm01_justification}}

**Mitigation adopted.** {{llm01_mitigation}}
Document the specific controls: enforcing a trust boundary between system instructions and untrusted input (e.g. dedicated input channels, delimiters, or structured/`system`-role separation); constraining model behavior and output format; least-privilege on any actions the model can trigger; treating indirect-injection sources (RAG corpus, tool outputs, agent observations) as hostile; and human-in-the-loop approval for high-impact operations.

## 🔐 LLM02:2025 — Sensitive Information Disclosure
**OWASP threat.** The model reveals sensitive data — PII, credentials, proprietary content, or other users' data — through its outputs, whether memorized from training/fine-tuning data, leaked from context, or surfaced via retrieval.

**Applies to {{project_name}}?** {{llm02_applies}} — {{llm02_justification}}

**Mitigation adopted.** {{llm02_mitigation}}
Cover: data minimization in prompts and context ({{context_data_policy}}); input/output PII detection and redaction; access controls so retrieval and tools only surface data the requesting principal is entitled to; sanitizing fine-tuning/embedding data; and clear user consent / data-handling terms. Cross-reference the data-handling doc if regulated data is in scope ({{regulated_status}}).

## 🔐 LLM03:2025 — Supply Chain
**OWASP threat.** Compromised third-party components undermine integrity — base/fine-tuned models from public hubs, model weights, datasets, LoRA adapters, inference runtimes, agent frameworks, and SDK dependencies can carry tampering, license traps, or backdoors.

**Applies to {{project_name}}?** {{llm03_applies}} — {{llm03_justification}}

**Mitigation adopted.** {{llm03_mitigation}}
Cover: vetted model/provider sourcing ({{model_provenance}}); pinning model and dependency versions; integrity verification (checksums/signatures) of weights and packages; an SBOM and dependency scanning for the AI toolchain; and vendor security assessment for hosted-model providers. Tighten these controls when supply-chain hardening is required ({{supply_chain_status}}).

## 🔐 LLM04:2025 — Data and Model Poisoning
**OWASP threat.** Manipulation of pre-training, fine-tuning, or embedding data (or RAG ingestion sources) introduces backdoors, biases, or degraded behavior — including poisoned documents that enter the retrieval corpus.

**Applies to {{project_name}}?** {{llm04_applies}} — {{llm04_justification}}

**Mitigation adopted.** {{llm04_mitigation}}
Cover: provenance and validation of any fine-tuning / embedding / RAG-ingestion data ({{training_data_source}}); anomaly detection and filtering on ingested content; trusted-source gating for the retrieval corpus; and behavioral monitoring / evals to catch drift after data changes.

## 🔐 LLM05:2025 — Improper Output Handling
**OWASP threat.** Downstream systems consume model output without validation. Because the output is attacker-influenceable (see LLM01), unvalidated output can drive XSS, SQL injection, command injection, SSRF, or path traversal in the consuming code.

**Applies to {{project_name}}?** {{llm05_applies}} — {{llm05_justification}}

**Mitigation adopted.** {{llm05_mitigation}}
Cover: treat all model output as untrusted user input; context-aware encoding/escaping before rendering ({{output_render_targets}}); parameterized queries rather than model-built SQL; schema validation of structured/tool-call output; sandboxing any model-generated code or shell; and never passing raw output into `eval`-class sinks.

## 🔐 LLM06:2025 — Excessive Agency
**OWASP threat.** The system grants the LLM too much functionality, too-broad permissions, or too much autonomy, so a manipulated model can take damaging actions (deleting data, sending funds, calling destructive tools) beyond what the use case needs.

**Applies to {{project_name}}?** {{llm06_applies}} — {{llm06_justification}}

**Mitigation adopted.** {{llm06_mitigation}}
Cover: minimize the tool/extension catalog to what's strictly needed; least-privilege scoping on each tool's permissions; avoid open-ended capabilities (run-shell, arbitrary-HTTP) where a narrow tool suffices; require human approval / explicit authorization for high-impact actions ({{hitl_policy}}); rate-limit and bound autonomous loops; and complete-mediation on every tool call rather than trusting the model's intent. For an agentic system, reference the agent-architecture doc and its autonomy level ({{agent_autonomy}}) and sandbox posture ({{agent_sandbox}}).

## 🔐 LLM07:2025 — System Prompt Leakage
**OWASP threat.** The system prompt is extracted or inferred, exposing instructions, embedded secrets, model guardrails, or business logic that an attacker can then bypass. The deeper failure is treating the system prompt as a security boundary in the first place.

**Applies to {{project_name}}?** {{llm07_applies}} — {{llm07_justification}}

**Mitigation adopted.** {{llm07_mitigation}}
Cover: never place secrets, credentials, connection strings, or access rules inside the system prompt — enforce those in the application/authorization layer instead; assume the system prompt is public; detect and rate-limit extraction attempts; and keep security-critical controls independent of any single prompt.

## 🔐 LLM08:2025 — Vector and Embedding Weaknesses
**OWASP threat.** Weaknesses in how embeddings and vector stores are generated, stored, and retrieved (especially in RAG): cross-tenant leakage, embedding-inversion that reconstructs source text, retrieval poisoning, and access-control gaps on the vector DB.

**Applies to {{project_name}}?** {{llm08_applies}} — {{llm08_justification}}

**Mitigation adopted.** {{llm08_mitigation}}
Cover: per-tenant / per-principal partitioning and access control on the vector store ({{vector_store}}); authorization enforced at retrieval time, not just at the application edge; validation and provenance of ingested chunks; encryption at rest for embeddings; and monitoring for anomalous query patterns. Omit / mark Not applicable if no RAG or vector store is used ({{rag_enabled}}).

## 🔐 LLM09:2025 — Misinformation
**OWASP threat.** The model produces false, fabricated ("hallucinated"), or misleading output that users over-rely on, leading to flawed decisions, security mistakes, or legal/reputational liability — amplified by overreliance and missing source attribution.

**Applies to {{project_name}}?** {{llm09_applies}} — {{llm09_justification}}

**Mitigation adopted.** {{llm09_mitigation}}
Cover: grounding answers in retrieval with source attribution / citations; confidence signaling and explicit uncertainty; user-facing disclaimers on AI-generated content; human review for high-stakes outputs; cross-verification against authoritative sources; and an eval suite that measures factuality / grounding before prompt or model changes ship.

## 🔐 LLM10:2025 — Unbounded Consumption
**OWASP threat.** Uncontrolled inference lets attackers (or runaway agents) drive denial-of-service, denial-of-wallet (runaway token cost), or model extraction through excessive or crafted requests.

**Applies to {{project_name}}?** {{llm10_applies}} — {{llm10_justification}}

**Mitigation adopted.** {{llm10_mitigation}}
Cover: per-user / per-session / per-org rate limits and token quotas ({{rate_limit_policy}}); maximum input/output length and max-tool-iteration / recursion bounds for agents; cost monitoring with alert thresholds and circuit breakers; throttling and queueing under load; and logging to detect extraction-style query patterns.

## 🛡️ Input Guardrails
The enforced controls on everything entering the model, independent of the per-risk table. Describe the input pipeline ({{input_guardrails}}): prompt-injection / jailbreak detection (heuristic + classifier, e.g. a moderation API or a dedicated guardrail model), PII and secret scanning, content moderation, input length caps, and the trust-boundary mechanism separating system instructions from untrusted content. State whether guardrails fail-open or fail-closed and what gets logged.

## 🛡️ Output Guardrails
The enforced controls on everything leaving the model. Describe the output pipeline ({{output_guardrails}}): output moderation / safety classification, PII redaction, schema/format validation for structured output, context-aware encoding before any downstream sink (per LLM05), citation/grounding checks (per LLM09), and the action-authorization gate for tool calls (per LLM06). State the fallback behavior when a guardrail blocks a response.

## 🚦 Red-Teaming & Continuous Assurance
How safety is verified over time, not just at design time. Cover: the adversarial test suite (prompt-injection, jailbreak, data-exfiltration, and excessive-agency probes); the regression gate that blocks model/prompt/tool changes from shipping if safety evals regress ({{eval_gate}}); the schedule and ownership of red-team exercises; incident response for an AI-specific security event; and how findings feed back into the guardrails and this document. Reference OWASP's companion guidance (GenAI Red Teaming, LLM Security Verification Standard) where adopted.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
