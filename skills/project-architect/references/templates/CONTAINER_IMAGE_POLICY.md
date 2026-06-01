---
template_name: CONTAINER_IMAGE_POLICY
generate_when: "conditional"
required_decisions:
  - deployment.containers
  - deployment.orchestrator
optional_decisions:
  - deployment.registry
  - deployment.base_image
  - deployment.target
  - constraints.supply_chain_security
  - constraints.regulated
  - security.secrets_management
revision_triggers:
  - deployment.containers
  - deployment.orchestrator
  - deployment.registry
  - deployment.base_image
  - constraints.supply_chain_security
depends_on: []
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Container Image & Runtime Security Policy: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document defines the build-time and run-time security policy for {{project_name}}'s
> container images. The runtime portion is grounded in the **[Kubernetes Pod Security
> Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)** —
> the three cumulative policy levels (**Privileged**, **Baseline**, **Restricted**) enforced
> by the built-in **Pod Security Admission** controller (which replaced the removed
> `PodSecurityPolicy`, gone since v1.25). The build-time portion adds image-provenance and
> supply-chain controls. Every control below records THIS project's verdict and its concrete
> enforcement, not generic advice. Targets: orchestrator = `{{orchestrator}}`, registry =
> `{{registry}}`, base image = `{{base_image}}`.

## Table of contents
- [Scope & Posture](#scope-posture)
- [📦 Image Provenance & Build Policy](#image-provenance-build-policy)
- [🏷️ Tagging, Digests & Immutability](#tagging-digests-immutability)
- [🔏 Signing & Verification](#signing-verification)
- [🛡️ Chosen Pod Security Standard Level](#chosen-pod-security-standard-level)
- [🚦 Pod Security Admission Enforcement](#pod-security-admission-enforcement)
- [🔒 Baseline Controls Checklist](#baseline-controls-checklist)
- [🔐 Restricted Controls Checklist](#restricted-controls-checklist)
- [🧱 Exemptions & Privileged Workloads](#exemptions-privileged-workloads)
- [🔍 Vulnerability Scanning & Admission Gates](#vulnerability-scanning-admission-gates)
- [🔑 Secrets, Registries & Pull Credentials](#secrets-registries-pull-credentials)
- [↻ Revision Log](#revision-log)

## Scope & Posture
State exactly what images {{project_name}} ships and where they run. Cover: which services are
containerized (`deployment.containers` = {{containers_enabled}}); the orchestrator
(`{{orchestrator}}` — Kubernetes / managed K8s / Nomad / plain Docker / serverless containers);
the base image and its distro (`{{base_image}}` — e.g. `distroless`, `alpine`, `ubuntu`, a
`scratch` static binary); whether supply-chain hardening is a hard requirement
(`constraints.supply_chain_security` = {{supply_chain_status}}); and whether regulated data is in
scope (`constraints.regulated` = {{regulated_status}}). This posture sets the lens for the level
choice below. **Default stance: least privilege — start at the Restricted level and exempt only
with written justification**, because the Pod Security Standards are *cumulative* (Restricted ⊃
Baseline ⊃ Privileged) and any single container's violation fails the whole Pod.

## 📦 Image Provenance & Build Policy
Where images come from and how they are built — the first link in the supply chain.

| Control | Decision for {{project_name}} |
|---|---|
| Approved base image(s) | {{base_image}} (pinned by digest, see below) |
| Build method | {{build_method}} (multi-stage Dockerfile / buildpacks / `ko` / Bazel) |
| Non-root by construction | {{nonroot_build}} — image declares a non-zero `USER` so it satisfies Restricted without runtime overrides |
| Minimal layers / no shells | {{minimal_image}} — prefer distroless/`scratch`; drop package managers, `curl`, debug tools from the final stage |
| SBOM generation | {{sbom_tool}} (e.g. Syft, `docker sbom`, BuildKit `--sbom`) attached to every build |
| Provenance attestation | {{provenance_attestation}} — SLSA provenance / in-toto attestation produced by the CI builder |
| Reproducibility | {{reproducible_build}} — pinned dependency versions, no `latest`, no unpinned `apt-get`/`apk` installs |

> Build the final image with the **least surface possible**: no shell, no package manager,
> a non-root `USER`, and a read-only root filesystem assumption. This makes the runtime
> Restricted policy (below) trivially satisfiable instead of a fight.

## 🏷️ Tagging, Digests & Immutability
- **No mutable `latest`.** Deployments pin images by **immutable digest** (`@sha256:...`),
  not floating tags: {{digest_pinning_policy}}.
- **Tag convention:** {{tag_convention}} (e.g. `git-<sha>` + semver release tags; never reuse a tag).
- **Registry immutability:** {{registry_immutability}} — enable tag immutability / image
  lock on `{{registry}}` so a pushed tag can never be overwritten.
- **`imagePullPolicy`:** {{image_pull_policy}} — set `Always` for mutable refs, or rely on the
  digest pin so the policy is moot.

## 🔏 Signing & Verification
Establish a verifiable chain from build to admission.

- **Signing:** {{signing_tool}} (e.g. Sigstore **cosign** keyless via OIDC, or Notation/Notary v2).
- **What is signed:** {{signed_artifacts}} — the image digest, plus SBOM and provenance attestations.
- **Verification at admission:** {{verification_policy}} — a policy controller (Sigstore
  **policy-controller**, **Kyverno** `verifyImages`, or **OPA Gatekeeper**) rejects any image
  whose signature/attestation doesn't match the expected identity + issuer.
- **Trust roots:** {{trust_roots}} — which signing identities / Fulcio issuers are accepted.

> Tighten signing + admission verification to *required* when supply-chain hardening is in
> scope ({{supply_chain_status}}); otherwise document why "scan-only" is acceptable risk.

## 🛡️ Chosen Pod Security Standard Level
The Pod Security Standards define three cumulative levels. State the level {{project_name}}
targets and why.

| Level | What it does | Intended for |
|---|---|---|
| **Privileged** | Unrestricted; allows known privilege escalations. | System / infra workloads (CNI, CSI, node agents) only. |
| **Baseline** | Minimally restrictive; prevents *known* privilege escalations. | Common application workloads needing modest compatibility. |
| **Restricted** | Heavily restrictive; enforces current hardening best practices (non-root, drop ALL caps, restricted volumes, seccomp). | Security-critical / internet-facing application workloads. |

**Target level for {{project_name}}'s application namespaces:** `{{target_pss_level}}`
**Justification:** {{level_justification}}
*(Choose `restricted` unless a concrete compatibility blocker forces `baseline`; reserve
`privileged` for explicitly-listed exempt infra namespaces only.)*

## 🚦 Pod Security Admission Enforcement
Pod Security Admission is a built-in admission controller that applies a level **per namespace
via labels**, in three independent **modes**:

- **`enforce`** — the Pod is **rejected** if it violates the level.
- **`audit`** — the violation is recorded in the audit log; the Pod is **allowed**.
- **`warn`** — a warning is returned to the user; the Pod is **allowed**.

Pin each mode to a Kubernetes minor version with `*-version` so policy doesn't silently
tighten on cluster upgrade.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: {{namespace}}
  labels:
    # Hard gate — reject violators.
    pod-security.kubernetes.io/enforce: {{enforce_level}}            # privileged | baseline | restricted
    pod-security.kubernetes.io/enforce-version: {{psa_version}}      # e.g. v1.31 — pin, don't track latest

    # Forward-looking visibility: surface what a *stricter* level would block, without breaking deploys.
    pod-security.kubernetes.io/audit: {{audit_level}}
    pod-security.kubernetes.io/audit-version: {{psa_version}}
    pod-security.kubernetes.io/warn: {{warn_level}}
    pod-security.kubernetes.io/warn-version: {{psa_version}}
```

**Rollout strategy:** {{rollout_strategy}} — typically start with `warn`+`audit` at the
target level on existing namespaces, fix violations, then promote to `enforce`.
**Cluster-wide default:** {{cluster_default}} — set an `AdmissionConfiguration` default (e.g.
enforce `baseline`, warn/audit `restricted`) so unlabeled namespaces aren't unprotected.

## 🔒 Baseline Controls Checklist
The Baseline policy disallows known privilege escalations. Record this project's compliance for
each control (every container — regular, init, ephemeral — must comply; one violation fails the Pod).

| # | Control | Restricted field(s) | Required / allowed value | Compliant? |
|---|---|---|---|---|
| 1 | HostProcess (Windows) | `securityContext.windowsOptions.hostProcess` | `nil` / `false` | {{baseline_hostprocess}} |
| 2 | Host Namespaces | `spec.hostNetwork`, `spec.hostPID`, `spec.hostIPC` | `nil` / `false` | {{baseline_host_ns}} |
| 3 | Privileged Containers | `securityContext.privileged` | `nil` / `false` | {{baseline_privileged}} |
| 4 | Capabilities (add) | `securityContext.capabilities.add` | only the Baseline-allowed set (`AUDIT_WRITE`, `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `FSETID`, `KILL`, `MKNOD`, `NET_BIND_SERVICE`, `SETFCAP`, `SETGID`, `SETPCAP`, `SETUID`, `SYS_CHROOT`) | {{baseline_caps}} |
| 5 | HostPath Volumes | `spec.volumes[*].hostPath` | forbidden (`nil`) | {{baseline_hostpath}} |
| 6 | Host Ports | `containers[*].ports[*].hostPort` | `nil` / `0` | {{baseline_hostports}} |
| 7 | AppArmor | `securityContext.appArmorProfile.type` | `nil` / `RuntimeDefault` / `Localhost` | {{baseline_apparmor}} |
| 8 | SELinux | `securityContext.seLinuxOptions.type` (+ no custom `user`/`role`) | `""` / `container_t` / `container_init_t` / `container_kvm_t` / `container_engine_t` | {{baseline_selinux}} |
| 9 | /proc Mount Type | `securityContext.procMount` | `nil` / `Default` | {{baseline_procmount}} |
| 10 | Seccomp | `securityContext.seccompProfile.type` | `nil` / `RuntimeDefault` / `Localhost` (never `Unconfined`) | {{baseline_seccomp}} |
| 11 | Sysctls | `securityContext.sysctls[*].name` | only the safe-namespaced allowlist (e.g. `net.ipv4.ip_local_port_range`, `kernel.shm_rmid_forced`) | {{baseline_sysctls}} |

**Notes / known deviations:** {{baseline_notes}}

## 🔐 Restricted Controls Checklist
The Restricted policy is Baseline **plus** the hardening below. Required when
`{{target_pss_level}}` is `restricted`.

| # | Control | Restricted field(s) | Required value | Compliant? |
|---|---|---|---|---|
| 1 | Volume Types | `spec.volumes[*]` | only `configMap`, `csi`, `downwardAPI`, `emptyDir`, `ephemeral`, `persistentVolumeClaim`, `projected`, `secret` | {{restricted_volumes}} |
| 2 | Privilege Escalation | `securityContext.allowPrivilegeEscalation` | `false` (explicit, on every container) | {{restricted_no_priv_esc}} |
| 3 | Running as Non-root | `securityContext.runAsNonRoot` | `true` | {{restricted_nonroot}} |
| 4 | runAsUser | `securityContext.runAsUser` | non-zero (must not be `0`) | {{restricted_runasuser}} |
| 5 | Seccomp (explicit) | `securityContext.seccompProfile.type` | `RuntimeDefault` or `Localhost` (must be set, not absent) | {{restricted_seccomp}} |
| 6 | Capabilities (drop) | `securityContext.capabilities.drop` | must include `ALL`; only `NET_BIND_SERVICE` may be re-added | {{restricted_caps}} |

**Canonical compliant `securityContext`** (the shape every {{project_name}} workload should
carry — adapt the placeholders):

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: {{run_as_user}}        # non-zero
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: {{container_name}}
      image: {{registry}}/{{image_name}}@sha256:{{image_digest}}
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: {{read_only_root_fs}}   # recommended hardening (not a PSS control)
        runAsNonRoot: true
        capabilities:
          drop: ["ALL"]
          # add: ["NET_BIND_SERVICE"]   # only if binding a privileged port; otherwise omit
```

> `readOnlyRootFilesystem` is **not** part of the Pod Security Standards but is a recommended
> complementary hardening; pair it with `emptyDir` mounts for any writable paths.

**Notes / known deviations:** {{restricted_notes}}

## 🧱 Exemptions & Privileged Workloads
Some infra workloads genuinely need `privileged`/`baseline`. List every exemption explicitly —
no silent escape hatches.

| Workload / namespace | Required level | Reason | Compensating control | Owner |
|---|---|---|---|---|
| {{exempt_workload_1}} | {{exempt_level_1}} | {{exempt_reason_1}} | {{exempt_compensation_1}} | {{exempt_owner_1}} |
| {{additional_exemptions}} | … | … | … | … |

PSA exemptions (by `usernames`, `runtimeClassNames`, or `namespaces` in the
`AdmissionConfiguration`) must be reviewed here: {{psa_exemption_config}}. Prefer per-namespace
labels over global exemptions.

## 🔍 Vulnerability Scanning & Admission Gates
Images are scanned at build and (optionally) re-scanned at admission/runtime.

- **Build-time scanner:** {{scan_tool}} (e.g. Trivy, Grype, Snyk, registry-native scanning).
- **Severity gate:** {{scan_gate}} — which CVE severities **fail the pipeline** (e.g. block on
  fixable `CRITICAL`/`HIGH`), and the documented exception/waiver process.
- **Admission policy:** {{admission_policy_engine}} — Kyverno / OPA Gatekeeper / Validating
  Admission Policy rules that enforce registry allowlists, digest pinning, and signature
  verification at deploy time, complementing PSA.
- **Drift / runtime:** {{runtime_security}} — continuous re-scan of running images for newly
  disclosed CVEs and (optionally) a runtime threat detector (e.g. Falco).
- **Patch cadence:** {{patch_cadence}} — base-image rebuild + redeploy SLA when a relevant CVE
  is published.

## 🔑 Secrets, Registries & Pull Credentials
- **Registry:** `{{registry}}` — private by default; public mirrors only for vetted base images.
- **Pull credentials:** {{pull_credentials}} — `imagePullSecrets` / workload-identity (IRSA,
  Workload Identity, federated OIDC) rather than long-lived registry passwords.
- **No secrets baked into images.** Secrets reach the container at runtime via
  {{secrets_delivery}} (mounted `secret` volume / CSI secrets-store / external secrets
  operator / 1Password Connect) — never `ENV`-burned into a layer or committed to the Dockerfile.
- **Build-arg hygiene:** {{build_arg_hygiene}} — no credentials in `ARG`/`ENV`; use BuildKit
  secret mounts (`--mount=type=secret`) so they never persist in image history.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
