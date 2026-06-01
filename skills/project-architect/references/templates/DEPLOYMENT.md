---
template_name: DEPLOYMENT
generate_when: "decisions.hosting.frontend != null OR decisions.hosting.backend != null"
required_decisions: [hosting.frontend, hosting.backend]
optional_decisions: [hosting.cdn, deployment.environments, deployment.iac, deployment.preview_deploys, deployment.rollback]
depends_on: []
revision_triggers: [hosting.frontend, hosting.backend, hosting.cdn, deployment.iac]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Deployment: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [⚙️ Environments](#environments)
- [🏗️ Infrastructure](#infrastructure)
- [Domain & DNS](#domain-dns)
- [⚙️ Environment Variables](#environment-variables)
- [🚀 Deployment Process](#deployment-process)
- [🚀 Rollback Strategy](#rollback-strategy)
- [🚀 Preview Deployments](#preview-deployments)
- [↻ Revision Log](#revision-log)

## ⚙️ Environments
Table: environment | URL | branch | purpose | data isolation. Typically dev / preview / staging / production with their promotion rules.

## 🏗️ Infrastructure
One subsection per service (frontend, backend, edge, database, cache, queue, CDN, object storage). Each captures: provider, configuration, scaling policy, and region(s).

## Domain & DNS
Domains owned, DNS provider, record layout (apex, www, api, status), and certificate strategy (ACME / managed).

## ⚙️ Environment Variables
Table: name | scope | description. Names and descriptions only — never values.

## 🚀 Deployment Process
Step-by-step how a change reaches production: trigger (git push / tag / manual), build, test, deploy, smoke. Reference the CI/CD platform without duplicating CI_CD.md detail.

## 🚀 Rollback Strategy
How to revert to a known-good state (atomic deploys / instant rollback / blue-green / canary), expected RTO, and the rehearsal cadence.

## 🚀 Preview Deployments
How preview / per-PR environments are created and torn down, data-scrubbing rules, and access controls.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
