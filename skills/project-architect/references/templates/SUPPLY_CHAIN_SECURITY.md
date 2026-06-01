---
template_name: SUPPLY_CHAIN_SECURITY
generate_when: "conditional"
required_decisions:
  - production_bound
  - scale
  - constraints.regulated
optional_decisions:
  - constraints.supply_chain_security
  - stack.language
  - stack.package_manager
  - stack.ci
  - stack.deploy_target
  - stack.containerized
  - stack.artifact_registry
depends_on: []
revision_triggers:
  - production_bound
  - scale
  - constraints.regulated
  - constraints.supply_chain_security
  - stack.package_manager
  - stack.ci
  - stack.artifact_registry
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Supply Chain Security: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document records the software-supply-chain posture for **{{project_name}}**. It is structured around two current authoritative standards: **[SLSA v1.0 (Supply-chain Levels for Software Artifacts)](https://slsa.dev/spec/v1.0/)** for build integrity and provenance, and **[CycloneDX 1.7](https://cyclonedx.org/specification/overview/)** (standardized as **ECMA-424**) for the bill of materials. SLSA defines *what integrity guarantee a build provides*; CycloneDX defines *what is in the artifact and where it came from*. Together they answer: "Can a consumer trust that this artifact was built from the source we claim, with the dependencies we declare, on infrastructure we control?"
>
> This project is **{{production_status}}** production-bound, operates at **{{scale}}** scale, and regulated-data handling is **{{regulated_status}}** — the combination of those three is why this hardening is in scope. Supply-chain hardening intensity: **{{supply_chain_intensity}}**.

## Table of contents
- [Scope & Trust Boundary](#scope-trust-boundary)
- [🎯 Target SLSA Build Level](#target-slsa-build-level)
- [⚠️ Threat Coverage (SLSA A–H)](#threat-coverage-slsa-ah)
- [🧾 Build Provenance (SLSA Provenance v1)](#build-provenance-slsa-provenance-v1)
- [📦 Software Bill of Materials (CycloneDX 1.7)](#software-bill-of-materials-cyclonedx-17)
- [🔗 Dependency Integrity & Pinning](#dependency-integrity-pinning)
- [✍️ Artifact Signing & Verification](#artifact-signing-verification)
- [🛡️ Vulnerability Management & VEX](#vulnerability-management-vex)
- [🔐 Build Platform Hardening](#build-platform-hardening)
- [✅ Consumer-Side Verification Policy](#consumer-side-verification-policy)
- [↻ Revision Log](#revision-log)

## Scope & Trust Boundary
What artifacts {{project_name}} produces and ships, and therefore what must be protected. State the deliverable artifact(s) ({{artifact_types}} — e.g. container image, npm/PyPI/crates package, binary, Helm chart), the registry/channel they are published to ({{artifact_registry}}), and the consumers who must be able to trust them ({{artifact_consumers}}). Identify the build platform / CI ({{ci_platform}}) as the **builder** in SLSA terms, the **source** (the canonical VCS repo + branch) the build draws from, and the **package** (the published, consumable artifact). Everything between "source under our control" and "artifact in the consumer's hands" is the supply chain this document hardens.

## 🎯 Target SLSA Build Level
SLSA v1.0 defines a single graded **Build track** (L0–L3). Each level is a strict superset of the one below. Record the level {{project_name}} targets and the concrete controls that achieve it — silence on a requirement is treated as "not met."

| Level | What it means (SLSA v1.0) | Protects against | Targeted here? |
|---|---|---|---|
| **Build L0** | No guarantees — the absence of SLSA. | Nothing. | {{slsa_l0}} |
| **Build L1** | Provenance exists, documenting build platform, process, and top-level inputs; producer follows a consistent build process and distributes provenance. Provenance may be incomplete and/or unsigned at L1, so it is trivial to forge. | Mistakes / unintentional release errors. | {{slsa_l1}} |
| **Build L2** | All of L1, plus the build runs on **dedicated infrastructure** (not an individual workstation) and provenance is tied to it by a **digital signature**; verification authenticates the provenance. | Tampering *after* the build; unsophisticated adversaries. | {{slsa_l2}} |
| **Build L3** | All of L2, plus a **hardened build platform**: runs cannot influence one another (isolation), and the provenance-signing secret material is inaccessible to user-defined build steps. | Tampering *during* the build; insider threats; compromised credentials; cross-tenant attacks. | {{slsa_l3}} |

**Target level for {{project_name}}:** `{{target_slsa_level}}`
**Why this level (and not higher/lower):** {{slsa_level_justification}}
*(SLSA explicitly notes higher levels trade engineering cost for stronger guarantees; for regulated or {{scale}}-scale workloads, L3 is the usual bar. Record the cost/benefit decision and any phased roadmap, e.g. "ship at L2 now, reach L3 once builds move to {{hardened_builder}}.")*

## ⚠️ Threat Coverage (SLSA A–H)
SLSA maps supply-chain threats across the stages `Source → Build → Package Registry → Consumer`, with dependencies (D) crossing all stages. For each labelled threat, state applicability and the mitigation adopted. SLSA v1.0's Build track directly addresses **E** and **F**; the others are recorded for completeness and addressed by adjacent controls.

| ID | Stage | Threat (SLSA) | Applies? | Mitigation adopted |
|---|---|---|---|---|
| **A** | Source | Submit unauthorized change (via normal SCM, no special privilege). | {{threat_a_applies}} | {{threat_a_mitigation}} *(branch protection, required reviews, signed commits)* |
| **B** | Source | Compromise source repo (admin/infra access). | {{threat_b_applies}} | {{threat_b_mitigation}} *(2FA/SSO, least-privilege admin, audit log)* |
| **C** | Source→Build | Build from a modified/unofficial source (wrong fork, branch, params). | {{threat_c_applies}} | {{threat_c_mitigation}} *(provenance records the exact source ref; verifier pins expected repo)* |
| **D** | Dependencies | Use a compromised dependency. | {{threat_d_applies}} | {{threat_d_mitigation}} *(pin by digest, verify dependency provenance recursively, SBOM — see [Dependency Integrity](#dependency-integrity-pinning))* |
| **E** | Build | Compromise the build process / inject false provenance. | {{threat_e_applies}} | {{threat_e_mitigation}} *(Build L2+: trusted control plane mints provenance; L3 hardening)* |
| **F** | Build→Package | Upload a modified package / package without proper provenance. | {{threat_f_applies}} | {{threat_f_mitigation}} *(signed provenance + artifact-digest match enforced at publish/admission)* |
| **G** | Package Registry | Compromise the package registry (admin/infra). | {{threat_g_applies}} | {{threat_g_mitigation}} *(out of SLSA v1.0 scope — registry access controls, immutable tags, transparency log)* |
| **H** | Consumer | Use a compromised package (typosquatting, post-registry tamper). | {{threat_h_applies}} | {{threat_h_mitigation}} *(consumer-side SLSA verification — see [Verification Policy](#consumer-side-verification-policy))* |

> Cross-cutting verification threats SLSA also names: **tampering with the verifier's expectations**, **forging change metadata**, and **hash collisions**. Note how the expectation config itself is protected: {{verifier_expectation_protection}}.

## 🧾 Build Provenance (SLSA Provenance v1)
Provenance is the signed statement of *how the artifact was built*. SLSA v1.0 carries it in an **in-toto attestation** envelope with `predicateType: "https://slsa.dev/provenance/v1"`. Record how {{project_name}} generates and stores provenance.

**Generator / signer:** {{provenance_generator}} *(e.g. the SLSA GitHub generator, `slsa-github-generator`, Tekton Chains, `cosign attest`, the platform's native attestation)*
**Where stored / distributed:** {{provenance_storage}} *(e.g. registry as an OCI referrer, Rekor transparency log, alongside the release artifact)*

The provenance predicate {{project_name}} emits MUST populate at least:

| in-toto / predicate field | Meaning | Value for {{project_name}} |
|---|---|---|
| `subject[].name` / `subject[].digest` | The produced artifact name + cryptographic digest (e.g. `sha256`). | {{provenance_subject}} |
| `buildDefinition.buildType` | TypeURI identifying *how* the build is performed. | {{provenance_build_type}} |
| `buildDefinition.externalParameters` | Parameters under external (user/tenant) control — incl. the source repo + ref. | {{provenance_external_params}} |
| `buildDefinition.internalParameters` | Parameters set by the build platform itself. | {{provenance_internal_params}} |
| `buildDefinition.resolvedDependencies` | Artifacts fetched at build init/execution, pinned by digest. | {{provenance_resolved_deps}} |
| `runDetails.builder.id` | TypeURI for the transitive closure of the trusted build platform. | {{provenance_builder_id}} |
| `runDetails.builder.version` | Component→version map for the builder. | {{provenance_builder_version}} |
| `runDetails.metadata.invocationId` | Unique build-invocation identifier. | {{provenance_invocation_id}} |
| `runDetails.metadata.startedOn` / `finishedOn` | RFC3339 build start/finish timestamps. | {{provenance_timestamps}} |
| `runDetails.byproducts` | Extra artifacts useful for debugging / incident response. | {{provenance_byproducts}} |

> Provenance only earns trust if it is *verified* — generating it is necessary but not sufficient. The verification gate is defined in [Consumer-Side Verification Policy](#consumer-side-verification-policy).

## 📦 Software Bill of Materials (CycloneDX 1.7)
The SBOM enumerates everything inside the artifact so downstream consumers (and your own vulnerability scanning) can reason about it. {{project_name}} emits **CycloneDX 1.7** (ECMA-424).

| BOM property | Decision for {{project_name}} |
|---|---|
| `bomFormat` / `specVersion` | `CycloneDX` / `1.7` |
| Serialization format | {{sbom_format}} *(JSON `application/vnd.cyclonedx+json`, XML, or Protobuf; `bom.json` / `*.cdx.json` is the conventional filename)* |
| `serialNumber` | Unique per-BOM URN, `urn:uuid:…`, regenerated each build. |
| `version` | BOM revision counter for a given serial. |
| BOM type(s) emitted | {{bom_types}} *(SBOM for the build; optionally SaaSBOM for service deps, ML-BOM for models, HBOM/CBOM/OBOM/VEX as needed)* |
| `metadata` | Supplier/manufacturer, `metadata.component` (the subject of the BOM), and the `tools` that generated it ({{sbom_generator}}, e.g. Syft, `cdxgen`, native build plugin). |

Each `components[]` entry MUST carry a **Package URL (`purl`)** — the canonical `pkg:<type>/<namespace>/<name>@<version>` coordinate (e.g. `pkg:npm/left-pad@1.3.0`, `pkg:pypi/requests@2.32.3`) — plus declared `licenses` and a content `hashes` digest where available. Direct and transitive relationships are recorded in the `dependencies[]` graph; `compositions[]` records completeness (e.g. whether the transitive set is complete). Components may be referenced across BOMs via a **BOM-Link** (`urn:cdx:<serialNumber>/<version>#<bom-ref>`).

**When the SBOM is generated:** {{sbom_generation_point}} *(at build time, attached to the artifact)*
**Where it is published / attested:** {{sbom_publication}} *(attached as an OCI referrer / release asset; optionally wrapped in an in-toto attestation so its provenance is itself verifiable)*

## 🔗 Dependency Integrity & Pinning
This is the front line for SLSA threat **D**. Record how third-party inputs are constrained so a build is reproducible and a swapped dependency is detected.

- **Lockfile + pinning policy:** {{lockfile_policy}} — committed lockfile ({{lockfile_name}}) with integrity hashes; **pin by digest, not by floating version range** (SLSA's explicit guidance for dependency threats).
- **Package manager + registry:** {{package_manager}} → {{dependency_registry}}; configured to reject unpinned or hash-mismatched installs.
- **Dependency-confusion defense:** {{dep_confusion_policy}} — scoped/namespaced internal packages, explicit registry routing, no implicit fallthrough to public registries for internal names.
- **Automated update + review:** {{dep_update_policy}} — e.g. Renovate/Dependabot with review-gated merges; no auto-merge of transitive bumps without a green scan.
- **Allowlist / vetting:** {{dependency_vetting}} — new direct dependencies pass a license + maintenance + known-CVE check before adoption.
- **Recursive provenance (aspirational):** {{recursive_provenance}} — where upstreams publish SLSA provenance, verify it as part of admission.

## ✍️ Artifact Signing & Verification
Signing binds the artifact, its provenance, and its SBOM to a verifiable identity (the basis of SLSA L2's "tied through a digital signature").

| Aspect | Decision |
|---|---|
| Signing tool / scheme | {{signing_tool}} *(e.g. Sigstore `cosign` keyless via OIDC, GPG, in-toto signing)* |
| Key custody | {{key_custody}} *(keyless ephemeral / KMS / hardware token; for SLSA L3 the signing key MUST be inaccessible to user build steps)* |
| Transparency log | {{transparency_log}} *(e.g. Rekor — append-only, publicly auditable record of signatures)* |
| What is signed | {{signed_objects}} *(artifact digest, provenance attestation, SBOM attestation)* |
| Identity bound | {{signing_identity}} *(the workflow/builder OIDC identity, not a long-lived personal key)* |

## 🛡️ Vulnerability Management & VEX
How known-vulnerability data is produced, triaged, and communicated. CycloneDX 1.7 carries vulnerabilities and **VEX (Vulnerability Exploitability eXchange)** natively.

- **Scanning:** {{vuln_scanning}} — SBOM-driven scanning ({{vuln_scanner}}, e.g. Grype/Trivy/osv-scanner) in CI and on a recurring schedule against the published artifact.
- **Severity gate:** {{vuln_gate_policy}} — which severities block a release ({{blocking_severity}}) vs. warn; SLA to remediate by severity.
- **VEX statements:** {{vex_policy}} — for each flagged CVE, publish a VEX assertion (`not_affected` / `affected` / `fixed` / `under_investigation`) with justification, so consumers don't chase false positives. Emitted via {{vex_format}} (CycloneDX VEX or OpenVEX).
- **Disclosure / response:** {{vuln_disclosure}} — `SECURITY.md`, contact channel, and the process for an upstream-dependency CVE that affects shipped artifacts.

## 🔐 Build Platform Hardening
The controls behind reaching SLSA L2/L3. Document the build environment itself.

- **Builder:** {{builder_platform}} — runs on dedicated, hosted infrastructure (L2 requirement), not a developer workstation.
- **Run isolation:** {{build_isolation}} — each build runs in an ephemeral, isolated environment so runs cannot influence one another (L3 requirement).
- **Hermeticity / reproducibility:** {{build_hermeticity}} — network/inputs constrained to declared, pinned dependencies; reproducible-build target if applicable.
- **Secret handling:** {{build_secret_handling}} — provenance-signing material and deploy secrets are held by the control plane and **not exposed to user-defined build steps** (L3 requirement); least-privilege OIDC over long-lived secrets.
- **Two-person / protected workflows:** {{protected_workflows}} — release workflows require review; the build definition itself is under branch protection.
- **Platform attestation:** {{platform_attestation}} — how the build platform's own trustworthiness is established (SLSA "Verifying build platforms").

## ✅ Consumer-Side Verification Policy
Provenance and signatures are worthless unprotected by enforcement. Define where verification is *required* before an artifact is used.

| Enforcement point | What is checked | Action on failure |
|---|---|---|
| Deploy / admission ({{deploy_target}}) | Valid signature; provenance `subject.digest` matches the artifact; expected `builder.id` + source repo/ref. | {{verify_fail_action}} *(block deploy)* |
| Registry pull / install | SLSA level meets `{{target_slsa_level}}`; SBOM present + scanned clean per gate. | {{registry_fail_action}} |
| CI dependency resolution | Lockfile hashes match; no unpinned inputs. | {{ci_fail_action}} |

- **Expectations source of truth:** {{expectations_source}} — where the "expected builder / expected source / required SLSA level" policy lives (e.g. a policy-as-code admission controller like Kyverno/Sigstore policy-controller; protected so it can't be silently relaxed — see verification-threats note above).
- **Verification tooling:** {{verification_tooling}} — e.g. `slsa-verifier`, `cosign verify-attestation`, policy engine at admission.
- **Break-glass / exceptions:** {{breakglass_policy}} — how an emergency unverified deploy is authorized, logged, and reverted.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
