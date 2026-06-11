---
template_name: CONTEXT_ENGINEERING
generate_when: "conditional"
required_decisions:
  - ai.enabled
  - ai.agent
  - ai.long_running
optional_decisions:
  - ai.provider
  - ai.model
  - ai.framework
  - ai.persistent_memory
  - ai.rag.enabled
  - ai.rag.retrieval
depends_on:
  - AGENT_DESIGN
revision_triggers:
  - ai.model
  - ai.provider
  - ai.long_running
  - ai.persistent_memory
  - ai.rag.retrieval
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Context Engineering: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> **Why this document exists.** Prompt engineering was about wording a single instruction well. **Context engineering** is the broader discipline that supersedes it: deciding *what set of tokens* enters the model's finite context window on every turn, in what *order*, and how that window is *maintained over a long-running session*. For an agent — which runs many turns, accumulates tool results, and must stay coherent across a growing transcript — the context window is the single most contended resource. This doc records how {{project_name}} budgets it, caches it, and keeps it from rotting. It builds on [AGENT_DESIGN](AGENT_DESIGN.md) (which fixes the agent's loop, tools, and memory model) and grounds its caching guidance in [Anthropic's prompt-caching documentation](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching).

## Table of contents
- [Context as a Finite Budget](#context-as-a-finite-budget)
- [What Goes In the Window (and in what order)](#what-goes-in-the-window-and-in-what-order)
- [💰 Prompt Caching](#prompt-caching)
- [🔧 Context Compaction & Summarization](#context-compaction--summarization)
- [Retrieval & Just-in-Time Context](#retrieval--just-in-time-context)
- [Avoiding Context Rot](#avoiding-context-rot)
- [Instrumentation & Cache Diagnostics](#instrumentation--cache-diagnostics)
- [↻ Revision Log](#-revision-log)

## Context as a Finite Budget

The context window is a hard cap shared by everything the model can "see": the system prompt, tool definitions, retrieved documents, the conversation/tool-call transcript, and the model's own thinking blocks. Every token spent on one is a token unavailable to another, and every token costs latency and money on every turn it survives.

Treat the window as an explicit budget, allocated by zone:

| Zone | Allocation | Notes |
|---|---|---|
| Model context window (total) | **{{context_budget}} tokens** | Hard ceiling for `{{primary_model}}` ({{ai_provider}}). |
| System prompt + persona | {{system_prompt_budget}} | Static; first thing in the prefix. |
| Tool definitions | {{tools_budget}} | Static unless the tool catalog changes. |
| Retrieved / just-in-time context | {{retrieval_budget}} | Bounded top-k; never "stuff everything." |
| Working transcript (history + tool results) | {{transcript_budget}} | The zone that *grows* — governed by compaction below. |
| Output reservation (`max_tokens`) | {{output_budget}} | Reserved headroom; not part of input. |

**Budget invariants this project enforces:**
- The sum of static zones (system + tools) MUST leave room for at least {{min_working_headroom}} tokens of working transcript before any compaction is required.
- A single retrieval call MUST NOT exceed `{{retrieval_budget}}`; retrieval is capped at top-{{retrieval_top_k}}, not unbounded.
- When projected next-turn input would exceed {{compaction_trigger}} of the window, the [compaction policy](#context-compaction--summarization) fires *before* the request is sent.

## What Goes In the Window (and in what order)

Per the Anthropic prompt-caching docs, the prompt prefix is assembled in a **strict hierarchical order** and the cache is fully prefix-based:

```
TOOLS  →  SYSTEM  →  MESSAGES
```

Each level builds on the previous; **a change at any level invalidates that level and everything after it.** Therefore {{project_name}} orders content from *most static* to *most dynamic* so the longest possible prefix stays cacheable:

```
STATIC (rarely changes — sits at the front, gets cached):
├─ Tool definitions ........... {{tools_summary}}
├─ System prompt / persona .... {{system_prompt_summary}}
├─ Long-lived background ...... {{background_context_summary}}
├─ Large documents / examples . {{static_docs_summary}}
│
└──── CACHE BREAKPOINT ◀ (last block identical across requests)
│
DYNAMIC (changes per request — sits at the back, never cached):
├─ Just-in-time retrieved context
├─ Per-request / timestamped context
└─ The incoming user (or tool-result) message
```

Ordering rules (binding):
- **Never** place per-request data (timestamps, the user message, freshly retrieved snippets) *before* static content — doing so poisons the prefix hash and forces a cache miss every turn.
- Tool definitions go first because they change least and changing them invalidates the entire prefix.
- Retrieved context is appended at the dynamic end unless a given corpus is genuinely static for the session, in which case it may be promoted ahead of the breakpoint (see [Retrieval](#retrieval--just-in-time-context)).

## 💰 Prompt Caching

Prompt caching lets the API resume from a previously-processed prefix, cutting both latency and cost on repetitive prefixes. This is the mechanical backbone of an affordable long-running agent. Anchored to [Anthropic prompt caching](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching):

**Strategy for {{project_name}}: `{{cache_strategy}}`** (one of: automatic top-level caching for multi-turn conversations; explicit multi-breakpoint caching for content with different change frequencies).

### Breakpoints
- The API allows **up to 4 cache breakpoints** per request. {{project_name}} uses **{{cache_breakpoint_count}}** of them: {{cache_breakpoint_plan}}.
- A breakpoint is set with `cache_control: {"type": "ephemeral"}` on the **last block whose prefix is identical across requests** — i.e. the end of the static prefix, *not* the varying block. Marking a per-request block writes an entry that never matches again.
- The lookback window is **20 blocks max** per breakpoint, so keep the static prefix contiguous and ahead of all variation.
- For multi-turn conversations, prefer **automatic caching** (single top-level `cache_control`): the breakpoint moves itself to the last cacheable block as the transcript grows, so markers never need manual updates.

### What we cache (mapped to the zones above)
| Content | Cached? | Why |
|---|---|---|
| Tool definitions | {{cache_tools}} | Static; large; front of prefix. |
| System prompt / persona | {{cache_system}} | Static; meets min-token floor. |
| Background docs / few-shot examples | {{cache_background}} | Static within a session. |
| Per-request retrieved context | {{cache_retrieval}} | Usually NOT — varies per turn. |
| The incoming message | No | Always dynamic. |

### TTL
- Default cache lifetime is **5 minutes** (`{"type": "ephemeral"}`); every hit refreshes the TTL (billed only at the 0.1× read multiplier, not a fresh write).
- For prefixes reused on a slower cadence, the **1-hour** option (`{"type": "ephemeral", "ttl": "1h"}`) trades a higher write multiplier for longer persistence. When mixing TTLs in one request, **1-hour entries MUST appear before 5-minute entries.**
- {{project_name}} chooses **{{cache_ttl}}** for its static prefix, because {{cache_ttl_rationale}}.

### Cost & latency model
Caching stacks multipliers on the base input price (figures are relative multipliers, not dollars):

| Operation | Multiplier |
|---|---|
| Base input tokens | 1.0× |
| 5-minute cache **write** | 1.25× |
| 1-hour cache **write** | 2.0× |
| Cache **read** / refresh | 0.1× |

A cached prefix pays the write premium **once**, then every subsequent turn reads it at **0.1×** — and cache hits don't count against rate limits. Expected steady-state cache-hit rate for {{project_name}}: **{{expected_cache_hit_rate}}**.

### Gotchas this project guards against
- The static prefix MUST clear the model's **minimum cacheable token count** (e.g. ~4,096 tokens for current Opus *and current Haiku* tiers, ~1,024 for current Sonnet tiers; older/retired tiers differ — confirm against the [pricing table](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching) for `{{primary_model}}`) — shorter prefixes silently process uncached (both `cache_creation_input_tokens` and `cache_read_input_tokens` come back 0, with no error).
- Changing `tool_choice`, or adding/removing an **image anywhere** in the prompt, invalidates the cache from that level onward.
- Tool-call JSON key ordering must be **stable** across requests, or the prefix hash diverges.
- With **extended thinking**: on current Opus/Sonnet tiers thinking blocks are preserved (cache stays valid) when non-tool-result user content is added; on older/Haiku tiers they're stripped (cache invalidated). {{project_name}}'s thinking-cache assumption: {{thinking_cache_note}}.
- Optional **pre-warming** (`max_tokens: 0`) loads the prefix before live traffic arrives: {{prewarm_policy}}.

## 🔧 Context Compaction & Summarization

A long-running agent's transcript grows without bound; left alone it eventually overruns the window and degrades attention. Compaction reclaims the working-transcript zone while preserving task-relevant state.

**Compaction trigger: `{{compaction_trigger}}`** — when projected next-turn input crosses this threshold (a fraction of the window, a turn count, or a token count), compaction runs before the next API call.

Compaction pipeline for {{project_name}}:
1. **Select** the compaction window — the oldest {{compaction_window}} of the transcript, keeping the most recent {{recent_turns_preserved}} turns verbatim (recency matters most for coherence).
2. **Summarize** the selected span with `{{summarization_model}}` into a compact state record capturing: open goals, decisions made, key tool outputs, and unresolved threads. Drop redundant intermediate tool chatter.
3. **Anchor** durable facts that must survive compaction (IDs, file paths, user constraints) into {{durable_memory_target}} — {{persistent_memory_note}}.
4. **Replace** the raw span with the summary in-place, keeping it *behind* the cache breakpoint where possible so the compacted prefix re-caches cleanly.
5. **Verify** no required state was dropped (a lightweight checklist or eval against {{compaction_eval}}).

Design notes:
- Compaction is **lossy by design** — the contract is "preserve everything the next step needs," not "preserve everything." What counts as required state is enumerated in [AGENT_DESIGN](AGENT_DESIGN.md).
- Because compaction rewrites the transcript, it forces a cache write on the changed suffix. Schedule it to amortize that cost (e.g. compact in larger, less frequent batches rather than every turn).
- If the agent persists across process restarts, the compacted summary IS the resumable state — align it with {{durable_memory_target}}.

## Retrieval & Just-in-Time Context

Prefer **just-in-time retrieval** over pre-loading: fetch only the context the current step needs, rather than stuffing a large corpus into the window up front. This keeps the dynamic zone small and the static prefix cacheable.

- **Source(s):** {{retrieval_sources}}.
- **Trigger:** retrieve when {{retrieval_trigger}} (e.g. a tool call, a detected knowledge gap, an explicit citation need) — not on every turn by default.
- **Budget & shape:** top-{{retrieval_top_k}}, capped at `{{retrieval_budget}}` tokens, {{retrieval_strategy}} (e.g. hybrid lexical + vector, reranked). See [RAG_ARCHITECTURE](RAG_ARCHITECTURE.md) if a full RAG pipeline backs this.
- **Placement:** retrieved snippets go in the **dynamic** zone (after the breakpoint) unless the corpus is fixed for the whole session, in which case promote it ahead of the breakpoint to cache it.
- **Provenance:** each retrieved block carries {{retrieval_provenance}} so the model (and downstream eval) can attribute claims.

## Avoiding Context Rot

"Context rot" is the slow degradation of agent quality as the window fills with stale, contradictory, or low-signal tokens — old tool errors, superseded plans, duplicated documents. It manifests as the agent ignoring recent instructions, repeating resolved steps, or drifting off-task. Countermeasures:

- **Prune aggressively.** Failed tool outputs, retracted plans, and superseded retrievals are removed at the next compaction, not carried forever.
- **One source of truth per fact.** Avoid duplicating the same document/spec at multiple positions; duplication wastes budget and creates contradictions.
- **Keep instructions late and singular.** The current objective lives near the dynamic end where attention is strongest; don't restate it five times across the prefix.
- **Bound the transcript.** The [compaction trigger](#context-compaction--summarization) is the structural defense — a window that never compacts always rots.
- **Watch the signal-to-noise ratio.** {{context_rot_signals}} (e.g. rising turn count with falling task-success rate) are tracked as a rot indicator.
- **Periodic re-grounding.** Optionally re-assert the system prompt / task contract after each compaction so the agent re-anchors on goals: {{regrounding_policy}}.

## Instrumentation & Cache Diagnostics

You cannot tune what you don't measure. Track per-request, from the `usage` response:

- `cache_creation_input_tokens` — tokens written to cache this turn.
- `cache_read_input_tokens` — tokens served from cache (the win).
- `input_tokens` — tokens **after the last breakpoint** only.
- Derived: `total_input = cache_read + cache_creation + input_tokens`; **cache-hit ratio** = `cache_read / total_input`.

Operational signals for {{project_name}}:
- Alert when cache-hit ratio drops below **{{cache_hit_floor}}** over {{cache_hit_window}} (signals prefix instability — usually an image toggle, `tool_choice` change, or a dynamic block that crept ahead of the breakpoint).
- Track tokens-per-turn and turns-to-compaction to validate the [budget allocations](#context-as-a-finite-budget) against real traffic.
- Use **Cache Diagnostics** to compare consecutive requests and pinpoint the first divergent block when hit rate regresses.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
