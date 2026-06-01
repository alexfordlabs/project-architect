---
template_name: CI_CD
generate_when: "decisions.devops.cicd != null"
required_decisions: [cicd.platform]
optional_decisions: [cicd.branch_strategy, testing.coverage_target, security.dep_scanning]
depends_on: [TESTING_STRATEGY, DEPLOYMENT]
revision_triggers: [cicd.platform, cicd.branch_strategy, testing.unit_framework, testing.e2e_framework]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# CI/CD: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🚀 CI/CD Platform](#cicd-platform)
- [🚀 Pipeline Stages](#pipeline-stages)
- [🚦 Quality Gates](#quality-gates)
- [Branch Strategy](#branch-strategy)
- [Secrets Management in CI](#secrets-management-in-ci)
- [Artifact Management](#artifact-management)
- [↻ Revision Log](#revision-log)

## 🚀 CI/CD Platform
Platform chosen (GitHub Actions / GitLab CI / CircleCI / Buildkite / Vercel / Cloudflare Workers Builds) with one-paragraph rationale and ADR link.

## 🚀 Pipeline Stages
Three numbered step lists — one each for: on PR, on merge to main, on release tag. Each step is one line stating purpose + executor (job name, container, runner).

## 🚦 Quality Gates
Required passing checks before merge / release: unit tests, integration tests, e2e tests, lint, type-check, security scan, build, bundle-size budget. Note which are blocking vs advisory.

## Branch Strategy
Branching model (trunk-based / GitFlow / GitHub Flow), naming conventions, protected branches, required reviewers, and merge style (squash / rebase / merge commit).

## Secrets Management in CI
Where CI secrets live, scoping (per env / per repo / per org), masking in logs, and the rotation procedure. Link to SECURITY_AND_COMPLIANCE.md for the broader policy.

## Artifact Management
Where build artifacts live (registry / object storage), versioning/tagging convention, retention policy, and how artifacts are promoted across environments.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
