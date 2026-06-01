---
template_name: ADR_TEMPLATE
generate_when: "n/a (used by agents, never selected as a standalone doc)"
required_decisions: []
optional_decisions: []
depends_on: []
revision_triggers: []
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

---
type: adr
schema_version: "4.0"                   # ADR frontmatter schema version (v8 MADR-4; see references/artifact-migration.md)
id: {{NNNN}}                            # zero-padded sequential
title: {{title}}
status: proposed | accepted | superseded | deprecated
date: {{YYYY-MM-DD}}
decision_makers: [{{who approved this decision}}]
plugin_version: {{plugin_version}}      # provenance: the plugin release that authored this ADR (← plugin.json version)
phase: {{phase}}                        # the phase this decision was made in (e.g. architecture, stack, iteration)
supersedes: {{prior_adr_id or null}}
superseded_by: null                     # filled in if a future ADR supersedes this
affected_docs: [{{list of doc filenames}}]
decision_keys: [{{list of decision keys this records}}]
research_refs: [{{paths to research findings consulted}}]
---

# ADR {{NNNN}}: {{title}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🚦 Status](#status)
- [Context](#context)
- [Prior decision (if superseding)](#prior-decision-if-superseding)
- [Decision](#decision)
- [Alternatives reconsidered](#alternatives-reconsidered)
- [Consequences](#consequences)
- [🚀 Rollback plan](#rollback-plan)
- [References](#references)

## 🚦 Status
{{status}} {{(supersedes ADR {{prior_id}} if applicable)}}

> Sibling-ADR links (`supersedes`, `superseded_by`, "see ADR NNNN") resolve against `{{state.decisions_dir}}` (default `docs/decisions/`) — read it from state; never hardcode `docs/adr/`. Resolve the real sibling filename (`<NNNN>-<slug>.md`), not a glob, when the target exists.

## Context
What changed. What new information surfaced. Why we're (re)deciding.

## Prior decision (if superseding)
What was chosen before and why. Link to prior ADR.

## Decision
What is being chosen and why. Concrete and specific.

## Alternatives reconsidered
- {{alt}} — why not

## Consequences
- {{consequence}} — affected doc, mitigation

## 🚀 Rollback plan
If this turns out wrong, how do we revert? What's the cost?

## References
- Prior ADR: {{prior_id}}
- Research: {{research_refs}}
- Related: {{external links}}

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
