---
template_name: DATA_CONTRACT
generate_when: "conditional"
required_decisions:
  - data_pipeline.enabled
  - data.contracts
optional_decisions:
  - data.warehouse
  - data.streaming
  - data.quality_framework
  - data.governance
  - data.pii
  - data.lineage
  - data.catalog
depends_on: []
revision_triggers:
  - data.contracts
  - data.warehouse
  - data.streaming
  - data.quality_framework
  - data.governance
  - data.pii
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Data Contract: {{dataset_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is a data-contract design doc for the **{{dataset_name}}** dataset produced by
> **{{project_name}}**. Its structure follows the
> [Data Contract Specification](https://datacontract.com/) — the open standard for the
> agreement between a **data provider** and its **consumers** on schema, semantics, quality,
> and service levels. The canonical artifact is a `datacontract.yaml` file; this doc captures
> the *decisions* behind it so the YAML can be authored, reviewed, and CI-validated (e.g. with
> the `datacontract` CLI: `datacontract lint`, `datacontract test`).
>
> **Spec version targeted:** `dataContractSpecification: {{spec_version}}` (current is `1.2.1`).

## Table of contents
- [📇 Identity & Info](#identity-info)
- [🖥️ Servers (where the data physically lives)](#servers-where-the-data-physically-lives)
- [📜 Terms (the agreement)](#terms-the-agreement)
- [🧱 Models (logical schema)](#models-logical-schema)
- [🏷️ Field Semantics, Classification & PII](#field-semantics-classification-pii)
- [♻️ Definitions (reusable types)](#definitions-reusable-types)
- [✅ Data Quality](#data-quality)
- [📊 Service Levels (SLA/SLO)](#service-levels-slaslo)
- [🔗 Lineage & Links](#lineage-links)
- [🔁 Versioning & Change Management](#versioning-change-management)
- [🚦 CI Enforcement](#ci-enforcement)
- [↻ Revision Log](#revision-log)

## 📇 Identity & Info

The `id` and `info` blocks identify the contract organization-wide.

| Spec key | Decision for {{dataset_name}} |
|---|---|
| `id` (unique technical id — UUID / URN / slug) | `{{contract_id}}` |
| `info.title` | `{{contract_title}}` |
| `info.version` (the *contract's* version, distinct from the spec version) | `{{contract_version}}` |
| `info.status` (`proposed` → `in development` → `active` → `deprecated` → `retired`) | `{{contract_status}}` |
| `info.description` | {{contract_description}} |
| `info.owner` (responsible team/domain) | `{{owning_team}}` |
| `info.contact.name` / `.email` / `.url` | {{contact_summary}} |

> Pin `info.status` deliberately. A contract marked `active` is a *promise* consumers may
> build on; `deprecated` triggers the notice period in [Terms](#terms-the-agreement) below.

## 🖥️ Servers (where the data physically lives)

`servers` is a map keyed by environment name. Each server declares a `type` and
type-specific connection fields, so a consumer can resolve the physical location of the
dataset described by the [models](#models-logical-schema).

| Server (env key) | `type` | `environment` | Type-specific fields | Roles |
|---|---|---|---|---|
| `{{server_key_prod}}` | `{{server_type_prod}}` | `prod` | {{server_fields_prod}} | {{server_roles_prod}} |
| `{{server_key_nonprod}}` | `{{server_type_nonprod}}` | `{{nonprod_env}}` | {{server_fields_nonprod}} | {{server_roles_nonprod}} |

**Server `type` choices** (data-store decision `data.warehouse` / `data.streaming`): `bigquery`,
`snowflake`, `redshift`, `postgres`, `databricks`, `s3`, `azure`, `kafka`, `sftp`, `local`,
`glue`, `oracle`, `databricksSQL`, `trino`, … Each type has its own required fields — e.g.
`s3` needs `location` + `format` (`parquet` / `json` / `csv` / `delta`) + `delimiter`;
`bigquery` needs `project` + `dataset`; `kafka` needs `host` + `topic`; `snowflake` needs
`account` + `database` + `schema`.

**Chosen physical store + format:** {{physical_store_rationale}}

## 📜 Terms (the agreement)

The `terms` block is the human-readable contract between provider and consumers.

| `terms` key | Value for {{dataset_name}} |
|---|---|
| `usage` (intended/expected use) | {{terms_usage}} |
| `limitations` (what consumers must NOT do — e.g. no PII joins, no re-export) | {{terms_limitations}} |
| `policies[]` (`name` / `description` / `url` — privacy, retention, compliance refs) | {{terms_policies}} |
| `billing` (cost model, if charged-back/per-query) | {{terms_billing}} |
| `noticePeriod` (ISO-8601 duration before a breaking change / decommission, e.g. `P3M`) | `{{terms_notice_period}}` |

> The `noticePeriod` is the contract's strongest consumer protection: a breaking schema
> change or `retired` transition must be announced at least this far in advance. Choose a
> value consumers can actually plan a migration around.

## 🧱 Models (logical schema)

`models` is a map of logical models (one entry per table/view/object). For each model:
`description`, `type` (`table` | `view` | `object`), optional `title`, the `fields` map,
optional compound `primaryKey: [...]`, model-level `quality`, and `examples`. Setting
`additionalFields: false` (the default) makes the schema *closed* — consumers may rely on the
field set being exactly as declared.

### Model: `{{model_name}}`

- **`description`:** {{model_description}}
- **`type`:** `{{model_type}}`
- **`primaryKey`:** {{model_primary_key}}
- **`additionalFields`:** `{{additional_fields}}` *(prefer `false` for a closed, stable schema)*

| Field | `type` | `required` | Key / `unique` | `references` | `description` |
|---|---|---|---|---|---|
| `{{field_1_name}}` | `{{field_1_type}}` | `{{field_1_required}}` | {{field_1_key}} | {{field_1_references}} | {{field_1_description}} |
| `{{field_2_name}}` | `{{field_2_type}}` | `{{field_2_required}}` | {{field_2_key}} | {{field_2_references}} | {{field_2_description}} |
| `{{field_3_name}}` | `{{field_3_type}}` | `{{field_3_required}}` | {{field_3_key}} | {{field_3_references}} | {{field_3_description}} |
| {{additional_fields_rows}} | … | … | … | … | … |

> **Logical `type` vocabulary** (portable across stores): strings — `string`, `text`,
> `varchar`; numerics — `number`, `decimal`, `numeric`, `int`, `integer`, `long`, `bigint`,
> `float`, `double`; temporal — `timestamp`, `timestamp_tz`, `timestamp_ntz`, `date`, `time`;
> other — `boolean`, `bytes`, `array`, `map`, `object`, `record`, `struct`, `variant`, `null`.
> Per-field constraints available: `enum: [...]`, `format` (`email` / `uri` / `uuid` / …),
> `pattern` (ECMA-262 regex), `minLength`/`maxLength`, `minimum`/`maximum`, `examples: [...]`.

*(Repeat this Model block for each model — e.g. fact + dimension, parent + line-items. Wire
foreign keys with `references: {{parent_model}}.{{parent_field}}`.)*

## 🏷️ Field Semantics, Classification & PII

Governance metadata lives at the field level. Make every sensitive field explicit so the
contract doubles as a data-governance record (`data.governance` / `data.pii`).

| Field | `pii` | `classification` | `tags` | Handling note |
|---|---|---|---|---|
| `{{sensitive_field_1}}` | `{{pii_1}}` | `{{classification_1}}` | {{tags_1}} | {{handling_1}} |
| `{{sensitive_field_2}}` | `{{pii_2}}` | `{{classification_2}}` | {{tags_2}} | {{handling_2}} |

- **`classification`** values follow your org's sensitivity ladder — commonly `public`,
  `internal`, `confidential`/`sensitive`, `restricted`. Org ladder used here: {{classification_ladder}}.
- **`pii: true`** flags personally identifiable fields; pair with the `policies[]` privacy
  reference in [Terms](#terms-the-agreement) and any masking/tokenization rule: {{pii_handling_policy}}.

## ♻️ Definitions (reusable types)

`definitions` holds reusable, domain-named field types referenced from models via
`$ref: '#/definitions/{{definition_name}}'`. A definition carries `type`, `title`,
`description`, `format`, `examples`, `pii`, and `classification` — so semantics + governance
are declared once and reused.

| Definition | `type` | `format` | `pii` / `classification` | Reused by |
|---|---|---|---|---|
| `{{definition_1_name}}` | `{{definition_1_type}}` | {{definition_1_format}} | {{definition_1_governance}} | {{definition_1_usage}} |
| {{additional_definitions}} | … | … | … | … |

> Use definitions for cross-model concepts (an `email`, a `customer_id`, a money type). It
> keeps PII/classification consistent and shrinks review surface when a type changes.

## ✅ Data Quality

The spec supports four `quality` styles, declarable at model or field level. Pick the lightest
style that actually catches the failure mode (`data.quality_framework`).

| Quality `type` | What it is | Use for {{dataset_name}}? |
|---|---|---|
| `text` | Natural-language quality statement for stakeholder discussion (not executable). | {{quality_text_use}} |
| `sql` | Custom SQL returning a single number, compared via `mustBe` / `mustNotBe` / `mustBeGreaterThan` / `mustBeLessThan` / `mustBeBetween` / `mustBeGreaterThanOrEqualTo` / `mustBeLessThanOrEqualTo`. | {{quality_sql_use}} |
| `library` | Predefined metrics — `rowCount`, `nullValues`, `missingValues`, `invalidValues`, `duplicateValues` — with standardized arguments. | {{quality_library_use}} |
| `custom` | Engine-specific blocks — **Soda** (SodaCL checks) or **Great Expectations** (Expectation objects). | {{quality_custom_use}} |

**Concrete checks for this dataset:**

| Check | Style | Target (model.field) | Rule | Threshold |
|---|---|---|---|---|
| {{quality_check_1_name}} | `{{quality_check_1_type}}` | `{{quality_check_1_target}}` | {{quality_check_1_rule}} | {{quality_check_1_threshold}} |
| {{quality_check_2_name}} | `{{quality_check_2_type}}` | `{{quality_check_2_target}}` | {{quality_check_2_rule}} | {{quality_check_2_threshold}} |
| {{additional_quality_checks}} | … | … | … | … |

**Execution engine:** `{{quality_engine}}` *(e.g. `soda`, `great-expectations`, `dbt` tests
re-expressed as `sql`/`library`)* — run via `datacontract test` in [CI](#ci-enforcement).

## 📊 Service Levels (SLA/SLO)

`servicelevels` is the operational promise. Fill only the categories that apply (a streaming
contract emphasizes `freshness`/`latency`; a daily batch emphasizes `frequency`/`freshness`).

| Category | Sub-fields | Commitment for {{dataset_name}} |
|---|---|---|
| `availability` | `description`, `percentage` (e.g. `99.9%`) | {{sla_availability}} |
| `retention` | `description`, `period` (`P1Y` or `1 year`), `unlimited`, `timestampField` | {{sla_retention}} |
| `latency` | `description`, `threshold` (`PT24H` / `24 hours`), `sourceTimestampField`, `processedTimestampField` | {{sla_latency}} |
| `freshness` | `description`, `threshold`, `timestampField` | {{sla_freshness}} |
| `frequency` | `description`, `type` (`batch` / `micro-batching` / `streaming` / `manual`), `interval`, `cron` | {{sla_frequency}} |
| `support` | `description`, `time` (`24/7` / `business hours`), `responseTime` | {{sla_support}} |
| `backup` | `description`, `interval`, `cron`, `recoveryTime` (RTO), `recoveryPoint` (RPO) | {{sla_backup}} |

> **`latency` vs `freshness`** are distinct: *latency* is source-event → available-in-store
> elapsed time (uses two timestamp fields); *freshness* is the max age of the newest row right
> now (uses one timestamp field). State which timestamp field each clause measures against —
> a contract SLA is only testable if the field it reads is named.

## 🔗 Lineage & Links

- **Field-level `lineage`** (`data.lineage`): for derived fields, record upstream provenance
  via the field's `lineage` object so consumers and a catalog can trace origin: {{lineage_summary}}.
- **`links`** (map of external refs by key): catalog entry, dashboards, runbook, source repo —
  {{links_summary}}.
- **`tags`** (top-level array): discovery/categorization metadata — {{contract_tags}}.
- **Catalog integration** (`data.catalog`): how this contract is published/registered
  (e.g. Data Mesh Manager, DataHub, OpenMetadata, Collibra): {{catalog_integration}}.

## 🔁 Versioning & Change Management

The contract is a versioned interface. Distinguish three things that each carry their own
version: the spec (`dataContractSpecification`), the contract (`info.version` — the version of
the contract document itself; the spec leaves the scheme open, but semver is the recommended
convention so consumers can reason about breaking vs. non-breaking bumps), and the physical
schema.

| Change kind | Examples | Version bump | Consumer protection |
|---|---|---|---|
| **Non-breaking** | new optional field; widened enum; doc/quality tightening | minor / patch (`info.version`) | none required |
| **Breaking** | removed/renamed field; type narrowing; `required` added; `primaryKey` change | **major** + `info.status: deprecated` on the old version | honor `noticePeriod` `{{terms_notice_period}}`; dual-publish window |

**Deprecation path for {{dataset_name}}:** {{deprecation_strategy}}
**How breaking changes are detected:** {{breaking_change_detection}} *(e.g. `datacontract changelog`
between this contract and the previously published one in CI — the changelog flags breaking
changes such as removed/renamed fields and type narrowing).*

## 🚦 CI Enforcement

The contract is dead unless CI enforces it. Wire these gates:

- **Lint** the YAML against the spec: `datacontract lint datacontract.yaml`.
- **Schema conformance** — the live store matches the declared `models`/`servers`:
  `datacontract test --server {{server_key_prod}}`.
- **Quality** — run the [Data Quality](#data-quality) checks on real data on the
  `{{quality_engine}}` engine: {{ci_quality_gate}}.
- **Breaking-change guard** — `datacontract changelog datacontract.yaml <previous-published.yaml>`
  to compare against the last published contract; a breaking change fails the PR unless the
  `info.version` major is bumped + `noticePeriod` honored. (Run the full CI suite via
  `datacontract ci`.)
- **Export drift** — if a DDL/SQL/Avro/JSON-Schema/dbt artifact is generated from the
  contract (`datacontract export --format {{export_format}}`), regenerate and assert no drift.

**CI surface:** {{ci_pipeline_location}} *(GitHub Actions / GitLab CI / data-platform CI).*

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
