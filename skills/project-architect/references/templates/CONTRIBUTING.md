---
template_name: CONTRIBUTING
generate_when: "decisions.open_source == true"
required_decisions: []
optional_decisions: [contributing.cla, contributing.code_of_conduct, contributing.review_process]
depends_on: []
revision_triggers: [cicd.branch_strategy, open_source]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Contributing: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🔐 Code of Conduct](#code-of-conduct)
- [CLA / DCO](#cla-dco)
- [Issue Templates](#issue-templates)
- [PR Templates](#pr-templates)
- [Review Process & Maintainers](#review-process-maintainers)
- [🚀 Release Cadence](#release-cadence)
- [Communication Channels](#communication-channels)
- [↻ Revision Log](#revision-log)

## 🔐 Code of Conduct
Link to the project's Code of Conduct (typically `CODE_OF_CONDUCT.md` at the repo root, often Contributor Covenant v2.1). Name the enforcement contact (alias or email), the response SLA for reports, and the escalation path.

## CLA / DCO
The contributor-licensing model in use (CLA / DCO / neither) with rationale and link. Cover how contributors sign (CLA-bot / `Signed-off-by` trailer), corporate-vs-individual handling, and the consequence for unsigned PRs.

## Issue Templates
The issue types accepted (bug, feature request, security report, docs) with the template file under `.github/ISSUE_TEMPLATE/` and the triage policy. Note the route for security reports (private channel, not public issues) and the SLA per issue type.

## PR Templates
The default PR template (`.github/pull_request_template.md`) with the required checklist sections: description, linked issue, test plan, screenshots/recordings for UI changes, breaking-change call-out, and changelog entry. Note any required labels and the auto-assignment rules.

## Review Process & Maintainers
Reviewer expectations: number of required approvals, required reviewer roles (CODEOWNERS), review SLA, and the etiquette for nits vs blockers. List the current maintainer set (link to CODEOWNERS or MAINTAINERS.md) and the path to becoming a maintainer.

## 🚀 Release Cadence
How often releases ship to the public registry, the relationship between merges and releases, and the announcement path. Link to RELEASE_PROCESS.md for the operational detail.

## Communication Channels
Where contributors talk: Discord / Slack / Discussions / IRC / mailing list, with topic per channel and the response-time expectation. Include the maintainer office-hours schedule if any, and the path to escalate a stalled PR.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
