---
template_name: BROWSER_EXTENSION
generate_when: "decisions.project.type == 'browser_extension'"
required_decisions: [extension.browsers, extension.manifest_version]
optional_decisions: [extension.framework, extension.permissions, extension.distribution]
depends_on: []
revision_triggers: [extension.browsers, extension.manifest_version, extension.permissions]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Browser Extension: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [⚙️ Target Browsers](#target-browsers)
- [⚙️ Manifest Version (V2 / V3)](#manifest-version-v2-v3)
- [Framework (vanilla / WXT / Plasmo / CRXJS)](#framework-vanilla-wxt-plasmo-crxjs)
- [⚙️ Permissions Justification](#permissions-justification)
- [Content Scripts vs Background Worker](#content-scripts-vs-background-worker)
- [🔧 DevTools / Popup / Side-panel surfaces](#devtools-popup-side-panel-surfaces)
- [🗄️ Storage Strategy](#storage-strategy)
- [🚀 Distribution Stores](#distribution-stores)
- [↻ Revision Log](#revision-log)

## ⚙️ Target Browsers
Supported browsers (Chrome / Edge / Brave / Opera, Firefox, Safari) with minimum versions and any browser-specific divergences in APIs.

## ⚙️ Manifest Version (V2 / V3)
Manifest version chosen (MV3 strongly preferred), migration plan from MV2 if applicable, and per-browser MV3 support caveats (notably Firefox event pages and Safari Web Extension differences).

## Framework (vanilla / WXT / Plasmo / CRXJS)
Build framework (vanilla + bundler, WXT, Plasmo, CRXJS+Vite) and rationale (HMR DX, cross-browser builds, asset handling).

## ⚙️ Permissions Justification
Each permission requested (host, activeTab, storage, scripting, identity, declarativeNetRequest, etc.) with the user-visible feature it enables — needed for store review.

## Content Scripts vs Background Worker
Architecture split: content-script responsibilities, background service-worker responsibilities, messaging contract between them, and lifecycle handling (service-worker idle timeouts).

## 🔧 DevTools / Popup / Side-panel surfaces
UI surfaces (browser action popup, side panel, DevTools panel, options page, full-page tabs) and which user flow each supports.

## 🗄️ Storage Strategy
Storage choice (chrome.storage.local / .sync / .session, IndexedDB, cookies via host permission) and quota / sync conflict handling.

## 🚀 Distribution Stores
Distribution targets (Chrome Web Store, Edge Add-ons, Firefox AMO, Safari App Store via Mac app, self-hosted CRX/XPI for enterprise), review timelines, and automation via store APIs.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
