<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Document Catalog

The orchestrator queries this catalog before Phase 4 to decide which templates to dispatch `document-author` for. Templates live in `templates/<NAME>.md` with YAML frontmatter that mirrors fields used here.

## Table of Contents
- [Selection algorithm](#selection-algorithm)
- [Always-generated templates](#always-generated-templates)
- [Type-anchored templates](#type-anchored-templates)
- [Conditional matrix](#conditional-matrix)
- [Plan documents](#plan-documents)
- [Programming language design (v2.3, Sketch F)](#programming-language-design-v23-sketch-f)
- [Dependency / generation order](#dependency--generation-order)

---

## Selection algorithm

```
def select_templates(state):
    selected = list(ALWAYS_TEMPLATES)
    # type-anchored
    for tmpl in TYPE_ANCHORS[state.decisions["project.type"]]:
        selected.append(tmpl)
    # conditional
    for tmpl in CONDITIONAL_TEMPLATES:
        if matches(tmpl.generate_when, state):
            selected.append(tmpl)
    # de-duplicate
    selected = unique(selected)
    # respect dependencies — write upstream before downstream
    return topological_sort(selected, key="depends_on")
```

`matches(expr, state)` evaluates the simple boolean expressions used in template frontmatter (e.g., `decisions.auth.enabled == true`, `decisions.scale != "hobby"`). The orchestrator parses these — no real engine, just key-lookup + comparison + `AND` / `OR` / `NOT`.

## Always-generated templates

| Template | File |
|---|---|
| PROJECT_OVERVIEW | `templates/PROJECT_OVERVIEW.md` |
| PROJECT_REQUIREMENTS | `templates/PROJECT_REQUIREMENTS.md` |
| CLAUDE_MD_ROOT | `templates/CLAUDE_MD_ROOT.md` |

(ADR_TEMPLATE and REVISION_LOG_FRAGMENT also live in `templates/` but are used by agents, not selected as standalone docs.)

## Type-anchored templates

Selected automatically when the top-level project type matches.

| Top-level project type | Anchored templates |
|---|---|
| Web application | UI_UX_DESIGN, PLATFORMS (if multi-target) |
| Mobile application | MOBILE_SPECIFIC, PLATFORMS (if cross-platform) |
| Multi-platform system | PLATFORMS |
| API / backend service | API_GATEWAY |
| CLI tool | *(no anchor — naturally smaller doc set)* |
| Library / SDK / package | SDK_DESIGN |
| Desktop application | DESKTOP_SPECIFIC |
| Browser extension | BROWSER_EXTENSION |
| Game | GAME_SPECIFIC |
| AI/ML application | AI_AND_ML, ML_OPS |
| Data pipeline | DATA_PIPELINE |
| Embedded / IoT | EMBEDDED_SPECIFIC, HARDWARE_FIRMWARE (if hardware combo) |
| Infrastructure tool | DEPLOYMENT, CI_CD (both anchored) |
| Claude Code plugin | PLUGIN_SPECIFIC |
| MCP server | MCP_SERVER_SPECIFIC |
| Web3 / smart contracts | WEB3_SPECIFIC, THREAT_MODEL |
| Scientific / research | SCIENTIFIC_COMPUTING |
| AR / VR / spatial | AR_VR_SPECIFIC, MOBILE_SPECIFIC (if mobile-AR) |

## Conditional matrix

| Template | `generate_when` expression |
|---|---|
| TECH_STACK | `decisions.stack.backend.language != null OR decisions.stack.frontend.framework != null` — the chosen stack + resolved `stack.versions.*` pins; the home the plan docs below reference |
| AUTHENTICATION_SYSTEM | `decisions.auth.enabled == true` |
| DATABASE_DESIGN | `decisions.database.engine != null` |
| API_GATEWAY | `decisions.api.enabled == true` *(also type-anchored for API projects)* |
| UI_UX_DESIGN | `decisions.frontend.framework != null` *(also type-anchored for web)* |
| PLATFORMS | `decisions.platforms.length > 1` |
| SECURITY_AND_COMPLIANCE | `decisions.auth.enabled == true OR decisions.constraints.includes('regulated')` |
| DEPLOYMENT | `decisions.hosting.frontend != null OR decisions.hosting.backend != null` |
| CI_CD | `decisions.devops.cicd != null` |
| TESTING_STRATEGY | `decisions.scale != "hobby" OR decisions.project.type != "library"` |
| THIRD_PARTY_INTEGRATIONS | `decisions.integrations.length > 0` |
| MONITORING_AND_OBSERVABILITY | `decisions.scale != "hobby" AND decisions.production_bound == true` |
| BILLING_AND_PAYMENTS | `decisions.monetization.enabled == true` |
| EMAIL_AND_NOTIFICATIONS | `decisions.notifications.enabled == true` |
| FILE_STORAGE | `decisions.file_handling.enabled == true` |
| AI_AND_ML | `decisions.ai.enabled == true` *(also type-anchored)* |
| REAL_TIME | `decisions.realtime.enabled == true` |
| SEARCH | `decisions.search.enabled == true` |
| CACHING_STRATEGY | `decisions.scale >= "growth" OR decisions.caching.enabled == true` |
| INTERNATIONALIZATION | `decisions.i18n.languages.length > 1` |
| ACCESSIBILITY | `decisions.frontend.framework != null AND decisions.a11y.target != null` |
| DATA_PIPELINE | `decisions.data_pipeline.enabled == true` *(also type-anchored)* |
| BACKGROUND_JOBS | `decisions.background_jobs.enabled == true` |
| COST_MODEL | `decisions.scale != "hobby" OR decisions.managed_services_in_stack == true` |
| RUNBOOK | `decisions.production_bound == true AND decisions.scale >= "growth"` |
| INCIDENT_RESPONSE | `decisions.production_bound == true AND decisions.scale >= "growth"` |
| DISASTER_RECOVERY | `decisions.production_bound == true AND decisions.scale >= "growth"` |
| SLO_AND_ERROR_BUDGETS | `decisions.scale >= "growth"` |
| THREAT_MODEL | `decisions.constraints.includes('regulated') OR decisions.security.formal_threat_model == true` *(also type-anchored for Web3)* |
| BACKUP_AND_DR | `decisions.database.engine != null AND decisions.scale != "hobby"` |
| PERFORMANCE_BUDGETS | `decisions.frontend.framework != null OR decisions.api.enabled == true` |
| ARCHITECTURE_DIAGRAMS | `decisions.scale >= "growth" OR decisions.complexity == "high"` |
| SDK_DESIGN | `decisions.project.type == "library" OR decisions.exposes_sdk == true` |
| TENANT_AND_ORGANIZATION_MODEL | `decisions.multi_tenancy == true` |
| EXPERIMENTS | `decisions.feature_flags.enabled == true OR decisions.ab_testing.enabled == true` |
| ANALYTICS_AND_TELEMETRY | `decisions.analytics.enabled == true` |
| ONBOARDING | `decisions.team_size != "solo"` |
| CONTRIBUTING | `decisions.open_source == true` |
| RELEASE_PROCESS | `decisions.production_bound == true` |
| CLI_UX_DESIGN | `project.sub_type in ["cli_tool", "cli_with_subcommands", "tui_app", "interactive_cli"]` — depends on `PROJECT_REQUIREMENTS.md`, `CLI_REFERENCE.md`, `ARCHITECTURE.md`, `TECH_STACK.md` |

## Plan documents

**Plan documents** are an intermediate artifact produced in Phase 6 (after the doc set is committed) and consumed in Phase 7 to actually generate CLAUDE.md files, scaffold the repository, write slash commands, and surface a next-step plan to the user. They are written to `docs/` like other catalog entries, but their downstream effect is *generative* — each plan describes what a Phase 7 agent will materialise on disk.

| Template | `generate_when` | `depends_on` |
|---|---|---|
| CLAUDE_MD_PLAN | `always` | `PROJECT_OVERVIEW.md`, `TECH_STACK.md` |
| CLAUDE_TOOLING_PLAN | `always` | `SECURITY_AND_COMPLIANCE.md`, `TECH_STACK.md`, `RELEASE_PROCESS.md` |
| SCAFFOLD_PLAN | `project.sub_type != "documentation_only"` | `TECH_STACK.md`, `ARCHITECTURE.md`, `BUILD_AND_RUN.md`, `LICENSE_NOTICE.md` |
| NEXT_STEP_PLAN | `always` | *(none)* |

Plan files live in `templates/<NAME>.md` alongside other templates. They are dispatched by `document-author` in the same Phase 4 / 6 wave as other docs, but the orchestrator routes their outputs to Phase 7 executors (`claude-md-author`, `claude-tooling-author`, `scaffolder`) rather than treating them as final deliverables.

## Programming language design (v2.3, Sketch F)

**Programming-language templates** are a v2.3 addition (Sketch F — "Designing a programming language"). They activate when `project.sub_type` is one of the six PL variants: `general_purpose_language`, `domain_specific_language`, `query_language`, `configuration_language`, `educational_language`, or `transpiler_target`. All seven templates share a single gate — they are dispatched together whenever the project is a language design, and skipped entirely otherwise. They sit downstream of `PROJECT_OVERVIEW` and `TECH_STACK` (which capture *that* a language is being built and on *what* host runtime), and form their own dependency chain among themselves so that the grammar is pinned before semantics, semantics before types, and so on.

| Template | `generate_when` | `depends_on` | Purpose |
|---|---|---|---|
| LANGUAGE_GRAMMAR | `project.sub_type in [PL-6]` | `PROJECT_OVERVIEW.md`, `TECH_STACK.md` | Surface syntax — lexer, parser, grammar, disambiguation rules. |
| SEMANTICS | `project.sub_type in [PL-6]` | `LANGUAGE_GRAMMAR.md`, `TECH_STACK.md` | Dynamic semantics — what programs *mean* once parsed. |
| TYPE_SYSTEM | `project.sub_type in [PL-6]` | `SEMANTICS.md`, `LANGUAGE_GRAMMAR.md` | Which programs are well-typed and what that guarantees. |
| STDLIB | `project.sub_type in [PL-6]` | `SEMANTICS.md`, `TYPE_SYSTEM.md` | Shape of the standard library — what ships in the box vs delegated to a package manager. |
| TOOLCHAIN | `project.sub_type in [PL-6]` | `SEMANTICS.md`, `LANGUAGE_GRAMMAR.md` | Developer-facing tooling — REPL, formatter, linter, LSP, debugger, package manager, build tool. |
| BOOTSTRAP_PLAN | `project.sub_type in [PL-6]` | `LANGUAGE_GRAMMAR.md`, `SEMANTICS.md`, `TYPE_SYSTEM.md` | How v0.1 of the implementation gets built — host language, MVP scope, milestones to self-hosting. |
| STABILITY_AND_RFC | `project.sub_type in [PL-6]` | `BOOTSTRAP_PLAN.md`, `TOOLCHAIN.md` | Social contract on change — versioning, stability tiers, breaking-change policy, RFC process, governance. |

`[PL-6]` is shorthand for the six PL sub_types listed above. The actual template frontmatter expands the list in full so the matcher in `select_templates` sees a literal array.

All seven templates depend (transitively) on `PROJECT_OVERVIEW.md` and `TECH_STACK.md` through `LANGUAGE_GRAMMAR.md`. The orchestrator topologically sorts them with the rest of the doc set, so a PL project's Phase 4 dispatch wave naturally places these between the always-generated docs and the closing `CLAUDE_MD_ROOT`.

## Dependency / generation order

The architect topologically sorts selected templates by `depends_on` before parallel dispatch, so cross-references resolve.

```
PROJECT_OVERVIEW
└─ PROJECT_REQUIREMENTS
   ├─ AUTHENTICATION_SYSTEM ──────────────┐
   ├─ DATABASE_DESIGN ────────────────────┤
   ├─ UI_UX_DESIGN                        │
   ├─ PLATFORMS                           │
   ├─ TESTING_STRATEGY                    │
   ├─ DEPLOYMENT ─────────────────┐       │
   ├─ TENANT_AND_ORGANIZATION_MODEL│      │
   ├─ EXPERIMENTS                  │      │
   ├─ ANALYTICS_AND_TELEMETRY      │      │
   │                               │      │
   ├─ API_GATEWAY ◄────────────────┼──────┤  depends on AUTH + DATABASE
   ├─ SECURITY_AND_COMPLIANCE ◄────┴──────┤  depends on AUTH + DATABASE
   │                                      │
   ├─ CI_CD ◄──────────────────── DEPLOYMENT + TESTING_STRATEGY
   ├─ MONITORING_AND_OBSERVABILITY ◄──────┘
   ├─ BACKUP_AND_DR ◄──── DATABASE_DESIGN
   ├─ COST_MODEL ◄──── DEPLOYMENT + DATABASE_DESIGN
   ├─ THIRD_PARTY_INTEGRATIONS
   ├─ THREAT_MODEL ◄──── SECURITY_AND_COMPLIANCE
   ├─ RUNBOOK ◄──── DEPLOYMENT + MONITORING_AND_OBSERVABILITY
   ├─ INCIDENT_RESPONSE ◄──── MONITORING_AND_OBSERVABILITY + RUNBOOK
   ├─ DISASTER_RECOVERY ◄──── BACKUP_AND_DR + DEPLOYMENT
   ├─ SLO_AND_ERROR_BUDGETS ◄──── MONITORING_AND_OBSERVABILITY
   ├─ ARCHITECTURE_DIAGRAMS ◄──── most architecture docs
   ├─ PERFORMANCE_BUDGETS ◄──── UI_UX_DESIGN + API_GATEWAY
   │
   ├─ MOBILE_SPECIFIC | DESKTOP_SPECIFIC | EMBEDDED_SPECIFIC | ML_OPS | GAME_SPECIFIC |
   │   BROWSER_EXTENSION | PLUGIN_SPECIFIC | HARDWARE_FIRMWARE | WEB3_SPECIFIC |
   │   SCIENTIFIC_COMPUTING | AR_VR_SPECIFIC | MCP_SERVER_SPECIFIC
   │   (each independent of the others; depends on PROJECT_OVERVIEW)
   │
   ├─ AI_AND_ML | DATA_PIPELINE | REAL_TIME | SEARCH | BILLING_AND_PAYMENTS |
   │   EMAIL_AND_NOTIFICATIONS | FILE_STORAGE | CACHING_STRATEGY |
   │   INTERNATIONALIZATION | ACCESSIBILITY | BACKGROUND_JOBS |
   │   ONBOARDING | CONTRIBUTING | RELEASE_PROCESS | SDK_DESIGN
   │   (feature-area templates; depend on PROJECT_REQUIREMENTS only)
   │
   ├─ CLI_UX_DESIGN ◄──── PROJECT_REQUIREMENTS + CLI_REFERENCE + ARCHITECTURE + TECH_STACK
   │   (CLI/TUI sub-types only; gated on project.sub_type)
   │
   ├─ Programming-language chain (v2.3, Sketch F — PL sub_types only):
   │     LANGUAGE_GRAMMAR ◄──── PROJECT_OVERVIEW + TECH_STACK
   │       └─ SEMANTICS ◄──── LANGUAGE_GRAMMAR + TECH_STACK
   │            ├─ TYPE_SYSTEM ◄──── SEMANTICS + LANGUAGE_GRAMMAR
   │            │    └─ STDLIB ◄──── SEMANTICS + TYPE_SYSTEM
   │            ├─ TOOLCHAIN ◄──── SEMANTICS + LANGUAGE_GRAMMAR
   │            └─ BOOTSTRAP_PLAN ◄──── LANGUAGE_GRAMMAR + SEMANTICS + TYPE_SYSTEM
   │                 └─ STABILITY_AND_RFC ◄──── BOOTSTRAP_PLAN + TOOLCHAIN
   ↓
CLAUDE_MD_ROOT (depends on all)
CLAUDE_MD_SUBFOLDER (per-folder, depends on root + folder-relevant docs)
   ↓
CLAUDE_MD_PLAN          ◄── PROJECT_OVERVIEW + TECH_STACK
CLAUDE_TOOLING_PLAN     ◄── SECURITY_AND_COMPLIANCE + TECH_STACK + RELEASE_PROCESS
SCAFFOLD_PLAN           ◄── TECH_STACK + ARCHITECTURE + BUILD_AND_RUN + LICENSE_NOTICE
NEXT_STEP_PLAN          (no dependencies; written last as a forward-looking summary)
```

The `claude-md-author` agent writes CLAUDE.md files **after** all other docs are committed. The `claude-tooling-author` runs in parallel with `claude-md-author`. In Phase 7 (Tooling Execution), the four plan documents above are consumed by Phase 7 agents (`claude-md-author`, `claude-tooling-author`, `scaffolder`) to materialise CLAUDE.md files, slash commands, and repo scaffolding on disk.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
