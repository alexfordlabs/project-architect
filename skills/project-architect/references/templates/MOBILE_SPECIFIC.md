---
template_name: MOBILE_SPECIFIC
generate_when: "decisions.project.type == 'mobile' OR decisions.platforms.includes('mobile')"
required_decisions: [mobile.platforms, mobile.framework]
optional_decisions: [mobile.distribution, mobile.offline, mobile.push, mobile.deep_links, mobile.in_app_purchases]
depends_on: []
revision_triggers: [mobile.platforms, mobile.framework, mobile.distribution]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Mobile Specific: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [⚙️ Platforms & Min OS](#platforms-min-os)
- [Framework](#framework)
- [🚀 Distribution (App Store / Play / TestFlight / sideload)](#distribution-app-store-play-testflight-sideload)
- [Offline & Sync](#offline-sync)
- [Push Notifications](#push-notifications)
- [Deep Links / Universal Links](#deep-links-universal-links)
- [💰 In-App Purchases (if applicable)](#in-app-purchases-if-applicable)
- [🔧 Native Integrations (camera, biometrics, location, etc.)](#native-integrations-camera-biometrics-location-etc)
- [🚀 Code-Push / OTA Update strategy](#code-push-ota-update-strategy)
- [↻ Revision Log](#revision-log)

## ⚙️ Platforms & Min OS
Target platforms (iOS, Android, both) with minimum supported OS versions and rationale (device coverage, API availability, security baseline).

## Framework
Framework choice (SwiftUI / UIKit, Jetpack Compose / Views, React Native, Flutter, Expo, Kotlin Multiplatform) and why — code-sharing goals, team expertise, native API needs.

## 🚀 Distribution (App Store / Play / TestFlight / sideload)
Distribution channels per platform: App Store + TestFlight (iOS), Play Store + internal/closed/open tracks (Android), enterprise sideload (MDM, Ad-Hoc, APK), and review-cycle expectations.

## Offline & Sync
Offline-first vs online-required posture, local persistence (SQLite, Realm, Core Data, Room, MMKV), conflict resolution, and sync triggers (background fetch, push, manual).

## Push Notifications
Provider stack (APNs, FCM, OneSignal, Pusher Beams), token lifecycle, opt-in UX, payload schema, silent push usage, and analytics on deliverability.

## Deep Links / Universal Links
URL scheme + Universal Links (iOS) / App Links (Android) configuration, AASA / assetlinks.json hosting, fallback to web, parameter validation.

## 💰 In-App Purchases (if applicable)
StoreKit 2 / Google Play Billing flows, subscription vs consumable vs non-consumable, receipt validation server-side, restore-purchases, family-sharing handling.

## 🔧 Native Integrations (camera, biometrics, location, etc.)
Native capabilities used (camera, microphone, Face ID / Touch ID / BiometricPrompt, location, HealthKit, contacts, photos), permission strings, and graceful-degradation paths.

## 🚀 Code-Push / OTA Update strategy
OTA update mechanism (Expo Updates, App Center CodePush, CodePush replacement, custom), what is OTA-eligible vs native-only, rollback plan, and store-policy compliance.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
