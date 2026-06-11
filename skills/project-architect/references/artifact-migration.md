<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Artifact migration framework (docs + decisions)

This is the forward-compat framework for project-architect's **non-state** artifacts — generated docs, ADRs, and the `decisions` key namespace. It is structurally identical to the state-migration framework in [`state-schema.md`](state-schema.md) (chained idempotent steps, a compat floor, a refuse-if-newer guard) — just applied per artifact class. For v5 the tables ship with a baseline row only; their value is forward (v6+ appends rows, and the engine that consumes them already exists and is tested for state).

## The three independent version axes

| Axis | Carried in | Bumps when | v5 value |
|---|---|---|---|
| `schema_version` (state) | `state.json` top-level | the `state.json` layout changes | `"3.0"` |
| `format_version` (docs) | every `docs/*.md` + `docs/decisions/*.md` frontmatter | the doc/ADR frontmatter schema changes | `"1.0"` (absent ≡ pre-1.0) |
| `decisions_schema_version` | `state.json` top-level (new in v5) | the `decisions` key namespace changes (rename/split/re-type) | `"1.0"` |

`produced_by_plugin_version` is **provenance**, not a migration axis — it records which plugin release authored an artifact (carried alongside `format_version` in doc/ADR frontmatter, and as `plugin_version` in state).

## Doc-format migration table

Same row format as the state table; each step idempotent. v5 ships the baseline row only.

| From | To | Steps |
|---|---|---|
| *(unstamped / pre-1.0)* | `1.0` | (1) add `format_version: "1.0"` to frontmatter; (2) add `produced_by_plugin_version` (← `state.plugin_version` if unknown). **Note:** in the upgrade flow the doc body is *re-derived* (spec §4 step 7), so this row only matters for an in-place stamp pass; the floor for migratable docs is the doc set that shipped with PA schema 2.0. |

**Convention for future entries:** one row per `from → to`; `Steps` lists field-level frontmatter operations (add / remove / rename / re-type / default-fill); keep each idempotent. Illustrative `1.0 → 1.1`: (1) rename frontmatter `template_name` → `doc_template`; (2) add `generated_from_decision_schema` default `"1.0"`.

## Decision-key migration table

Renames / splits / re-types of `decisions` keys across namespace versions. v5 ships the baseline row only.

| From | To | Steps |
|---|---|---|
| *(any pre-v5 namespace at the compat floor)* | `1.0` | (no key changes for v5 — the v5 namespace IS the floor namespace; baseline is identity). Future rows handle renames. |

**Convention for future entries:** one row per `from → to`; `Steps` lists key operations — `rename a.b → c.d`, `split a.b → {a.b1, a.b2}` (with a documented split rule), `retype a.b (string → enum)` (with the value map), `default-fill a.b` — each idempotent (a key already migrated is left alone). The `decision-revisor` and `revision-playbook` are updated in lockstep when a row is added, so a migrated key is never an "unknown key."

## Migration policy (mirrors state-schema.md)

For each artifact class, at ingest, compare the artifact's version against the plugin's expected version:

| Comparison | Action |
|---|---|
| `== current` | proceed |
| `< current` AND a migration-table entry exists | run the chained migration; proceed |
| `< current` AND no entry (below the **compat floor** = PA schema 2.0) | **refuse** with re-bootstrap guidance ("this project predates the migratable layout; re-bootstrap fresh") |
| `> current` | **refuse**: artifact newer than plugin; upgrade the plugin |

The compat floor is **PA schema 2.0** (the first with today's `docs/` + `docs/decisions/` + `decisions`-namespace layout). The `/upgrade-project` flow (spec §4) consumes this framework; this reference is the data it reads.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
