<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Tech Stack Options Reference

Concise option lists with trade-offs for each technology category. Present relevant options to the user, let them decide.

## Table of Contents
- [Frontend Frameworks](#frontend-frameworks)
- [Backend Frameworks](#backend-frameworks)
- [Databases](#databases)
- [ORMs & Query Builders](#orms--query-builders)
- [Authentication](#authentication)
- [Hosting & Deployment](#hosting--deployment)
- [CSS & Styling](#css--styling)
- [Component Libraries](#component-libraries)
- [State Management](#state-management)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Monitoring & Observability](#monitoring--observability)
- [Payments](#payments)
- [Email & Notifications](#email--notifications)
- [File Storage](#file-storage)
- [AI & ML](#ai--ml)
- [Package Managers](#package-managers)

---

## Frontend Frameworks

### Web
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Next.js** | Full-stack React apps, SSR/SSG | Feature-rich but complex, Vercel-optimized |
| **Nuxt** | Vue ecosystem, SSR/SSG | Great DX, smaller ecosystem than React |
| **SvelteKit** | Performance-critical, simpler mental model | Smaller ecosystem, fewer developers |
| **Remix** | Nested routing, progressive enhancement | React-based, smaller community than Next |
| **Astro** | Content-heavy sites, multi-framework | Not ideal for highly interactive SPAs |

### Mobile
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **React Native / Expo** | JS teams, code sharing with web | Not truly native, bridge overhead |
| **Flutter** | Beautiful cross-platform UI, single codebase | Dart language, large binary size |
| **SwiftUI** | iOS-first, best native experience | Apple only |
| **Jetpack Compose** | Android-first, modern Android | Android only |
| **.NET MAUI** | .NET teams, enterprise | Smaller community, Microsoft ecosystem |

### Desktop
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Tauri** | Small bundle, Rust backend, web frontend | Rust knowledge helpful, younger ecosystem |
| **Electron** | Maximum web compatibility, large ecosystem | Large memory/bundle, security surface |
| **SwiftUI** | macOS native | Apple only |
| **WinUI 3 / WPF** | Windows native | Windows only |

---

## Backend Frameworks

### Node.js / TypeScript
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Hono** | Edge-first, multi-runtime, lightweight | Newer, smaller ecosystem |
| **Fastify** | Performance, schema validation | More setup than Express |
| **Express** | Simplicity, massive ecosystem | Dated patterns, no built-in types |
| **NestJS** | Enterprise, structured architecture | Heavy, opinionated, Angular-like |
| **tRPC** | Type-safe APIs with TypeScript frontend | Requires TypeScript client |

### Python
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **FastAPI** | Modern async APIs, auto-docs | Async complexity, Pydantic learning curve |
| **Django** | Batteries-included, admin panel | Monolithic, heavier for small APIs |
| **Flask** | Simplicity, microservices | Minimal built-in features |

### Go
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Chi** | Lightweight, idiomatic | Minimal features, manual wiring |
| **Gin** | Performance, familiar API | Less idiomatic Go |
| **Echo** | Balance of features and performance | Smaller community than Gin |

### Rust
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Axum** | Tokio ecosystem, tower middleware | Steep learning curve |
| **Actix-web** | Raw performance | Actor model can be complex |

### Edge / Serverless
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Cloudflare Workers** | Edge-first, global low latency | V8 isolates, some Node API gaps |
| **AWS Lambda** | AWS ecosystem, event-driven | Cold starts, vendor lock-in |
| **Vercel Functions** | Next.js integration | Vercel ecosystem |
| **Supabase Edge Functions** | Supabase integration, Deno | Supabase-coupled |

---

## Databases

### Relational
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **PostgreSQL** | General purpose, extensions (pgvector, PostGIS) | Self-managed complexity |
| **Supabase (Postgres)** | Managed Postgres + auth + storage + realtime | Vendor coupling, pricing at scale |
| **Neon (Postgres)** | Serverless Postgres, branching | Newer, cold starts on free tier |
| **PlanetScale (MySQL)** | Serverless MySQL, branching | MySQL not Postgres, no FK enforcement |
| **SQLite / Turso** | Embedded, edge, local-first | Limited concurrent writes, simpler |
| **CockroachDB** | Distributed SQL, global scale | Complex, expensive at scale |

### Document
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **MongoDB** | Flexible schema, document-oriented | No ACID joins, schema drift |
| **Firestore** | Firebase ecosystem, real-time | Vendor lock-in, query limitations |
| **DynamoDB** | AWS, massive scale, key-value + document | Complex pricing, rigid access patterns |

### Key-Value / Cache
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Redis / Upstash** | Caching, sessions, queues | Data loss risk (in-memory default) |
| **Cloudflare KV** | Edge key-value, global reads | Eventually consistent, write latency |

### Vector
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **pgvector** | Postgres users, unified DB | Scaling limits vs dedicated vector DB |
| **Pinecone** | Managed, easy to use | Expensive, vendor lock-in |
| **Weaviate** | Self-hosted, hybrid search | Operational complexity |
| **Qdrant** | Performance, Rust-based | Smaller ecosystem |

---

## ORMs & Query Builders

### TypeScript
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Drizzle** | Type-safe, SQL-like, lightweight | Newer, migration story evolving |
| **Prisma** | Schema-first, great DX, migrations | Performance overhead, large engine binary |
| **Kysely** | Type-safe query builder, no codegen | Manual migrations, lower-level |
| **TypeORM** | Decorator-based, familiar to Java/C# devs | Performance issues, maintenance concerns |

### Python
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **SQLAlchemy** | Flexible, powerful, async support | Steep learning curve |
| **Django ORM** | Django projects, batteries included | Django-coupled |

---

## Authentication

### Managed
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Clerk** | Best DX, prebuilt components | Pricing at scale, vendor lock-in |
| **Auth0** | Enterprise, extensive features | Complex, expensive |
| **Supabase Auth** | Supabase users, Row Level Security | Supabase-coupled |
| **Firebase Auth** | Firebase ecosystem | Google lock-in |
| **Kinde** | Simple, generous free tier | Smaller ecosystem |

### Self-Hosted / Library
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Better Auth** | TypeScript, flexible, self-hosted | Newer, smaller community |
| **Auth.js (NextAuth)** | Next.js projects | Complex configuration, session-focused |
| **Lucia** | Lightweight, any framework | Manual implementation, discontinued maintenance |
| **Keycloak** | Enterprise SSO, self-hosted | Heavy, Java-based, complex setup |
| **Ory** | Cloud-native identity, API-first | Steep learning curve |

---

## Hosting & Deployment

### Frontend
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Vercel** | Next.js, great DX, preview deploys | Pricing at scale, some lock-in |
| **Cloudflare Pages** | Edge-first, generous free tier | Fewer framework integrations |
| **Netlify** | Static/Jamstack, forms, functions | Less capable edge |
| **AWS Amplify** | AWS ecosystem | Complex setup |

### Backend
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Cloudflare Workers** | Edge, global, low-latency | V8 runtime limitations |
| **Railway** | Simple PaaS, databases included | Pricing, limited regions |
| **Fly.io** | Global edge, containers | Ops complexity, pricing changes |
| **AWS (ECS/Lambda)** | Full control, enterprise | Complex, expensive for small projects |
| **GCP Cloud Run** | Containers, Google ecosystem | Google lock-in |

---

## CSS & Styling
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Tailwind CSS** | Utility-first, rapid UI development | Verbose class names, learning curve |
| **CSS Modules** | Scoped CSS, framework-agnostic | No utility classes, more files |
| **vanilla-extract** | Type-safe CSS-in-TS, zero runtime | Build step required, TS coupling |
| **UnoCSS** | Customizable utilities, fast | Smaller community than Tailwind |

---

## Component Libraries
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **shadcn/ui** | Customizable, copy-paste, Radix-based | React only, manual updates |
| **Radix UI** | Accessible primitives, unstyled | React only, needs styling |
| **MUI** | Material Design, comprehensive | Heavy, opinionated design |
| **Ant Design** | Enterprise dashboards, rich components | Large bundle, Chinese origin docs |
| **Headless UI** | Tailwind Labs, accessible | Limited component set |

---

## State Management
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Zustand** | Simple, lightweight, React | Limited devtools vs Redux |
| **Jotai** | Atomic state, fine-grained updates | Different mental model |
| **Redux Toolkit** | Complex state, time-travel debugging | Boilerplate, overkill for simple apps |
| **TanStack Query** | Server state, caching, mutations | Only for async/server state |
| **Valtio** | Proxy-based, mutable API | Less predictable updates |

---

## Testing
| Type | Options |
|------|---------|
| **Unit (JS/TS)** | Vitest (fast, Vite-native), Jest (established, large ecosystem) |
| **Unit (Python)** | pytest (standard), unittest (built-in) |
| **Unit (Go)** | testing (built-in), testify (assertions) |
| **E2E** | Playwright (multi-browser, fast), Cypress (great DX, single-tab) |
| **API** | Supertest, httpx, Bruno, Insomnia |
| **Visual** | Chromatic, Percy, Playwright screenshots |
| **Mobile** | Detox (React Native), XCTest (iOS), Espresso (Android) |

---

## CI/CD
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **GitHub Actions** | GitHub users, large marketplace | YAML complexity, debugging |
| **GitLab CI** | GitLab users, built-in | GitLab ecosystem |
| **CircleCI** | Performance, Docker layers | Pricing, config complexity |
| **Buildkite** | Scale, self-hosted agents | Setup complexity |

---

## Monitoring & Observability
| Concern | Options |
|---------|---------|
| **Error tracking** | Sentry (standard), Bugsnag, Datadog |
| **APM** | Datadog, New Relic, Grafana Cloud |
| **Logging** | Datadog, Loki/Grafana, CloudWatch, Axiom |
| **Uptime** | Better Uptime, Checkly, Pingdom |
| **Analytics** | PostHog (OSS, full-stack), Plausible (privacy), Mixpanel, Amplitude |

---

## Payments
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Stripe** | Full-featured, developer-first | Complex pricing, US-centric |
| **Lemon Squeezy** | Simple, MoR (handles tax) | Fewer features than Stripe |
| **Paddle** | B2B SaaS, MoR | Limited customization |
| **RevenueCat** | Mobile subscriptions | Mobile only |

---

## Email & Notifications
| Concern | Options |
|---------|---------|
| **Transactional email** | Resend (modern DX), SendGrid (established), Postmark (deliverability), AWS SES (cheap) |
| **Push notifications** | OneSignal, Firebase Cloud Messaging, APNs direct |
| **Multi-channel** | Novu (OSS), Knock, Courier |

---

## File Storage
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **Cloudflare R2** | S3-compatible, no egress fees | Cloudflare ecosystem |
| **AWS S3** | Standard, massive ecosystem | Egress costs |
| **Supabase Storage** | Supabase users, RLS integration | Supabase-coupled |
| **UploadThing** | Simple file uploads in TypeScript | Limited to uploads, T3-ecosystem |
| **MinIO** | Self-hosted S3-compatible | Operational complexity |

---

## AI & ML
| Concern | Options |
|---------|---------|
| **LLM Provider** | Anthropic Claude (best reasoning), OpenAI (ecosystem), Google Gemini (multimodal), Ollama (local) |
| **AI SDK** | Vercel AI SDK (streaming, multi-provider), LangChain (chains, agents), LlamaIndex (RAG-focused) |
| **Vector DB** | pgvector (unified), Pinecone (managed), Weaviate (hybrid search) |
| **Embeddings** | OpenAI text-embedding-3, Cohere embed, local sentence-transformers |

---

## Package Managers
| Option | Best For | Trade-off |
|--------|----------|-----------|
| **pnpm** | Monorepos, disk space, strict | Different node_modules structure |
| **bun** | Speed, all-in-one runtime | Compatibility gaps, newer |
| **npm** | Universal, no setup | Slower, flat node_modules |
| **yarn** | Berry (PnP), workspaces | PnP compatibility issues |

---

## Web3 / Smart Contracts

| Layer | Options | Trade-offs |
|---|---|---|
| **Chain (EVM)** | Ethereum mainnet, Optimism, Arbitrum, Base, Polygon zkEVM, Linea, Scroll | mainnet = highest security + cost; L2s = cheap + fast, ecosystem-fragmented |
| **Chain (non-EVM)** | Solana, Aptos, Sui, Starknet, Near | high throughput, different tooling, smaller dev ecosystems |
| **Contract language** | Solidity (EVM), Vyper (EVM), Rust+Anchor (Solana), Move (Aptos/Sui), Cairo (Starknet) | Solidity = most learning material; Rust = strong typing; Move = resource-oriented |
| **Dev framework** | Foundry, Hardhat, Truffle (deprecated), Anchor, Starknet Foundry | Foundry = Rust-fast tests; Hardhat = JS-native; Anchor = Solana standard |
| **Indexing** | The Graph, Goldsky, Subsquid, Ponder, custom | hosted vs self-host; cost vs control |
| **Wallet integration** | RainbowKit, ConnectKit, wagmi, ethers, viem, web3.js (legacy) | wagmi+viem = modern TS-first |
| **Audits** | Trail of Bits, OpenZeppelin, Sherlock contest, Code4rena | firm vs contest; cost vs depth |

## Game Engines

| Option | Best for | Trade-offs |
|---|---|---|
| **Unity** | Cross-platform, mobile, AR/VR, indie + AAA | C#, royalty model after threshold |
| **Unreal Engine** | High-fidelity 3D, AAA, console | C++ + Blueprints, heavier |
| **Godot** | 2D + 3D indie, OSS | GDScript / C#, smaller ecosystem |
| **Bevy** | Rust-based, OSS, ECS | Rust expertise required, younger |
| **PlayCanvas / Phaser / Pixi.js** | Web-native games | Browser only, no native AOT |

## Mobile-Specific Tooling

| Layer | Options | Trade-offs |
|---|---|---|
| **Cross-platform framework** | React Native (bare or Expo), Flutter, .NET MAUI, NativeScript, KMP+Compose Multiplatform | RN+Expo = JS speed; Flutter = pixel-perfect; KMP = native UI per platform |
| **Native (iOS)** | SwiftUI, UIKit (legacy) | SwiftUI = modern, UIKit needed for some controls |
| **Native (Android)** | Jetpack Compose, View system (legacy) | Compose = modern, Views needed for some libs |
| **State (RN/Flutter)** | Zustand+Jotai (RN), Riverpod+BLoC (Flutter) | per-ecosystem standard |
| **Distribution / OTA** | EAS Update (Expo), CodePush (deprecated), Shorebird (Flutter), App Center | EAS for Expo; Shorebird for Flutter dart hot updates |
| **In-app purchases** | RevenueCat (cross-platform), StoreKit 2 (iOS native), Google Play Billing (Android native) | RevenueCat = subscription unification |

## Embedded / Firmware

| Layer | Options | Trade-offs |
|---|---|---|
| **MCU class** | Cortex-M0+/M3/M4F/M7 (STM32, NXP), RP2040/RP2350 (Raspberry Pi), ESP32 (Espressif), nRF52/nRF53 (Nordic BLE) | RP2040 = cheap+RP; ESP32 = built-in WiFi+BLE; nRF = BLE-first |
| **RTOS** | FreeRTOS, Zephyr, ThreadX (Azure RTOS), bare-metal | Zephyr = modular + DTS; FreeRTOS = simplest |
| **Language** | C, C++ (modern), Rust (embedded-hal), MicroPython | Rust = memory safety, learning curve |
| **OTA** | esp-idf OTA, MCUboot, Nordic DFU, custom | MCUboot = vendor-neutral |
| **Connectivity** | BLE, Wi-Fi, Thread/Matter, LoRa(WAN), NB-IoT, Cellular (LTE-M / 4G / 5G), Ethernet | Matter = unified IoT; LoRa = long-range low-power |
| **Tooling** | PlatformIO, esp-idf, STM32CubeIDE, Zephyr west, probe-rs | PlatformIO unifies across MCUs |

## Browser Extensions

| Layer | Options | Trade-offs |
|---|---|---|
| **Manifest** | Manifest V3 (required for Chrome new submissions), Manifest V2 (Firefox supports longer) | MV3 = service worker model |
| **Framework** | WXT, Plasmo, CRXJS, vanilla | WXT/Plasmo = DX boost, type-safe |
| **Cross-browser** | webextension-polyfill, browser API shims | extension code largely portable |
| **Distribution** | Chrome Web Store, Mozilla Add-ons, Edge Add-ons, Safari (Mac App Store) | Safari requires Xcode wrapper |

## Desktop App Frameworks

| Option | Best for | Trade-offs |
|---|---|---|
| **Tauri** | Rust backend + web frontend, small bundle | Rust learning |
| **Electron** | Max compatibility, large ecosystem | Heavy memory, large bundle |
| **Wails** | Go backend + web frontend | Smaller ecosystem |
| **SwiftUI (macOS-only)** | Native macOS UX | Apple only |
| **WinUI 3 (Windows-only)** | Native Windows UX | Microsoft only |
| **GTK / Qt** | Native Linux + cross-platform | Older stacks, harder UX polish |

## AR / VR / Spatial

| Layer | Options | Trade-offs |
|---|---|---|
| **Headset/device** | Apple Vision Pro (visionOS), Meta Quest 2/3/Pro, smartphone AR (ARKit/ARCore), WebXR | visionOS = native spatial; Quest = standalone; WebXR = browser-only |
| **Engine** | Unity (broad support), Unreal, RealityKit (Apple), Three.js+react-three-fiber (WebXR) | Unity = most cross-platform; RealityKit = visionOS native |
| **Tracking** | controllers, hand-tracking, eye-tracking, gaze, voice | varies by device capability |
| **Multi-user** | Photon, Mirror, Normcore, ROS (research) | Photon = managed; Mirror = open-source Unity |

## MCP Server Hosts

| Option | Best for | Trade-offs |
|---|---|---|
| **stdio** | Local development, Claude Desktop integration | Single-user, no remote |
| **HTTP + SSE** | Remote, multi-user, web auth | Need hosting + auth |
| **Cloudflare Workers (McpAgent)** | Edge, durable state via DO, OAuth | Cloudflare-coupled |
| **Vercel Functions** | Serverless, Next.js-adjacent | Cold starts |

## Claude Code Plugin Components

| Layer | When to use | Notes |
|---|---|---|
| **Skills** | Reusable techniques, workflows, references | Default unit — see `skill-creator:skill-creator` |
| **Commands** | User-invoked slash commands | See `plugin-dev:command-development` |
| **Agents** | Long-running, isolated context tasks | See `plugin-dev:agent-development` |
| **Hooks** | Event-driven (PreToolUse, PostToolUse, Stop, etc.) | See `plugin-dev:hook-development` |
| **MCP servers** | External tool integrations | See `plugin-dev:mcp-integration` |

## Scientific / Research Stacks

| Layer | Options | Trade-offs |
|---|---|---|
| **Compute backend** | NumPy / SciPy, PyTorch, JAX, cuDF, Polars, DuckDB, Dask, Ray | JAX = autodiff + JIT; Polars/DuckDB = OLAP local |
| **Notebooks** | Jupyter, marimo, Pluto.jl (Julia), Quarto | marimo = reactive; Quarto = publication |
| **Environment** | conda / mamba, uv, pixi, Nix, devcontainer | pixi = conda+lockfile speed; Nix = full reproducibility |
| **Workflow** | Snakemake, Nextflow, Pachyderm (data versioning) | Nextflow = bioinformatics standard |
| **Publication** | Quarto, Pandoc, LaTeX, Manuscripts | Quarto unifies notebooks + papers |

## Data Pipeline Orchestrators

| Option | Best for | Trade-offs |
|---|---|---|
| **Airflow (Astronomer-managed)** | Mature, large community | Heavy, complex |
| **Dagster** | Modern, asset-aware | Newer, less battle-tested |
| **Prefect** | Python-native, dynamic | Smaller community than Airflow |
| **Argo Workflows** | Kubernetes-native | K8s required |
| **Temporal** | Durable execution, code-defined | Different mental model |
| **GitHub Actions / cron** | Simple schedules | Limited for complex DAGs |

## IaC / Cloud Infrastructure

| Option | Best for | Trade-offs |
|---|---|---|
| **Terraform / OpenTofu** | Multi-cloud, mature ecosystem | HCL learning |
| **Pulumi** | Real programming languages | Smaller community |
| **AWS CDK** | AWS-only, TypeScript/Python | AWS lock-in |
| **SST** | Serverless + Next.js + AWS | Opinionated |
| **Crossplane** | K8s-native infrastructure | K8s required |

---

## Programming language implementation backends (v2.3, Sketch F)

When `project.sub_type` is one of the v2.3 PL variants (`general_purpose_language`, `domain_specific_language`, `query_language`, `configuration_language`, `educational_language`, `transpiler_target`), the `host_runtime` decision picks the implementation backend the new language sits on top of. The 14 enum values below are the canonical options surfaced in Phase 2 / Phase 3 PL question batches; pick by use-case fit, not by familiarity. 2026 status notes are research-anchored as of 2026-05-13 — re-verify before locking a v1.0 design if more than ~6 months have passed.

| host_runtime | Maturity | Complexity | Ecosystem fit | Typical use case | 2026 version/cite |
|---|---|---|---|---|---|
| `llvm` | production | high | broad | industrial default | LLVM 22.x stable |
| `mlir` | production (Mojo proves general) | very high | accelerator-friendly (GPU/FPGA/TPU) | dialect-driven design | Mojo 2026 |
| `cranelift` | production for Wasm/JIT; experimental general | medium | Wasm runtimes | fast-debug Rust codegen | Wasmtime 26+ |
| `qbe` | production for niche | low | small backend (~14 kLOC C) | teaching/bootstrap; x86-64/aarch64/riscv64 | active |
| `truffle` | production | medium | GraalVM 24/25 LTS | host a new language with free JIT+Native+polyglot | GraalVM 24/25 LTS |
| `jvm` | production | medium | massive ecosystem | target JVM bytecode | Java 25 LTS |
| `beam` | production but narrow | medium | functional/actor only | Gleam exemplar | OTP 27+ |
| `wasm` | production | medium | portable target | raw Wasm 3.0 (WasmGC + EH + tail calls + multi-memory shipped Sept 2025) | Wasm 3.0 W3C |
| `wasm_component` | stable on WASI 0.2; 0.3 RC | medium | cross-component composition | plug-in architecture | WASI 0.2 stable |
| `js_host` | production | low | web embedding | compile to JS | ES2026 |
| `python_embedded` | production but narrow | low | DSL inside Python | prototyping/education; no-GIL opt-in only | Python 3.14 |
| `rust_host` | production | medium | embedded DSL in Rust | proc-macro or runtime interpreter | Rust 1.86+ |
| `native_no_runtime` | expert-only | very high | minimal deps | hand-rolled codegen | varies |
| `custom_vm` | production for niche | medium | teaching/educational | hand-rolled bytecode VM | varies |

**Cross-references:** the chosen `host_runtime` shapes downstream PL templates. See `references/templates/BOOTSTRAP_PLAN.md` for the v0.0 → v0.1 → v1.0 bootstrap plan that operationalises this choice (which compiler/VM the implementation rides), and `references/templates/TYPE_SYSTEM.md` for the type-system stance that interacts with it (e.g., affine/linear typing on LLVM vs Cranelift, dependent types on a custom VM, gradual typing on `js_host`).

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
