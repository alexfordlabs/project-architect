---
template_name: LLM_OBSERVABILITY
generate_when: "conditional"
required_decisions: [ai.enabled, scale]
optional_decisions:
  - ai.provider
  - ai.model
  - ai.agent
  - ai.framework
  - ai.rag.enabled
  - agent.autonomy
  - observability.tracing
  - observability.metrics
  - observability.platform
depends_on: []
revision_triggers:
  - ai.enabled
  - ai.provider
  - ai.model
  - ai.agent
  - observability.tracing
  - observability.metrics
  - observability.platform
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# LLM Observability: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document defines how {{project_name}} instruments, traces, meters, and audits its LLM
> calls. It is grounded in the **[OpenTelemetry Semantic Conventions for Generative AI Systems](https://opentelemetry.io/docs/specs/semconv/gen-ai/)**
> (Experimental, `gen_ai.*` namespace). Standardising on these conventions means traces and
> metrics emitted by {{project_name}} are portable across any OTLP-compatible backend
> ({{observability_platform}}) and comparable with the rest of the industry, instead of a
> bespoke schema only this project understands. Where this project predates a vendor SDK's
> migration to `gen_ai.provider.name` (the attribute formerly emitted as `gen_ai.system`),
> note the bridge below.

## Table of contents
- [Why GenAI Observability Here](#why-genai-observability-here)
- [Instrumentation Strategy](#instrumentation-strategy)
- [📐 Span Conventions](#span-conventions)
- [📊 Metric Conventions](#metric-conventions)
- [🪵 Event & Content Capture](#event-content-capture)
- [🔐 Sensitive-Data & Privacy Controls](#sensitive-data-privacy-controls)
- [🤖 Agent & Tool Spans](#agent-tool-spans)
- [💰 Cost & Token Accounting](#cost-token-accounting)
- [🚨 Dashboards, SLOs & Alerting](#dashboards-slos-alerting)
- [🧪 Verification](#verification)
- [↻ Revision Log](#revision-log)

## Why GenAI Observability Here

LLM calls fail in ways ordinary RPCs do not — silent quality regressions, runaway token
spend, latency cliffs under load, and non-deterministic output. **Scale = `{{scale}}`** for
{{project_name}}, which is past the `hobby` threshold, so we treat LLM telemetry as a
first-class operational signal rather than ad-hoc logging.

| Question we must answer in production | Signal that answers it |
|---|---|
| Is a model/prompt change degrading latency? | `gen_ai.client.operation.duration` histogram, sliced by `gen_ai.request.model` |
| Are we about to blow the token budget? | `gen_ai.client.token.usage` histogram, by `gen_ai.token.type` |
| Which call errored, and why? | Span status + `error.type` + `gen_ai.response.finish_reasons` |
| What did the model actually see/produce? | Opt-in `gen_ai.input.messages` / `gen_ai.output.messages` (privacy-gated) |
| How does one user turn fan out across calls/tools? | Trace correlation via `gen_ai.conversation.id` |

## Instrumentation Strategy

- **Provider in play:** `{{ai_provider}}` → `gen_ai.provider.name = {{gen_ai_provider_value}}`
  (one of the spec enum: `anthropic`, `openai`, `aws.bedrock`, `azure.ai.inference`,
  `azure.ai.openai`, `gcp.gemini`, `gcp.vertex_ai`, `cohere`, `mistral_ai`, `deepseek`,
  `groq`, `perplexity`, `x_ai`, `ibm.watsonx.ai`).
- **Primary model:** `{{primary_model}}` → emitted as `gen_ai.request.model`; the model that
  actually served the response is `gen_ai.response.model`.
- **Instrumentation layer:** {{instrumentation_layer}} — auto-instrumentation (e.g. OpenLLMetry /
  OpenInference / vendor OTel SDK) vs. hand-rolled spans around the client call. Prefer
  auto-instrumentation that already emits `gen_ai.*` so the schema stays canonical.
- **Convention stability flag:** set `OTEL_SEMCONV_STABILITY_OPT_IN={{semconv_opt_in}}`
  (e.g. `gen_ai_latest_experimental`) so the SDK emits the current `gen_ai.*` shape rather
  than a frozen older one.
- **Exporter / backend:** {{otlp_exporter}} → {{observability_platform}} over OTLP.
- **Resource attributes:** `service.name = {{service_name}}`, `service.version =
  {{service_version}}`, `deployment.environment.name = {{deployment_environment}}`.

## 📐 Span Conventions

Every inference call MUST emit a span. Per the GenAI **model span** convention:

- **Span name:** `{gen_ai.operation.name} {gen_ai.request.model}` — e.g. `chat {{primary_model}}`.
- **Span kind:** `CLIENT` (remote model API) or `INTERNAL` (in-process model).
- **`gen_ai.operation.name`** (Required) — one of `chat`, `text_completion`,
  `generate_content`, `embeddings`, `execute_tool`, `create_agent`, `invoke_agent`,
  `invoke_workflow`, `retrieval`. This project uses: `{{operation_names_used}}`.

**Inference-span attributes adopted by {{project_name}}:**

| Attribute | Requirement (spec) | Captured? | Notes |
|---|---|---|---|
| `gen_ai.operation.name` | Required | {{capture_operation_name}} | enum above |
| `gen_ai.provider.name` | Required | {{capture_provider_name}} | `{{gen_ai_provider_value}}` |
| `gen_ai.request.model` | Conditionally Required | {{capture_request_model}} | the model we asked for |
| `gen_ai.response.model` | Recommended | {{capture_response_model}} | the model that answered |
| `gen_ai.response.id` | Recommended | {{capture_response_id}} | correlate to provider logs |
| `gen_ai.response.finish_reasons` | Recommended | {{capture_finish_reasons}} | e.g. `stop`, `length`, `tool_calls`, `content_filter` |
| `gen_ai.usage.input_tokens` | Recommended | {{capture_input_tokens}} | prompt tokens |
| `gen_ai.usage.output_tokens` | Recommended | {{capture_output_tokens}} | completion tokens |
| `gen_ai.usage.cache_read.input_tokens` | Recommended | {{capture_cache_read_tokens}} | prompt-cache hits (cost-relevant) |
| `gen_ai.usage.reasoning.output_tokens` | Recommended | {{capture_reasoning_tokens}} | thinking/reasoning tokens |
| `gen_ai.request.temperature` | Recommended | {{capture_temperature}} | sampling param |
| `gen_ai.request.top_p` | Recommended | {{capture_top_p}} | sampling param |
| `gen_ai.request.max_tokens` | Recommended | {{capture_max_tokens}} | output cap |
| `gen_ai.request.stop_sequences` | Recommended | {{capture_stop_sequences}} | — |
| `gen_ai.output.type` | Conditionally Required | {{capture_output_type}} | `text` / `json` / `image` / `speech` |
| `gen_ai.conversation.id` | Conditionally Required | {{capture_conversation_id}} | thread/session correlation |
| `gen_ai.request.choice.count` | Conditionally Required | {{capture_choice_count}} | set only if ≠ 1 |
| `error.type` | Conditionally Required | {{capture_error_type}} | set on error; pairs with span status `ERROR` |
| `server.address` / `server.port` | Recommended / Cond. | {{capture_server_address}} | endpoint host:port |

> **Error handling:** when a call fails, set the span status to `ERROR` and populate
> `error.type` with the exception class or a domain-specific code ({{error_type_taxonomy}}).
> A 429 rate-limit, a timeout, and a content-filter refusal are distinct `error.type`
> values — do not collapse them.

## 📊 Metric Conventions

{{project_name}} emits the GenAI **client metrics** (all histograms) so dashboards aggregate
without re-deriving from spans. The spec mandates these explicit histogram bucket boundaries —
do **not** override them unless {{metric_bucket_justification}}, because shared boundaries are
what make cross-service comparison meaningful.

| Metric | Instrument | Unit | Explicit buckets (spec) | Adopted? |
|---|---|---|---|---|
| `gen_ai.client.token.usage` | Histogram | `{token}` | `1, 4, 16, 64, 256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304, 16777216, 67108864` | {{adopt_token_usage}} |
| `gen_ai.client.operation.duration` | Histogram | `s` | `0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92` | {{adopt_operation_duration}} |
| `gen_ai.client.operation.time_to_first_chunk` | Histogram | `s` | same as `operation.duration` | {{adopt_ttfc}} |
| `gen_ai.client.operation.time_per_output_chunk` | Histogram | `s` | same as `operation.duration` | {{adopt_tpoc}} |

If {{project_name}} **serves** a model (self-hosted inference), also emit the **server
metrics** — note their different, finer buckets tuned for streaming:

| Metric | Unit | Explicit buckets (spec) | Adopted? |
|---|---|---|---|
| `gen_ai.server.request.duration` | `s` | `0.01 … 81.92` (same as client duration) | {{adopt_server_duration}} |
| `gen_ai.server.time_to_first_token` | `s` | `0.001, 0.005, 0.01, 0.02, 0.04, 0.06, 0.08, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0` | {{adopt_ttft}} |
| `gen_ai.server.time_per_output_token` | `s` | `0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 2.5` | {{adopt_tpot}} |

**Required metric dimensions:** `gen_ai.operation.name`, `gen_ai.provider.name`; plus
`gen_ai.token.type` (`input` / `output`) on `token.usage`, and `error.type` on the duration
metrics. Recommended: `gen_ai.request.model`, `gen_ai.response.model`, `server.address`,
`server.port`. **Cardinality guard:** never add `gen_ai.conversation.id`, user IDs, or raw
prompt text as metric attributes — they are unbounded and will explode the time-series count
({{cardinality_policy}}).

## 🪵 Event & Content Capture

Prompt and completion content is captured via the GenAI **events/log** convention, NOT as
default span attributes. The relevant fields — `gen_ai.input.messages`,
`gen_ai.output.messages`, `gen_ai.system_instructions`, and `gen_ai.tool.definitions` — are
**Opt-In** in the spec precisely because they "are likely to contain sensitive information."

- **Content capture for {{project_name}}:** {{content_capture_policy}} — enabled / disabled /
  sampled / redacted-only.
- **Opt-in mechanism:** content capture is off by default; enable it explicitly via the
  instrumentation's capture flag (e.g. `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT={{capture_message_content_flag}}`)
  and only in environments cleared for it (`deployment.environment.name` ∈ {{content_capture_environments}}).
- **Message schema:** messages follow the spec's structured JSON message schema (role +
  typed content parts) recorded on events; if the backend can't store structured event
  bodies, fall back to JSON-string span attributes. Format chosen: {{message_record_format}}.
- **Sampling:** {{content_sample_rate}} (capture full content on an error/anomaly sample,
  metadata-only otherwise) to bound storage cost and exposure.

## 🔐 Sensitive-Data & Privacy Controls

Telemetry is a data-egress path. Controls before any content leaves the process:

- **Redaction pipeline:** {{redaction_pipeline}} — PII / secret scrubbing on
  `gen_ai.input.messages` and `gen_ai.output.messages` prior to export (regex + classifier).
- **Field allow/deny list:** {{telemetry_field_policy}} — which attributes are ever permitted
  to carry free text; `gen_ai.system_instructions` is treated as confidential by default.
- **Retention & access:** {{telemetry_retention}} on {{observability_platform}}, with access
  scoped to {{telemetry_access_roles}}.
- **Regulated data:** {{regulated_telemetry_note}} — if regulated data can appear in prompts,
  content capture defaults to OFF and requires the redaction pipeline to be proven; cross-ref
  the data-handling / AI-safety docs.

## 🤖 Agent & Tool Spans

> Applies when `ai.agent` is true (autonomy: `{{agent_autonomy}}`). Omit if {{project_name}}
> is a single-shot inference feature.

The GenAI **agent** and **tool** span conventions make multi-step trajectories legible:

- **`create_agent {gen_ai.agent.name}`** (kind `CLIENT`) — agent provisioning. Attributes:
  `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.description`, `gen_ai.request.model`.
- **`invoke_agent {gen_ai.agent.name}`** (kind `CLIENT` for remote, `INTERNAL` for
  in-process frameworks like LangChain / CrewAI) — one agent run. Carries
  `gen_ai.conversation.id` so the whole turn correlates.
- **`execute_tool {gen_ai.tool.name}`** (kind `INTERNAL`) — each tool call. Required:
  `gen_ai.operation.name` (= `execute_tool`), `gen_ai.tool.name`. Recommended:
  `gen_ai.tool.call.id`, `gen_ai.tool.description`, `gen_ai.tool.type`. Opt-In (sensitive):
  `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result`.

| Span concern | Decision for {{project_name}} |
|---|---|
| Agent naming → `gen_ai.agent.name` | {{agent_name_convention}} |
| Tool spans as children of invoke_agent? | {{tool_span_nesting}} |
| Capture tool args/results? (Opt-In) | {{capture_tool_io}} |
| Loop-iteration / step count surfaced | {{agent_step_metric}} |

> Cross-reference the agent-design doc for the loop topology; this section governs only how
> that trajectory is *observed*.

## 💰 Cost & Token Accounting

Token usage is the cost driver and the denial-of-wallet attack surface (OWASP LLM10).

- **Cost derivation:** {{cost_model}} — map `gen_ai.usage.input_tokens` /
  `gen_ai.usage.output_tokens` (and cache-read / reasoning token splits) to per-model unit
  prices `{{token_unit_prices}}`. Reasoning and cache-read tokens are priced differently —
  keep them as separate series.
- **Budget signal:** {{cost_budget_signal}} — rolling token/cost aggregation per
  `{{cost_attribution_dimension}}` (per user / per org / per feature).
- **Anomaly detection:** {{cost_anomaly_policy}} — alert on token-usage histogram tail growth
  or a spike in `length` finish-reasons (truncation = wasted spend).

## 🚨 Dashboards, SLOs & Alerting

On {{observability_platform}}, built from the spans + metrics above:

| Dashboard / SLO | Source signal | Threshold |
|---|---|---|
| p95 inference latency | `gen_ai.client.operation.duration` | {{latency_slo}} |
| Error rate by `error.type` | span status + `error.type` | {{error_rate_slo}} |
| Token spend / hour | `gen_ai.client.token.usage` | {{token_budget_alert}} |
| Truncation rate (`length` finishes) | `gen_ai.response.finish_reasons` | {{truncation_alert}} |
| TTFT (streaming) | `gen_ai.server.time_to_first_token` | {{ttft_slo}} |

- **Alert routing:** {{alert_routing}}.
- **Trace correlation:** link an alerting metric back to exemplar traces via
  `gen_ai.conversation.id` / `gen_ai.response.id` for root-cause drill-down.

## 🧪 Verification

How we prove the instrumentation actually works before relying on it:

- **Span-shape test:** {{span_assertion_test}} — assert a sample call emits a span named
  `{gen_ai.operation.name} {gen_ai.request.model}` with the Required attributes present.
- **Metric-emission test:** {{metric_assertion_test}} — confirm `gen_ai.client.token.usage`
  and `gen_ai.client.operation.duration` are recorded with the spec buckets.
- **Privacy test:** {{privacy_assertion_test}} — confirm content fields are absent when
  capture is OFF and redacted when ON.
- **Backend round-trip:** {{backend_smoke_test}} — a synthetic call appears correctly in
  {{observability_platform}}.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
