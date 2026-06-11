---
template_name: RECOVERED_DESIGN
generate_when: "re_architect_only"
required_decisions: []
optional_decisions: []
depends_on: []
revision_triggers: []
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Recovered Design — {{project.name}}

> **This is a run artifact, not a permanent doc.** The `design-recovery` agent reconstructed it from the project's existing docs, ADRs, and research during `/re-architect`. It is the **triage surface**: the human reviews every row, validates the recovered value/rationale against its `source`, and fills the `triage` column. After triage + re-decide it has served its purpose — it is snapshotted with the run (`docs/versions/<old>/`), not kept as a living design doc.
>
> Recovered: `{{recovered_summary}}` (e.g. `RECOVERED 31 decisions (6 low-confidence) across 5 areas; sources: 16 docs + 22 ADRs`).

## How to read this document

One table **per decision area** (project/vision, tech-stack, architecture, security, ops, …). Each row is one recovered decision. The columns:

| field | meaning |
|---|---|
| `key` | canonical decision name — the v5 flat key when it maps cleanly (`crypto.ratchet`, `infra.runtime`), else a descriptive project-specific slug |
| `current_value` | the choice as it stands today, recovered from the artifacts |
| `rationale` | ≤3-line summary of *why*, drawn from the prose / ADR |
| `source` | pointer(s) back to the artifact: `docs/…md` and/or `docs/decisions/NNNN-*.md` — so you can verify, not just trust |
| `confidence` | `high` \| `low`. `low` = ambiguous, conflicting across docs, or inferred rather than stated. **Low-confidence rows are surfaced FIRST in triage** — they are where your attention is most needed. |
| `triage` | **YOU fill this in the review step**: `keep` \| `revise` \| `drop`. Rows you ADD for missing decisions get `add`. Leave blank until reviewed. |

> **Triage is the human validation gate.** The recovery agent reconstructs; it never decides and never invents. If a `current_value` or `rationale` is wrong, correct it here. If a row is `confidence: low`, scrutinize its `source` before you trust it. Nothing is researched or re-derived until the triage column is complete.
>
> - `keep` — carry the decision forward unchanged.
> - `revise` — re-decide it (the challenge/research pass will inform the new value).
> - `drop` — the decision no longer applies; remove it.
> - `add` — a decision that exists in the project but the agent missed, or a new one you want; write a fresh row and mark it `add`.

---

## Area: Project / Vision

| key | current_value | rationale | source | confidence | triage |
|---|---|---|---|---|---|
| `{{key}}` | `{{current_value}}` | `{{rationale}}` | `{{source}}` | `{{confidence}}` | |

## Area: Tech Stack

| key | current_value | rationale | source | confidence | triage |
|---|---|---|---|---|---|
| `{{key}}` | `{{current_value}}` | `{{rationale}}` | `{{source}}` | `{{confidence}}` | |

## Area: Architecture

| key | current_value | rationale | source | confidence | triage |
|---|---|---|---|---|---|
| `{{key}}` | `{{current_value}}` | `{{rationale}}` | `{{source}}` | `{{confidence}}` | |

## Area: Security

| key | current_value | rationale | source | confidence | triage |
|---|---|---|---|---|---|
| `{{key}}` | `{{current_value}}` | `{{rationale}}` | `{{source}}` | `{{confidence}}` | |

## Area: Ops

| key | current_value | rationale | source | confidence | triage |
|---|---|---|---|---|---|
| `{{key}}` | `{{current_value}}` | `{{rationale}}` | `{{source}}` | `{{confidence}}` | |

> Add or remove area sections to match the project. Every ADR in the decisions directory and every material decision in the docs MUST appear as at least one row, each with a resolving `source`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
