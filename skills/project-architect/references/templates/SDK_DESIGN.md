---
template_name: SDK_DESIGN
generate_when: "decisions.project.type == 'library' OR decisions.exposes_sdk == true"
required_decisions: [sdk.target_languages]
optional_decisions: [sdk.versioning_policy, sdk.publication, sdk.docs_site, sdk.types_strategy]
depends_on: []
revision_triggers: [sdk.target_languages, sdk.versioning_policy]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# SDK Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Target Consumers](#target-consumers)
- [Languages Supported](#languages-supported)
- [🌐 Public API Surface](#public-api-surface)
- [Versioning Policy](#versioning-policy)
- [🚀 Publication](#publication)
- [📝 Docs Site](#docs-site)
- [Examples & Quickstarts](#examples-quickstarts)
- [Bundle Size Targets](#bundle-size-targets)
- [Type System Strategy](#type-system-strategy)
- [↻ Revision Log](#revision-log)

## Target Consumers
Who uses this SDK (backend service authors / mobile app authors / data-pipeline authors / external developers) and the primary use cases each consumer group has. Drives surface-area, ergonomic, and packaging decisions.

## Languages Supported
Each target language with the minimum supported runtime/version, why it was chosen, and the parity tier (first-class / community / experimental). Note which language hosts the canonical implementation if there is one.

## 🌐 Public API Surface
Entry points, key types, and the public/private boundary. One subsection per language. Call out clients, builders, async patterns (Promise / Future / async-await / callbacks), and error types. Mark anything intentionally not exposed.

## Versioning Policy
Versioning scheme (semver / calver) with the meaning of each part for this SDK. Deprecation timeline (how long deprecated APIs live before removal), breaking-change criteria, and how minor/patch releases interact with the underlying service. Link to RELEASE_PROCESS.md.

## 🚀 Publication
Where each language artifact is published (npm / cargo / PyPI / Maven Central / NuGet / Go module proxy), the package name, signing/provenance setup, and who can publish. Include the release command and any required environment.

## 📝 Docs Site
Where API reference lives (generated from source / hand-written), tutorial structure, search, versioning of the docs, and the build/deploy pipeline. Note the canonical URL and any vanity domains.

## Examples & Quickstarts
Where runnable examples live (in-repo `/examples`, separate repo, docs site). Cover the "5-minute hello world" for each language plus 2-3 representative real-world snippets. Each example must compile/run in CI.

## Bundle Size Targets
Per-language size budgets (KB gzipped for JS, install size for Python, binary size for Rust, etc.), the tools that enforce them in CI, and the action when a PR exceeds the budget. Note tree-shaking and side-effect-free guarantees where applicable.

## Type System Strategy
Per-language stance on types: TypeScript `.d.ts` shipping policy, Python type stubs / inline annotations, Rust trait surface, Go interface design. Note generation source (hand-maintained vs generated from a schema) and how breaking type changes are versioned.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
