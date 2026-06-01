---
template_name: DESKTOP_SPECIFIC
generate_when: "decisions.project.type == 'desktop'"
required_decisions: [desktop.platforms, desktop.framework]
optional_decisions: [desktop.distribution, desktop.auto_update, desktop.system_integration, desktop.sandboxing]
depends_on: []
revision_triggers: [desktop.platforms, desktop.framework, desktop.distribution]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Desktop Specific: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [⚙️ Target Platforms](#target-platforms)
- [Framework (Tauri / Electron / native)](#framework-tauri-electron-native)
- [🚀 Distribution](#distribution)
- [🚀 Auto-Update Mechanism](#auto-update-mechanism)
- [🔧 System Integration (menu bar, tray, file associations, deep links)](#system-integration-menu-bar-tray-file-associations-deep-links)
- [Sandboxing / Entitlements](#sandboxing-entitlements)
- [Code-Signing & Notarization](#code-signing-notarization)
- [↻ Revision Log](#revision-log)

## ⚙️ Target Platforms
Supported OSes (macOS, Windows, Linux) with minimum versions, architectures (x86_64, arm64), and rationale for inclusion or exclusion.

## Framework (Tauri / Electron / native)
Framework choice (Tauri, Electron, Wails, native — SwiftUI / WinUI / GTK / Qt) with trade-offs (bundle size, memory footprint, native fidelity, web stack reuse).

## 🚀 Distribution
Distribution channels (Mac App Store, direct download with Developer ID, Microsoft Store, Snap, Flatpak, MSI, Homebrew Cask) and per-platform installer formats (.dmg, .pkg, .msi, .exe, .deb, .rpm, AppImage).

## 🚀 Auto-Update Mechanism
Update framework (Sparkle, WinSparkle, Squirrel, Tauri updater, custom), update channels (stable / beta / nightly), signing of update manifests, and rollback strategy.

## 🔧 System Integration (menu bar, tray, file associations, deep links)
Platform integrations: menu bar / system tray, dock badging, file-type associations, URL-scheme handlers, global shortcuts, launch-at-login, notifications.

## Sandboxing / Entitlements
App Sandbox (macOS), AppContainer (Windows), entitlement requests (network, file access, camera, microphone, hardened runtime), and justifications for sensitive entitlements.

## Code-Signing & Notarization
Code-signing identity per OS (Apple Developer ID, EV Authenticode cert), notarization workflow (Apple notarytool, Microsoft SmartScreen), and CI integration.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
