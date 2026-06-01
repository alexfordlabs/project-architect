---
template_name: BOUNDED_CONTEXTS
generate_when: "conditional"
required_decisions:
  - architecture.ddd
  - architecture.style
optional_decisions:
  - architecture.bounded_contexts
  - architecture.events
  - architecture.service_boundaries
  - team.structure
  - team_size
  - data.store
depends_on: []
revision_triggers:
  - architecture.ddd
  - architecture.bounded_contexts
  - architecture.service_boundaries
  - team.structure
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Bounded Contexts: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document maps the **Bounded Contexts** of **{{project_name}}** and the explicit
> relationships between them. Its structure follows Martin Fowler's
> *[BoundedContext](https://martinfowler.com/bliki/BoundedContext.html)* (the canonical
> bliki entry) for the core pattern, and Domain-Driven Design **strategic design /
> context-mapping** (Evans, *Domain-Driven Design*; Vernon, *Implementing Domain-Driven
> Design* ch. 3 — which Fowler cites as "the best source on drawing context maps") for the
> relationship taxonomy. Pair this doc with **DOMAIN_EVENTS** — the events are the messages
> that flow *between* the contexts named here.

> The governing idea, in Fowler's framing: **"total unification of the domain model for a
> large system will not be feasible or cost-effective."** Bounded Context is the answer —
> "dividing [large models] into different Bounded Contexts and being explicit about their
> interrelationships." We do *not* pursue one unified model. We pursue several internally
> consistent models with mapped seams.

## Table of contents
- [🧭 What a Bounded Context Is (and why)](#what-a-bounded-context-is-and-why)
- [🗣️ Ubiquitous Language per Context](#ubiquitous-language-per-context)
- [📦 The Contexts of This System](#the-contexts-of-this-system)
- [🔁 Polysemic Concepts (same word, different model)](#polysemic-concepts-same-word-different-model)
- [🗺️ The Context Map](#the-context-map)
- [🤝 Relationship Patterns](#relationship-patterns)
- [👥 Contexts → Teams → Services](#contexts-teams-services)
- [🚧 Boundary Decisions & Open Questions](#boundary-decisions-open-questions)
- [↻ Revision Log](#revision-log)

## 🧭 What a Bounded Context Is (and why)

A **Bounded Context** is "a central pattern in Domain-Driven Design" (Fowler). It is the
*boundary within which a single domain model is defined and applicable* — every term,
entity, and rule inside it has one unambiguous meaning. Outside the boundary, the same word
may mean something different, and that is fine: each context owns its own model.

The boundary is **not primarily technical**. Per Fowler: *"Usually the dominant one is human
culture, since models act as Ubiquitous Language, you need a different model when the
language changes."* When the people, the vocabulary, or the rules of the conversation change,
you have crossed into a new context.

Why {{project_name}} is divided this way rather than kept as one model:

| Forcing factor | Applies here? | Notes |
|---|---|---|
| One model would be too large to keep consistent | {{factor_scale}} | "not feasible or cost-effective" to unify |
| Distinct human cultures / departments / vocabularies | {{factor_language}} | the dominant boundary determinant |
| A term means different things to different people | {{factor_polysemy}} | see [Polysemic Concepts](#polysemic-concepts-same-word-different-model) |
| Independent change/release cadences needed | {{factor_autonomy}} | maps to service / deploy boundaries |
| Team ownership / Conway's-law alignment | {{factor_teams}} | see [Contexts → Teams](#contexts-teams-services) |

**Number of bounded contexts in {{project_name}}:** `{{context_count}}`
**Decision record:** `architecture.bounded_contexts` = {{bounded_contexts_decision}}

## 🗣️ Ubiquitous Language per Context

A model "acts as Ubiquitous Language" — the shared, internally-consistent vocabulary used by
developers *and* domain experts *within one context*. Each context below carries its own
glossary. The same surface word appearing in two glossaries is expected; reconcile the
*meanings* only at the context seams, never by forcing one global definition.

| Context | Core domain term | Meaning *inside this context* |
|---|---|---|
| {{context_a_name}} | {{context_a_term_1}} | {{context_a_term_1_meaning}} |
| {{context_a_name}} | {{context_a_term_2}} | {{context_a_term_2_meaning}} |
| {{context_b_name}} | {{context_b_term_1}} | {{context_b_term_1_meaning}} |
| {{additional_glossary_rows}} | … | … |

## 📦 The Contexts of This System

One row per Bounded Context. The **upstream/downstream** column is the dependency direction
in DDD terms (upstream = influences; downstream = is influenced / consumes).

| Context | Responsibility (what it owns) | Key aggregates / entities | Owns data store? | Upstream of | Downstream of |
|---|---|---|---|---|---|
| {{context_a_name}} | {{context_a_responsibility}} | {{context_a_aggregates}} | {{context_a_store}} | {{context_a_upstream_of}} | {{context_a_downstream_of}} |
| {{context_b_name}} | {{context_b_responsibility}} | {{context_b_aggregates}} | {{context_b_store}} | {{context_b_upstream_of}} | {{context_b_downstream_of}} |
| {{context_c_name}} | {{context_c_responsibility}} | {{context_c_aggregates}} | {{context_c_store}} | {{context_c_upstream_of}} | {{context_c_downstream_of}} |
| {{additional_contexts}} | … | … | … | … | … |

> **Each context owns its own data.** Sharing a database across contexts re-couples the very
> models the boundary exists to separate. If `{{data_store}}` is shared physically, the logical
> boundary (schema/ownership) must still hold. Justify any shared store: {{shared_store_justification}}

## 🔁 Polysemic Concepts (same word, different model)

Fowler's early illustration is the electricity utility where **"meter"** meant different things
across departments; he adds that the confusion *"recur[s] with polysemes like 'Customer' and
'Product'"* across an organization with subtly different meanings. Catalog the words in
{{project_name}} that are *polysemic* — one term, several context-specific models — and how
they are mapped at the seam (Fowler: contexts hold *"completely different models of common
concepts with mechanisms to map between these polysemic concepts for integration"*).

| Shared word | In `{{context_a_name}}` it is… | In `{{context_b_name}}` it is… | Mapping mechanism at the seam |
|---|---|---|---|
| {{polysemic_term_1}} | {{polysemic_1_meaning_a}} | {{polysemic_1_meaning_b}} | {{polysemic_1_mapping}} |
| {{polysemic_term_2}} | {{polysemic_2_meaning_a}} | {{polysemic_2_meaning_b}} | {{polysemic_2_mapping}} |
| {{additional_polysemic_terms}} | … | … | … |

> Concrete shape of the classic example: a *support ticket* exists only in a customer-support
> context, while *products* and *customers* appear across several contexts with different
> models. Don't unify them — map them. Record {{project_name}}'s equivalent above.

## 🗺️ The Context Map

Fowler: *"It's usually worthwhile to depict these using a context map."* The map shows every
context and labels each seam with its relationship pattern (next section). Keep this in sync
with the C4 / system diagram if one exists.

```
{{context_map_diagram}}

  ┌────────────────────┐                      ┌────────────────────┐
  │  {{context_a_name}}│  ── {{rel_a_b}} ──▶  │  {{context_b_name}}│
  │   (U)              │                      │        (D)         │
  └────────────────────┘                      └────────────────────┘
            │                                           │
        {{rel_a_c}}                                 {{rel_b_c}}
            ▼                                           ▼
                      ┌────────────────────┐
                      │  {{context_c_name}}│
                      └────────────────────┘

  Legend: (U) upstream · (D) downstream · arrow = direction of influence
          seam labels (SK / CS / ACL / OHS / …) defined in Relationship Patterns
```

**Integration style across seams:** {{integration_style}}
*(synchronous API calls / asynchronous domain events / shared kernel / batch — note which
seams are event-driven and cross-reference DOMAIN_EVENTS.)*

## 🤝 Relationship Patterns

The DDD strategic-design taxonomy. For **each seam** on the map, pick exactly one pattern and
record it. (These are Evans' context-mapping patterns, detailed in Vernon ch. 3 — Fowler's
bliki names the Context Map but defers the pattern catalog to those sources.)

| Pattern | What it means | Choose when | Used at seam |
|---|---|---|---|
| **Partnership** | Two contexts succeed or fail together; teams coordinate planning & releases jointly. | Mutual dependency, aligned goals, willing to co-plan. | {{seam_partnership}} |
| **Shared Kernel** (SK) | A small shared subset of the model/code that both contexts agree to and cannot change unilaterally. | A tiny overlap is genuinely identical and change is coordinated. | {{seam_shared_kernel}} |
| **Customer–Supplier** (CS) | Downstream (customer) needs drive the upstream (supplier) backlog; supplier accommodates. | Clear up/down direction and the upstream team will prioritize downstream needs. | {{seam_customer_supplier}} |
| **Conformist** | Downstream conforms to the upstream model as-is, no translation, no negotiating leverage. | Upstream won't change for you and translation isn't worth it. | {{seam_conformist}} |
| **Anticorruption Layer** (ACL) | Downstream builds a translation layer so the upstream model never leaks into its own. | You must integrate with a messy/legacy/foreign model and protect your own. | {{seam_acl}} |
| **Open-Host Service** (OHS) | Upstream publishes a well-defined protocol/API for *many* downstreams to consume. | One context serves many integrators; a stable public interface pays off. | {{seam_ohs}} |
| **Published Language** (PL) | A shared, well-documented interchange format (often paired with OHS) for communication. | Multiple parties exchange data and need an agreed schema/contract. | {{seam_published_language}} |
| **Separate Ways** | No integration at all — the contexts deliberately do not connect. | Integration cost outweighs value; duplicate the small bit instead. | {{seam_separate_ways}} |

**Seam-by-seam record:**

| Seam (A → B) | Direction | Pattern | Why this pattern | Contract / interface |
|---|---|---|---|---|
| {{seam_1}} | {{seam_1_direction}} | {{seam_1_pattern}} | {{seam_1_rationale}} | {{seam_1_contract}} |
| {{seam_2}} | {{seam_2_direction}} | {{seam_2_pattern}} | {{seam_2_rationale}} | {{seam_2_contract}} |
| {{additional_seams}} | … | … | … | … |

> **ACL is the default for any integration with a system you don't control** (legacy,
> third-party, foreign-team). It is the cheapest insurance against an external model
> corrupting yours. Note every external dependency that warrants one: {{acl_targets}}

## 👥 Contexts → Teams → Services

Bounded contexts naturally align with organizational divisions — and, in a distributed
system, with deployable services and their datastores. Conway's Law makes this alignment
load-bearing: a context owned by two teams tends to fracture; a service spanning two contexts
tends to leak. Map the three layers explicitly.

| Context | Owning team | Deployable unit (service / module / package) | Data store | Repo / path |
|---|---|---|---|---|
| {{context_a_name}} | {{context_a_team}} | {{context_a_service}} | {{context_a_store}} | {{context_a_repo}} |
| {{context_b_name}} | {{context_b_team}} | {{context_b_service}} | {{context_b_store}} | {{context_b_repo}} |
| {{additional_context_teams}} | … | … | … | … |

- **Architecture style:** `{{architecture_style}}` (`architecture.style`) — monolith /
  modular-monolith / microservices. In a **modular monolith**, contexts are module/package
  boundaries enforced in-process; in **microservices**, contexts are service boundaries.
- **Team topology:** `{{team_structure}}` (`team.structure`), team size `{{team_size}}`.
- **One team can own several contexts; a context should have exactly one owning team.**
  Violations to revisit: {{ownership_violations}}

## 🚧 Boundary Decisions & Open Questions

- **Drawing the lines is iterative.** Fowler notes the considerations involve "history and
  human relationships," not just clean domain logic (citing Verraes & Wirfs-Brock). Record
  the boundaries we are *unsure* about and the signal that would move them.
- **Candidate splits / merges:** {{candidate_boundary_changes}}
- **Boundaries deferred (deliberately one context for now):** {{deferred_splits}}
- **Risks of the current map:** {{boundary_risks}} — e.g. a polysemic term not yet mapped, a
  shared store hiding two contexts, a seam without an explicit pattern.
- **Open questions:** {{open_questions}}

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
