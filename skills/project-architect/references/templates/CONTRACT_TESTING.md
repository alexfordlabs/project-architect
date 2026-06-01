---
template_name: CONTRACT_TESTING
generate_when: "conditional"
required_decisions:
  - api.contract
optional_decisions:
  - architecture.style
  - architecture.bounded_contexts
  - messaging.broker
  - messaging.async
  - api.style
  - ci.provider
  - testing.framework
depends_on: []
revision_triggers:
  - api.contract
  - architecture.style
  - architecture.bounded_contexts
  - messaging.async
  - ci.provider
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Contract Testing: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This contract-testing design follows **[Pact](https://docs.pact.io/)**, the consumer-driven
> contract (CDC) testing framework. The governing idea from that guidance: Pact is *"in effect,
> 'contract by example'"* — the contract is a collection of concrete request/response pairs,
> each generated *during the execution of the automated consumer tests* (rather than written as
> a static schema up front). This lets each integration be verified **without spinning up both
> services together**. Every choice below is justified against that bar.

## Table of contents
- [🎯 Why Contract Testing Here](#why-contract-testing-here)
- [🔁 The Consumer-Driven Flow](#the-consumer-driven-flow)
- [🗺️ Integration Map (Pacticipants)](#integration-map-pacticipants)
- [🧪 Consumer Side: Generating the Pact](#consumer-side-generating-the-pact)
- [🏗️ Provider Side: Verifying the Pact](#provider-side-verifying-the-pact)
- [🧩 Provider States](#provider-states)
- [📬 Message (Asynchronous) Pacts](#message-asynchronous-pacts)
- [🗄️ The Pact Broker / PactFlow](#the-pact-broker-pactflow)
- [🚦 can-i-deploy: Gating Deployment in CI](#can-i-deploy-gating-deployment-in-ci)
- [🔀 Alternatives: Bi-Directional & Schema-Compat](#alternatives-bi-directional-schema-compat)
- [✅ Pre-Merge / Pre-Deploy Checklist](#pre-merge-pre-deploy-checklist)
- [↻ Revision Log](#revision-log)

## 🎯 Why Contract Testing Here

Pact's documented sweet spot is **microservice architectures where one organisation controls
both the consumer and the provider**, both teams are actively developing, and you want fast
feedback *before* deployment without slow end-to-end tests. State why {{project_name}} qualifies.

| Property | This project |
|---|---|
| Architecture style | `{{architecture_style}}` (microservices / modular monolith / …) |
| Bounded contexts / services | {{bounded_context_count}} — contract testing earns its keep above ~4 |
| Both sides controlled in-org? | {{both_sides_controlled}} (Pact assumes yes) |
| Sync APIs in scope | {{sync_apis}} (`{{api_style}}` — REST / GraphQL / gRPC) |
| Async messages in scope | {{async_in_scope}} (`messaging.async`) |
| Decision: use Pact CDC | `{{api_contract}}` |

> **When NOT to use Pact** (from the docs — record any in-scope edge case and how it's handled):
> public APIs with **unknown consumers**, pass-through/BFF providers that don't validate content,
> stable non-consumer-driven (e.g. OAuth) providers, functional/business-logic testing, UI/browser
> testing, and performance/load testing. Pact checks the **contents and format of requests and
> responses** — not side effects or downstream-integration correctness.
> **Out-of-scope integrations + their substitute coverage:** {{out_of_scope_integrations}}

## 🔁 The Consumer-Driven Flow

The canonical Pact lifecycle, end to end:

```
{{cdc_flow_diagram}}

  1. CONSUMER TEST   — consumer test defines an *interaction* (expected request +
                       minimal expected response) against a *mock provider*; running it
                       generates a *pact file* (JSON) of request/response pairs.
  2. PUBLISH         — consumer CI publishes the pact to the Broker, tagged with the
                       consumer's version + branch.
  3. WEBHOOK         — publishing (or a changed pact) fires a webhook that triggers the
                       provider's verification build.
  4. PROVIDER VERIFY — provider replays each request from the pact against the *real*
                       provider; passes when every response *contains at least* the
                       minimal expected response. Results are published back to the Broker.
  5. can-i-deploy    — both sides query the verification *matrix* before deploying.
```

> Verification is asymmetric on purpose: Pact passes when *"each request generates a response
> that contains at least the data described in the minimal expected response."* A provider may
> add fields without breaking the consumer; it may not remove or change the ones the consumer
> relies on.

## 🗺️ Integration Map (Pacticipants)

Every application in a Pact relationship is a **pacticipant**. List each consumer→provider edge
{{project_name}} owns; one pact file exists per edge.

| Consumer (pacticipant) | Provider (pacticipant) | Interaction(s) | Transport |
|---|---|---|---|
| {{consumer_1}} | {{provider_1}} | {{interactions_1}} | {{transport_1}} (HTTP / message) |
| {{consumer_2}} | {{provider_2}} | {{interactions_2}} | {{transport_2}} |
| {{additional_edges}} | … | … | … |

**Naming convention for pacticipants:** {{pacticipant_naming}} *(must be stable — the Broker
keys the matrix on these names; renaming orphans history).*

## 🧪 Consumer Side: Generating the Pact

The consumer test registers an **interaction** with the **mock provider** via the Pact DSL,
exercises the real consumer client code against the mock, and the framework asserts the actual
request matches the expected one before returning the canned response. **Only specify the fields
the consumer actually uses** — over-specifying makes the contract brittle.

| Concern | Decision for {{project_name}} |
|---|---|
| Pact library / language | `{{pact_library}}` (e.g. pact-js / pact-jvm / pact-python / pact-go / pact_rust FFI) |
| Test framework integration | `{{testing_framework}}` — where consumer pact tests live |
| Pact specification version | `{{pact_spec_version}}` (e.g. v2 / v3 / v4) |
| Matchers used | {{matchers}} — type/regex/`eachLike` matchers, never hard-coded volatile values |
| Pact output dir | {{pact_output_dir}} (e.g. `pacts/`) |

**Publish on consumer CI:**

```
{{publish_command}}
# e.g. pact-broker publish ./pacts \
#        --consumer-app-version "$GIT_SHA" \
#        --branch "$GIT_BRANCH" \
#        --broker-base-url "$PACT_BROKER_BASE_URL" --broker-token "$PACT_BROKER_TOKEN"
```

> Tag/version every publish with the **git SHA** as the consumer app version and the **branch**.
> The Broker versions contracts by content change while tracking the consumer application version —
> this is what the matrix and `can-i-deploy` later key off.

## 🏗️ Provider Side: Verifying the Pact

During verification the Pact framework takes the lead entirely — it fetches the relevant pacts
and replays each request against the running provider, then checks each actual response against
the minimal expected response in the pact. Configure which pacts to fetch via **consumer
version selectors** (don't verify every pact ever published — verify the ones deployed/in-flight).

| Concern | Decision for {{project_name}} |
|---|---|
| Provider verifier | `{{provider_verifier}}` (language-native verifier / `pact_verifier_cli`) |
| Consumer version selectors | {{consumer_version_selectors}} (e.g. `mainBranch`, `deployedOrReleased`, matching branch) |
| Pending pacts | {{pending_pacts}} — enable so a *new, unverified* consumer pact can't fail the provider build |
| WIP pacts | {{wip_pacts}} — include work-in-progress pacts from consumer feature branches as non-blocking |
| Publish verification results | {{publish_verification_results}} — **required** so the matrix knows the outcome |
| Provider app version / branch | {{provider_app_version}} (git SHA) + branch |

> **Always publish verification results back to the Broker** (with the provider version + branch).
> A verification that isn't published is invisible to the matrix, so `can-i-deploy` can't see it.

## 🧩 Provider States

When an interaction needs preconditions, Pact uses **provider states** — the necessary
preconditions for a particular test scenario to run (for example, the existence of specific
user data), analogous to a Cucumber `Given`. Rather than one test that creates then reads data,
write separate interactions and attach a named state (the `given(...)` / provider-state string)
the provider sets up before replay.

| Provider state string | Set-up performed before verification | Owning interaction |
|---|---|---|
| `{{state_1}}` (e.g. "user 123 exists") | {{state_1_setup}} | {{state_1_interaction}} |
| `{{state_2}}` | {{state_2_setup}} | {{state_2_interaction}} |
| {{additional_states}} | … | … |

- **State-handler mechanism:** {{state_handler}} — the provider-side hook (HTTP state-change
  endpoint or in-process handler) that seeds/tears down data per state, keyed by the state string.
- **Isolation:** {{state_isolation}} — each state sets up only what it needs; states must not leak
  data into one another. Use a real/seeded test DB or fixtures, reset between interactions.

## 📬 Message (Asynchronous) Pacts

> Include only if `{{async_in_scope}}` is true. Omit this section for a purely synchronous-API project.

Pact supports **message pacts** for asynchronous / event-driven integrations (queues, topics,
streams). Instead of an HTTP request/response, the contract captures the **message body + metadata**
a consumer expects; the test verifies the consumer's *message handler* can process it, and the
provider verifies it can *produce* a message matching the contract — the broker/transport itself is
mocked out (Pact tests the message content, not the delivery infrastructure).

| Concern | Decision for {{project_name}} |
|---|---|
| Message broker / transport | `{{messaging_broker}}` (e.g. Kafka / RabbitMQ / SQS / SNS) |
| Message pact spec | {{message_pact_spec}} (Pact v3+ for messages; v4 for richer interaction types) |
| Consumer = message handler | {{message_consumer}} — the function under test that consumes the message |
| Provider = message producer | {{message_producer}} — verified by producing a message that matches |
| Metadata / headers contracted | {{message_metadata}} (e.g. content-type, partition key, schema id) |

## 🗄️ The Pact Broker / PactFlow

The **Pact Broker** is *"an application for sharing consumer driven contracts and verification
results."* It is the source of truth that decouples consumer and provider CI pipelines.

| Concern | Decision for {{project_name}} |
|---|---|
| Broker | `{{broker_choice}}` (self-hosted Pact Broker / **PactFlow** managed / OSS docker image) |
| Base URL | {{broker_base_url}} |
| Auth | {{broker_auth}} — token / basic auth (store via the project's secret mechanism, never in repo) |
| Branches | {{broker_branches}} — main + feature branches drive selectors & WIP pacts |
| Environments | {{broker_environments}} — e.g. `test`, `staging`, `production` (used by `can-i-deploy`) |
| Webhooks | {{broker_webhooks}} — on pact publish / changed pact → trigger provider verification build |

What the Broker stores and exposes:

- **Pacts** — consumer-generated JSON contracts, auto-versioned by content with the consumer app version.
- **Verification results** — provider outcomes, keyed to provider version + branch.
- **The matrix** — the grid of every consumer/provider version pair that has been tested together;
  shows *"which versions can be safely deployed together."*
- **Webhooks** — automation hooks so the consumer and provider pipelines stay decoupled yet coordinated.

> **PactFlow** is the fully managed Pact Broker (adds bi-directional contracts, secrets, RBAC, a free
> Developer Plan). Choose managed vs. self-hosted explicitly: {{broker_choice_rationale}}.

## 🚦 can-i-deploy: Gating Deployment in CI

`can-i-deploy` is the deployment safety gate. It queries the **matrix** to ensure *"there is a
successful verification result between the version that is about to be deployed, and all the
versions of the integrated applications that are already in that environment."* Exit `0` = safe,
exit `1` = unsafe — so it gates the pipeline directly.

```
{{can_i_deploy_command}}
# Gate before deploy:
#   pact-broker can-i-deploy \
#     --pacticipant {{this_pacticipant}} \
#     --version "$GIT_SHA" \
#     --to-environment {{target_environment}}
#   → "Computer says yes \o/"  (exit 0)  ⇒ proceed to deploy
#
# After a successful deploy, record it so future checks know what's live:
#   pact-broker record-deployment \
#     --pacticipant {{this_pacticipant}} \
#     --version "$GIT_SHA" \
#     --environment {{target_environment}}
```

| CI step | Tool / command | When |
|---|---|---|
| Publish pact (consumer) | {{ci_publish_step}} | every consumer build |
| Verify pacts (provider) | {{ci_verify_step}} | provider build + webhook-triggered |
| Gate deploy | `can-i-deploy --to-environment {{target_environment}}` | before every deploy |
| Record deployment | `record-deployment` (or `record-release`) | after every successful deploy/release |
| CI provider | `{{ci_provider}}` | — |

> Use **`record-deployment`** for environments where one version is "live" at a time (it replaces the
> previous), and **`record-release`** for catalogues where multiple versions can be available at once.
> Without recording deployments, `can-i-deploy` can't know which versions are actually in an environment.

## 🔀 Alternatives: Bi-Directional & Schema-Compat

CDC isn't always the right tool (see the *when NOT to use Pact* list above). Record which mechanism
governs each integration:

| Mechanism | What it is | Use when | Used here? |
|---|---|---|---|
| **Pact CDC** (default) | Consumer examples drive a verified contract. | Both sides in-org, both actively developed. | {{uses_pact_cdc}} |
| **Bi-Directional Contracts** (PactFlow) | Provider supplies its own contract (an **OpenAPI spec**); Broker cross-checks the consumer's pact against it — no live provider replay needed. | Provider already maintains an OpenAPI spec, or can't run consumer-driven verification. | {{uses_bidirectional}} |
| **OpenAPI diff** | Compare successive OpenAPI specs to flag breaking schema changes (e.g. `oasdiff`). | Public-ish API with a spec but unknown/uncontrolled consumers. | {{uses_openapi_diff}} |
| **Buf breaking** | `buf breaking` detects backward-incompatible changes to Protobuf/gRPC schemas in CI. | gRPC / Protobuf interfaces. | {{uses_buf_breaking}} |
| **Schema-registry compat** | Broker-enforced subject compatibility (e.g. Avro/JSON Schema BACKWARD/FORWARD). | Event streams with a schema registry (Kafka). | {{uses_schema_registry}} |

**Decision per integration:** {{alternative_decision}} *(default to Pact CDC for in-org synchronous
services; reach for a schema-compat alternative where the consumer is unknown or a canonical spec
already exists).*

## ✅ Pre-Merge / Pre-Deploy Checklist

Run before merging a contract-affecting change and before each deploy. Confirm each for {{project_name}}:

- [ ] Consumer tests specify **only the fields the consumer uses** (matchers, no volatile literals).
- [ ] Pacts are **published with the git SHA as version + the branch** on every consumer build.
- [ ] Provider verification uses **consumer version selectors** (not "verify everything") and has **pending pacts** enabled.
- [ ] Provider **publishes verification results** back to the Broker (with version + branch).
- [ ] Every interaction needing data has a named **provider state** with an isolated set-up handler.
- [ ] A webhook re-verifies the provider when a **changed pact** is published.
- [ ] `can-i-deploy --to-environment {{target_environment}}` gates **every** deploy (build fails on exit 1).
- [ ] `record-deployment` / `record-release` runs after **every** successful deploy.
- [ ] Async edges (if any) are covered by **message pacts**; broker/transport infra has its own tests.
- [ ] Integrations Pact doesn't fit use the chosen **alternative** ({{alternative_decision}}).
- [ ] `{{additional_checklist_item}}`

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
