---
template_name: TESTING_STRATEGY
generate_when: "decisions.scale != \"hobby\" OR decisions.project.type != \"library\""
required_decisions: [testing.unit_framework]
optional_decisions: [testing.integration_framework, testing.e2e_framework, testing.visual_framework, testing.coverage_target]
depends_on: []
revision_triggers: [testing.unit_framework, testing.integration_framework, testing.e2e_framework, testing.coverage_target]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Testing Strategy: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🧪 Testing Philosophy](#testing-philosophy)
- [🧪 Testing Stack](#testing-stack)
- [🏗️ Test Structure](#test-structure)
- [🧪 Key Testing Scenarios](#key-testing-scenarios)
- [🧪 Test Data Strategy](#test-data-strategy)
- [🚀 CI Integration](#ci-integration)
- [🧪 Performance Testing](#performance-testing)
- [🧪 Contract Testing](#contract-testing)
- [🧪 Property-Based Testing](#property-based-testing)
- [↻ Revision Log](#revision-log)

## 🧪 Testing Philosophy
One paragraph: how this project balances unit / integration / e2e (test pyramid vs trophy vs honeycomb), the role of TDD, and any explicit non-goals.

## 🧪 Testing Stack
Table: test type | tool | coverage target. Rows for unit, integration, e2e, visual / snapshot, performance, accessibility, and contract testing as applicable.

## 🏗️ Test Structure
Directory convention (`__tests__/` vs co-located vs separate top-level), filename pattern, fixture/mocks location, and helper-utility conventions.

## 🧪 Key Testing Scenarios
Bulleted list of critical user paths that must always be tested (signup, checkout, primary domain workflow, etc.) regardless of refactors.

## 🧪 Test Data Strategy
How test data is created (factories / fixtures / Faker / record-replay), database isolation (per-test / per-suite / shared), and any deterministic-seed rules.

## 🚀 CI Integration
How tests run in CI (matrix, sharding, parallelization), retry policy for flakes, and reporting (annotations, summaries, screenshots, traces).

## 🧪 Performance Testing
Make performance a *tested* property, not a hope. Define it across the relevant tiers and gate on it:
- **Load / stress / soak.** Tools (k6 / Artillery / Gatling / Locust). Specify the workload model (closed vs open, RPS or VUs, ramp), the SLO-derived pass/fail thresholds (e.g. `p95 < {{p95_target}}`, `error_rate < {{err_target}}` — these MUST match SLO_AND_ERROR_BUDGETS.md), and soak duration for leak/degradation detection.
- **Frontend / web-vitals.** Lighthouse CI budgets for LCP / INP / CLS with a CI assertion (`assertions` budget file), per route.
- **Micro-benchmarks.** For hot paths / libraries (e.g. `pytest-benchmark`, `criterion`, `Benchmark.js`) with a regression guard (fail if slower than baseline by > {{regression_pct}}%).
- **Where results live + the regression gate.** Archive runs ({{perf_results_store}}); fail CI on threshold breach so a perf regression can't merge silently. Skip a tier only with a recorded reason.

## 🧪 Contract Testing
For any service boundary (HTTP/gRPC API, event/message, or a published SDK) where producer and consumer deploy independently, add **consumer-driven contract tests** so an incompatible change is caught in CI rather than in production. Tooling: [Pact](https://docs.pact.io/) (HTTP + message), Spring Cloud Contract, or schema-compat checks (OpenAPI diff, [Buf breaking](https://buf.build/docs/breaking/overview) for protobuf, a schema registry's compat mode for events/Avro). Specify: which boundaries have contracts, where the contracts/pacts are stored + verified (a broker or the repo), and that the producer's CI runs `can-i-deploy` (or equivalent) against every consumer contract before release. Cross-link CONTRACT_TESTING.md if this project generates it (microservices / >4 bounded contexts).

## 🧪 Property-Based Testing
For pure logic with a large/edge-heavy input space (parsers, serializers, money/units math, state machines, encoders), complement example-based tests with **property-based tests** that assert invariants over generated inputs. Tooling: [Hypothesis](https://hypothesis.readthedocs.io/) (Python), [fast-check](https://fast-check.dev/) (JS/TS), [proptest](https://docs.rs/proptest/)/QuickCheck (Rust), jqwik (Java). Name the invariants to check (round-trip `decode(encode(x)) == x`, idempotence, commutativity, never-panics, output-always-valid), and enable the framework's **shrinking** + a persisted failure DB so a found counterexample is replayed deterministically in CI. Identify which modules warrant it ({{property_test_targets}}); don't force it on glue code.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
