<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Questioning Flow Reference

The interview is a tree: **universal kickoff** (always asked) → **per-type drill-down** (one branch) → **architecture deep dive** (per-area). Skip questions that prior answers render irrelevant.

## Divergent questioning (Vision discipline)

The per-type drill-downs (Vision, Phase 2) absorb the divergent-questioning principles of `superpowers:brainstorming` directly — there is **no nested interactive skill** (a nested skill would clash with project-architect's own commit cadence; the principles are baked in here instead). Apply them while drilling into the chosen project type:

- **Ask one question at a time** for the genuinely-open design questions (vision, problem framing, hard constraints). Batch only the mechanical multiple-choice picks. A wall of questions gets shallow answers.
- **Surface unstated assumptions.** When the user states a goal, name the assumption it rests on and confirm it ("you said 'real-time' — does that mean sub-second, or just not-batch?"). A run might never challenge an assumption like "messenger" → "needs a backend" → a specific vendor.
- **Diverge before converging.** Generate 2–3 framings of the problem before narrowing to one. Note the roads not taken (they become ADR "Alternatives reconsidered" later).
- **Probe for the threat/abuse model early** when the project touches privacy, identity, money, or safety — this seeds the `anonymity_threat_preflight` check (25) input and the THREAT_MODEL doc.
- **Reflect back** the user's answer in your own words before recording it, so a misread is caught at the question, not at lock.

## Table of Contents
- [Universal Kickoff (Kickoff, Phase 1)](#universal-kickoff-kickoff-phase-1)
- [Per-Type Drill-Downs (Vision)](#per-type-drill-downs-vision)
- [Architecture Deep Dive (Architecture phase)](#architecture-deep-dive-architecture-phase)
- [Tech Stack Drill-Downs (Tech Stack phase)](#tech-stack-drill-downs-tech-stack-phase)
- [Cost Modeling (Cost, Phase 5)](#cost-modeling-cost-phase-5)
- [Routing Rules](#routing-rules)

> **Phase order (v8 ladder):** preflight → kickoff (1) → vision (2) → architecture (3) → tech stack (4) → cost (5) → doc generation (6) → iteration (7) → lock (8) → tooling execution (9) → handoff (10) → complete (11). The interview sections below are documented in the order the orchestrator runs them: kickoff first, then per-type drill-downs in Vision, then Architecture (which runs **before** the stack), then Tech Stack, then Cost. (Repo Init / Golden Paths is Phase 0a, run inside Kickoff.)

---

## Universal Kickoff (Kickoff, Phase 1)

Always asked first, in 3 `AskUserQuestion` batches.

### Batch 1 — Identity & Type
1. **Elevator pitch.** One sentence: what is it, who is it for, why does it exist? *(open-ended)*
2. **Top-level project type.** *(multiple-choice from the taxonomy below)*
3. **Sub-type within that category.** *(multiple-choice; options depend on Q2)*

### Batch 2 — Stage & Problem
4. **Project stage.** *(multiple-choice: greenfield / extending existing / rewriting / migrating / PoC only)*
5. **Primary problem & target users.** *(open-ended)*

### Batch 3 — Constraints & Scale
6. **Constraints.** *(multi-select: budget tight / regulated (GDPR/HIPAA/PCI-DSS/SOC2) / tight timeline / pre-existing tech mandates / open-source vs proprietary)*
7. **Team & scale.** *(multiple-choice combining team size {solo / small / larger} × scale tier {hobby / MVP / growth / enterprise})*
8. **Hard pre-existing decisions.** "Must be on AWS", "Must use Postgres", etc. *(open-ended)*

After Batch 3: dispatch `research-scout` for **domain research** (similar projects, pitfalls for this type/domain, regulatory implications, market context). Findings → `docs/research/phase1-domain.md`.

### Top-level project type taxonomy

```
Web application          → SaaS | marketplace | content/blog | dashboard | social | portfolio
                           | internal tool | e-commerce | course/LMS | community forum
                           | wiki/knowledge base | newsletter platform
Mobile application       → consumer | B2B | enterprise | utility | game (→ Game)
                           | health & fitness | finance/banking | productivity
                           | media (streaming/social)
Multi-platform system    → web + mobile + desktop + API combined
API / backend service    → REST | GraphQL | gRPC | WebSocket | event-driven | hybrid
                           | webhook receiver | proxy/gateway | batch processor | scheduled service
CLI tool                 → developer tool | system utility | data/CSV tool | network/security tool
                           | package manager | build tool | scaffolder | REPL | productivity CLI
Library / SDK / package  → SDK for a service | framework | utility lib | type lib
                           | language binding / FFI | code generator | linter/formatter | test library
Desktop application      → macOS | Windows | Linux | cross-platform
                           | full app | menu bar / tray utility | system extension | daemon
Browser extension        → Chrome/Edge | Firefox | Safari | cross-browser
                           | productivity | content filter | DevTools | security/privacy
Game                     → 2D | 3D | mobile | web | console | VR/AR
AI/ML application        → model training | inference serving | RAG | agents | classical ML
                           | computer vision | NLP | recommendation | time-series
                           | reinforcement | multi-modal
Data pipeline / ETL      → batch | streaming | hybrid
                           | ETL | reverse-ETL | CDC | analytics pipeline | feature store
Embedded / firmware/IoT  → MCU class (Cortex-M / RP2 / ESP32 / STM32) | edge gateway | hardware combo
Infrastructure tool      → IaC | CLI for infra | platform / internal developer platform
                           | cluster operator | observability/monitoring tool | CI/CD tool | networking
Claude Code plugin       → command-focused | skill-focused | agent-focused | full plugin
MCP server               → stdio | HTTP/SSE | Cloudflare Workers | other host
                           | tool-focused | resource-focused | prompt-focused | full
Programming language     → general-purpose | DSL | query language | configuration language
                           | educational | transpiler target
Agentic system           → single agent | multi-agent orchestrator | agentic tool
Web3 / smart contracts   → EVM (Solidity) | Solana (Rust/Anchor) | Move (Aptos/Sui) | Cairo (Starknet)
Scientific / research    → numerical sim | data analysis (notebooks) | reproducible study
                           | bioinformatics | geospatial/GIS
AR / VR / spatial        → visionOS | Meta Quest | mobile AR (ARKit/ARCore) | WebXR
Other                    → describe; route to closest neighbor
```

---

## Per-Type Drill-Downs (Vision)

Run in the Vision phase (Phase 2). Adaptive — keep asking batches until each relevant area is locked. Typical 3–7 batches per project. Dispatch ad-hoc `research-scout` on red flags (see `research-prompts.md`). End-of-phase: `research-scout` for scope realism.

### Web application
- Which platforms (web only / web + PWA / web + mobile)? Browser support floor?
- Offline / sync requirements?
- Public-facing vs auth-walled? Sign-up flow expectations?
- Real-time features (chat, presence, live updates)?
- Content / media handling (uploads, video, large files)?
- Search needs (full-text, faceted, semantic)?

### Mobile application
- Platforms (iOS / Android / both / cross-platform)? Minimum OS versions?
- Distribution (App Store + Play / TestFlight / enterprise / sideload)?
- Offline capability and sync model?
- Push notifications and background tasks?
- Native integrations needed (camera, biometrics, payments, HealthKit, location)?

### Multi-platform system
- Which platforms in scope (web / iOS / Android / macOS / Windows / Linux / API)?
- Code-sharing strategy goal (max share / per-platform native UI)?
- Sync / state model across clients?
- Release cadence per platform?

### API / backend service
- Consumers (internal-only / public-API / partner-only / SDK-distributed)?
- Sync vs async vs event-driven boundary?
- Auth required at the API edge?
- Versioning policy (URL path / header / none)?
- Rate-limiting needs?
- Real-time delivery (WebSocket / SSE / polling)?

### CLI tool
- Distribution channel (homebrew / cargo / npm / pip / binary release / pkg manager combos)?
- Interactive vs strictly scriptable? TTY assumptions?
- Config file format (TOML / YAML / JSON / env)?
- Plugin / extension model?
- Cross-platform (Windows in scope)?
- Telemetry policy (opt-in / opt-out / none)?

#### CLI experience model (universal gate)

For CLI projects (`project.sub_type` in `cli_tool`, `cli_with_subcommands`, `tui_app`, `interactive_cli`), ask this universal question via `AskUserQuestion`:

**Q: CLI experience model — which best describes your tool's interaction style?**

| Option | Description | Examples |
|---|---|---|
| **One-shot** | Input → output → exit. No prompts, no UI state. | md2pdf, jq, ripgrep, fd, gh CLI, kubectl |
| **Interactive prompts** | CLI asks the user via prompts, then runs. | `npm init`, `cargo init`, `gh repo create`, Cookiecutter |
| **Full TUI** | Keyboard-driven persistent terminal UI. | atuin, gitui, lazygit, zellij, helix, gh dash, tig |
| **Hybrid** | One-shot default + optional interactive flag. | git (`git rebase -i`), aws-cli (`aws configure`) |

Save the answer as the flat decision `cli.experience_model` (via `architect-brain set-decision cli.experience_model <value>`).

**Routing:**
- `one-shot` → skip the rest of CLI-UX questions
- `interactive_prompts` → ask universal UX intent (style, output_format, color_policy, accessibility)
- `tui` → ask universal UX intent + TUI-specific (input_patterns, persistence)
- `hybrid` → ask both prompts + TUI questions

The per-language library picker (`ratatui` vs `bubbletea` vs `textual` vs `ink` vs etc.) is asked in the Tech Stack phase (Phase 4). This Vision-phase gate only asks the universal experience-model question — the language-specific options come later, once the language is chosen.

#### Universal UX intent (asked unless answer was `one-shot`)

**Q-style-1**: Visual style?
- Minimal (text only, no color, no banner)
- Branded (banner + colors + spinners + progress)

**Q-style-2**: Output format(s)?
- Human-only (default)
- Human + `--json` (machine-pipe)
- `--quiet` / `--verbose` discipline

**Q-style-3**: Color policy?
- Auto-detect (NO_COLOR, FORCE_COLOR, CI, tty) — recommended default
- Always-color (force, even in non-tty)
- Never-color (text-only)

**Q-style-4**: Accessibility commitments?
- NO_COLOR support (mandatory baseline)
- Screen-reader friendly (no purely-visual cues; semantic exit codes)
- Low-bandwidth/SSH (banner sizes, animation throttling)

#### TUI-specific (only if `tui` or `hybrid` chosen)

**Q-tui-1**: Input/UX patterns? (multi-select)
- Vi-style modal navigation
- Emacs-style chord
- Arrow keys + Tab + Enter only
- Mouse-aware

**Q-tui-2**: Persistence? (multi-select)
- Reads/writes a config file (TOML/YAML/JSON) at `~/.config/$tool/`
- Maintains a session/history database (e.g., SQLite)
- Pure ephemeral

### Library / SDK / package
- Target consumers (other devs / specific platform / public)?
- Public-API discipline (semver, deprecation policy)?
- Bundled docs site (Mintlify / TypeDoc / Sphinx / Rustdoc)?
- Example projects shipped alongside?
- Tree-shaking / bundle-size targets?
- TypeScript types shipped?

### Desktop application
- macOS / Windows / Linux / cross? Native vs Electron vs Tauri?
- Distribution (App Store / Developer ID + notarization / direct download / package managers)?
- Auto-update mechanism?
- System integration (menu bar, tray, services, file associations, deep links)?
- Sandboxing requirements?

### Browser extension
- Manifest V3? Cross-browser (Chrome / Firefox / Safari / Edge)?
- Permissions (content scripts / activeTab / host permissions / declarativeNetRequest)?
- DevTools panel / sidebar / popup?
- Distribution (Chrome Web Store / Mozilla Add-ons / enterprise self-host)?
- Data sync (chrome.storage.sync limits)?

### Game
- Engine (Unity / Unreal / Godot / custom / web-native)?
- 2D / 3D / hybrid?
- Single-player / multiplayer (netcode requirements)?
- Platforms (mobile / PC / console / web / VR-AR)?
- Monetization (paid / freemium / IAP / subscription / ads)?
- Save / progression storage (local / cloud)?

### AI/ML application
- Training vs inference vs both?
- Model source (own model / fine-tuned / API-only / open weights / mixture)?
- Dataset handling and provenance?
- Evaluation framework / benchmarks?
- Inference latency targets?
- Cost ceiling per request?
- Vector store needs (RAG / semantic search)?

### Data pipeline
- Sources / sinks (databases, warehouses, APIs, files)?
- Batch / streaming / hybrid?
- Orchestrator (Airflow / Dagster / Prefect / Argo / cron / managed)?
- Schedule / SLA?
- Schema evolution policy?
- Data quality / observability (Great Expectations / Soda / OpenLineage)?

### Embedded / IoT
- MCU class / SoC (Cortex-M / ESP32 / RP2 / STM32 / Linux SoC)?
- RTOS? Bare-metal?
- Power budget?
- Connectivity (BLE / Wi-Fi / LoRa / cellular / none)?
- OTA update mechanism?
- Hardware combo (PCB design / off-the-shelf dev board)?

### Infrastructure tool
- Target users (own team / customers / OSS community)?
- Cloud focus (multi-cloud / single)?
- IaC integration (Terraform / Pulumi / CDK / CloudFormation / Crossplane)?
- Operator / controller model (Kubernetes)?
- Observability / logging / metrics?

### Claude Code plugin
- Components (skills / commands / agents / hooks / MCP servers / mix)?
- Triggers (slash command / natural language / file change / event)?
- Distribution (own marketplace / Anthropic marketplace / private)?
- Configurable per project (`.claude/plugin-name.local.md`)?

### MCP server
- Host environment (stdio / HTTP+SSE / Cloudflare Workers / Vercel / other)?
- Surface (tools / resources / prompts / mix)?
- Auth model (OAuth / API key / none)?
- Stateful (durable per-user) or stateless?
- Languages (TypeScript / Python / Rust / Go)?

### Web3 / smart contracts
- Chain (Ethereum / L2s / Solana / Aptos / Sui / Starknet)?
- Smart-contract language (Solidity / Rust / Move / Cairo)?
- Indexing layer (The Graph / Goldsky / custom)?
- Front-end integration (RainbowKit / wagmi / web3.js / ethers / web3.swift)?
- Upgradeability pattern?
- Audit budget / firm?

### Scientific / research
- Reproducibility requirements (environment freeze, seeds, container/Nix)?
- Notebook vs scripts vs both?
- Data scale (fits-in-RAM / out-of-core / cluster)?
- Computation backend (NumPy / JAX / PyTorch / cuDF / Spark / Ray)?
- Publication / pre-print artifacts?
- Domain-specific tooling (bioinformatics, geospatial, etc.)?

### AR / VR / spatial
- Headset / device target (visionOS / Quest / smartphone AR / WebXR)?
- Tracking / input (controllers / hand tracking / gaze / voice)?
- Rendering engine (Unity / Unreal / RealityKit / Three.js / custom)?
- Mixed-reality vs immersive?
- Multi-user / shared sessions?
- App-store distribution?

### Programming language design

This batch fires when the user's pitch (Kickoff, Phase 1) or any later answer mentions designing a **programming language**, a **compiler**, an **interpreter**, a **DSL**, or a **transpiler** — and the project type was either chosen as `Programming language` or routed here from `Library / SDK` (a language embedded as a host library) or `CLI tool` (a language shipped behind a `lang run …` CLI). The orchestrator should re-confirm the intent before drilling in: language design is a different shape of project than a normal library/CLI, with its own template set (generated in Doc Generation, Phase 6) and its own follow-up questions in the Architecture (Phase 3) and Tech Stack (Phase 4) phases.

#### Vision → Programming language sub_type routing

Ask via `AskUserQuestion` (single-select):

**Q-pl-1:** Which best describes the **scope** of the language you want to design?

| Option | One-line cue | Examples |
|---|---|---|
| **General-purpose language** | Full stdlib, broad use cases, you expect users to write whole applications in it. | Rust, Go, Python, Zig, Gleam |
| **Domain-specific language** | Narrow grammar, embedded inside a host program or workflow; one problem domain. | HCL (Terraform), regex, jq, Cue, Dhall |
| **Query language** | Reads/filters/aggregates over a data store; the runtime is a query engine, not a general VM. | SQL, GraphQL, KQL, PromQL, Cypher |
| **Configuration language** | Declarative, deterministic, no general computation; outputs structured data. | Nix, Starlark, Jsonnet, KCL |
| **Educational language** | Teaching-first; simplicity and pedagogy beat performance and ecosystem. | Scratch, Logo, Pyret, Hedy |
| **Transpiler target** | You compile a *source* language **to** an existing target language (your output is code, not a binary). | TypeScript → JS, Elm → JS, Kotlin → JVM/JS/Native, ReScript → JS |

The orchestrator saves the chosen variant as the flat decision `project.sub_type` (via `architect-brain set-decision project.sub_type <value>`) using the exact enum value from `references/decision-keys.md`:

- `general_purpose_language`
- `domain_specific_language`
- `query_language`
- `configuration_language`
- `educational_language`
- `transpiler_target`

If the user describes something that straddles two variants (e.g. "a DSL that's also a query language"), pick the *narrower* one — DSL beats general-purpose, query beats DSL when the grammar is built around data retrieval. Edge cases are recorded as ADRs and surfaced to the user before Phase 4.

**Cross-references:**
- **Tech Stack (Phase 4)** picks up with the PL-specific batch: `pl.impl_strategy` (tree-walking interpreter / bytecode VM / native compiler / transpiler / hosted-embedded) and, when `pl.impl_strategy` is anything but a tree-walking interpreter, a follow-up `pl.host_runtime` question (LLVM / MLIR / Cranelift / QBE / Truffle / JVM / BEAM / WASM / WASM component / JS host / Python-embedded / Rust-host / native-no-runtime / custom-VM). Compare table in `tech-stack-options.md` § PL implementation backends.
- **Architecture (Phase 3)** adds the `pl.paradigm` and `pl.type_system` axes.
- **Doc Generation (Phase 6)** generates the 7 PL templates registered in `document-catalog.md`: `LANGUAGE_GRAMMAR.md`, `SEMANTICS.md`, `TYPE_SYSTEM.md`, `STDLIB.md`, `TOOLCHAIN.md`, `BOOTSTRAP_PLAN.md`, `STABILITY_AND_RFC.md`. Their `catalog.json` conditions key off `project.sub_type` being one of the 6 PL sub_types above.

**Skip the rest of the per-type drill-down** (web-app questions, mobile questions, etc.) once a PL sub_type has been chosen — the language-design batches in the Architecture (Phase 3) and Tech Stack (Phase 4) phases take over.

---

## Tech Stack Drill-Downs (Tech Stack phase)

Runs in the Tech Stack phase (Phase 4), **after** Architecture (Phase 3) — the stack is chosen to FIT the architecture already decided. For each category that applies (skip categories based on prior answers — see Routing Rules). See `tech-stack-options.md` for option tables.

Grouped batches:
1. **Language & runtime** (+ build/package manager)
2. **Frontend framework** (skip if no frontend)
3. **Backend framework** (skip if pure client-side)
4. **Database + ORM** (skip if no persistence)
5. **Authentication** (skip if no accounts)
6. **Hosting (frontend + backend separately) + CDN**
7. **Styling & UI** (skip if no frontend)
8. **Payments** (skip if no monetization)
9. **Email / notifications** (skip if not needed)
10. **File storage** (skip if no files)
11. **AI / ML integration** (skip if no AI features)
12. **Observability stack** (skip if scale = hobby)
13. **Testing stack**
14. **CI / CD**

For each major decision, the orchestrator files an ADR (one per major: language, framework choice, db engine, auth provider, host, etc.).

End-of-phase: `research-scout` on stack-combination gotchas. Findings → `docs/research/phase4-stack.md`.

### Per-language CLI-UX library picker

**Routing:** When `stack.backend.language` (or `stack.frontend.language`) is set AND `cli.experience_model != "one_shot"`, ask the per-language picker below. The picker offers a 4-library shortlist per language for TUI / prompts / progress / color, gated on the universal CLI-experience-model answer captured in the Vision phase.

This sub-question runs once the language has been picked in the Tech Stack phase's "Language & runtime" batch. It deliberately follows the language decision because the shortlist depends on which ecosystem the project lives in. Save the selected libraries as flat decisions under `cli.ux_libraries.*` (one key per concern, e.g. `cli.ux_libraries.tui`, `cli.ux_libraries.prompts`).

#### Rust

| Concern | Recommended | Alternatives |
|---|---|---|
| TUI framework | `ratatui` | `crossterm` (lower-level), `cursive` |
| Interactive prompts | `inquire` | `dialoguer` |
| Progress bars | `indicatif` | `pbr` |
| Color | `owo-colors` | `colored`, `nu-ansi-term` |

#### Go

| Concern | Recommended | Alternatives |
|---|---|---|
| TUI framework | `bubbletea` | `tview` |
| Styling | `lipgloss` | `aec` |
| Interactive forms | `huh` | `survey` |
| Progress bars | `mpb` | `progressbar` |

#### Python

| Concern | Recommended | Alternatives |
|---|---|---|
| TUI framework | `textual` | `urwid` |
| Rich output / colors | `rich` | `colorama` |
| Interactive prompts | `prompt_toolkit` | `questionary`, `inquirer` |
| CLI framework | `typer` | `click`, `argparse` |

#### Node

| Concern | Recommended | Alternatives |
|---|---|---|
| TUI framework | `ink` | `blessed` |
| Interactive prompts | `@clack/prompts` | `inquirer`, `prompts` |
| Task list / progress | `listr2` | `ora` |
| Color | `chalk` | `kleur`, `picocolors` |

#### Ruby

| Concern | Recommended | Alternatives |
|---|---|---|
| TUI / forms / progress / color | TTY toolkit (`tty-prompt`, `tty-spinner`, `tty-progressbar`, `pastel`) | `curses` (stdlib) |

#### C#

| Concern | Recommended | Alternatives |
|---|---|---|
| TUI framework | `Spectre.Console` | (stdlib `System.Console`) |
| TUI app (windowed) | `Terminal.Gui` | (rarely needed for CLI) |

**Skip the picker** if `cli.experience_model == "one_shot"` (e.g., a script that emits text and exits — no need for color or progress libraries). For other language ecosystems not in this table (Java, Kotlin, Elixir, Swift, etc.), fall back to a free-form research-scout dispatch and record findings in `docs/research/phase4-cli-ux.md`.

The selected libraries feed into `CLI_UX_DESIGN.md` and influence the dependency footprint in the Doc Generation phase (`SCAFFOLD_PLAN.md`).

### Programming language — PL-specific batch

**Trigger:** runs when `project.sub_type` is one of the 6 PL variants (`general_purpose_language`, `domain_specific_language`, `query_language`, `configuration_language`, `educational_language`, `transpiler_target`). It replaces the normal Tech Stack "Language & runtime" batch — a *language being designed* needs its own implementation-strategy and host-runtime axes, not a framework picker.

Skip the rest of the Tech Stack category list (frontend / database / auth / hosting / styling / payments / email / file storage / AI / observability) entirely — a PL project's Tech Stack phase is just these two questions plus a Testing/CI batch. The host runtime and impl strategy together cover the "what tech does this run on" question that TECH_STACK.md captures for non-PL projects.

#### Q-pl-2 · `pl.impl_strategy` — how is v0.1 of the language implemented?

Ask via `AskUserQuestion` (single-select). Save the answer as the flat decision `pl.impl_strategy` using the exact enum value (see `references/decision-keys.md`).

| Value | One-line distinguishing prompt |
|---|---|
| `tree_walking_interpreter` | **Simplest path.** Walk the AST node-by-node at runtime; no IR, no codegen. Right for educational languages and DSL bootstraps where you want to iterate on semantics weekly. (See `BOOTSTRAP_PLAN.md` § *Tree-walking v0.1*.) |
| `bytecode_vm` | **Moderate complexity.** Compile to a custom bytecode and run on your own VM. Portable, faster than tree-walking, lets you ship a small runtime. Right when you outgrow tree-walking but don't need native speed. |
| `native_compiler` | **AOT to machine code.** Highest performance. Pairs with `pl.host_runtime = llvm | mlir | cranelift | qbe | native_no_runtime` below. Right for general-purpose languages targeting production workloads. |
| `transpiler` | **Compile to an existing language.** Your output is *source code* (JS, C, Go, Rust), not a binary. Fastest path to a "real" language with full ecosystem inheritance. Mandatory if `project.sub_type == transpiler_target`. |
| `hosted_embedded` | **DSL inside a host language.** Lua-in-C, Ruby DSL, Rust proc-macro, Python decorator, JS template-string. No standalone runtime — the host evaluates. Right for `domain_specific_language` and `configuration_language` sub_types that don't justify their own VM. |

The orchestrator saves the chosen value as the flat decision `pl.impl_strategy`. Cross-references: `BOOTSTRAP_PLAN.md` § *Implementation-strategy decision table*, `SEMANTICS.md` § *Evaluation model*, `tech-stack-options.md` § *PL implementation backends*.

#### Q-pl-3 · `pl.host_runtime` — what runs the compiled/interpreted code?

Ask via `AskUserQuestion` (single-select). Save the answer as the flat decision `pl.host_runtime`. The 14-option enum is research-informed as of 2026-05-13 — see `references/decision-keys.md` for the canonical key and `references/tech-stack-options.md` § *PL implementation backends* for the comparison matrix. Each option carries a status verdict (production / experimental-but-usable / research-only).

| Value | One-line distinguishing prompt (2026 status) |
|---|---|
| `llvm` | **Industrial default — production.** LLVM 22.x stable, broadest target coverage (x86_64, aarch64, riscv64, wasm, GPU, …). Right when you want production-grade native codegen and a deep optimizer. Used by Rust, Swift, Zig, Clang. |
| `mlir` | **Accelerator-friendly — production-but-niche.** Dialect-driven compiler IR; first-class GPU/FPGA/TPU/quantum targets. Mojo proves general-purpose viability. Right when your language targets ML hardware or domain-specific accelerators. |
| `cranelift` | **Fast-debug / Wasm — production.** Rust-native backend; the codegen for `wasmtime` and `rustc -Cback=cranelift`. Lower peak performance than LLVM but 10× faster build times. Right for Wasm runtimes and developer-tools languages. |
| `qbe` | **Small-backend alternative — experimental-but-usable.** ~14 kLOC C; trivial to vendor into a teaching compiler. x86-64 / aarch64 / riscv64 only. Right for bootstrap compilers and educational projects (`educational_language`). |
| `truffle` | **Host on GraalVM — production.** Truffle framework on GraalVM 24/25 LTS gives you a free JIT, Native Image AOT, and polyglot interop with JVM/JS/Python. Right when you want to inherit a mature managed runtime. |
| `jvm` | **Target JVM bytecode — production.** Java 25 LTS; you ship `.class` files. Right for languages with JVM-shaped semantics (Kotlin, Scala, Clojure, Gleam-on-JVM). |
| `beam` | **Erlang/OTP VM — production-but-niche.** Functional, actor-model, soft-real-time. Gleam is the 2026 exemplar. Right *only* if your language has actor/process semantics — don't pick BEAM for imperative code. |
| `wasm` | **Raw Wasm 3.0 — production.** W3C standard since Sept 2025: WasmGC + EH + tail calls + multi-memory. Right for browser/edge/sandboxed embeds and language portability. |
| `wasm_component` | **Component Model — experimental-but-usable.** WASI 0.2 stable, 0.3 RC. Right for cross-component composition (call Python from Rust from JS, all sandboxed). |
| `js_host` | **Compile to JavaScript — production.** TypeScript, ClojureScript, ReScript, Elm, Kotlin/JS exemplars. Right when web-first or polyglot piggyback is the goal. Mandatory-ish for `transpiler_target` sub_type aiming at JS. |
| `python_embedded` | **DSL inside Python 3.14+ — production.** Right for `domain_specific_language` and `configuration_language` sub_types embedded in scientific or data workflows. (No-GIL is opt-in; don't depend on it for v0.1.) |
| `rust_host` | **Embedded DSL in Rust — production.** Proc-macro at compile time OR runtime interpreter (`rhai`, `rune`). Right when host is Rust and you want zero-cost or near-zero-cost integration. |
| `native_no_runtime` | **Hand-rolled native codegen — expert-only.** No backend library; you emit machine code yourself. Right for research languages or when you need full control of the binary. |
| `custom_vm` | **Hand-rolled bytecode VM — teaching/niche.** Like `bytecode_vm` impl_strategy but explicitly choosing to *write* the VM rather than reuse one. Right for `educational_language` and for "Crafting Interpreters"-style teaching projects. |

The shortlist visible to the user is filtered by the `pl.impl_strategy` answer:

| `pl.impl_strategy` answer | Shortlist filter |
|---|---|
| `tree_walking_interpreter` | host_runtime is informational only — the interpreter runs in its host language. Show `python_embedded`, `rust_host`, `js_host`, `custom_vm` as host-language candidates. |
| `bytecode_vm` | Show `truffle`, `jvm`, `beam`, `wasm`, `wasm_component`, `custom_vm`. |
| `native_compiler` | Show `llvm`, `mlir`, `cranelift`, `qbe`, `native_no_runtime`. |
| `transpiler` | Show `js_host`, `wasm`, `wasm_component`. (Plus free-form "other target" — TS-to-Go, KCL-to-YAML, etc.) |
| `hosted_embedded` | Show `python_embedded`, `rust_host`, `js_host`. |

Cross-references: `tech-stack-options.md` § *PL implementation backends* (comparison matrix), `BOOTSTRAP_PLAN.md` § *Backend selection rationale*, `TOOLCHAIN.md` § *Build pipeline* (the host runtime decides which build steps exist).

---

## Cost Modeling (Cost, Phase 5)

Runs in the Cost phase (Phase 5), after Tech Stack (Phase 4).

1. Dispatch `research-scout` with the pricing-research prompt (see `research-prompts.md`).
2. Walk the user through the findings: base costs, per-unit costs, hidden line items, free-tier limits.
3. Optionally revise tech-stack decisions in light of cost reality (any revision spawns the `decision-revisor`).
4. Capture cost estimates in `COST_MODEL.md` at MVP / growth / enterprise tiers.

---

## Architecture Deep Dive (Architecture phase)

Runs in the Architecture phase (Phase 3), **before** Tech Stack (Phase 4) — the architecture decided here constrains the viable technologies chosen next. Per-area drill-downs. Only ask about areas that apply (per prior phases). Each area concludes a "ready to record" question — if yes, file an ADR.

### Auth (if auth chosen)
- Session strategy (JWT / cookies / hybrid)?
- Token storage (httpOnly / secure storage / both)?
- RBAC / ABAC / simple permissions?
- Multi-tenancy isolation model?
- OAuth providers list?
- Lockout / rate-limit policy?
- MFA support (TOTP / passkeys / SMS)?

### Database design (if DB chosen)
- Normalization level (3NF / denormalized / event-sourced)?
- Migration strategy (code-first / SQL-first / hybrid)?
- Key entities + relationships (high-level ERD)?
- Soft vs hard deletes?
- Audit-logging needs?
- Read replicas / sharding?
- Multi-tenancy data isolation (shared DB / schema-per-tenant / DB-per-tenant)?

### API design (if API)
- Style (REST / GraphQL / gRPC / tRPC / hybrid)?
- Versioning (URL path / header / none)?
- Rate-limiting policy?
- Pagination (cursor / offset / keyset)?
- API docs (OpenAPI / GraphQL introspection / manual)?
- Real-time channel (WebSocket / SSE / polling)?
- Webhook outbound (events, retry, signature)?

### Security architecture (if regulated OR security flagged)
- Encryption at rest / in transit?
- Secret management (env vars / Vault / Infisical / KMS)?
- Input validation library / schema enforcement?
- CORS policy?
- CSP?
- Dep-vuln scanning (Snyk / GitHub Advanced Security / Trivy)?
- Post-quantum / E2E encryption needs?
- Compliance gates (SOC2 / HIPAA / PCI-DSS / GDPR)?

### Frontend architecture (if frontend)
- State management (Context / Zustand / Redux / Jotai / signals)?
- Data fetching (TanStack Query / SWR / tRPC / Apollo)?
- Routing model (file-based / manual)?
- Rendering strategy (SSR / SSG / CSR / ISR / mix)?
- i18n requirements?
- a11y target (WCAG level)?
- Form library?
- Animation library?

### Testing strategy
- Unit framework (Vitest / Jest / pytest / cargo test / etc.)?
- Integration / API test framework?
- E2E framework (Playwright / Cypress / Detox / XCTest / Espresso)?
- Coverage target?
- CI integration cadence?
- Visual / snapshot tests?

### DevOps & deployment
- Environment tiers (dev / staging / production)?
- CI / CD platform?
- IaC (Terraform / Pulumi / SST / CDK / Crossplane / none)?
- Containerization (Docker / Podman / native)?
- Preview deploys (per-PR / per-branch)?
- Blue-green / canary?

### Monitoring & observability (if scale > MVP)
- Error tracking (Sentry / Bugsnag / Datadog)?
- APM (Datadog / New Relic / Grafana Cloud)?
- Logging (Loki / Datadog / Axiom / CloudWatch)?
- Uptime monitoring?
- Analytics (PostHog / Plausible / Mixpanel / Amplitude)?
- Alerting destinations (Slack / PagerDuty / email)?

### Third-party integrations
- Which services are critical (which are nice-to-have)?
- Webhook handling needs?
- Queue / event system?
- Background jobs / scheduled tasks?
- SDK quality / portability concerns?

### Programming language — PL-specific batch

**Trigger:** runs when `project.sub_type` is one of the 6 PL variants (`general_purpose_language`, `domain_specific_language`, `query_language`, `configuration_language`, `educational_language`, `transpiler_target`). It replaces the entire Architecture (Phase 3) per-area drill-down list above (Auth / Database / API / Security / Frontend / Testing / DevOps / Monitoring / Third-party integrations) — those areas don't apply to a language being designed. The Architecture phase for a PL project is just these two axes plus a Testing-strategy batch (which still applies, since the language itself needs a test suite).

The two questions feed `TYPE_SYSTEM.md` (the canonical PL type-system document) and inform `SEMANTICS.md`. Cross-references at the bottom of each question.

#### Q-pl-4 · `pl.paradigm` — primary programming paradigm

Ask via `AskUserQuestion` (single-select). Save the answer as the flat decision `pl.paradigm` using the exact enum value (see `references/decision-keys.md`).

| Value | One-line distinguishing prompt | Examples |
|---|---|---|
| `imperative` | **Statements, mutable state, top-to-bottom control flow.** Pick when programs read like recipes — assign, loop, branch, call. | C, Go, Zig |
| `functional` | **Expressions, immutable data, first-class functions.** Pick when programs read like math — map, fold, compose, no statements. | Haskell, OCaml, Elm |
| `logic` | **Declarative facts + queries; the runtime is a solver.** Pick when programs describe *what* relations hold, not *how* to compute. | Prolog, miniKanren, Datalog |
| `oop` | **Objects, messages, encapsulation, often dynamic dispatch.** Pick when programs read as "tell this object to do X." | Smalltalk, Java, Ruby |
| `multi_paradigm` | **Deliberately blends two or more paradigms with equal first-class support.** Pick when the design intent is "you can write OO *or* functional *or* imperative in this language." | Rust, Scala, Swift, F# |
| `data_oriented` | **Data layout and transformation are the primary abstraction.** Pick when the program is shaped around arrays / tables / EDN-like data structures rather than control flow. | Clojure, APL, J |

Cross-references: `TYPE_SYSTEM.md` § *Paradigm interactions* (paradigm constrains type system choice — `logic` excludes `affine_linear`, `data_oriented` excludes `dependent`), `SEMANTICS.md` § *Evaluation model* (paradigm determines whether semantics are big-step / small-step / denotational).

#### Q-pl-5 · `pl.type_system` — primary static-analysis stance

Ask via `AskUserQuestion` (single-select). Save the answer as the flat decision `pl.type_system` using the exact enum value (see `references/decision-keys.md`). The chosen value becomes the canonical type-system axis recorded in `TYPE_SYSTEM.md` § *Stance*; the document then drills into per-feature decisions (subtyping, variance, inference, ad-hoc polymorphism, …).

| Value | One-line distinguishing prompt | Examples |
|---|---|---|
| `static_strong` | **Static, no implicit coercion, no `Any` escape hatch.** All type errors caught at compile time; explicit casts only. | Rust, Haskell, OCaml |
| `static_gradual` | **Static, with opt-in dynamic / opt-out static regions.** A `dynamic` (or `Any`-style) type lives alongside checked types. | TypeScript, Python + mypy, Dart, Hack |
| `dynamic` | **Runtime types only.** No type-checker between source and execution; types are properties of values, not bindings. | Python, Ruby, JavaScript, Lua |
| `dependent` | **Types depend on values.** `Vec n Int` (a vector of length `n`) is a type. Lets you express "this list is non-empty" or "this index is in-bounds" at the type level. | Lean 4 (closest to general-purpose 2026), Idris 2, Agda, Coq |
| `affine_linear` | **Resources tracked by the type system.** Linear types must be used exactly once; affine types at most once. Right for ownership-tracking, file handles, capabilities. | Rust ownership, Linear Haskell, Austral |
| `none_untyped` | **No type system at all.** Untyped lambda calculus, Forth-style stack languages. Right only for tiny educational languages or `none_untyped` is a deliberate research stance. | BF, untyped λ-calc, Forth |

Cross-references: `TYPE_SYSTEM.md` (entire document — the type_system value is the *opening* decision the template drills into), `SEMANTICS.md` § *Type-system pairing* (static stances change which evaluation rules apply), `BOOTSTRAP_PLAN.md` § *Type-system rollout* (dependent and affine systems materially affect v0.1 scope — usually a deferred v0.2 feature).

**Skip the rest of the Architecture phase** (the Auth / Database / API / Security / Frontend / DevOps / Monitoring / Third-party drill-downs above) once a PL sub_type has been chosen. The only Architecture-phase area that *does* still apply is Testing strategy — a language project needs a test framework for its compiler/interpreter, and the existing Testing-strategy batch covers that without modification.

After all areas: **inline consistency check** (architect cross-checks decisions; surfaces contradictions for user resolution before doc gen).

End-of-phase: `research-scout` on pattern validation. Findings → `docs/research/phase3-architecture.md`.

---

## Routing Rules

Skip questions when prior answers make them irrelevant.

| Kickoff answer | Skip in later phases |
|---|---|
| Project type = Library / SDK | Auth, database, hosting, UI, payments, notifications |
| Project type = CLI tool | Frontend, UI, payments (usually), styling |
| No user accounts | All auth questions |
| No persistence | Database, ORM, schema design |
| No frontend | Styling, components, frontend architecture |
| No monetization | Payments & billing |
| Budget = free-tier only | Bias options toward open-source / self-hosted |
| Scale = hobby/personal | Monitoring deep dive, enterprise security, multi-tenancy |
| Solo team | Simplify CI/CD; skip team collaboration tooling |
| No regulatory requirements | Compliance section in security |
| Offline = yes | Add sync strategy, local-first patterns |
| Real-time = yes | WebSocket/SSE architecture, presence model |
| AI features = yes | AI/ML section, vector DB, embeddings |
| Stage = greenfield | Commit on `main`; no branch strategy questions |
| Stage = extending/rewriting/migrating | Create `bootstrap/architect-<date>` branch |
| Project type = Programming language | Skip web/mobile/hosting/auth/payments; run Vision (Phase 2) PL sub_type routing → Architecture (Phase 3) `pl.paradigm` + `pl.type_system` → Tech Stack (Phase 4) `pl.impl_strategy` + `pl.host_runtime` → Doc Generation (Phase 6) generates the 7 PL templates |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
