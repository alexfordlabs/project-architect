---
template_name: DOCUMENTATION_STRATEGY
generate_when: "conditional"
required_decisions:
  - docs
optional_decisions:
  - docs.surface
  - docs.tooling
  - docs.versioned
  - docs.host
  - project.type
  - scm.host
  - ci.provider
depends_on: []
revision_triggers:
  - docs
  - docs.surface
  - docs.tooling
  - docs.versioned
  - docs.host
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Documentation Strategy: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document defines the docs-as-code strategy for **{{project_name}}**'s public
> documentation surface. The content model is grounded in **[Diátaxis](https://diataxis.fr/)**,
> the systematic framework that organizes technical documentation around *user needs* rather
> than the structure of the product. Diátaxis "prescribes approaches to content, architecture
> and form that emerge from a systematic approach to understanding the needs of documentation
> users." Its central claim: there are **four** distinct documentation modes, each serving a
> different user need, and **mixing them degrades all four**.

## Table of contents
- [🧭 The Diátaxis Compass](#the-diátaxis-compass)
- [🗺️ The Four Modes](#the-four-modes)
- [📚 Content Inventory by Mode](#content-inventory-by-mode)
- [🛠️ Docs-as-Code Toolchain](#docs-as-code-toolchain)
- [🔁 CI Pipeline (build · preview · link-check)](#ci-pipeline-build--preview--link-check)
- [🧱 Information Architecture & Navigation](#information-architecture--navigation)
- [📦 Versioning](#versioning)
- [♻️ Freshness & Ownership](#freshness--ownership)
- [↻ Revision Log](#revision-log)

## 🧭 The Diátaxis Compass

Diátaxis distinguishes the four modes along **two axes** — *action vs. cognition* and
*acquisition vs. application of skill*:

- **action**: practical steps, *doing* — vs. **cognition**: theoretical/propositional
  knowledge, *thinking*.
- **acquisition**: serving the user's *study* (learning) — vs. **application**: serving the
  user's *work* (performing a task).

The compass forces a single decision before a page is written. Place every candidate page on it:

| If the content… | …and serves the user's… | …then it must belong to… |
|---|---|---|
| informs **action** | **acquisition** of skill (study) | a **tutorial** |
| informs **action** | **application** of skill (work) | a **how-to guide** |
| informs **cognition** | **application** of skill (work) | **reference** |
| informs **cognition** | **acquisition** of skill (study) | **explanation** |

> **The discipline: do not mix modes on one page.** A tutorial that pauses to explain
> machinery, or a reference page that lapses into a how-to, fails both readers. When a page
> blurs, split it. {{mixing_policy}}
> *(State how authors and reviewers catch blurred pages — e.g. "every page declares its mode
> in frontmatter; PR review rejects pages that serve two needs.")*

## 🗺️ The Four Modes

What each mode is, who it serves, and where responsibility lies (per Diátaxis):

| Mode | Orientation | Serves | The page is… | Responsibility |
|---|---|---|---|---|
| **Tutorials** | learning-oriented (action × acquisition) | the *learner* engaged in **study**, acquiring basic competence | a **lesson** — a guided, guaranteed-to-succeed learning experience | the **teacher**: "if the learner gets into trouble, that's the teacher's problem to put right" |
| **How-to guides** | task-oriented (action × application) | the *already-competent* user engaged in **work** | a **recipe** — directions to achieve a specific real-world goal | the **user**: they "have responsibility for getting themselves in and out of trouble" |
| **Reference** | information-oriented (cognition × application) | the user *at work*, needing to look something up | a **description of the machinery** — austere, structured to mirror the product | accuracy & completeness; structured around the code/product, not a narrative |
| **Explanation** | understanding-oriented (cognition × acquisition) | the user *studying*, building a mental model | a **discussion** — discursive, provides context, answers *why* | clarifying connections, alternatives, design rationale |

**Modes present in {{project_name}}'s docs:** {{modes_in_scope}}
*(Most public docs surfaces need all four; a CLI or library may lean on reference + how-to with
a single onboarding tutorial. State which modes ship and why any is omitted.)*

## 📚 Content Inventory by Mode

The concrete pages this project ships, sorted into the four modes. Each page lives in
**exactly one** mode. (`docs` concern, surface: `{{docs_surface}}`.)

### 📖 Tutorials — *learning-oriented; serve study*

A short, ordered set of lessons that take a beginner from zero to first success. Keep the
count small; tutorials are expensive to maintain and each must be guaranteed to work.

| Tutorial | Outcome the learner reaches | Path |
|---|---|---|
| {{tutorial_1_title}} | {{tutorial_1_outcome}} | `{{tutorial_1_path}}` |
| {{additional_tutorials}} | … | … |

- **Entry tutorial ("Getting started"):** {{getting_started_tutorial}}
- **Maintenance rule:** every tutorial is **runnable end-to-end** in CI or a periodic check —
  a tutorial that no longer works is the worst kind of doc. {{tutorial_test_policy}}

### 🔧 How-to guides — *task-oriented; serve work*

Goal-titled recipes ("How to {{verb}} {{thing}}"). Each addresses one real problem a competent
user already has; it assumes context and does not teach fundamentals.

| Goal | When a user needs it | Path |
|---|---|---|
| {{howto_1_goal}} | {{howto_1_context}} | `{{howto_1_path}}` |
| {{additional_howtos}} | … | … |

### 📑 Reference — *information-oriented; serve work*

Dry, complete, consistently structured descriptions: API/CLI surface, config keys, schemas,
return values, error codes. Mirror the structure of the product. Prefer **generated** reference
where possible (from docstrings/OpenAPI/schema) so it can't drift.

| Reference area | Source of truth | Generated or hand-written? | Path |
|---|---|---|---|
| {{reference_1_area}} | {{reference_1_source}} | {{reference_1_generated}} | `{{reference_1_path}}` |
| {{additional_reference}} | … | … | … |

- **Reference generator:** {{reference_generator}}
  *(e.g. typedoc / Sphinx autodoc / OpenAPI → docs / `--help` capture. Wire it into CI so the
  reference regenerates on every merge.)*

### 💡 Explanation — *understanding-oriented; serve study*

Discursive background: architecture, design decisions, trade-offs, the *why*. Cross-link to the
ADRs and architecture docs rather than duplicating them.

| Explanation topic | Question it answers | Path |
|---|---|---|
| {{explanation_1_topic}} | "{{explanation_1_question}}" | `{{explanation_1_path}}` |
| {{additional_explanations}} | … | … |

## 🛠️ Docs-as-Code Toolchain

Documentation is **source in the repo**, reviewed and shipped like code. (`docs.tooling`)

| Concern | Choice |
|---|---|
| Docs source location | {{docs_source_path}} (e.g. `docs/` in the main repo, or a dedicated docs repo) |
| Markup format | {{docs_format}} (Markdown / MDX / reStructuredText / AsciiDoc) |
| Site generator | {{docs_generator}} (e.g. Docusaurus / MkDocs Material / Astro Starlight / Sphinx / VitePress) |
| Hosting / deploy target | {{docs_host}} (`docs.host`) |
| Search | {{docs_search}} (built-in / Algolia DocSearch / Pagefind) |
| Diagrams-as-code | {{diagrams_tool}} (Mermaid / D2 / PlantUML — kept in-repo, rendered at build) |
| Custom domain | {{docs_domain}} |

**Authoring conventions:** {{authoring_conventions}}
*(Page frontmatter declares its Diátaxis mode; one H1 per page; sentence-case headings;
relative links between docs; code samples that are tested or copy-paste-runnable.)*

## 🔁 CI Pipeline (build · preview · link-check)

Docs changes flow through the same review + CI gates as code, on `{{ci_provider}}`. A broken
docs build or dead link blocks the merge.

| Gate | Tool | Blocking? |
|---|---|---|
| Markdown / prose lint | {{prose_linter}} (markdownlint / Vale) | {{prose_lint_blocking}} |
| Site build (no warnings) | {{docs_generator}} | {{build_blocking}} |
| Internal link check | {{link_checker}} (lychee / linkinator / built-in) | {{link_check_blocking}} |
| External link check | {{external_link_checker}} (scheduled, not per-PR — external sites flake) | {{external_link_blocking}} |
| Spelling | {{spell_checker}} (cspell / typos) | {{spell_blocking}} |
| Code-sample / tutorial execution | {{sample_test_tool}} | {{sample_test_blocking}} |
| Deploy preview per PR | {{preview_deploy}} (Netlify/Vercel/CF Pages preview, or PR artifact) | n/a (advisory) |

- **PR preview deploys** let reviewers *see* the rendered change before approving —
  reviewing raw Markdown hides layout/nav regressions. {{preview_policy}}
- **Reference is regenerated in CI**, not committed by hand, so it can never drift from the
  code it describes. {{reference_ci_policy}}

## 🧱 Information Architecture & Navigation

The four Diátaxis modes are also the **top-level navigation**. Don't bury the mode structure;
expose it, so a user who is *working* lands in how-to/reference and a user *studying* lands in
tutorials/explanation.

```
{{docs_root}}/
├── tutorials/        📖 learning-oriented — start here (lessons)
├── how-to/           🔧 task-oriented — solve a specific problem
├── reference/        📑 information-oriented — look it up
└── explanation/      💡 understanding-oriented — understand why
```

| IA decision | Choice |
|---|---|
| Top-level nav = the four modes? | {{nav_by_mode}} |
| Landing page / docs home | {{docs_home}} — routes the visitor to the right mode by intent |
| Cross-linking convention | {{cross_link_convention}} (how-to → reference for detail; explanation → ADRs) |
| URL stability | {{url_stability}} (stable slugs; redirects on rename so links never rot) |
| Audience segmentation | {{audience_segmentation}} (e.g. end-user vs. contributor vs. operator docs) |

> Diátaxis is also a **gradual-adoption** path: you can map an existing, messy docs tree onto
> the four modes incrementally rather than rewriting it all at once. Record the current state
> vs. target below if migrating: {{ia_migration_state}}

## 📦 Versioning

Whether and how docs track product releases. (`docs.versioned`)

| Versioning dimension | Decision |
|---|---|
| Versioned docs? | {{docs_versioned}} |
| Versioning scheme | {{docs_version_scheme}} (per release tag / "latest" + "stable" / single rolling) |
| Where old versions live | {{old_version_hosting}} (generator multi-version / branch per release / snapshot) |
| Default version shown | {{default_doc_version}} |
| Deprecation / sunset policy for old versions | {{version_sunset_policy}} |
| Unreleased / "next" docs | {{unreleased_docs_policy}} (preview branch, banner-flagged) |

*(Single-product, fast-moving tools often ship a single rolling docs site; libraries/APIs with
supported old majors usually need versioned docs. Choose the cheapest option that doesn't lie
to users on an old version.)*

## ♻️ Freshness & Ownership

Docs rot silently. Make staleness *detectable* and ownership *explicit*.

| Concern | Policy |
|---|---|
| Docs owner(s) | {{docs_owners}} — CODEOWNERS entry for the docs path |
| "Docs updated with the change" gate | {{docs_with_change_policy}} — user-visible change → docs update in the **same** PR |
| Last-reviewed metadata | {{last_reviewed_metadata}} (per-page `last_reviewed` date; flag pages older than {{staleness_threshold}}) |
| Staleness audit cadence | {{staleness_audit}} (scheduled CI job / periodic review) |
| Reader feedback loop | {{feedback_mechanism}} ("Was this helpful?" / issue-from-page link) |
| Broken-link monitoring (post-deploy) | {{post_deploy_link_monitor}} |
| Source-of-truth rule | reference is **generated** from code; explanation **links** to ADRs — neither is re-typed by hand |

> **The freshness contract:** a tutorial or how-to that no longer works is worse than no doc,
> because it costs the user time *and* trust. Tie at least the tutorials and primary how-tos to
> an executable check so failure surfaces in CI, not in a support ticket. {{freshness_contract}}

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
