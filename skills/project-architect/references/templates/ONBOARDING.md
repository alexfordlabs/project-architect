---
template_name: ONBOARDING
generate_when: "decisions.team_size != 'solo'"
required_decisions: []
optional_decisions: [onboarding.target_time_to_first_pr, onboarding.required_tools]
depends_on: [CLAUDE_MD_ROOT]
revision_triggers: [language.primary, frontend.framework, backend.framework]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Onboarding: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Setup Steps](#setup-steps)
- [🔧 Required Tools](#required-tools)
- [Local-Run Walk-Through](#local-run-walk-through)
- [Common Pitfalls](#common-pitfalls)
- [First-Task Recommendations](#first-task-recommendations)
- [Where to Ask Questions](#where-to-ask-questions)
- [↻ Revision Log](#revision-log)

## Setup Steps
A numbered, 1-2-hour-target checklist that takes a new contributor from a fresh laptop to a passing local test run. Each step is one line of action with the expected output. Cover access (repo, secrets, services), clone, install, env config, bootstrap, and verify. Mention the target time-to-first-PR and what to skip on day one.

## 🔧 Required Tools
Versioned tool list with install command per OS (macOS / Linux / Windows). Cover language runtimes, package managers, container runtime, database CLI, CLI tools for the chosen cloud, and any project-specific binaries. Pin every version (or specify the version-manager file that pins it). Link to CLAUDE_MD_ROOT.md for the agent-tooling subset.

## Local-Run Walk-Through
Concrete commands to start each runnable surface (web app, API, workers, jobs, mobile dev build) and how to verify each is healthy. Include sample data seeding and the path to log in as a test user. Note the URL/port for each surface and the way to switch environments.

## Common Pitfalls
Issues new contributors hit in the first week (port conflicts, missing env vars, Node/Python/Rust version drift, certificate trust, docker volumes filling up). One bullet per pitfall: symptom, root cause, fix. Keep this list fresh — when a new pitfall recurs three times, add it.

## First-Task Recommendations
Suggested onboarding tasks ordered by difficulty: 1-2 read-only orientation tickets, 2-3 well-scoped small PRs labeled `good-first-issue`, and the path to the first real feature. Name the buddy/mentor pattern and the review SLA for first-week PRs.

## Where to Ask Questions
The communication map: synchronous channels (Slack/Discord rooms with topics), asynchronous channels (issue tracker, discussion forum), on-call rotation, and office hours. Include the response-time expectation per channel and the escalation path when blocked.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
