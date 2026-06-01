---
template_name: AI_AND_ML
generate_when: "decisions.ai.enabled == true"
required_decisions:
  - ai.llm_provider
optional_decisions:
  - ai.sdk
  - ai.vector_db
  - ai.embeddings_model
  - ai.streaming
  - ai.guardrails
  - ai.evaluation
depends_on: []
revision_triggers:
  - ai.llm_provider
  - ai.sdk
  - ai.vector_db
  - ai.embeddings_model
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# AI & ML: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [LLM Provider & Models](#llm-provider-models)
- [🔧 SDK / Integration Layer](#sdk-integration-layer)
- [💰 Prompt Caching & Cost Optimization](#prompt-caching-cost-optimization)
- [Streaming Strategy](#streaming-strategy)
- [🔧 Tool Use / Function Calling](#tool-use-function-calling)
- [RAG Pipeline](#rag-pipeline)
- [Vector Store](#vector-store)
- [Guardrails & Safety](#guardrails-safety)
- [🚦 Evaluation & Quality Gates](#evaluation-quality-gates)
- [💰 Cost Controls](#cost-controls)
- [↻ Revision Log](#revision-log)

## LLM Provider & Models
Primary provider (Anthropic, OpenAI, Google, Bedrock, self-hosted) and the specific model tiers used per feature (e.g., Sonnet 4.7 for chat, Haiku for classification). Document fallback providers and switchover criteria.

## 🔧 SDK / Integration Layer
SDK choice (Anthropic SDK, Vercel AI SDK, LangChain, LlamaIndex, native HTTP) and where the abstraction lives. Note streaming wire format and structured output (tool use / JSON mode) usage.

## 💰 Prompt Caching & Cost Optimization
Caching strategy (Anthropic prompt caching, semantic caching, KV-cache reuse), what to cache (system prompts, tools, RAG context), TTL behavior, and expected cache-hit rate.

## Streaming Strategy
SSE vs WebSocket vs server-action streaming, partial-tool-use handling, client renderer (tokens vs structured deltas), backpressure on slow clients.

## 🔧 Tool Use / Function Calling
Tool catalog and definitions, parallel-tool-call policy, validation/coercion of tool inputs, error reporting back to the model, max-tool-iterations safeguard.

## RAG Pipeline
If applicable: ingestion sources, chunking strategy (size, overlap, semantic vs fixed), embedding model, indexing cadence, retrieval (top-k, hybrid lexical + vector, reranking).

## Vector Store
Chosen store (pgvector, Pinecone, Qdrant, Turbopuffer, Weaviate), index type (HNSW/IVF), dimension, metric, partitioning per tenant.

## Guardrails & Safety
Input/output filtering, jailbreak detection, PII redaction, content moderation API, system-prompt protection, refusal policies.

## 🚦 Evaluation & Quality Gates
Evaluation harness (Anthropic Console evals, Braintrust, LangSmith, custom), regression suite, golden examples, CI gates blocking model/prompt changes.

## 💰 Cost Controls
Per-user/per-org token budgets, rate limits, model-tier downgrade rules under load, real-time cost dashboards, alerting thresholds.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
