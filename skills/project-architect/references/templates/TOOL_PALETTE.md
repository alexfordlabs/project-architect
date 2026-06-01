---
template_name: TOOL_PALETTE
generate_when: "conditional"
required_decisions: [ai.agent, project.type]
optional_decisions: [ai.framework, ai.provider, ai.model, agent.tools.sandbox, agent.hitl, mcp.surface, mcp.auth_model, mcp.statefulness, stack.api.protocol]
depends_on: [AGENT_DESIGN]
revision_triggers: [ai.agent, project.type, ai.framework, agent.tools.sandbox, agent.hitl, mcp.surface]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Tool Palette: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> **Grounded in** the [Model Context Protocol specification, revision 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18) — §Server Features (Tools / Resources / Prompts), §Security and Trust & Safety, and [§Server / Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools). This document inventories and designs the **tools** that {{project_name}} exposes for a language model to invoke — whether {{project_name}} is an autonomous agent that *consumes* tools or an MCP server that *publishes* them. It is the companion design to [AGENT_DESIGN](AGENT_DESIGN.md), which fixes the agent's loop, autonomy, and memory; this doc fixes the *verbs* the agent acts through.

## Table of contents
- [Role & Scope](#role-scope)
- [🔧 MCP Primitives in Play (Tools / Resources / Prompts)](#mcp-primitives-in-play-tools-resources-prompts)
- [🗂️ Tool Catalog](#tool-catalog)
- [🧩 Tool Definition Contract](#tool-definition-contract)
- [🏷️ Behavioral Annotations (the safety hints)](#behavioral-annotations-the-safety-hints)
- [📤 Result Shape & Token Efficiency](#result-shape-token-efficiency)
- [⚠️ Error Handling (protocol vs execution errors)](#error-handling-protocol-vs-execution-errors)
- [📚 Resources & Prompts Exposed](#resources-prompts-exposed)
- [🚚 Transport & Capability Negotiation](#transport-capability-negotiation)
- [🔐 Authorization & Trust Boundary](#authorization-trust-boundary)
- [🛡️ Security: Consent, Least Privilege, Human-in-the-Loop](#security-consent-least-privilege-human-in-the-loop)
- [🧪 Validation & Testing](#validation-testing)
- [↻ Revision Log](#revision-log)

## Role & Scope
State which side of the MCP boundary {{project_name}} sits on, because it changes everything downstream:

- **Tool consumer (agent):** {{project_name}} is an LLM application that *calls* tools (model-controlled invocation per the spec's User Interaction Model). The palette below is the set of tools the agent is granted — sourced from {{tool_source}} (in-process functions, one or more MCP servers, or both).
- **Tool publisher (MCP server):** {{project_name}} *exposes* tools over MCP for hosts (Claude Code, Claude Desktop, IDEs) to discover via `tools/list` and invoke via `tools/call`.
- **Both:** an agent that also re-exposes a curated subset of its capabilities as an MCP surface.

Selected role for {{project_name}}: **{{tool_role}}**. The model that drives or consumes this palette: **{{primary_model}}** via {{ai_framework}}.

## 🔧 MCP Primitives in Play (Tools / Resources / Prompts)
The 2025-06-18 spec defines three server features. Declare which {{project_name}} uses and why:

| Primitive | Control | What it is | Used here? |
|---|---|---|---|
| **Tools** | model-controlled | Functions the model executes (query a DB, call an API, run a computation) | {{uses_tools}} |
| **Resources** | application/user-controlled | Context and data, identified by URI, for the user or model to read | {{uses_resources}} |
| **Prompts** | user-controlled | Templated messages / workflows the user selects | {{uses_prompts}} |

Tools are the primary surface of this document. Rationale for the split (why a given capability is a tool vs. a resource): {{primitive_split_rationale}}.

## 🗂️ Tool Catalog
The complete, named inventory. Each row is a distinct verb. Keep names `snake_case`, descriptions agent-facing (written *for the model*, not for a human reader), and one clear purpose per tool — do not overload.

| Tool `name` | `title` (display) | Purpose (one line) | Inputs (key → type) | Output | Read-only? | Idempotent? |
|---|---|---|---|---|---|---|
| `{{tool_1_name}}` | {{tool_1_title}} | {{tool_1_purpose}} | {{tool_1_inputs}} | {{tool_1_output}} | {{tool_1_readonly}} | {{tool_1_idempotent}} |
| `{{tool_2_name}}` | {{tool_2_title}} | {{tool_2_purpose}} | {{tool_2_inputs}} | {{tool_2_output}} | {{tool_2_readonly}} | {{tool_2_idempotent}} |
| `{{tool_3_name}}` | {{tool_3_title}} | {{tool_3_purpose}} | {{tool_3_inputs}} | {{tool_3_output}} | {{tool_3_readonly}} | {{tool_3_idempotent}} |
| `{{additional_tools}}` | … | … | … | … | … | … |

**Catalog discipline (anti-bloat):** {{catalog_sizing_rationale}}. Per Anthropic/MCP guidance, fewer well-described tools beat many overlapping ones — a large or ambiguous palette degrades the model's tool-selection accuracy and inflates the system-prompt token cost. Target count: **{{target_tool_count}}**. Tools added later trigger the `notifications/tools/list_changed` notification (see §Transport).

## 🧩 Tool Definition Contract
Every tool in the catalog conforms to the MCP `Tool` shape. Define each field deliberately:

- **`name`** — unique identifier; the only field the model uses to select the tool. Stable; renaming is a breaking change.
- **`title`** — optional human-readable display name (for host UIs); never relied on for behavior.
- **`description`** — human-/model-readable functionality. **This is the most load-bearing field for tool recall** — write it as a precise instruction to the model: what it does, when to use it, when *not* to, and any preconditions. Convention for {{project_name}}: {{description_convention}}.
- **`inputSchema`** — JSON Schema (`type: object`) defining expected parameters, marking `required` fields, and giving each property its own `description`. Authored via {{schema_authoring_tool}} (e.g. Zod → JSON Schema, Pydantic, hand-written JSON Schema).
- **`outputSchema`** — optional JSON Schema for the structured result. When present, the server **MUST** return structured results conforming to it and clients **SHOULD** validate against it. Use it for any tool whose result is consumed programmatically: {{output_schema_policy}}.

### Worked example — `{{example_tool_name}}`
```json
{
  "name": "{{example_tool_name}}",
  "title": "{{example_tool_title}}",
  "description": "{{example_tool_description}}",
  "inputSchema": {
    "type": "object",
    "properties": {
      "{{example_input_field}}": {
        "type": "{{example_input_type}}",
        "description": "{{example_input_field_description}}"
      }
    },
    "required": ["{{example_input_field}}"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "{{example_output_field}}": {
        "type": "{{example_output_type}}",
        "description": "{{example_output_field_description}}"
      }
    },
    "required": ["{{example_output_field}}"]
  },
  "annotations": {
    "readOnlyHint": {{example_readonly_hint}},
    "destructiveHint": {{example_destructive_hint}},
    "idempotentHint": {{example_idempotent_hint}},
    "openWorldHint": {{example_openworld_hint}}
  }
}
```

## 🏷️ Behavioral Annotations (the safety hints)
The spec's optional `annotations` describe how a tool behaves so hosts can render the right confirmation UI and the agent can reason about blast radius. **Annotations are hints, not guarantees** — the spec is explicit that clients **MUST** treat annotations as *untrusted* unless they come from a trusted server, so {{project_name}} never relies on them for an actual access-control decision (that lives in §Authorization). Assign each tool:

| Annotation | Meaning | Default | Policy for this palette |
|---|---|---|---|
| `readOnlyHint` | Tool does not modify its environment | `false` | {{readonly_policy}} |
| `destructiveHint` | Tool may perform destructive updates (only meaningful when not read-only) | `true` | {{destructive_policy}} |
| `idempotentHint` | Repeated calls with same args have no additional effect | `false` | {{idempotent_policy}} |
| `openWorldHint` | Tool interacts with an open external world (e.g. the web) vs. a closed domain | `true` | {{openworld_policy}} |

**Idempotency design:** {{idempotency_strategy}} — for any non-idempotent, state-changing tool, document the de-duplication / request-key mechanism so retried agent calls are safe.

## 📤 Result Shape & Token Efficiency
Per the spec, a tool result carries a `content` array (unstructured) and/or a `structuredContent` object, plus the `isError` flag. Content items may be `text`, `image`, `audio`, `resource_link`, or embedded `resource`.

- **Content types used by this palette:** {{content_types_used}}.
- **Structured vs. unstructured:** {{structured_content_policy}}. When returning `structuredContent`, also emit the serialized JSON in a text block (spec's backwards-compatibility note).
- **Token-efficiency rules (critical — tool results are re-fed into the model's context every turn):**
  - Return only what the agent needs to act; paginate / truncate large payloads with a continuation handle: {{pagination_strategy}}.
  - Prefer `resource_link` over inlining large blobs so the agent can fetch on demand instead of paying for the bytes every turn.
  - Strip incidental fields; keep IDs and the minimal projection: {{result_projection_rules}}.
  - Set a per-result size budget: {{result_size_budget}}.

## ⚠️ Error Handling (protocol vs execution errors)
The spec mandates **two** distinct error channels — get this right or the agent cannot recover gracefully:

1. **Protocol errors** — standard JSON-RPC `error` (e.g. unknown tool → code `-32602`, invalid arguments, server faults). These are transport-level and not seen by the model as a tool result.
2. **Tool execution errors** — returned *inside* a normal result with `isError: true` and a human-/model-readable message in `content` (API failure, invalid input data, business-logic rejection). The model **sees** these and is expected to react.

Policy for {{project_name}}: surface recoverable failures the agent can act on (bad input, rate limit, transient upstream) as `isError: true` results with actionable text → {{execution_error_policy}}; reserve protocol errors for genuinely malformed calls. Error message convention (no secrets, no stack traces, actionable next step): {{error_message_convention}}.

## 📚 Resources & Prompts Exposed
If {{project_name}} publishes resources and/or prompts alongside tools:

- **Resources:** {{resources_exposed}} — URI scheme {{resource_uri_scheme}}, subscription/`list_changed` behavior {{resource_subscription}}. (Note: `resource_link`s returned by tools are not guaranteed to appear in `resources/list`.)
- **Prompts:** {{prompts_exposed}} — parameterized templates surfaced to the user, with arguments {{prompt_arguments}}.

## 🚚 Transport & Capability Negotiation
- **Transport:** **{{transport}}** — `stdio` (local: Claude Code / Claude Desktop launching the server as a subprocess) or **Streamable HTTP** (remote clients). Rationale tied to {{deployment_target}}.
- **Declared capabilities:** the server advertises `"tools": { "listChanged": {{list_changed}} }` during initialization; when the catalog changes at runtime it emits `notifications/tools/list_changed` and the client re-issues `tools/list`.
- **Pagination:** `tools/list` is cursor-paginated; this palette {{pagination_needed}}.
- **Statefulness:** {{statefulness}} (stateless request/response vs. durable per-session/per-user state).

## 🔐 Authorization & Trust Boundary
- **Auth model:** **{{auth_model}}** — `none` for trusted local stdio; **OAuth 2.1** for the Streamable HTTP transport per the spec's Authorization section; or API-key / bearer / signed-JWT / per-tenant credential passthrough. Token rotation & refresh: {{token_rotation}}.
- **Trust boundary:** which caller is trusted to invoke which tool, and how identity propagates from the host through to the downstream system {{project_name}} acts on: {{trust_boundary}}.
- **Secrets:** tool credentials are never embedded in schemas, descriptions, or results — sourced at runtime from {{secret_source}}.

## 🛡️ Security: Consent, Least Privilege, Human-in-the-Loop
Apply the spec's **Security and Trust & Safety** key principles and the Tools-section Security Considerations:

- **User consent & control** — the host must obtain explicit consent before invoking any tool; {{project_name}} expects/provides a clear UI indicating which tools are exposed and a visible indicator on each invocation. Consent model: {{consent_model}}.
- **Human-in-the-loop** — there **SHOULD** always be a human able to deny an invocation. Tools flagged destructive / not read-only require an explicit confirmation prompt: {{hitl_policy}} (ties to `agent.hitl`).
- **Least privilege** — each tool is scoped to the narrowest capability that satisfies its purpose; no "do-anything" escape hatch. Privilege scoping: {{least_privilege_scoping}}.
- **Server MUST (publisher side):** validate all tool inputs, implement proper access controls, rate-limit invocations, sanitize outputs. Concrete measures: input validation {{input_validation}}, rate limiting {{rate_limiting}}, output sanitization {{output_sanitization}}.
- **Sandboxing** — tools that execute code or touch the filesystem/network run inside {{sandbox}} (ties to `agent.tools.sandbox`).
- **Client SHOULD (consumer side):** confirm sensitive operations, show inputs to the user before the call (prevent exfiltration), validate results before passing to the LLM, set per-call timeouts ({{tool_timeout}}), and log usage for audit ({{audit_logging}}).

## 🧪 Validation & Testing
- **Schema contract tests** — every tool's `inputSchema`/`outputSchema` round-trips and rejects malformed args: {{contract_test_approach}}.
- **MCP Inspector / host smoke** — manual + scripted invocation through {{inspector_or_host}}.
- **Fuzz the inputs** — adversarial / boundary inputs per tool to confirm graceful `isError` returns, not crashes: {{fuzz_approach}}.
- **Token-budget assertion** — results stay within the §Result size budget: {{token_budget_test}}.
- **CI gates:** {{ci_gates}}.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
