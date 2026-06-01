---
template_name: DOMAIN_EVENTS
generate_when: "conditional"
required_decisions:
  - architecture.ddd
  - architecture.bounded_contexts
optional_decisions:
  - architecture.event_sourcing
  - architecture.messaging
  - architecture.cqrs
  - data.store
  - stack.language
depends_on:
  - BOUNDED_CONTEXTS
revision_triggers:
  - architecture.bounded_contexts
  - architecture.event_sourcing
  - architecture.messaging
  - architecture.cqrs
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Domain Events: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the domain-events catalog for **{{project_name}}**. It records *the things that
> happen in the domain* that other parts of the system care about. Its structure follows
> Martin Fowler's **[Domain Event](https://martinfowler.com/eaaDev/DomainEvent.html)**
> pattern (12 December 2005), which defines a Domain Event as something that
> **"captures the memory of something interesting which affects the domain."**
> Pair this document with **[BOUNDED_CONTEXTS.md](./BOUNDED_CONTEXTS.md)** — every event
> below is *emitted from* and *consumed within or across* the contexts defined there.

## Table of contents
- [📖 What a Domain Event Is](#what-a-domain-event-is)
- [⏱️ Two Times: Occurred vs. Noticed](#two-times-occurred-vs-noticed)
- [🗂️ Event Catalog](#event-catalog)
- [🔀 Domain Events vs. Integration Events](#domain-events-vs-integration-events)
- [🌩️ Discovery via Event Storming](#discovery-via-event-storming)
- [📐 Event Schema & Naming Convention](#event-schema-naming-convention)
- [🚚 Delivery, Ordering & Idempotency](#delivery-ordering-idempotency)
- [📼 Audit Log & Event Sourcing](#audit-log-event-sourcing)
- [↻ Revision Log](#revision-log)

## 📖 What a Domain Event Is

A **Domain Event** is *a record of something that happened* — a fact, past-tense, immutable
once recorded. Fowler's framing: the event "captures the memory of something interesting
which affects the domain." It is the past tense made first-class — you don't change a Domain
Event; you record a *new* event that supersedes it.

Fowler identifies four pieces of information worth capturing on an event. Map each to
{{project_name}}'s convention:

| Fowler's property | What it is | {{project_name}} mapping |
|---|---|---|
| **Event Type** | The classification of what happened (`OrderPlaced`, `AddressChanged`). | {{event_type_field}} |
| **Subject** | What the event concerns (the entity/aggregate it's about). | {{event_subject_field}} |
| **Occurred Date** | When it happened *in the world*. | {{occurred_field}} |
| **Noticed Date** | When the *system* became aware of it. | {{noticed_field}} |

Fowler further separates the *data* an event carries by mutability:

- **Source data** *(immutable)* — the core facts of what occurred. Never edited after the
  fact. {{source_data_policy}}
- **Processing data** *(mutable)* — the system's responses and derived results from handling
  the event. {{processing_data_policy}}
- **Cached data** *(occasional)* — summarized information rolled up from past events, kept for
  convenience and rebuildable from source. {{cached_data_policy}}

> Why events at all? Fowler: recording domain events creates an **Audit Log** — "a full record
> that is valuable both for audit and debugging purposes" — and it cleanly **separates input
> handling from business-logic processing** (a first layer logs the event; a second layer "can
> then be ignorant of the actual input source, it just reacts to the event and processes it").
> Fowler also notes "clear event streams make it easier for other system to replace some or all
> of an application in the future." For {{project_name}} the load-bearing reason is:
> {{why_events_here}}

## ⏱️ Two Times: Occurred vs. Noticed

Fowler stresses there are **two time points** worth storing on an event: *"the time the event
occurred in the world and the time the event was noticed."* They are frequently not the same.

His canonical example: *"I go to Babur's for a meal on Tuesday… If Babur's uses an old manual
system and doesn't transmit the transaction until Friday, the noticed date would be Friday."*
The meal *occurred* Tuesday; the system *noticed* it Friday.

Getting this wrong corrupts every time-based query and any retroactive correction. Decide
{{project_name}}'s policy:

| Question | Decision |
|---|---|
| Do we record both occurred and noticed time? | {{records_both_times}} |
| Source of `occurred` time (caller-supplied vs. server clock) | {{occurred_source}} |
| Clock authority for `noticed` time (single server clock / NTP / logical clock) | {{noticed_source}} |
| How are late-arriving / out-of-order events handled? | {{late_arrival_policy}} |
| How are retroactive corrections modeled (new compensating event, not edit)? | {{correction_policy}} |

## 🗂️ Event Catalog

The heart of this document. One row per domain event. An event belongs to exactly one
**emitting aggregate** (the consistency boundary that produces it) inside one **bounded
context** (see `BOUNDED_CONTEXTS.md`). Subscribers may live in the same context (domain
event) or another context (integration event — see below).

| Event (past tense) | Trigger (command/action) | Emitting aggregate · context | Payload (source data) | Subscribers | Domain / Integration |
|---|---|---|---|---|---|
| `{{event_1_name}}` | {{event_1_trigger}} | {{event_1_aggregate}} · {{event_1_context}} | {{event_1_payload}} | {{event_1_subscribers}} | {{event_1_scope}} |
| `{{event_2_name}}` | {{event_2_trigger}} | {{event_2_aggregate}} · {{event_2_context}} | {{event_2_payload}} | {{event_2_subscribers}} | {{event_2_scope}} |
| `{{event_3_name}}` | {{event_3_trigger}} | {{event_3_aggregate}} · {{event_3_context}} | {{event_3_payload}} | {{event_3_subscribers}} | {{event_3_scope}} |
| {{additional_events}} | … | … | … | … | … |

**Catalog rules** (apply to every row above):

- **Name in the past tense, in domain language.** `OrderPlaced`, `PaymentCaptured`,
  `AddressChanged` — never `PlaceOrder` (that's the *command*) or `OrderEvent` (no meaning).
  The name is a sentence the business would recognize.
- **One emitting aggregate per event.** The aggregate that owns the state transition is the
  authoritative emitter. Two aggregates emitting "the same" event is a smell — split it.
- **Payload carries source data, not pointers to mutable state.** A subscriber must be able to
  react from the event alone (or with a clearly documented lookup). Capture *what was true at
  the moment it happened*, e.g. the shipping address as recorded, not "go re-read the customer."
- **The trigger is a command or another event.** Record what causes the event so the
  cause→effect chain is legible end-to-end.

## 🔀 Domain Events vs. Integration Events

A single label "event" hides a sharp boundary that maps directly onto `BOUNDED_CONTEXTS.md`:

| | **Domain event** | **Integration event** |
|---|---|---|
| Scope | *Inside* one bounded context | *Across* context / service boundaries |
| Audience | Other aggregates / handlers in the same context | Other contexts, other services, external consumers |
| Coupling | Can share the domain model | Decoupled — published as a stable contract |
| Schema stability | May evolve with the model | Versioned, backward-compatible contract |
| Transport | In-process bus / mediator (often) | Durable broker / message bus |

- **In-context domain events** for {{project_name}}: {{in_context_events}}
- **Cross-context integration events** for {{project_name}}: {{cross_context_events}}
- **Translation at the boundary** — how a domain event becomes a published integration event
  (anti-corruption layer / outbound translator; the published shape is *not* the internal one):
  {{event_translation_policy}}

> Keep the internal domain model out of the published contract. A leaked internal event shape
> becomes an accidental public API that every downstream context pins to.

## 🌩️ Discovery via Event Storming

The events above weren't guessed — they were *discovered*. **Event Storming** (Alberto
Brandolini's workshop technique) is the recommended discovery method: gather domain experts
and developers at a wall, surface every **domain event** (orange stickies, past tense) along a
timeline, then attach the **commands** that cause them, the **aggregates** that own them, the
**actors** who trigger them, and the **policies** ("whenever X happened, do Y") that chain one
event to the next.

| Storming element | Color (convention) | For {{project_name}} |
|---|---|---|
| Domain event (past tense) | orange | {{storming_events}} |
| Command (triggers an event) | blue | {{storming_commands}} |
| Aggregate (enforces the rule) | yellow | {{storming_aggregates}} |
| Actor / external system | small yellow / pink | {{storming_actors}} |
| Policy ("whenever … then …") | purple | {{storming_policies}} |
| Hotspot / open question | red | {{storming_hotspots}} |

**Where the seams fell:** the clusters of events that don't talk to each other across the
timeline are candidate bounded-context boundaries. Reconcile them against
`BOUNDED_CONTEXTS.md`: {{storming_to_contexts}}

## 📐 Event Schema & Naming Convention

Every event in {{project_name}} carries a consistent **envelope** (metadata) plus a
type-specific **payload** (the source data). The envelope is what makes events routable,
deduplicable, and auditable.

```
{{event_schema_example}}

# Envelope (every event):
#   event_id        — globally unique id (dedupe key for idempotent consumers)
#   event_type      — fully-qualified type name + schema version
#   subject         — aggregate / entity id the event concerns
#   occurred_at     — when it happened in the world
#   noticed_at      — when the system recorded it
#   correlation_id  — ties this event to the request/saga that produced it
#   causation_id    — the command or prior event that caused this one
# Payload (per type): the immutable source data, named in domain terms.
```

| Schema decision | Value |
|---|---|
| Serialization format | {{serialization_format}} (e.g. JSON, Avro, Protobuf, CloudEvents) |
| Schema registry / governance | {{schema_registry}} |
| Versioning strategy (additive-only? new type on breaking change?) | {{schema_versioning}} |
| Naming convention for types | {{naming_convention}} (e.g. `Context.Aggregate.PastTenseVerb.vN`) |

## 🚚 Delivery, Ordering & Idempotency

Events become unreliable the moment they leave the process. State the guarantees explicitly —
silence here is where production incidents come from.

| Concern | Decision | Rationale |
|---|---|---|
| Delivery guarantee | {{delivery_guarantee}} (at-most-once / at-least-once / exactly-once-effectively) | {{delivery_rationale}} |
| Ordering guarantee | {{ordering_guarantee}} (none / per-partition / per-aggregate / global) | {{ordering_rationale}} |
| Idempotency mechanism | {{idempotency_mechanism}} (dedupe on `event_id`, idempotency key, upsert) | {{idempotency_rationale}} |
| Atomic state-change + publish | {{publish_atomicity}} (transactional outbox / CDC / 2-phase) | avoid the dual-write trap |
| Failure handling | {{failure_handling}} (retry policy, dead-letter queue, poison-message quarantine) | {{failure_rationale}} |
| Transport | {{event_transport}} (in-proc bus, Kafka, SQS/SNS, RabbitMQ, EventBridge, …) | {{transport_rationale}} |

> **At-least-once is the realistic default for a durable broker**, which forces consumers to be
> **idempotent**. Per-aggregate ordering (partition by aggregate id) is usually sufficient and
> far cheaper than global ordering — most domains only need events about *one* entity to arrive
> in order. The **transactional outbox** is the standard cure for the dual-write problem of
> "committed the DB row but the broker publish failed" (or vice-versa).

## 📼 Audit Log & Event Sourcing

Even without full event sourcing, the recorded events form an **Audit Log** — Fowler's "full
record that is valuable both for audit and debugging purposes."

`architecture.event_sourcing` for {{project_name}}: **{{event_sourcing_enabled}}**

> Fowler is explicit that "Domain Event is particularly important as a necessary pattern for
> **Event Sourcing**, which organizes a system so that *all* updates are made through Domain
> Event." If event sourcing is enabled, the event log *is* the source of truth; current state
> is a left-fold (projection) over the events, not a separately-mutated table.

| Aspect | Decision |
|---|---|
| Event store | {{event_store}} (append-only log / `data.store` table / dedicated ES db) |
| Current state derivation | {{state_derivation}} (projections / read models — see CQRS if `architecture.cqrs`) |
| Snapshotting strategy | {{snapshot_strategy}} (every N events / on schedule / none) |
| Replay / rebuild procedure | {{replay_procedure}} |
| Retention & archival of the event log | {{event_retention}} |
| Audit-log access (who can read history, redaction of PII) | {{audit_access_policy}} |

**Open questions / deferred decisions:** {{open_questions}}

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
