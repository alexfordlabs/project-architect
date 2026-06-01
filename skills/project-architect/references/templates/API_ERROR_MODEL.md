---
template_name: API_ERROR_MODEL
generate_when: "conditional"
required_decisions:
  - api.enabled
optional_decisions:
  - api.style
  - api.versioning
  - api.error_format
  - api.problem_type_base_uri
  - api.localization
  - observability.tracing
depends_on: []
revision_triggers:
  - api.enabled
  - api.style
  - api.error_format
  - api.problem_type_base_uri
  - api.versioning
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# API Error Model: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the API error-contract design doc for **{{project_name}}**. Its structure and
> guidance follow **[RFC 9457 — Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc9457)**
> (which obsoletes RFC 7807). RFC 9457 defines a *machine-readable* format for carrying the
> details of errors in an HTTP response so clients don't have to invent one-off, ad-hoc error
> structures per API. The governing rule: **a problem detail is a data model, not a free-form
> blob — consumers must not assume any structure beyond what they are documented to expect.**

## Table of contents
- [📐 Error Contract Overview](#error-contract-overview)
- [📬 Media Types & Content Negotiation](#media-types-content-negotiation)
- [🧱 Standard Members](#standard-members)
- [🔗 Problem Type URIs & Registry](#problem-type-uris-registry)
- [➕ Extension Members](#extension-members)
- [🗂️ Problem Type Catalog](#problem-type-catalog)
- [🧪 Worked Examples](#worked-examples)
- [↔️ HTTP Status Code Relationship](#http-status-code-relationship)
- [🤝 Consumer Processing Rules](#consumer-processing-rules)
- [🔐 Security Considerations](#security-considerations)
- [🌍 Localization](#localization)
- [🔧 Implementation Packages](#implementation-packages)
- [↻ Revision Log](#revision-log)

## 📐 Error Contract Overview

How {{project_name}} represents *all* error responses across its HTTP surface.

- **API style:** `{{api_style}}` (REST / RPC-over-HTTP / hypermedia)
- **Error format:** `{{api_error_format}}` — this project commits to **RFC 9457 Problem Details**
  as the canonical error body for every 4xx/5xx response (state any documented exceptions below).
- **Scope:** {{error_scope}} — which routes/resources emit problem details; whether a parallel
  format is used for non-error representations.
- **Versioning interaction:** {{versioning_note}} (`api.versioning`) — error contracts are part
  of the public API surface; changing a problem `type` URI or removing an extension member is a
  breaking change.

> RFC 9457 §1: "This specification's aim is to define common error formats for applications that
> need one so that they aren't required to define their own or, worse, tempted to redefine the
> semantics of existing HTTP status codes."

## 📬 Media Types & Content Negotiation

Problem details are serialized using one of two registered media types defined by RFC 9457 §3:

| Serialization | Media type | Used by {{project_name}}? |
|---|---|---|
| JSON | **`application/problem+json`** | {{uses_problem_json}} |
| XML | **`application/problem+xml`** (per the schema in RFC 9457 Appendix B) | {{uses_problem_xml}} |

- **Default content type for error responses:** `{{default_error_content_type}}`
  (`application/problem+json` unless an XML-first contract requires otherwise).
- **Content negotiation:** {{content_negotiation_policy}} — how the server selects the
  serialization (typically honor `Accept`; fall back to `application/problem+json`).
- **`charset`:** {{charset_policy}} (e.g. `application/problem+json; charset=utf-8`).

> Note: the `+json`/`+xml` structured-syntax suffix means generic JSON/XML tooling can parse the
> body; the dedicated media type signals *this is a problem detail* without inspecting the payload.

## 🧱 Standard Members

The data model is a single top-level object with five reserved members (RFC 9457 §3.1). **All
five are optional**; define which {{project_name}} populates and when.

| Member | Type | Default | Meaning | Populated by us? |
|---|---|---|---|---|
| `type` | URI reference (string) | **`about:blank`** | Primary identifier of the *problem type*. Consumers MUST use this (after resolution, if relative) as the identity of the problem. | {{populates_type}} |
| `status` | integer | — | The HTTP status code for *this occurrence*. **Advisory only** — duplicates the response status line. | {{populates_status}} |
| `title` | string | — | Short, human-readable summary of the problem *type*. SHOULD NOT change between occurrences (except for localization). | {{populates_title}} |
| `detail` | string | — | Human-readable explanation specific to *this occurrence*. Consumers SHOULD NOT parse it for data — use extensions instead. | {{populates_detail}} |
| `instance` | URI reference (string) | — | Identifies the specific *occurrence* of the problem. | {{populates_instance}} |

**Member rules this project enforces:**

- **`type` default = `about:blank`.** When `type` is absent it is assumed to be `about:blank`,
  which means "the problem has no semantics beyond the HTTP status code." When we emit
  `about:blank`, `title` SHOULD equal the recommended HTTP status phrase for the code (e.g.
  `"Not Found"` for 404). Our policy: {{about_blank_policy}}.
- **`title` is type-level, `detail` is occurrence-level.** `title` is stable per problem type;
  `detail` varies per request. {{title_detail_policy}}
- **`status` is advisory.** It MUST match the HTTP status line; we treat the status line as
  authoritative (proxies/load balancers ignore the body). Whether we include `status` at all:
  {{include_status_member}}.
- **`instance`:** {{instance_policy}} — RFC 9457 RECOMMENDS absolute URIs, and when relative,
  the full path (e.g. `/instances/123`). If dereferenceable, what it returns: {{instance_deref}}.

## 🔗 Problem Type URIs & Registry

Each distinct error condition that carries semantics beyond a bare status code gets its own
stable `type` URI.

- **Problem-type base URI:** `{{problem_type_base_uri}}` (e.g.
  `https://{{domain}}/probs/` or `https://{{domain}}/errors/`). Every project-defined `type`
  is a URI under this base.
- **Dereferenceability:** RFC 9457 §3.1.1 — if a `type` URI is a locator (`http`/`https`),
  dereferencing it SHOULD return *human-readable documentation* (e.g. HTML) for that problem
  type. Where those docs live: {{type_docs_location}}.
  > Consumers SHOULD NOT automatically dereference `type` URIs except when surfacing info to
  > developers (e.g. a debugging tool). Our docs at the URI are for humans, not for runtime
  > branching.
- **Stability:** A `type` URI is a published identifier — once shipped, it is **immutable**.
  Retiring/renaming a `type` is a breaking API change. {{type_stability_policy}}
- **Registered types:** RFC 9457 establishes the IANA **"HTTP Problem Types" registry** for
  common, reusable problem type URIs. Whether {{project_name}} reuses any registered types
  (vs. minting its own): {{registered_types_used}}.

## ➕ Extension Members

Per RFC 9457 §3.2, a problem type MAY define additional members beyond the five reserved ones.
This is the *correct* place to put machine-readable, occurrence-specific data — NOT in `detail`.

**Extension naming rules (RFC 9457 §4.2):** names SHOULD start with a letter (ALPHA), comprise
characters from `ALPHA`, `DIGIT`, and `_` (so they serialize outside JSON too), and SHOULD be
three characters or longer.

| Extension member | Type | Defined on which problem type(s) | Meaning |
|---|---|---|---|
| `{{ext_1_name}}` | {{ext_1_type}} | {{ext_1_scope}} | {{ext_1_meaning}} |
| `{{ext_2_name}}` | {{ext_2_type}} | {{ext_2_scope}} | {{ext_2_meaning}} |
| `{{additional_extensions}}` | … | … | … |

**Common extension patterns for {{project_name}}** (define those used):

- **Field-level validation errors** — e.g. an `errors`/`invalid_params` array of
  `{ "name": "<field>", "reason": "<msg>" }` for 422 responses. Shape used: {{validation_ext_shape}}.
- **Correlation / trace id** — e.g. `trace_id` tying the error to a distributed trace
  (`observability.tracing`). Member used: {{trace_id_ext}}.
- **Retry guidance** — e.g. surfacing retry-after or quota reset alongside the standard
  `Retry-After` header. {{retry_ext}}.

> A client that doesn't recognize an extension **MUST ignore it** (RFC 9457 §3.2). This is what
> lets us add fields later without versioning the error contract.

## 🗂️ Problem Type Catalog

The authoritative list of problem types {{project_name}} emits. This table is the contract.

| `type` URI | `title` | Typical `status` | Extensions | When emitted |
|---|---|---|---|---|
| `{{base}}/{{prob_1_slug}}` | {{prob_1_title}} | {{prob_1_status}} | {{prob_1_ext}} | {{prob_1_when}} |
| `{{base}}/{{prob_2_slug}}` | {{prob_2_title}} | {{prob_2_status}} | {{prob_2_ext}} | {{prob_2_when}} |
| `{{base}}/{{prob_3_slug}}` | {{prob_3_title}} | {{prob_3_status}} | {{prob_3_ext}} | {{prob_3_when}} |
| `about:blank` | _(HTTP status phrase)_ | {{generic_statuses}} | — | Errors with no semantics beyond the status code |
| {{additional_problem_types}} | … | … | … | … |

## 🧪 Worked Examples

**Validation failure (HTTP 422), `application/problem+json`** — extension members carry the
structured field errors; `detail` stays human-readable:

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json
Content-Language: en

{
  "type": "{{base}}/validation-error",
  "title": "Your request parameters didn't validate.",
  "status": 422,
  "detail": "{{example_validation_detail}}",
  "instance": "{{example_instance_uri}}",
  "{{validation_ext_member}}": [
    { "name": "{{example_field}}", "reason": "{{example_reason}}" }
  ]
}
```

**Bare status (HTTP 404) with `about:blank`** — no extra semantics, `title` mirrors the status
phrase:

```http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404
}
```

*(Add a 401/403 auth example, a 429 rate-limit example with the `Retry-After` header, and a 500
example here as {{project_name}}'s surface requires — never leak stack traces, see Security.)*

## ↔️ HTTP Status Code Relationship

- The **HTTP status line is authoritative.** The `status` member only duplicates it for the
  consumer's convenience and MAY be omitted. Generic HTTP intermediaries (proxies, load
  balancers, firewalls, scanners) do not read the body, so the two MUST agree.
- A single HTTP status code can map to **multiple problem types** (e.g. several distinct 400
  conditions), and that's the point — the `type` URI disambiguates what the status alone can't.
- **Don't reach for problem details when the status code suffices.** RFC 9457 §3: "defined HTTP
  status codes cover many situations with no need to convey extra detail." Use `about:blank`
  (or no body) for those. Project mapping: {{status_to_type_mapping}}.

## 🤝 Consumer Processing Rules

How clients of {{project_name}} (and our own SDKs) MUST parse error bodies (RFC 9457 §3.1, §3.2):

1. **Identify by `type`, not `status` or `title`.** The `type` URI (resolved if relative) is the
   problem's primary identifier. Branch on it; never string-match `title` or `detail`.
2. **Ignore unrecognized extension members** — this is mandatory and is what keeps the contract
   forward-compatible.
3. **Type-mismatch → ignore the member.** "If a member's value type does not match the specified
   type, the member MUST be ignored — i.e., processing will continue as if the member had not
   been present."
4. **Treat `detail` as human-facing only** — do not parse it for data; read the corresponding
   extension member instead.
5. **Do not auto-dereference `type`/`instance` URIs** at runtime (only when surfacing info to a
   developer/debugging tool).

Where these rules are enforced for our own client SDK: {{client_sdk_enforcement}}.

## 🔐 Security Considerations

RFC 9457 §5 — error detail is an information-disclosure surface. Vet every member before it ships.

- **No implementation leakage.** Never expose stack traces, internal hostnames, SQL, file paths,
  framework versions, or raw exception text via `detail`, `instance`, or any extension.
  RFC 9457 explicitly warns against making stack dumps reachable through the HTTP interface.
  Our scrubbing policy: {{detail_scrubbing_policy}}.
- **No privacy/enumeration leaks.** Don't let error responses confirm the existence of resources
  or accounts an unauthenticated caller shouldn't know about (e.g. login should not reveal
  "user exists" vs "wrong password" via distinct types). {{enumeration_policy}}
- **Vet new problem types.** When defining a `type`, scrutinize what it reveals about system
  internals; least-information by default. {{new_type_review_gate}}.
- **`instance` URIs** that are dereferenceable must themselves be access-controlled and must not
  leak occurrence data to unauthorized callers. {{instance_access_control}}
- **Consistent error shape ≠ consistent error timing.** Be mindful of timing oracles in
  auth-related errors. {{timing_policy}}

## 🌍 Localization

`title` and `detail` are human-readable and MAY be localized (`api.localization`).

- **`title` localization:** RFC 9457 allows `title` (and the `about:blank` status phrase) to be
  localized to client preferences. Driven by `Accept-Language`; echoed via `Content-Language`.
  Policy: {{title_localization_policy}}.
- **`type` URIs are NOT localized** — they are stable identifiers. Localization lives only in
  the human-readable members.
- **Strategy:** {{localization_strategy}} (server-side message catalog keyed by problem `type`).

## 🔧 Implementation Packages

Concrete libraries/middleware that produce and consume RFC 9457 problem details — pin versions.

| Layer | Package / mechanism | Notes |
|---|---|---|
| Server (emit) | {{server_problem_lib}} | e.g. framework exception handler → `application/problem+json` |
| Client / SDK (consume) | {{client_problem_lib}} | parses by `type`, ignores unknown extensions |
| Validation → problem mapping | {{validation_mapping_lib}} | maps validation failures to the 422 problem type |
| OpenAPI / schema | {{schema_artifact}} | error responses documented as `application/problem+json` in the API spec |

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
