---
template_name: AR_VR_SPECIFIC
generate_when: "decisions.project.type == 'ar_vr'"
required_decisions: [ar_vr.device, ar_vr.engine]
optional_decisions: [ar_vr.tracking, ar_vr.multi_user, ar_vr.rendering_engine, ar_vr.distribution]
depends_on: []
revision_triggers: [ar_vr.device, ar_vr.engine, ar_vr.tracking]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# AR / VR Specific: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [⚙️ Target Device / Platform](#target-device-platform)
- [Engine](#engine)
- [Tracking & Input Modalities](#tracking-input-modalities)
- [🎨 Rendering Strategy](#rendering-strategy)
- [Multi-User Sessions (skip if single)](#multi-user-sessions-skip-if-single)
- [Comfort & Locomotion Patterns](#comfort-locomotion-patterns)
- [🚀 Distribution (App Store / sideload)](#distribution-app-store-sideload)
- [↻ Revision Log](#revision-log)

## ⚙️ Target Device / Platform
Target headsets / devices (Apple Vision Pro, Meta Quest 2/3/Pro, PSVR2, Pico, Valve Index, HoloLens 2, Magic Leap 2, mobile AR via ARKit / ARCore) with minimum OS / runtime version.

## Engine
Engine choice (Unity + XR Interaction Toolkit, Unreal + OpenXR, RealityKit + visionOS, Godot XR, custom WebXR / Three.js / Babylon.js) and rationale.

## Tracking & Input Modalities
Tracking modes (6DoF inside-out, hand tracking, eye tracking, controllers, body tracking, marker-based AR, image / plane / mesh tracking) and primary input modality per feature.

## 🎨 Rendering Strategy
Render pipeline (forward / deferred / URP / HDRP / Lumen), foveated rendering, MSAA / TAA, single-pass instanced stereo, target framerate (72/90/120 Hz), and quality scaling.

## Multi-User Sessions (skip if single)
Multi-user architecture (colocated shared space, networked photon / Mirror / Netcode / Normcore, OpenXR session-sharing), state sync, and anchor sharing.

## Comfort & Locomotion Patterns
Locomotion options (teleport, smooth, room-scale only, seated), vignetting, snap-turn, comfort settings exposed to users, and motion-sickness mitigations.

## 🚀 Distribution (App Store / sideload)
Distribution channel (Meta Horizon Store, App Lab, visionOS App Store, SteamVR, sideload via SideQuest / Developer Hub) and store-review constraints.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
