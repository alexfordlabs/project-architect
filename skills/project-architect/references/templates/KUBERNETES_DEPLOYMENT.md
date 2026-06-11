---
template_name: KUBERNETES_DEPLOYMENT
generate_when: "conditional"
required_decisions: [deployment.orchestrator]
optional_decisions:
  - deployment.target
  - deployment.registry
  - deployment.ingress
  - deployment.secrets_manager
  - deployment.iac
  - deployment.gitops
  - observability.stack
depends_on: []
revision_triggers:
  - deployment.orchestrator
  - deployment.target
  - deployment.registry
  - deployment.ingress
  - deployment.secrets_manager
  - deployment.gitops
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Kubernetes Deployment: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This deployment design follows the Kubernetes
> *[Configuration Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)*.
> The governing rule from that guidance: **keep configuration minimal** — do not set values
> that Kubernetes already defaults, version-control every manifest, and prefer declarative
> `kubectl apply` over imperative commands. Every choice below is justified against that bar.

## Table of contents
- [🎯 Cluster Target & Topology](#cluster-target-topology)
- [📦 Workload Resources](#workload-resources)
- [🌐 Services & Networking](#services-networking)
- [🚪 Ingress & External Access](#ingress-external-access)
- [🏷️ Labels, Annotations & Naming](#labels-annotations-naming)
- [🖼️ Container Images & Registry](#container-images-registry)
- [📊 Resource Requests, Limits & Probes](#resource-requests-limits-probes)
- [🔐 Configuration & Secrets](#configuration-secrets)
- [🛡️ Security & Policy](#security-policy)
- [♻️ Rollout, Rollback & GitOps](#rollout-rollback-gitops)
- [👁️ Observability](#observability)
- [✅ Pre-Apply Checklist](#pre-apply-checklist)
- [↻ Revision Log](#revision-log)

## 🎯 Cluster Target & Topology

| Property | Decision for {{project_name}} |
|---|---|
| Cluster target | `{{deployment_target}}` (e.g. EKS / GKE / AKS / k3s / kind) |
| Kubernetes version | `{{k8s_version}}` — pin to a supported minor; check skew policy |
| Namespace(s) | `{{namespaces}}` — never deploy app workloads into `default` or `kube-system` |
| Environments | `{{environments}}` (e.g. dev / staging / prod) and how they map to clusters or namespaces |
| Multi-tenancy / isolation | {{tenancy_model}} |

> **Use the latest stable API version.** Run `kubectl api-resources` to list the
> available kinds and their `apiVersion`. Avoid alpha/beta `apiVersion`s for
> production resources — they may be removed without a stable migration path.

## 📦 Workload Resources

Pick the controller that matches each workload's lifecycle. **Never create naked Pods** —
a Pod without an owning controller is not rescheduled if its node dies and is not
recovered automatically (acceptable only for one-off debugging).

| Workload | Kind | Why this kind |
|---|---|---|
| {{workload_1_name}} | `{{workload_1_kind}}` | {{workload_1_rationale}} |
| {{workload_2_name}} | `{{workload_2_kind}}` | {{workload_2_rationale}} |
| {{additional_workloads}} | … | … |

Kind selection per the guidance:

- **`Deployment`** — for apps that should *always be running* and are stateless. Manages a
  `ReplicaSet`, keeps the desired replica count available, and supports the default
  `RollingUpdate` strategy for instant rollout and rollback.
- **`StatefulSet`** — for workloads needing stable network identity and stable persistent
  storage (databases, queues, anything with per-replica state).
- **`Job` / `CronJob`** — for tasks that should *run to completion*: database migrations,
  batch processing, scheduled work. Jobs retry on pod failure and report success when done.
- **`DaemonSet`** — for one-pod-per-node agents (log shippers, node exporters).

**Replicas / scaling:** {{replica_strategy}} — base replica count, HorizontalPodAutoscaler
targets (CPU/memory/custom metrics), and `PodDisruptionBudget` for availability during drains.

## 🌐 Services & Networking

> **Create the Service *before* its backing workloads.** When the kubelet starts a Pod, it
> injects a set of environment variables for each active Service; a Pod created *before* its
> Service exists will be missing them. Better still, **rely on DNS** (the cluster DNS add-on
> resolves `<svc>.<namespace>.svc.cluster.local`) for discovery — it works regardless of
> creation order, so you don't have to depend on the injected env vars at all.

| Service | Type | Selector labels | Notes |
|---|---|---|---|
| {{service_1_name}} | `{{service_1_type}}` (ClusterIP / NodePort / LoadBalancer / headless) | {{service_1_selector}} | {{service_1_notes}} |
| {{additional_services}} | … | … | … |

Networking constraints (per best practices):

- **Do NOT set `hostPort`** unless absolutely required — it bypasses normal networking and
  constrains scheduling (no two Pods may claim the same `hostPort` on a node).
- **Do NOT set `hostNetwork: true`** unless there's a specific host-networking need.
- **NetworkPolicy:** {{network_policy}} — default-deny ingress/egress where supported, then
  allow only the flows the [Services](#services-networking) table requires.
- **Service mesh (if any):** {{service_mesh}} (e.g. Istio / Linkerd / none) and what it provides
  (mTLS, traffic shaping, retries).

## 🚪 Ingress & External Access

| Property | Decision |
|---|---|
| Ingress controller / Gateway | `{{deployment_ingress}}` (e.g. ingress-nginx / Gateway API / cloud LB) |
| Hostnames / routes | {{ingress_routes}} |
| TLS termination | {{tls_strategy}} (cert-manager + issuer / cloud-managed certs) |
| External DNS | {{external_dns}} |

> Prefer the **Gateway API** (`gateway.networking.k8s.io`) for new clusters where the
> controller supports it; fall back to `networking.k8s.io/v1 Ingress` otherwise. State the
> chosen API and version explicitly.

## 🏷️ Labels, Annotations & Naming

Apply **semantic labels consistently** across every manifest so controllers select the right
Pods and `kubectl` queries work. The best-practices baseline set:

```yaml
metadata:
  labels:
    app: {{app_label}}            # name of the application
    release: {{release_label}}    # release / version, e.g. v1.0
    environment: {{env_label}}    # e.g. production
    tier: {{tier_label}}          # e.g. frontend / backend / cache
```

- **Recommended common labels:** prefer the `app.kubernetes.io/*` set
  (`app.kubernetes.io/name`, `/instance`, `/version`, `/component`, `/part-of`, `/managed-by`)
  for tooling interop in addition to the short labels above. Chosen convention: {{label_convention}}
- **Annotations** describe *why* something exists and are copied into the API for team
  visibility — the most useful is `kubernetes.io/description`. Annotations to standardize:
  {{annotation_convention}}
- **Naming convention** for resources: {{naming_convention}}

## 🖼️ Container Images & Registry

| Property | Decision |
|---|---|
| Registry | `{{deployment_registry}}` (e.g. GHCR / ECR / GAR / Docker Hub) |
| Image reference convention | {{image_naming}} — repo/path + **explicit version tag** |
| Pull secrets | {{image_pull_secrets}} |

> **Never use the `:latest` tag in production.** It is ambiguous — you can't tell which
> build is running, which makes rollbacks and debugging unreliable. Always pin an explicit
> tag (or, more robustly, a digest): `image: {{image_repo}}:{{image_tag}}` (e.g. `myapp:v1.2.3`)
> or `image: {{image_repo}}@sha256:{{image_digest}}`.

> **`imagePullPolicy`:**
> - `IfNotPresent` — default for non-`:latest` tags; use for production images with explicit
>   versions. Pulls only if the image isn't already on the node.
> - `Always` — default for the `:latest` tag; use only during development.
>
> Production block to mirror:
> ```yaml
> containers:
> - name: {{container_name}}
>   image: {{image_repo}}:{{image_tag}}
>   imagePullPolicy: IfNotPresent
> ```

## 📊 Resource Requests, Limits & Probes

Set requests/limits so the scheduler can place Pods and the kubelet can enforce QoS. Keep
config minimal — only override defaults that matter for {{project_name}}.

| Workload | CPU request/limit | Memory request/limit | QoS class |
|---|---|---|---|
| {{workload_1_name}} | {{workload_1_cpu}} | {{workload_1_mem}} | {{workload_1_qos}} |
| {{additional_workloads}} | … | … | … |

- **Liveness probe:** {{liveness_probe}} — restarts a wedged container.
- **Readiness probe:** {{readiness_probe}} — gates traffic until the Pod can serve.
- **Startup probe:** {{startup_probe}} — protects slow-starting containers from premature liveness kills.

## 🔐 Configuration & Secrets

> **Group related objects in one manifest file** (Deployment + Service + ConfigMap for one
> component) and apply directories declaratively: `kubectl apply -f {{manifest_dir}}/`.
> Write configs in **YAML, not JSON**, and for YAML booleans use only `true` / `false`
> (quote any value that looks boolean, e.g. `"yes"`).

| Concern | Mechanism for {{project_name}} |
|---|---|
| Non-secret config | `ConfigMap` — {{configmap_strategy}} |
| Secret material | `{{deployment_secrets_manager}}` (e.g. External Secrets Operator / Sealed Secrets / Vault / SOPS) |
| Secret injection | {{secret_injection}} (env / mounted volume / CSI driver) |
| Rotation | {{secret_rotation}} |

> Plaintext `Secret` objects are only base64-encoded, not encrypted at rest by default —
> enable encryption-at-rest on the cluster and/or use a dedicated secrets manager. Never
> commit raw `Secret` manifests with real values to version control.

## 🛡️ Security & Policy

- **`securityContext`:** {{security_context}} — run as non-root, drop Linux capabilities,
  `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false` where feasible.
- **Pod Security Admission:** {{pod_security_level}} — target standard (`privileged` /
  `baseline` / `restricted`) enforced per namespace.
- **RBAC & ServiceAccounts:** {{rbac_model}} — least-privilege ServiceAccount per workload;
  no use of the namespace `default` ServiceAccount for app pods.
- **Policy engine (optional):** {{policy_engine}} (e.g. Kyverno / OPA Gatekeeper) for admission rules.
- **Supply chain:** {{supply_chain}} — image scanning, signature verification, provenance.

## ♻️ Rollout, Rollback & GitOps

| Property | Decision |
|---|---|
| Manifest source of truth | {{manifest_source}} — Git, **never** apply from a laptop ad hoc |
| Templating / packaging | {{packaging_tool}} (e.g. Helm / Kustomize / raw manifests) |
| Delivery method | `{{deployment_gitops}}` (e.g. Argo CD / Flux / CI `kubectl apply`) |
| Rollout strategy | {{rollout_strategy}} (RollingUpdate / Blue-Green / Canary) |
| Rollback procedure | {{rollback_procedure}} (`kubectl rollout undo` / Git revert + reconcile) |

> Store all configuration in **version control** so any change can be reviewed and reverted
> to a previous commit. Declarative `kubectl apply` (or a GitOps reconciler) over a versioned
> directory is the canonical path; imperative `kubectl create/edit/scale` is for break-glass only.

## 👁️ Observability

- **Metrics:** {{metrics_stack}} (e.g. Prometheus + kube-state-metrics) and which SLIs are tracked.
- **Logs:** {{logging_stack}} — aggregation target and retention.
- **Traces:** {{tracing_stack}} (if applicable).
- **Dashboards / alerts:** {{dashboards_alerts}} — what pages on-call and the alert thresholds.

## ✅ Pre-Apply Checklist

A gate to run before `kubectl apply` to each environment. Confirm each item for {{project_name}}:

- [ ] No naked Pods — every workload has an owning controller.
- [ ] Every image uses an explicit version tag/digest (no `:latest` in prod) with the right `imagePullPolicy`.
- [ ] Services exist before/with their backing workloads, or discovery is DNS-based.
- [ ] No stray `hostPort` / `hostNetwork: true`.
- [ ] Semantic labels (`app`, `release`, `environment`, `tier`) present and consistent.
- [ ] Requests/limits and liveness/readiness probes set on every container.
- [ ] No raw secrets committed; secrets flow through `{{deployment_secrets_manager}}`.
- [ ] Manifests are version-controlled and applied via `{{deployment_gitops}}` (not from a desktop).
- [ ] `apiVersion`s are the latest stable for each kind (`kubectl api-resources`).
- [ ] `{{additional_checklist_item}}`

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
