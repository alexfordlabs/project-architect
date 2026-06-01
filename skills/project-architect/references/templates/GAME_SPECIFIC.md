---
template_name: GAME_SPECIFIC
generate_when: "decisions.project.type == 'game'"
required_decisions: [game.engine, game.dimensionality]
optional_decisions: [game.multiplayer, game.platforms, game.monetization, game.save_strategy]
depends_on: []
revision_triggers: [game.engine, game.multiplayer, game.platforms]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Game Specific: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Engine & Rationale](#engine-rationale)
- [2D / 3D / Hybrid](#2d-3d-hybrid)
- [Platforms](#platforms)
- [Asset Pipeline](#asset-pipeline)
- [🗄️ Save / Progression Storage](#save-progression-storage)
- [Multiplayer / Netcode (skip if single-player)](#multiplayer-netcode-skip-if-single-player)
- [💰 Monetization Model](#monetization-model)
- [Live-Ops Strategy](#live-ops-strategy)
- [↻ Revision Log](#revision-log)

## Engine & Rationale
Engine choice (Unity, Unreal, Godot, Bevy, custom, web — Phaser/PixiJS/Three.js) with reasoning around target platforms, team skills, licensing, and shipping risk.

## 2D / 3D / Hybrid
Dimensionality (pure 2D, 2.5D, full 3D, hybrid) and rendering style (pixel, vector, low-poly, photoreal, stylized PBR) — implications for asset budget and engine config.

## Platforms
Target platforms (PC: Steam/Epic/itch, console: PS/Xbox/Switch, mobile, web/HTML5, VR) with dev-kit/cert requirements per platform.

## Asset Pipeline
Asset workflow (DCC tools → engine import), source-control strategy for binary assets (Git LFS, Perforce, Plastic SCM), and automation for re-imports.

## 🗄️ Save / Progression Storage
Save format (binary, JSON, SQLite, cloud-only), local + cloud sync (Steam Cloud, iCloud, Google Play Saves), versioning of save schema, and corruption recovery.

## Multiplayer / Netcode (skip if single-player)
Netcode model (lockstep, rollback, client-server authoritative, P2P relay), transport (UDP/QUIC/WebRTC), matchmaking, anti-cheat, and dedicated-server hosting.

## 💰 Monetization Model
Model (premium, F2P with IAP, ads, subscription, season pass, DLC) and per-store implementation hooks; comply with platform policies on loot boxes / minors.

## Live-Ops Strategy
Content cadence (seasons, events), remote config, A/B testing, telemetry into balance dashboards, and player-comms channels (Discord, in-game news).

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
