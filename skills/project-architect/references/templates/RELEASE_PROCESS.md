---
template_name: RELEASE_PROCESS
generate_when: "decisions.production_bound == true"
required_decisions: []
optional_decisions: [release.cadence, release.versioning, release.changelog_strategy, release.announcement_channels]
depends_on: [CI_CD, DEPLOYMENT]
revision_triggers: [cicd.platform, release.cadence, release.versioning]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Release Process: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Versioning Scheme](#versioning-scheme)
- [🚀 Release Cadence](#release-cadence)
- [📝 Changelog Generation](#changelog-generation)
- [🚀 Release Branches](#release-branches)
- [Announcement Channels](#announcement-channels)
- [🚀 Hot-Fix Process](#hot-fix-process)
- [🚀 Yank / Recall Procedure](#yank-recall-procedure)
- [↻ Revision Log](#revision-log)

## Versioning Scheme
Versioning scheme chosen (semver 2.0 / calver YYYY.MM.PATCH / ZeroVer / custom) with the meaning of each segment for this project, the rule for bumping each segment, and how pre-release identifiers are used (`-alpha`, `-beta`, `-rc`). Note where the canonical version lives (package.json / Cargo.toml / VERSION file) and the bump command.

## 🚀 Release Cadence
Cadence (continuous on merge / weekly / biweekly / monthly / on-demand) with rationale, the release window (day + time zone), and the freeze policy around the release. Note the relationship to the team's planning cadence and any blackout periods (e.g., end-of-quarter, holidays).

## 📝 Changelog Generation
Changelog source of truth (`CHANGELOG.md` Keep-a-Changelog / generated from conventional commits / generated from PR labels / release-please / changesets), the format, and the workflow (who edits it, when entries are added, how unreleased entries are promoted). Link to CI_CD.md for the automation.

## 🚀 Release Branches
Branching model for releases (single trunk + tags / `release/x.y` long-lived branches / hotfix branches off tags). Cover cherry-pick rules between trunk and release branches, who can push, and the support window per release line.

## Announcement Channels
Where each release is announced (GitHub Releases / blog / Twitter or X / Mastodon / Discord / Slack / customer email / status page) and the audience per channel. Note the template content (highlights, breaking changes, migration steps, link to changelog) and the owner per channel.

## 🚀 Hot-Fix Process
The end-to-end hotfix path: how an urgent bug is triaged, the branch model (off the affected release tag), the truncated review process, the deploy steps, and the post-fix backport to trunk. Include the on-call escalation and the communication template.

## 🚀 Yank / Recall Procedure
When and how to yank a published release (registry yank for npm / cargo / PyPI, GitHub Release un-publish, container-image deletion), the customer-communication template, the rollback steps for already-deployed customers, and the post-mortem trigger. Link to DEPLOYMENT.md for the rollback runbook.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
