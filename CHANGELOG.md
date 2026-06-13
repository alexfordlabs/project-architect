<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Changelog

All notable changes to the `project-architect` plugin.

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v9.2.0 — 2026-06-13

**Latest-Fable everywhere + the three remaining tiger-panther run bugs.**

### Changed

- **Every model surface now targets the latest Fable-class Claude model**
  (operator standing rule). All 7 subagent frontmatters and every SKILL.md
  dispatch use the auto-tracking `fable` alias; the Preflight model gate
  targets Fable-class (`claude-fable-5` as of this release; any newer
  Fable/Mythos id qualifies), with a current Opus + 1M context as the accepted
  floor; generated-artifact surfaces (claude-tooling-author's `settings.json`
  quality bar, golden-path `ai.model`, claude-code-integration's generated
  agent examples) name `claude-fable-5`. `tests/test_v92_model_fable.sh` pins
  all surfaces so an Opus-pinned dispatch can't silently return.
- **check_19 `audit_freshness` no longer fails on clean post-lock re-audits** —
  SKILL Phase 9 (Tooling Execution) runs after lock and prescribes re-audits,
  so "any post-lock audit = defect" made the skill contradict its own gate
  (every post-Phase-9 audit went permanently red). New semantics: the lock
  must be vetted by a CLEAN audit at-or-before `locked_at` (missing or blocked
  vetting audit still fails), and a post-lock audit only fails when it is
  itself BLOCKED (state degraded after lock).
- **check_20 `no_oob_phase_advance` tolerates the `preflight` opener** —
  pre-v9.2 SKILL.md instructed `set-phase preflight`, so real projects carry a
  `PhaseAdvanced` to=preflight in their append-only log forever; check_20
  treated it as an unknown phase and permanently blocked their audits.

### Fixed

- **`reconcile-adrs` TypeError on mixed ADR id types** — YAML parses an
  unquoted `id: 0001` as the int 1; mixed with quoted-string ids from sibling
  files, the index sort crashed (`'<' not supported between 'str' and 'int'`).
  Ids (and `supersedes`/`superseded_by` entries) now normalize to the
  canonical zero-padded string form.
- **SKILL.md no longer instructs `set-phase preflight`** — preflight is the
  banner-only opener and is not on check_20's phase ladder; the run's first
  phase event is the Phase 0a → Kickoff `set-phase kickoff`.

## v9.1.0 — 2026-06-13

**Latest-stable everywhere: the version-pin chain is now enforced end-to-end.**
A live forensic audit of a scaffolded project found a generated `biome.json`
shipping a full major behind newest-stable because the pin chain had three
silent gaps: a stale generator floor, a research-obligation that didn't match
the emission condition, and an audit blind spot. All three classes are fixed,
plus every sibling defect a repo-wide scan surfaced.

### Added

- **New audit check 36 `version_pins_recorded` (WARNING)** — for every pin
  token the chosen stack makes applicable, if the generated artifact exists on
  disk and `stack.versions.<token>` was never recorded, the audit flags it with
  the exact `set-decision` remediation. A floor fallback can no longer ship
  silently. Applicability comes from `configs.applicable_pin_tokens` — the SAME
  predicates `generate-configs` emits by, so obligation and emission cannot
  diverge. The auditor is now **36 checks**.
- **`bin/floor-check`** — release-time freshness audit for `configs.FLOORS`:
  queries npm + endoflife.date and reports any floor that has drifted off the
  newest stable line. Non-zero exit = bump the floors before tagging.
- **Pinned `devDependencies` in generated `package.json`** — every tool the
  generated scripts invoke is now declared: `@biomejs/biome` (exact pin),
  `typescript`, `@types/node` (tracks the node major), and on Next.js stacks
  `@types/react`/`@types/react-dom` (track the react pin). Previously the
  scripts referenced an undeclared global toolchain.
- **`stack.versions.typescript`** joins the canonical pin-token set
  (`next`, `react`, `node`, `python`, `postgres`, `redis`, `biome`,
  `typescript`) across `decision-keys.md`, SKILL Phase 4, research-scout § 1a,
  research-prompts, and the TECH_STACK template.
- **Golden-path expiry is honored** — `golden-path list` now annotates any path
  whose `valid_through` has passed (`[EXPIRED <date> — re-verify stack +
  versions]`); previously the field was dead metadata and an expired bundle
  would be offered as current forever.

### Changed

- **`configs.FLOORS` refreshed to newest stable as of 2026-06-13** and
  consolidated into one registry: next `^16.0.0` (was `^15.0.0`), node `24`
  (was `22`), python `3.14` (was `3.11`), postgres `18` (was `17`), redis `8`
  (was `7`), biome `2.5.0` (was `1.9.4`), typescript `^6.0.0` (new). Floors
  are a fallback only — research-resolved `stack.versions.*` pins always win.
- **`gen_biome_json` is version-aware** — a 2.x pin (and the 2.x floor) emits
  the Biome 2 shape (`assist.actions.source.organizeImports`); a 1.x pin emits
  the legacy top-level `organizeImports`. Previously the 1.x-only shape was
  emitted unconditionally — a hard config error under any 2.x binary. The
  linter block stays on `rules.recommended: true`, valid across 1.x and all
  2.x (the `rules.preset` alias is 2.5-only; live-validated against 2.4.15).
- **`generate-configs` no longer emits a silent node `Dockerfile` for every
  stack** — emission rides the new shared `dockerfile_language` predicate:
  python and JS/TS stacks get their runtime's Dockerfile; rust/go/undecided
  stacks get none (the old behavior based a rust project on a node image).
  `tsconfig.json` now ships whenever `package.json` does (its build script
  runs `tsc`).
- **Check 23 `dependency_freshness` scans the whole tree** — nested manifests
  (`web/package.json`, `crates/core/Cargo.toml`, …) are now audited;
  third-party/build dirs (`node_modules`, `vendor`, `dist`, `target`, …) are
  pruned. Previously only root-level manifests were scanned, and a repo with
  no root manifest was never scanned at all.
- **`revision-playbook.md` migrated to the canonical `stack.*` namespace** —
  its tables still used pre-v8 keys (`database.engine`, `frontend.framework`),
  so `decision-revisor` lookups for canonical keys (`stack.database.engine`)
  missed every stack row; `ai.*` rows renamed to their canonical equivalents
  and rows added for `stack.frontend.language`, `stack.cache.engine`, and
  `stack.versions.*`.
- **Stale literals swept from decision surfaces**: the `modern_saas_2026`
  golden path no longer hardcodes "Next.js 15" in its description nor seeds
  the superseded `stack.frontend.version` key (removed from `decision-keys.md`
  too); `ai.model` examples bumped `claude-opus-4-7` → `claude-opus-4-8`;
  document-author's version-family example unstuck from "15.x"; the
  STABILITY_AND_RFC template no longer asserts Go 1.22 as "the latest at time
  of writing"; SKILL Phase 4 records pins via `<resolved-pin>` placeholders
  instead of copy-able stale literals, and now enumerates all 8 tokens + all
  5 consuming generators.
- CI matrix extended to Python 3.14.

### Fixed

- The tiger-panther-game defect chain (stale `biome.json` 1.9.4, invalid-shape
  config for a 2.x pin, undeclared toolchain, unaudited nested manifest) is
  fixed at every link; `tests/test_v91_pin_coverage.sh` pins the four
  obligation surfaces (research-scout, SKILL, decision-keys, configs.FLOORS)
  to the same token set so they cannot drift apart again.

## v9.0.0 — 2026-06-11

**Relicense: MIT → Apache License 2.0.** No functional change. Rationale: the
NOTICE file's attribution becomes a binding redistribution condition (Apache-2.0
§4(d)); the license itself now states that no trade-name/trademark rights are
granted (§6); and users gain an explicit patent grant with defensive
termination (§3). **Every version up to and including v8.2.1 remains MIT** —
those grants are irrevocable for those versions; this change governs v9.0.0
onward.

### Changed

- `LICENSE` is now the Apache License, Version 2.0 (was MIT).
- `NOTICE` rewritten for Apache-2.0 (§4(d) redistribution condition; §6
  trade-name non-grant; MIT note for ≤ v8.2.1).
- All 332 source attribution headers flipped `License: MIT` →
  `License: Apache-2.0`. Templates and defaults that set **the user's
  generated project license** (e.g. `SCAFFOLD_PLAN`'s MIT block,
  `stack.license` examples, golden-path descriptions) are intentionally
  unchanged — they describe the user's project, not this one.
- `plugin.json` declares `"license": "Apache-2.0"`.

## v8.2.1 — 2026-06-11

**Licensing & provenance.** Documentation-only patch; no behavior change.

### Added

- **`NOTICE` file.** Makes explicit the attribution the MIT license already requires (copyright + permission notice must travel with copies and substantial portions), claims the project's trade names ("project-architect", "Alex Ford Labs"), and records that authorship/provenance are independently archived (Software Heritage; third-party timestamped repositories) from the project's inception in February 2026 onward.

## v8.2.0 — 2026-06-05

**Catalog & config-generation correctness.** Additive fixes that make advertised project types reachable and make generated scaffolds track researched versions. No change to the 12-phase flow, the event-sourced state model, or the 35-check audit.

### Added

- **Three project types are now first-class: `web3`, `scientific`, `ar_vr`.** They were advertised and already shipped catalog documents and interview drill-downs, but were missing from the canonical type registry — so their signature documents (`WEB3_SPECIFIC`, `SCIENTIFIC_COMPUTING`, `AR_VR_SPECIFIC`) could never be selected. Registered, with a guard test pinning the catalog↔registry contract (scanning both the `==`/`!=` and `IN [...]` condition forms).
- **More config versions are state-driven.** `pyproject.toml`, `docker-compose.yml`, and `biome.json` now read their pins from the `stack.versions.*` namespace (`postgres`, `redis`, `biome`) — and `research-scout` is instructed to record them — instead of frozen constants, so a researched pin flows into the scaffold.

### Fixed

- **Catalog type-literal typos.** Four catalog conditions referenced `mobile` / `desktop` / `ai_ml` / `embedded`, none of which match the registry's `mobile_app` / `desktop_app` / `ml_project` / `embedded_system`, so those archetypes silently received a smaller document set. Corrected.
- **`pyproject.toml` now agrees with the Dockerfile on Python.** `requires-python` and the ruff `target-version` track the same researched Python pin the Dockerfile already used, instead of a frozen `3.11`.

## v8.1.2 — 2026-06-01

**CI green.** A one-line follow-up to v8.1.1: the new CI's first run did its job and caught a non-portable test. No plugin behavior change.

### Fixed

- **`test_v7_changelog_curated.sh` is now portable.** It asserted the on-disk presence of the **gitignored** `CHANGELOG.dev.md`, which holds in the author's working tree but not in a fresh clone / CI checkout — so the suite was green locally yet red in CI. The existence check is now conditional (run only when the file is present); the real invariant — that the file is untracked, and the public CHANGELOG is curated — is still pinned, so a clean checkout stays green.

## v8.1.1 — 2026-06-01

**Correctness + CI.** A focused fix release: the two cross-version commands are runnable again, the plugin version is single-sourced, dispatched subagents can resolve their reference paths, and the repo now runs CI on itself. No change to the 12-phase flow, the event-sourced state model, or the 35-check audit.

### Fixed

- **`/upgrade-project` and `/re-architect` are runnable again.** Both commands invoked the v7 `architect-ledger` binary (removed at the v8 cutover) with a flag `architect-brain` rejects; they now call `architect-brain detect` and their prose is reconciled to its real `{situation, schema_version, state_layout}` output (the `below_floor` / `newer_than_plugin` / `can_rederive` signals are orchestrator-derived, per the canonical flow docs).
- **Plugin version is single-sourced from `plugin.json`.** `architect_brain.__version__` (and the `--version` output) had drifted to a hardcoded `8.0.0`; it now resolves from `.claude-plugin/plugin.json`, and the migrator stamps that resolved version into migrated ADR/doc `plugin_version` frontmatter instead of a stale literal — so a release bump propagates everywhere automatically.
- **Dispatched subagents can resolve their reference paths.** The template / catalog / integration-recipe / playbook paths handed to subagents are now absolute (`${CLAUDE_PLUGIN_ROOT}/…`) — a dispatched agent runs in the user's project, so the previous bare `skills/…` paths were unresolvable (a silent template-read failure → fabricated structure). `document-author` now receives a `catalog_path` INPUT, and `agent-common.md` makes a bare relative reference path a hard BLOCKER.

### Added

- **Continuous integration.** A GitHub Actions workflow runs the full suite (bash harness + the `architect_brain` Python suite) across Python 3.10–3.13 on every push and PR, plus `shellcheck` and a full-tree `gitleaks` secret scan; a release-guard job refuses any tag whose number disagrees with `plugin.json` or that lacks a CHANGELOG entry.

### Changed

- **CONTRIBUTING / README hygiene.** Removed a dead test-plan link and stale "markdown-only" / marketplace claims; surfaced the hard Python 3.10+ prerequisite and the required `commit-commands` install in the README install path.

## v8.1.0 — 2026-06-01

**Enforcement + coherence.** Hardens the v8 gates that were still advisory prose, closes the version-pin pipeline end-to-end, and removes the raw-traceback / phantom-doc rough edges surfaced by a forensic review of a real bootstrap. The 12-phase flow and event-sourced state model are unchanged — this is additive features + behavioral hardening.

### Added

- **35th audit check — `user_provenance` (35, WARNING).** Flags a LOCKED project whose `DecisionMade` events are all orchestrator-sourced (zero `by:"user"`) — the signature of a skipped interview, previously invisible in the ledger. The orchestrator now records `AskUserQuestion` answers with `--by user` (Kickoff / Vision / Architecture / Stack / CLI-gate); only derived/mechanical keys keep `--by orchestrator`.
- **`TECH_STACK.md` — a real generated document** (the catalog is now 107 documents). Surfaces the chosen stack plus a **version-pins table** fed by the new `stack.versions.*` namespace, and makes `document-catalog.md`'s previously-dangling `TECH_STACK.md` dependency resolve.
- **`stack.versions.*` decision namespace.** `research-scout` § 1a delivers each newest-stable pin (e.g. `stack.versions.next`); the Stack phase records them; `generate-configs` reads them via `configs._pin` — so the scaffold ships current versions instead of plugin-baked floors.
- **`append-event --force`** — the audited escape hatch for the new mechanical LOCK gate.

### Changed

- **The LOCK gate is now mechanical, not advisory prose.** `append-event --type LockSet` refuses (exit 1) unless the latest recorded `AuditCompleted` verdict is `clean` (`--force` overrides); `check_19 audit_freshness` now reads the vetting audit's `result`, not just its timestamp. A lock can no longer be placed atop a `blocked` (or absent) audit.
- **`generate-configs` versions come from researched state, not frozen constants.** `gen_package_json` / `gen_dockerfile` read `stack.versions.*` (conservative floors as fallback); output stays deterministic.
- **The 4-tier auditor is now 35 checks** (was 34).
- **`AuditCompleted` ledger entries record `worst_severity` + the `--ack` reason.** Two same-count audits ("3 failed / clean" vs "3 failed / blocked") are now distinguishable, and an acked-clean is distinguishable from a genuinely-clean run.
- **`check_03 decisions_in_docs` precision.** Exempts operational/bookkeeping keys (`git.*` / `scm.*` / `scaffold.*` / `carry_forward.*` / `memory_pointer`) so the WARNING surfaces only substantive undocumented decisions. Severity unchanged.

### Fixed

- **No more raw tracebacks on a degraded state.** `bin/architect-brain` checks its interpreter floor (python3 present + ≥ 3.10) and exits with a clean message; `main()` wraps subcommand dispatch, so a corrupt `events.jsonl` / projection yields a clean `architect-brain: <Type>: <msg>` + exit 1 instead of a `JSONDecodeError` traceback (argparse `--help` / usage still exit normally).
- **`architecture-specialist` recorded decisions via the wrong invocation** — the bare `python3 -m architect_brain …` (a `ModuleNotFoundError` in a subagent with no `PYTHONPATH`) is now the `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain` wrapper.
- **`research-prompts.md` renumbered to the v8 phase ladder** (was pre-v8 "Phase 0/1/2/2.5/3", with the Stack prompt before pattern-validation).

## v8.0.0 — 2026-05-29

**The declarative, event-sourced major.** The 11-phase orchestration discipline is unchanged — but the machinery underneath is rebuilt. A single Python brain replaces the bash tooling, state becomes an append-only event log with derived projections, document selection becomes declarative, and the quality gate grows to 34 checks across four severity tiers.

### Added

- **`architect-brain` — one Python binary for all state + machinery** (`bin/architect-brain`, a thin shim over `python -m architect_brain`). Subcommands: `init` · `detect` · `set-decision` · `set-phase` · `set-substep` · `record-adr` · `reserve-adr` · `record-doc` · `reconcile-adrs` · `replay` · `check-state` · `audit` · `catalog {list,cycle}` · `generate-configs` · `generate-diagram` · `golden-path {list,apply}` · `migrate` · `ui {banner,phase-bar,progress}`.
- **Event-sourced, multi-file state (schema 4.0).** `docs/_architect_state/` holds an append-only `events.jsonl` (the authoritative log) + 11 per-concern projections + a flat decision index (`99-flat-index.json`) + an ADR ledger (`decisions/index.json`). Every mutation is an event; the projections are a pure `replay()` of the log. The replay invariant — `replay(events) == projections` — is the central correctness property, enforced as a FATAL audit check.
- **Architecture is decided BEFORE the tech stack.** New phase order, and a new **`architecture-specialist`** subagent (7 total) that chooses the architectural style (monolith / modular monolith / SOA / microservices / serverless / event-driven / hexagonal), boundaries, data-flow, and scaling axis — with rationale, and an explicit anti-microservices-by-default guard — before any stack choice. Cost is promoted to its own phase.
- **34-check, 4-tier auditor (`architect-brain audit`).** In-process Python checks with severities **FATAL** (blocks LOCK unconditionally) / **BLOCKING** (blocks unless `--ack=<reason>`) / **WARNING** / **INFO**. `--only NN` spot-runs one; a full run records an `AuditCompleted` event. The auditor never crashes on a bad check — each check's `run()` is wrapped.
- **Declarative document catalog.** `references/catalog.json` (106 documents) declares per-doc `conditions` (a conditions-DSL over the flat decision keyspace), `depends_on` (topological order), and producing agent. `architect-brain catalog list` returns the applicable docs in dependency order; `catalog cycle` (a FATAL check) guards acyclicity. Replaces v7's prose doc-selection logic.
- **Golden Paths.** `architect-brain golden-path apply <id>` pre-fills a complete decision set for 9 common stacks (Modern SaaS, AI/RAG, cross-platform mobile, high-perf API, PL interpreter, Rust CLI, CC plugin, MCP server, agentic system) — offered as the first kickoff question.
- **Deterministic config-as-code + diagrams.** `generate-configs` emits package.json / tsconfig / pyproject / Dockerfile / docker-compose (etc.) as pure functions of the decisions; `generate-diagram` emits Mermaid C4 (context / container / component).
- **Migrator.** `architect-brain migrate` brings a pre-v8 monolith (`docs/_architect_state.json`, schema < 4.0) to the event-sourced 4.0 layout — snapshot → synthesize events → replay → re-stamp ADRs/docs → compare (`replay == projections`) → atomic flip. Reversible via the kept backup tarball.
- **New project type: agentic systems** (single-agent / multi-agent orchestrator / agentic tool) + `ai_agent` and `api_contract` bounded contexts, and **37 new doc templates** spanning AI-agent design/evaluation/memory/context-engineering/safety, web-security headers, API contracts (idempotency, versioning, error model, rate limiting), SRE/ops (SLOs, postmortems, on-call), supply-chain security, OSS governance, and DDD (bounded contexts, domain events) — each grounded in a current external standard.

### Changed

- **Phase order:** 12 phases — `preflight → kickoff → vision → architecture → tech stack → cost → doc generation → iteration → lock → tooling execution → handoff → complete` (architecture before stack; cost its own phase), aligned with Spec-Kit / DDD / Anthropic guidance.
- **Decisions are flat dotted keys** (`stack.frontend.framework`, `architecture.style`, …) per a canonical `references/decision-keys.md`; **ADRs are MADR-4** with structured frontmatter.
- **Doc generation is plan-then-execute:** Phase 6 authors the `*_PLAN.md` plans; Phase 9 (Tooling Execution) materializes the root `CLAUDE.md`, `.claude/` tree, and scaffold from them.
- `SKILL.md` + all reference docs + all agent prompts rewritten to the v8 mechanics.

### Removed

- **The entire v7 bash surface.** `bin/architect-ledger`, `bin/architect-ui`, and the `quality-gate-auditor` subagent with its 27 bash `check_*.{sh,py}` + `run_all.sh` — all replaced by `architect-brain`. A clean break: no compatibility shims. The audit is now a direct CLI call, not a dispatched subagent (the roster is 7 agents).

### Fixed

- **The `/iterate-design` unlock lifecycle.** The `LockSet` event now honors an explicit `locked: false` (unlock), stores the design `version` (the `v1.0 → v1.1-draft → v1.1` bump), and stamps `locked_at` from the binary's own clock — so unlock → revise → re-lock works end-to-end against the event-sourced state.

### Tests

- 938 Python unit tests (the `architect_brain` package) + a thin bash smoke layer (entrypoint exec, event-replay round-trip, migrate-from-v7, clean-break guard, golden-path, agent roster). The ~116 v7 bash tests that asserted the deleted mechanics were removed; their logic is covered by the Python suite.

## v7.2.0 — 2026-05-24

**The run UI now actually shows. The banner and the advancing phase bar render by *running* `bin/architect-ui` — not by transcribing its art into the reply.**

### Fixed

- **The banner, progress bar, and phase indicators were not appearing during real runs.** They had been specified as *inline* narration: the orchestrator was asked to transcribe the embedded ASCII art into its reply at each phase boundary. That is a discretionary act, and it gets dropped under the load of a multi-phase run — so a real run showed nothing. Two prior reinforcements (v7.1.0 embedded the art; v7.1.1 added a NARRATE step to the transition contract) strengthened the prose but could not fix what was structurally discretionary. The UI was, in effect, the last part of the orchestrator still left to model compliance while every other fragile step had been converted to a mechanical gate.

### Added

- **`architect-ui phase-bar <phase_key>`** — maps an internal `set-phase` key (`phase_0`…`phase_8`, including `phase_2.5`, and `complete`) to its row in the 11-step progress ladder. It is the single source of truth for the ladder; an unknown key is a chain-safe no-op so it can never break a transition.

### Changed

- **The progress bar is folded into the mandatory ledger write.** The Phase transition contract's first step is now a single Bash call — `architect-ledger … set-phase <next> && architect-ui phase-bar <next>` — so the advancing bar prints into the same tool-result block as the gate-enforced phase advance, and rides on an action that can never be skipped. `set-phase` is silent on stdout, so the box shows only the bar.
- **The banner is run once at Preflight** (`architect-ui banner`) rather than transcribed.
- `references/output-style.md` rewritten: `architect-ui`'s stdout is the one mechanical output you do *not* capture-and-suppress — you run the binary and let the tool-result block show it (that block is the user-visible surface). The embedded banner + ladder remain as a reference of what the binary prints.
- Test suite: the two inline-mechanism tests are replaced by `test_v72_ui_run_the_binary.sh`, which pins the binary's `phase-bar` map and the run-the-binary wiring across `SKILL.md` and `output-style.md`.

## v7.1.2 — 2026-05-24

**Distribution: project-architect now installs from the shared `alexfordlabs/skills` marketplace.**

### Changed

- The marketplace moved to its own repository, [`alexfordlabs/skills`](https://github.com/alexfordlabs/skills) — a dedicated collection that also serves `reverse-engineer` (and future plugins), so `claude plugin marketplace add alexfordlabs/skills` reads as a collection rather than a single plugin. Install instructions updated accordingly. The marketplace **name** is unchanged (`alexfordlabs`), so the `@alexfordlabs` install namespace and existing installs are unaffected.

### Removed

- The in-repo `.claude-plugin/marketplace.json` (superseded by the dedicated `alexfordlabs/skills` repo). This repo is now a plain plugin — nothing about the plugin's behavior changes.

## v7.1.1 — 2026-05-24

**The inline run UI now renders reliably — emission is wired into the per-phase mechanism, not just the preamble.**

### Fixed

- v7.1.0 introduced the inline banner + advancing progress bar as a strong preamble directive, but the **Phase transition contract** — the step-by-step heartbeat the orchestrator runs at every phase boundary — carried no UI-emission step. A run that followed the contract literally could still render neither. The contract now has a fifth **NARRATE (UI)** step: as each phase begins, the reply opens with that phase's progress-ladder row + `✓`/`→`/`✗` step lines, rendered inline (never left only in a tool-result block). Phase −1 (Preflight), the run's first reply, now reminds to open with the `architect-ui` banner. `bin/architect-ui` and the embedded ladder are unchanged.

## v7.1.0 — 2026-05-24

**The run is now visibly beautiful — the banner + advancing progress bar render inline.**

### Added

- **Inline run UI.** Every flow opens with the `architect-ui` ASCII **banner** and leads each phase boundary with an advancing block-char **progress bar** (`Phase 6/11  [██████████░░░░░░░░░░]  54%  Architecture`) plus `✓`/`→`/`✗` step lines — rendered inline in the conversation, so you watch the bootstrap fill from Preflight to Handoff. `bin/architect-ui` is the canonical renderer; the banner + the per-phase progress ladder are embedded in `references/output-style.md` so the orchestrator reproduces them verbatim.

### Fixed

- The presentation helper shipped in v7.0.0 (`bin/architect-ui`) was never wired into the orchestrator — `SKILL.md` mentioned it once but no flow opened with the banner or emitted the progress bar, so runs rendered neither. It is now wired into the SKILL preamble + the `output-style.md` convention, which also resolves the prior capture-vs-surface ambiguity (the UI is the curated narration you surface inline; only raw tool output is captured).

## v7.0.0 — 2026-05-23

**Major: cross-version resume + situation routing, self-healing error handling, a fast/quiet/beautiful run, and a clean publish-ready release.**

This release lets project-architect resume an interrupted or old-version project on its own, recover gracefully from errors, render clean informational progress instead of raw script output, and ship as a polished, generic plugin any developer can install.

### Added

- **Preflight situation-router** — when you open a project that already has architect history, the Preflight assesses the full situation (the state ledger, the project folder, and *all* git branches — read-only, never a checkout) and routes you: resume an interrupted `/re-architect` or `/iterate-design` flow from where it stopped, upgrade (`/upgrade-project`), re-architect in place (`/re-architect`), or **start fresh seeded** from the recovered design (a clean bootstrap pre-filled with your prior decisions). Documented in `references/situation-assessment.md`.
- **Foreign-project detection + `reverse-engineer` handoff** — the same Preflight now also recognises a *foreign* (brownfield) project: one with real code, manifests, or docs but no project-architect state. Instead of treating it as either a greenfield bootstrap or a project-architect project, it offers the companion **[`reverse-engineer`](https://github.com/alexfordlabs/reverse-engineer)** plugin (installable from the same `alexfordlabs` marketplace), which recovers a design from the existing code and docs and hands it back through the shared state contract. Its output then rides the existing seeded-greenfield path — you continue in project-architect with your prior design already in hand.
- **Self-healing error handling** — on any blocker the orchestrator surfaces a concise *informational error state* (what failed, what's known so far, what's at risk) and offers two paths: write a diagnostic report and stop, or propose a concrete fix from the information already gathered and continue after you approve.
- **State-ledger commands** — `architect-ledger set-decision` / `import-decisions` (persist decisions into the flat keyspace — no hand-edited JSON), `set-substep` (records per-step flow progress so an interrupted run is resumable), and `reserve-adr` / `reserved_adrs` (set aside an ADR number without tripping the missing-file gate). `detect` now reports interrupted-flow and resumability.
- **`bin/architect-ui`** — a banner, an advancing block-char progress bar, and styled ✓/→/✗ step lines, used to render clean informational progress. The `references/output-style.md` convention documents the "capture mechanical output, surface progress not plumbing" discipline.

### Changed

- **Generated docs are validated harder** — the document and tooling authors self-check for unresolved `{{placeholder}}` markers and only cross-link the docs a project actually selected; `/re-architect` now preserves-and-updates docs richer than their template (rather than overwriting from a blank skeleton) and recovers decisions under canonical keys; the scaffold records the project layout from what it actually created and validates it early.
- **Quality gate** — research notes (`docs/research/`) and version snapshots (`docs/versions/`) are excluded from the documentation-quality checks (footer / placeholder / link / cross-link), so reference material isn't held to design-deliverable standards.
- **Clean, publish-ready release** — a comprehensive new README, a curated public CHANGELOG (this file), and the internal development scaffolding (implementation plans, design specs, migration runbooks) removed from the published repository.

### Fixed

- `detect.can_rederive` now reflects whether decisions are *actually* flat, instead of flipping true the moment state is migrated.
- Snapshots capture a defined, consistent file manifest on every run.

## v6.0.0 — 2026-05-23

**Major: `/re-architect` (ingest & re-architect) + a safe `/upgrade-project` preserve mode.**

Real, docs-rich projects carry *narrative* design decisions and a hand-evolved doc set rather than the flat, re-derivable decision keyspace the upgrade path expects. v6.0.0 ships both halves of the fix: a non-destructive **preserve-mode** upgrade and a new **`/re-architect`** flow that recovers a project's design from its own docs and lets you re-decide it from first principles.

### Added

- **`/re-architect`** — a bespoke flow for revisiting a docs-rich project's design without re-interviewing from scratch: recover the design from `docs/`, decision records, and research into a reviewable **`RECOVERED_DESIGN.md`** → triage every decision (keep / revise / drop / add — the human validation gate; grouped, low-confidence-first, and resumable) → research the deltas *and* challenge the keeps against current sources → re-decide into a flat, re-derivable keyspace → re-derive every artifact (docs + superseding ADRs + `CLAUDE.md` + `.claude/` tooling) → re-gate → re-lock at a major bump. Snapshot-first and branch-isolated; never rewrites code (it flags the areas a decision change affects).
- **`design-recovery` agent** — reconstructs an existing design into the structured `RECOVERED_DESIGN.md`, capturing each decision's value, rationale, source pointer, and a confidence rating; it reconstructs only, never invents, and marks low-confidence recoveries for human scrutiny.
- **`/upgrade-project` preserve mode** — when a project's decisions are narrative rather than flat, the upgrade migrates state and reconciles the decision-record ledger from disk while **keeping the existing docs** and flagging manual follow-ups, instead of a destructive re-derive.
- **Ledger reconcile + help** — `architect-ledger reconcile-adrs` rebuilds the recorded-ADR list from the on-disk decision files (the authoritative record), and `architect-ledger --help`/`-h` now prints usage.

## v5.0.0 — 2026-05-23

**Major: the "hardening + cross-version upgrade" release.** v5 makes the orchestrator's quality gates *mechanical* (not advisory), gives project state a tamper-evident ledger, and makes every project project-architect produces **perpetually forward-migratable** — an old-version project can be detected and upgraded to the current format instead of re-interviewed from scratch.

State migrates automatically (`schema_version` `2.0 → 3.0` on first run); existing projects need no manual action.

### Added

- **`bin/architect-ledger`** — a state write-helper that stamps every mutation with a real `date -u` timestamp, so the decision ledger, phase trajectory, and audit record can't be back-filled with fabricated values. Subcommands cover phase transitions, doc/ADR/audit recording, memory sync, layout, migration, plus `detect` / `snapshot` / `relock`.
- **State schema 3.0** — adds a decisions directory, project layout, last-audit, decision-schema version, and ADR provenance fields (filed-at, phase); idempotent migrator with a Preflight auto-migrate.
- **Quality-gate auditor expanded from 16 to 27 mechanical checks** — ADR-file existence, ledger completeness, required-docs-generated, cross-link integrity, out-of-band phase-advance detection, audit freshness, settings-permission validity, dependency freshness (no pre-release pins on foundational dependencies), anonymity-threat preflight, and more. Each is a self-contained pass/fail check; the gate is enforced, not improvised.
- **Transition contract (SKILL.md)** — phase-transition gates wired through the ledger at every boundary; ADRs filed as a side-effect of the decision (not back-filled at lock time); a mandatory pre-lock audit that must be green before LOCK; and branch-handoff clarity for existing-codebase bootstraps (name the branch, state that deploys read `main`, offer a fast-forward merge).
- **`/upgrade-project`** — a nine-step flow: detect → floor-check → snapshot → migrate state + decisions → re-walk the changed-decision delta → re-derive docs / `CLAUDE.md` / `.claude/` tooling → re-gate to green → re-lock at a bumped version. Snapshot-first (nothing is lost); refuses below the compatibility floor and refuses artifacts produced by a newer plugin than the one running.
- **Artifact version stamping** — every generated doc and ADR is stamped with its format version and the producing plugin version, backed by an artifact-migration framework (chained, idempotent, with a compatibility floor) that mirrors the state-migration one.
- **Version-awareness gate** — a single consistent four-option intent menu (upgrade-then-continue / upgrade-then-rebuild / start-fresh / proceed-warned), wired identically into the main skill and the generated `/implement`, `/scaffold`, and `/iterate-design` commands.

### Changed

- Agent prompts hardened: live newest-stable version resolution (no stale or pre-release pins on foundational dependencies), consistent project-layout / decisions-directory handling across all authoring subagents, and self-validation of generated deny-glob permission recipes.

## v4.0.1 — 2026-05-22

**Patch: portability fix for published source.** No behaviour or schema changes.

### Fixed

- **`agents/document-author.md`** — removed a hardcoded absolute home-directory path that pointed at a local plugin cache; replaced with a portable, optional "consult the `doc-coauthoring` skill if installed" instruction that hardcodes no path. This shipped broken to installs other than the author's machine.
- **`references/state-schema.md`** — the memory-pointer example now uses a portable `~/.claude/projects/<project-id>/…` form.

### Added

- **`tests/test_v401_no_absolute_home_paths.sh`** — regression guard asserting no published source file contains an absolute home path.

## v4.0.0 — 2026-05-20

**Packaging & metadata release.** No behaviour changes, no API changes, no schema changes — every test still green (69 / 69).

### Changed

- Packaging & metadata updates — author, repository, marketplace, organization, and license-header metadata were brought under a single consistent brand identity. The published marketplace identifier is now `alexfordlabs`; install with `claude plugin install project-architect@alexfordlabs`.

### Added

- **`.gitleaks.toml`** + **`.pre-commit-config.yaml`** — secret-scanning config and a pre-commit hook (gitleaks) so contributions are scanned automatically.

### Migration for existing installs

```bash
claude plugin marketplace add alexfordlabs/project-architect
claude plugin install project-architect@alexfordlabs
/reload-plugins
```

## v3.1.0 — 2026-05-20

**Universal research checklist for every research dispatch + a refreshed brand-asset kit.** Backward-compatible: same 11-phase orchestrator, same 6 subagents, same 16-check auditor, same state schema.

### Added

- **Universal research checklist** — every `research-scout` dispatch now MUST cover four bases before topic-specific work begins: (1) latest official docs, (2) `llms.txt` + `llms-full.txt` per the [`llmstxt.org`](https://llmstxt.org/) standard, (3) current best practices via web search, (4) three to five similar projects / prior art. Findings files cite the official-docs URL and any `llms.txt` source for each tool researched. This shifts the scout from "recall from training" (which is stale by some unknown number of months) to "fetch current source-of-truth", which makes downstream ADRs defensible.
- **Brand-asset kit** (`.github/assets/brand/`) — a full visual identity: scale-infinite SVG masters plus PNGs at every standard resolution (lockup, mark/favicon, wordmark, social preview), in light and dark variants, with zero font dependency at render time and a regenerable build script.

### Changed

- README hero image now references the new brand-kit social preview.

## v3.0.0 — 2026-05-19

**Packaging & metadata release.** No behaviour changes, no API changes, no schema changes — every test still green (68 / 68).

### Changed

- Packaging & metadata updates — author, repository, marketplace, and organization metadata were updated to a new brand identity. Existing installs continue to work; new installs target the updated marketplace identifier.

## v2.3.0 — 2026-05-13

**Programming-language design as a first-class project type.** Same orchestrator, same 11 phases, same 6 subagents, same 16-check auditor; new project-type taxonomy entries, templates, questioning paths, and decision axes.

### Added

- **6 programming-language sub-types**: general-purpose, domain-specific, query, configuration, educational, and transpiler-target languages.
- **7 PL design templates** — grammar (lexer/parser/EBNF/precedence), semantics (evaluation, scoping, memory, concurrency), type system (static/dynamic/gradual, inference, generics, variance), standard library, toolchain (REPL, formatter, LSP, debugger, package manager, build/test), bootstrap plan (host-language → self-hosted trajectory), and stability/RFC process.
- **4 PL decision axes** — implementation strategy (interpreter / bytecode VM / JIT / AOT / transpiled), host runtime (LLVM, MLIR, Cranelift, QBE, GraalVM, JVM, BEAM, Wasm, JS, Python, Rust, native, and more), paradigm, and type system — each filed as an ADR, with research-dated comparison tables of current language-implementation backends.
- **2 end-to-end fixtures** — a tree-walking educational interpreter and a gradually-typed functional language transpiled to JavaScript.

### Changed

- SKILL.md, the marketplace description, and the README "project types supported" list now include programming-language design.

### Migration

Forward-compatible. New fields default to safe absent values; projects bootstrapped before v2.3.0 keep working — PL questioning paths only activate when the project is a language.

## v2.2.1 — 2026-05-13

**Patch: end-user update flow + docs polish.** No new features.

### Changed

- **Preflight version-freshness check** now uses a `gh release view` → GitHub API cascade, so end users without `gh` installed (or unauthenticated) still get the freshness notice instead of a silent skip.
- **Preflight update-notice text** modernised — `/plugin` + `/reload-plugins` is presented as the primary update flow, with the older `claude plugin …` CLI form as a fallback.

### Added

- **README "Keeping project-architect up to date"** section documenting the `/plugin` + `/reload-plugins` flow, with `Watch → Releases only` as a zero-poll notification option.

## v2.2.0 — 2026-05-13

**Major architectural release: the quality-gate auditor, runtime budgets, the multi-session plan/execute/handoff lifecycle, and a cross-language CLI-UX picker.**

### Added

- **Quality-gate auditor** — a new agent that runs 16 cross-cutting checks after the architecture phase closes; findings auto-seed the iteration menu (BLOCKER / WARNING / INFO).
- **Per-agent runtime budgets** — every subagent declares a runtime budget; the orchestrator wraps each dispatch with an observer that surfaces "silent for too long" and "over budget" warnings (observation only, never auto-kill).
- **Multi-session lifecycle** — the doc-generation phase now produces four plan docs (CLAUDE.md plan, tooling plan, scaffold plan, next-step plan); a new tooling-execution phase consumes them; and a handoff phase wires `CLAUDE.md` as a router with three slash commands (`/scaffold`, `/implement`, `/iterate-design`). Adds project lock / version / locked-at state and per-phase memory persistence for cross-session continuity.
- **Inline write-time validators** in the tooling author — shellcheck, `jq`, and Python YAML checks catch malformed `.sh`/`.json` before declaring done.
- **Per-language CLI-UX library picker** (Rust, Go, Python, Node, Ruby, C#) and a new `CLI_UX_DESIGN.md` template.

### Changed

- The doc-generation phase no longer writes `CLAUDE.md` or `.claude/*` directly — that moves to the tooling-execution phase.
- LOCK snapshots state to `docs/versions/{version}/` and marks the project locked without deleting the state file.
- Phase-boundary gates block downstream dispatch until upstream phase prerequisites are satisfied.

### Migration

Forward-compatible: existing state files gain the new fields with safe defaults, and the plugin offers to migrate at startup.

## v2.1.5 — 2026-05-13

**Tactical fixes.**

### Fixed

- `schema_version` now initializes to the state-schema version (`2.0`), separate from the plugin's semver.
- All `state.json` timestamps now use ISO-8601 UTC.
- Template selection now force-includes the union of every ADR's affected docs (intersected with the catalog), so ADR-promised docs are never skipped.
- The tooling authors now use `architect(phase-N): …` commit subjects, matching the orchestrator convention.
- The decision-revisor prompt gained explicit scope + cost-budget guidance to prevent runtime overruns on surgical patches.
- LOCK no longer deletes the project state file — it's preserved as the canonical entry point for re-invocations and `/iterate-design`.

### Added

- A universal CLI-UX gate question for CLI/TUI projects (one-shot / interactive prompts / full TUI / hybrid), routing follow-up questions accordingly.
- A `tests/` harness with shared helpers and an `run_all.sh` runner.

## [2.1.4] — 2026-05-12

### Changed

- **Template footer glyph** changed to `★` across all user-facing templates, aligning the generated-doc footer attribution with the social-preview image.

## [2.1.3] — 2026-05-12

### Added

- A publisher logo in the social-preview image's top-left line (replacing a Unicode placeholder).

## [2.1.2] — 2026-05-12

### Changed

- **Social-preview image redesigned** — corrected footer star glyph and a dedicated pill-shaped **Install →** button.

## [2.1.1] — 2026-05-12

### Added

- **GitHub social-preview image** (1280×640, dark theme), embedded at the top of the README and regenerable on each release.

## [2.1.0] — 2026-05-12

### Added

- **Modern README** with badges, a mermaid architecture diagram, terminal "screenshot" code blocks, a comprehensive project-types list, and a recommended-plugins table.
- **GitHub repo hardening** — issue templates, a pull-request template, and `CONTRIBUTING.md`.
- **Template beautification** for generated docs — status callout under H1, table-of-contents on long docs, judicious section-emoji prefixes, a Revision Log rendered as a table, and a "Skillfully made with…" footer.

### Changed

- **Marketplace description** rewritten for public release.

## [2.0.5] — 2026-05-12

### Added

- **MIT LICENSE**.
- **Author-attribution comment block** in every text file in the repo.
- **"Skillfully made with…" footer** appended to every doc template, so generated user-project docs carry downstream attribution automatically.
- **Attribution policy + License section** in the README.

### Changed

- `plugin.json` and `marketplace.json` now declare `license: MIT` and a `repository` field.

## [2.0.4] — 2026-05-12

### Changed

- **Marketplace renamed** to match the publishing org. **Breaking for install commands** — re-register the marketplace and reinstall the plugin under the new identifier, then `/reload-plugins`.

## [2.0.3] — 2026-05-12

### Fixed

- **`commit-commands` dependency resolved to the wrong marketplace** — bare-string dependencies resolve to the dependent plugin's own marketplace, which doesn't host `commit-commands`. Changed to the object form with an explicit `marketplace` (the canonical pattern for cross-marketplace dependencies).

## [2.0.2] — 2026-05-12

### Added

- **Preflight cache-hygiene step** — after the version-freshness check, the architect proactively removes stale plugin-cache version directories so future sessions can't accidentally load an older cached version.

### Fixed

- The plugin's own repo gained a `.gitignore` and a pre-created `.remember/logs/` directory to silence foreign-plugin hook spam during development.

## [2.0.1] — 2026-05-12

### Fixed

- **Plugin manifest schema conformance** — `dependencies` is now the canonical array form; the unrecognized `softDependencies` key was removed (recommendations now surface via the README, a runtime Preflight check, and a generated `recommended-plugins.md`).
- A phase-enum mismatch on Preflight abort/resume was corrected.
- Added the missing `Skill` tool grant to the two authoring agents that invoke other skills.

### Added

- **`references/state-schema.md`** — the canonical runtime reference for `state.json` (schema, lockfile protocol, migration policy).
- **Soft-dependency Preflight check** — lists recommended plugins at startup, scans for missing ones, and offers to install them.
- **Auto-creation of `.remember/logs/`** in Preflight, and `.remember/` added to the default `.gitignore` the repo-init phase writes.
- **Version-freshness check** in Preflight (best-effort; silently skips without `gh`, network, or releases).
- **Manual test plan** covering CLI bootstrap, plugin bootstrap, iteration, resumability, and snapshot versioning.

## [2.0.0] — 2026-05-12

### Added — major redesign as an orchestrator

- **Multi-phase bootstrap model** — preflight → repo init → universal kickoff → vision → tech stack → cost → architecture → doc generation → iteration → post-gen setup → optional plan handoff.
- **Universal kickoff** that classifies any project type before branching to type-specific drill-downs.
- **Project-type taxonomy** covering 18 top-level types: web app, mobile, multi-platform, API, CLI, library, desktop, browser extension, game, AI/ML, data pipeline, embedded/IoT, infrastructure, Claude Code plugin, MCP server, Web3, scientific code, AR/VR.
- **5 subagents** (research-scout, document-author, decision-revisor, claude-md-author, claude-tooling-author), each dispatched with a max-effort prompt.
- **Research-augmented questioning** — end-of-phase and on-demand web research, with findings persisted to `docs/research/`.
- **Architecture Decision Records** — every major decision filed as a sequentially-numbered ADR; supersession chains form the audit trail.
- **Iteration with consequence propagation** — a revisor agent rewrites every affected doc when a decision changes and files a superseding ADR.
- **Hybrid versioning** — in-place edits + git history + opt-in snapshot bundles + ADRs.
- **Per-folder `CLAUDE.md`** generation for monorepo subdirectories with materially different conventions.
- **Generated `.claude/` directory** — `settings.json` (opus, 1M context, stack-aware permissions, hook wiring), lint/test/secret-scan hooks, project-specific subagents, project slash commands, and a recommended-plugins doc.
- **Auto-commit cadence** (per batch / per artifact / per phase).
- **Resumable state** in `docs/_architect_state.json` with a concurrency lockfile.

### Changed

- SKILL.md restructured from an inline workflow into a slim orchestrator that loads references on demand.
- Templates split from a monolithic file into one file per template under `references/templates/`.

## [1.0.0] — 2026-05-01

- Initial release. A three-phase interview (vision, tech stack, architecture deep dive), a monolithic template file, and generation of `docs/` and `CLAUDE.md`.
