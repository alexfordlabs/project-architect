---
template_name: AGENT_MEMORY
generate_when: "conditional"
required_decisions: [ai.agent, ai.persistent_memory]
optional_decisions: [ai.framework, ai.orchestration, agent.memory, stack.database.engine, stack.cache.engine]
depends_on: [AGENT_DESIGN]
revision_triggers: [ai.persistent_memory, ai.framework, agent.memory, stack.database.engine]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Agent Memory: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> Grounded in the [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/memory)
> model: **short-term** memory is thread-scoped state persisted via checkpoints,
> **long-term** memory lives in a cross-thread `Store` organized by namespaces.
> The agent's reasoning loop and tool surface are defined in
> [AGENT_DESIGN](./AGENT_DESIGN.md) — this document specifies what that agent
> *remembers* and how.

## Table of contents
- [🧠 Memory Model Overview](#memory-model-overview)
- [Short-Term Memory (thread / checkpoint)](#short-term-memory-thread-checkpoint)
- [🧠 Long-Term Memory (cross-thread store)](#long-term-memory-cross-thread-store)
- [Memory Types](#memory-types)
- [🔧 The Store Abstraction](#the-store-abstraction)
- [Namespacing & Retrieval](#namespacing-retrieval)
- [⏱️ Write Policy: Hot-Path vs Background](#write-policy-hot-path-vs-background)
- [Semantic Search & Indexing](#semantic-search-indexing)
- [🧹 Managing Memory Growth](#managing-memory-growth)
- [🔐 Privacy, Tenancy & Lifecycle](#privacy-tenancy-lifecycle)
- [Observability & Evaluation](#observability-evaluation)
- [↻ Revision Log](#revision-log)

## 🧠 Memory Model Overview
{{project_name}} runs a persistent agent (see AGENT_DESIGN), so it needs memory that
survives beyond a single LLM call. Following the LangGraph two-tier model:

- **Short-term (within-thread)** — conversation history, retrieved documents, tool
  results, and working artifacts. Persisted as part of the agent's *state* via a
  thread-scoped **checkpointer**. Scope: one session/thread (`thread_id = {{thread_id_source}}`).
- **Long-term (cross-thread)** — durable facts, learned procedures, and past
  episodes that must be recalled in *any* future thread. Persisted in a **Store**
  under custom **namespaces**.

| Tier | Scope | Backed by | Lifespan | Example in {{project_name}} |
|---|---|---|---|---|
| Short-term | single thread | checkpointer (`{{checkpointer_backend}}`) | session / configurable TTL | {{short_term_example}} |
| Long-term | cross-thread | store (`{{memory_backend}}`) | durable | {{long_term_example}} |

**What we choose to remember:** {{what_is_remembered}}

## Short-Term Memory (thread / checkpoint)
A **thread** organizes the interactions of one session (LangGraph's analogy:
threads group messages the way an email thread does). Short-term memory is the
agent's *state*, read at the start of each step and rewritten when the graph step
completes.

- **Checkpointer:** {{checkpointer_backend}} (e.g. `InMemorySaver` for dev,
  Postgres/Redis-backed saver for prod). Enables pause/resume, replay, and
  time-travel debugging.
- **Thread key:** `thread_id = {{thread_id_source}}` (conversation id / user+task).
- **What's held in state:** {{short_term_state_contents}} (message list, scratchpad,
  retrieved-doc handles, pending tool calls).
- **Resumption semantics:** {{resumption_policy}} — how a thread is reloaded, and
  whether interrupted runs replay from the last checkpoint.

## 🧠 Long-Term Memory (cross-thread store)
Long-term memories are written to a `Store` and recalled at any time in any thread,
scoped by **namespace** rather than by `thread_id`.

- **Memory backend:** {{memory_backend}} (e.g. LangGraph `InMemoryStore` for dev;
  Postgres / `stack.database.engine` or a vector DB for prod).
- **Promotion rule:** {{promotion_rule}} — what causes a short-term observation to
  be promoted into durable long-term memory (e.g. an explicit `save_memory` tool
  call, end-of-thread distillation, or a confidence threshold).
- **Recall trigger:** {{recall_trigger}} — when the agent reads long-term memory
  (every turn, on session start, or only when the router asks for it).

## Memory Types
Per the LangGraph taxonomy, classify each kind of long-term memory and define its
shape and write path explicitly — different types have different update cadences.

| Type | Stores | Used for | In {{project_name}} | Write path |
|---|---|---|---|---|
| **Semantic** | facts & concepts | personalization; grounding responses in known user/domain facts | {{semantic_memory_use}} | {{semantic_write_path}} |
| **Episodic** | past experiences / action sequences | few-shot exemplars; learning from prior successful (or failed) runs | {{episodic_memory_use}} | {{episodic_write_path}} |
| **Procedural** | instructions & rules | the agent's evolving system prompt / how-to knowledge (meta-prompting) | {{procedural_memory_use}} | {{procedural_write_path}} |

> Semantic memory may be modeled as a continuously-updated **profile** (one
> document per subject) or as a growing **collection** of discrete facts —
> document which: **{{semantic_memory_shape}}**. Profiles risk lossy overwrites;
> collections risk unbounded growth (see [Managing Memory Growth](#managing-memory-growth)).

## 🔧 The Store Abstraction
All long-term reads/writes go through the store interface (LangGraph `BaseStore`),
keeping the agent decoupled from the storage engine.

```python
# namespace is a tuple ("folder" path); key is the "file name"
store.put(namespace, key, value)          # write / upsert a memory document
store.get(namespace, key)                 # fetch one memory by key
store.search(namespace, query="...",      # semantic + filtered retrieval
             filter={"...": "..."}, limit={{search_top_k}})
```

- **Implementation:** {{store_implementation}} (`InMemoryStore` dev → {{prod_store}} prod).
- **Document schema per memory:** {{memory_document_schema}} (e.g. `{content, type,
  source_thread_id, created_at, importance}`).
- **Consistency model:** {{store_consistency}} — strong vs eventual; whether a
  hot-path write is read-your-writes within the same turn.

## Namespacing & Retrieval
Namespaces are hierarchical "folders"; keys are the "file names" inside them.
Design the namespace tuple so that isolation and retrieval scope fall out naturally.

- **Namespace shape:** `{{namespace_tuple}}` — typically
  `({{tenant_or_user_id}}, "{{memory_category}}")` so each user/org's memories are
  isolated and queryable as a unit. {{namespacing_rationale}}
- **Retrieval keys:** {{retrieval_keys}} — the exact namespace + filter fields the
  agent uses to fetch relevant memories (e.g. `(user_id, "preferences")` filtered by
  `{"topic": <current_topic>}`).
- **Cross-namespace search:** {{cross_namespace_policy}} — whether the agent ever
  searches across namespaces (e.g. org-wide shared knowledge) and the access rule
  that permits it.

## ⏱️ Write Policy: Hot-Path vs Background
Choose, per memory type, *when* memories are written. LangGraph frames this as the
central memory-engineering trade-off.

| Approach | Pro | Con | Used here for |
|---|---|---|---|
| **Hot-path** (write during the agent run, e.g. a `save_memory` tool) | immediately available; transparent to the user | adds latency; couples reasoning with memory logic | {{hotpath_use}} |
| **Background** (write asynchronously after the run / on a schedule) | no user-facing latency; separates concerns | freshness lag; needs a trigger (cron / queue / end-of-thread) | {{background_use}} |

- **Chosen write policy:** {{write_policy}}
- **Background trigger:** {{background_trigger}} (end-of-thread hook, scheduled job,
  message-count threshold, or manual). Omit if all writes are hot-path.
- **De-duplication / reconciliation:** {{dedup_policy}} — how a background writer
  avoids re-storing or contradicting existing memories.

## Semantic Search & Indexing
If memories are retrieved by meaning rather than exact key, configure the store's
vector index.

- **Index config:** `index = {"embed": {{embed_function}}, "dims": {{embedding_dims}},
  "fields": {{embedded_fields}}}` — embedding model `{{embedding_model}}`. The `fields`
  list (e.g. `["content"]`, or `["$"]` to embed the whole document) selects which parts
  of each memory get embedded.
- **What gets embedded:** {{embedded_fields_rationale}} (the `content` field vs a derived
  summary). `store.search(namespace, query=...)` then ranks by vector similarity;
  add `filter={...}` for hybrid filtered + semantic recall.
- **Top-k & relevance floor:** {{search_top_k}} results, drop below similarity
  `{{relevance_threshold}}` to keep stale/irrelevant memories out of the context.

## 🧹 Managing Memory Growth
Full history rarely fits the context window, and models get "distracted" by stale
content. Bound both tiers.

- **Short-term trimming:** {{trimming_strategy}} — message trimming / removal of
  stale turns, preserving valid human↔model alternation; token budget
  `{{context_token_budget}}`.
- **Summarization / distillation:** {{summarization_policy}} — when the running
  message list is condensed into a summary (and whether that summary becomes a
  long-term memory).
- **Long-term compaction:** {{longterm_compaction}} — merging duplicate facts,
  decaying low-importance episodes, capping per-namespace document count
  ({{max_memories_per_namespace}}).
- **Conflict resolution:** {{conflict_resolution}} — newest-wins, confidence-weighted,
  or human-in-the-loop when a new memory contradicts an existing one.

## 🔐 Privacy, Tenancy & Lifecycle
- **Tenant isolation:** memories are namespaced by `{{tenant_or_user_id}}`; no
  cross-tenant read path except {{cross_namespace_policy}}.
- **PII & sensitive data:** {{pii_policy}} — what may be stored, redaction before
  write, and encryption at rest.
- **Retention & deletion:** {{retention_policy}} — TTLs, user-initiated "forget me"
  (delete by namespace), and right-to-erasure compliance.
- **Auditing:** {{memory_audit}} — log of memory writes/reads for traceability.

## Observability & Evaluation
- **Tracing:** {{memory_tracing}} — surface which memories were retrieved and
  injected into each prompt (e.g. via {{tracing_tool}}).
- **Quality signals:** {{memory_quality_metrics}} — retrieval precision/recall,
  stale-memory rate, and whether recalled memories improved task outcomes.
- **Regression guard:** {{memory_eval_gate}} — eval examples that assert the agent
  recalls the right memory and ignores irrelevant ones before a prompt/model change ships.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
