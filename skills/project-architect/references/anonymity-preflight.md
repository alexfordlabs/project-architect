<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Anonymity / privacy preflight

This reference backs the `anonymity_threat_preflight` (B25, WARNING) check and the Preflight + Phase 2.5 prose. Privacy/anonymity is **one optional project concern among many** — most projects never trigger this check. But **when** a project is privacy- or anonymity-sensitive, centralized analytics/identity/telemetry backends can silently undermine the threat model: a privacy-sensitive project (e.g. an E2E-encrypted messenger) can commit a centralized backend + a debug log that quietly undermines its threat model. The check exists to surface that risk only for the projects where it applies — it is not a default emphasis.

## Trigger criteria

The preflight fires when EITHER holds:
- `state.decisions["project.privacy_sensitive"] == true` (set during the kickoff/threat-model questioning), OR
- a keyword scan of `docs/` matches: `anonymous`, `anonymity`, `Tor`, `onion service`, `zero-knowledge`, `end-to-end encrypt`, `threat model`, `metadata-resistant`.

When neither holds, the check INFO-passes (not applicable).

## Deanonymizing / centralized-service blocklist

When triggered, SURFACE (WARNING — not an auto-block; the user may have a justified reason) any dependency/config that references a centralized analytics, identity, telemetry, or push backend, including:

`firebase`, `firebase-admin`, `google-analytics`, `googleapis`, `gtag`, `google-tag-manager`, `@sentry`, `sentry-sdk`, `mixpanel`, `segment`, `amplitude`, `fullstory`, `hotjar`, `datadog`, `aws-amplify`, `cognito`, `onesignal`, `@vercel/analytics`.

## Why these undermine anonymity

- **Centralized identity/auth** (Firebase Auth, Cognito) ties a user to a provider account + device + IP.
- **Analytics/telemetry** (GA, Mixpanel, Segment, Amplitude, FullStory, Hotjar) exfiltrate usage metadata to a third party that can correlate sessions.
- **Crash/error SaaS** (Sentry, Datadog) ship stack traces + device context off-device.
- **Push** (OneSignal, FCM) registers a device token with a central broker.

## Remediation guidance (surfaced to the user)

- Replace centralized auth with self-hosted / cryptographic identity.
- Drop third-party analytics, or make it self-hosted + opt-in + metadata-minimal.
- Self-host error reporting, or strip device/PII context before sending.
- For push, prefer a metadata-resistant transport over a central broker.

The check SURFACES these; it does NOT auto-remove them — the architecture decision (and any justified exception) belongs to the user against their threat model.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
