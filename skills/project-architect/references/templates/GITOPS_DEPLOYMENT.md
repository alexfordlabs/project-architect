---
template_name: GITOPS_DEPLOYMENT
generate_when: "conditional"
required_decisions:
  - deployment.gitops
optional_decisions:
  - deployment.orchestrator
  - deployment.target
  - deployment.registry
  - deployment.secrets_manager
  - deployment.iac
  - observability.stack
depends_on: []
revision_triggers:
  - deployment.gitops
  - deployment.orchestrator
  - deployment.target
  - deployment.registry
  - deployment.secrets_manager
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# GitOps Deployment: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This deployment design follows the **[OpenGitOps Principles v1.0.0](https://opengitops.dev/)**,
> the vendor-neutral standard maintained by the **GitOps Working Group under the Cloud Native
> Computing Foundation (CNCF)**. OpenGitOps defines exactly **four** principles — *Declarative*,
> *Versioned and Immutable*, *Pulled Automatically*, *Continuously Reconciled* — and a glossary
> ([open-gitops/documents](https://github.com/open-gitops/documents)) that fixes the meaning of
> *Software System*, *Desired State*, *State Store*, and *Reconciliation*. Every choice below is
> justified against those four principles; if a choice violates one, it is not GitOps.

## Table of contents
- [📜 The Four OpenGitOps Principles](#the-four-opengitops-principles)
- [🧭 Glossary Mapping (this project)](#glossary-mapping-this-project)
- [🗂️ State Store: Git as Source of Truth](#state-store-git-as-source-of-truth)
- [🤖 Reconciliation Controller](#reconciliation-controller)
- [🌲 Repository Structure](#repository-structure)
- [🌍 Environments & Promotion](#environments-promotion)
- [🔁 Drift Detection & Auto-Heal](#drift-detection-auto-heal)
- [🔐 Secrets in GitOps](#secrets-in-gitops)
- [🚦 Sync, Health & Progressive Delivery](#sync-health-progressive-delivery)
- [🚪 Bootstrap & Access Control](#bootstrap-access-control)
- [✅ GitOps Conformance Checklist](#gitops-conformance-checklist)
- [↻ Revision Log](#revision-log)

## 📜 The Four OpenGitOps Principles

These are the principles verbatim from OpenGitOps v1.0.0. The right column records how
{{project_name}} satisfies each one — a blank means the design is not yet GitOps-conformant.

| # | Principle | Definition (OpenGitOps v1.0.0) | How {{project_name}} satisfies it |
|---|---|---|---|
| 1 | **Declarative** | "A system managed by GitOps must have its desired state expressed declaratively." | {{declarative_approach}} |
| 2 | **Versioned and Immutable** | "Desired state is stored in a way that enforces immutability, versioning and retains a complete version history." | {{versioning_approach}} |
| 3 | **Pulled Automatically** | "Software agents automatically pull the desired state declarations from the source." | {{pull_approach}} |
| 4 | **Continuously Reconciled** | "Software agents continuously observe actual system state and attempt to apply the desired state." | {{reconciliation_approach}} |

> **Pull, not push.** Principle 3 is the line that separates GitOps from CI-driven `kubectl apply`.
> A CI pipeline that *pushes* manifests with cluster credentials is **not** GitOps — it inverts the
> trust boundary and skips continuous reconciliation. The reconciler must run *inside* (or adjacent to)
> the target and **pull** the desired state. State the chosen agent in
> [Reconciliation Controller](#reconciliation-controller).

## 🧭 Glossary Mapping (this project)

Bind the OpenGitOps glossary terms to concrete artifacts so the rest of this doc is unambiguous.

| OpenGitOps term | Glossary meaning | Concrete instance for {{project_name}} |
|---|---|---|
| **Software System** | Runtime environments + management agents + access/management policies | {{software_system}} (e.g. `{{deployment_target}}` cluster + the reconciler + RBAC policies) |
| **Desired State** | "The aggregate of all configuration data that is sufficient to recreate the system so that instances of the system are behaviourally indistinguishable." | {{desired_state_location}} (the Git repo/path holding all manifests) |
| **State Store** | "A system for storing immutable versions of desired state declarations … with access control and auditing." | {{state_store}} (e.g. the Git provider — GitHub / GitLab / Gitea) |
| **Reconciliation** | "The process of ensuring the actual state of a system matches its desired state … triggered whenever there is a divergence." | {{reconciliation_owner}} (the controller named below) |

## 🗂️ State Store: Git as Source of Truth

| Property | Decision for {{project_name}} |
|---|---|
| Config repo(s) | {{config_repos}} (the state store; **the single source of truth for runtime state**) |
| App-code vs config separation | {{repo_separation}} — typically separate the app source repo from the config/state repo so a code build never directly mutates the cluster |
| Branching model | {{branching_model}} (e.g. trunk-based; environment-per-directory rather than environment-per-branch — see [Environments](#environments-promotion)) |
| Immutability enforcement | {{immutability_controls}} (protected branches, required PR review, signed commits, no force-push) |
| Auditability | {{audit_trail}} — every change is a reviewable, revertable commit; `git log` IS the deploy history |

> **Versioned and Immutable (Principle 2) in practice.** The State Store must *retain a complete
> version history*. Do not bypass Git: never `kubectl edit`/`apply` against the live cluster, never
> let a CI job patch resources out-of-band. If the only way to change the running system is to merge
> a commit, then `git revert` is a guaranteed rollback and the cluster's whole history is auditable.

## 🤖 Reconciliation Controller

The **Software Agent** that pulls desired state and reconciles it. For Kubernetes targets this is
typically [Argo CD](https://argo-cd.readthedocs.io/) or [Flux](https://fluxcd.io/) (both are CNCF
Graduated projects).

| Property | Decision |
|---|---|
| Tool | `{{deployment_gitops}}` (e.g. Argo CD / Flux / Rancher Fleet) |
| Where the agent runs | {{agent_location}} — in-cluster (pull model) so cluster credentials never leave the target |
| Sync trigger | {{sync_trigger}} — polling interval and/or webhook-driven, plus on-divergence (drift) |
| Templating / rendering | {{rendering_tool}} (e.g. Helm / Kustomize / Jsonnet / plain YAML) rendered *by the agent*, not in CI |
| Manifest source ref | {{source_ref}} — pin to a branch, tag, or commit SHA the agent watches |

**Argo CD specifics (if chosen):** the unit of deployment is an `Application` CR; a parent
`Application` that points at a directory of child `Application`s is the **App-of-Apps** pattern (or use
`ApplicationSet` to template many Applications from a generator). Sync state is reported as
`Synced`/`OutOfSync` and health as `Healthy`/`Degraded`/`Progressing`.

**Flux specifics (if chosen):** composed controllers — `source-controller` (a `GitRepository` /
`OCIRepository` source), `kustomize-controller` (`Kustomization`) and/or `helm-controller`
(`HelmRelease`). Reconciliation interval is set per-object via `spec.interval`.

Chosen pattern for {{project_name}}: {{controller_pattern}}

## 🌲 Repository Structure

Lay out the config repo so each environment's desired state is a distinct, reviewable directory and
a single root object renders the whole system.

```text
{{config_repo_root}}/
├── apps/                          # per-application manifests (Helm/Kustomize bases)
│   ├── {{app_1}}/
│   │   ├── base/                  # environment-agnostic base
│   │   └── overlays/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   └── {{app_2}}/...
├── infrastructure/                # cluster-scoped: ingress, cert-manager, CRDs, policy
│   └── {{infra_components}}/
├── clusters/                      # the App-of-Apps / Flux Kustomization entrypoints
│   ├── {{cluster_dev}}/           # root that points the agent at apps/ + infrastructure/
│   ├── {{cluster_staging}}/
│   └── {{cluster_prod}}/
└── README.md
```

> **Environment-per-directory, not environment-per-branch.** Long-lived per-environment branches
> drift and make promotions a merge-conflict exercise. Prefer directory/overlay separation on a
> single trunk so a promotion is a single PR that copies a rendered/version pin forward. Chosen
> layout rationale: {{layout_rationale}}

## 🌍 Environments & Promotion

| Environment | Cluster/Namespace | Source path | Auto-sync? | Promotion gate |
|---|---|---|---|---|
| {{env_dev}} | {{env_dev_target}} | `{{env_dev_path}}` | {{env_dev_autosync}} (usually yes) | {{env_dev_gate}} |
| {{env_staging}} | {{env_staging_target}} | `{{env_staging_path}}` | {{env_staging_autosync}} | {{env_staging_gate}} |
| {{env_prod}} | {{env_prod_target}} | `{{env_prod_path}}` | {{env_prod_autosync}} (often manual/gated) | {{env_prod_gate}} |

**Promotion mechanism:** {{promotion_mechanism}} — how a tested image tag / chart version moves
from one environment's desired state to the next (e.g. PR that bumps the image tag in the prod
overlay; an image-update automation that opens that PR; a release-please / renovate bot). The
promotion artifact is **always a commit**, never a manual cluster action.

## 🔁 Drift Detection & Auto-Heal

This is **Principle 4 (Continuously Reconciled)** operationalized: the agent *continuously observes
actual state* and corrects any divergence from the State Store.

| Property | Decision |
|---|---|
| Drift detection | {{drift_detection}} — agent compares live cluster state vs desired state on every reconcile |
| Self-heal / auto-prune | {{self_heal}} — should the agent automatically revert out-of-band changes and prune deleted resources? |
| Reconcile interval | {{reconcile_interval}} (e.g. Flux `spec.interval: 5m`; Argo CD `timeout.reconciliation`) |
| Manual-change policy | {{manual_change_policy}} — break-glass `kubectl edit` is reverted on next sync; document the escape hatch |

> **Trade-off to decide explicitly:** auto-heal (Argo CD `selfHeal: true` / Flux default) gives true
> closed-loop convergence — any manual hotfix is erased on the next reconcile, which is correct GitOps
> but can surprise operators mid-incident. If you allow break-glass, define how a manual change is
> captured back into Git so the next reconcile doesn't undo a needed fix: {{breakglass_workflow}}

## 🔐 Secrets in GitOps

Secrets are the hardest part of GitOps: the State Store is Git, but plaintext secrets must **never**
be committed. Pick a pattern that keeps secret *material* out of Git while keeping a *declarative,
versioned* reference in Git (so Principles 1 and 2 still hold).

| Approach | How it preserves GitOps | Decision for {{project_name}} |
|---|---|---|
| **Sealed Secrets** (Bitnami) | Commit a `SealedSecret` encrypted with the cluster controller's public key; only the in-cluster controller can decrypt → cipher-text is safe in Git. | {{sealed_secrets_use}} |
| **SOPS** (+ age/KMS, often via Flux or `ksops`) | Encrypt values in-place in the YAML with `age`/cloud-KMS keys; the agent decrypts at apply time. | {{sops_use}} |
| **External Secrets Operator (ESO)** | Commit only an `ExternalSecret` *reference*; ESO fetches the real value at runtime from an external store. | {{eso_use}} |
| **External store backing ESO/SOPS** | The actual secret material lives outside Git entirely. | `{{deployment_secrets_manager}}` (e.g. 1Password Connect / Vault / AWS Secrets Manager / cloud KMS) |

Chosen secrets architecture: {{secrets_architecture}}

> **Never** commit a raw Kubernetes `Secret` with real values — base64 is encoding, not encryption.
> The committed artifact must be either encrypted (Sealed Secrets / SOPS) or a pointer (ESO). Key
> material (the Sealed Secrets controller key, SOPS age/KMS keys, the ESO store credential) is the one
> bootstrap secret that lives *outside* the GitOps loop: {{key_material_location}}.

## 🚦 Sync, Health & Progressive Delivery

| Property | Decision |
|---|---|
| Sync policy | {{sync_policy}} (automated vs manual sync; ordered sync waves / dependency ordering) |
| Health assessment | {{health_assessment}} — how the agent decides a resource/app is Healthy before marking the sync complete |
| Rollback | {{rollback_strategy}} — `git revert` the offending commit; the agent reconciles back to the prior desired state |
| Progressive delivery | {{progressive_delivery}} (e.g. Argo Rollouts / Flagger for canary / blue-green; or none) |
| Notifications | {{notifications}} — where sync failures / degraded health are surfaced (Slack, PagerDuty) |

## 🚪 Bootstrap & Access Control

| Property | Decision |
|---|---|
| Bootstrap method | {{bootstrap_method}} (e.g. `flux bootstrap github`, Argo CD install + root App-of-Apps) |
| Agent → Git auth | {{git_auth}} (deploy key / GitHub App / token) — least-privilege, read-only where possible |
| Git → agent webhook | {{webhook_config}} (optional, to make reconciliation near-instant on merge) |
| Repo access policy | {{repo_access_policy}} — who can merge to the prod path; required reviewers; CODEOWNERS |
| Multi-cluster | {{multi_cluster}} — hub-and-spoke (one agent managing many) vs agent-per-cluster |

## ✅ GitOps Conformance Checklist

A gate to confirm {{project_name}} actually *is* GitOps before declaring this design done. Each item
maps to an OpenGitOps principle:

- [ ] **(P1 Declarative)** The entire desired state is expressed declaratively — no imperative deploy scripts as the source of truth.
- [ ] **(P2 Versioned & Immutable)** All desired state lives in the Git State Store with full history; branches protected; no out-of-band cluster edits.
- [ ] **(P3 Pulled Automatically)** A `{{deployment_gitops}}` agent runs in/near the target and **pulls** state — CI never holds cluster credentials to push.
- [ ] **(P4 Continuously Reconciled)** Drift detection is on; the agent continuously observes and re-applies desired state.
- [ ] No plaintext secrets in Git — secret material flows through `{{deployment_secrets_manager}}` / encrypted-at-rest.
- [ ] Promotions between environments are **commits/PRs**, not manual cluster actions.
- [ ] Rollback is a `git revert` and converges automatically.
- [ ] Bootstrap key material (controller keys / SOPS keys) is documented and stored outside the loop.
- [ ] `{{additional_checklist_item}}`

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
