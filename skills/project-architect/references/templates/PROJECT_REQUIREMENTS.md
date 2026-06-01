---
template_name: PROJECT_REQUIREMENTS
generate_when: "always"
required_decisions:
  - project.problem_statement
  - project.target_users
  - features
optional_decisions:
  - non_functional.performance
  - non_functional.scalability
  - non_functional.availability
  - non_functional.security
  - non_functional.accessibility
  - non_functional.i18n
  - project.constraints
  - success_metrics
depends_on: [PROJECT_OVERVIEW]
revision_triggers:
  - features
  - project.target_users
  - non_functional.*
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Project Requirements: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🎯 Problem Statement](#problem-statement)
- [Target Users](#target-users)
- [Functional Requirements](#functional-requirements)
- [Non-Functional Requirements](#non-functional-requirements)
- [Technical Constraints](#technical-constraints)
- [Success Metrics](#success-metrics)
- [↻ Revision Log](#revision-log)

## 🎯 Problem Statement
What problem this solves, for whom, and why now.

## Target Users
User personas / categories with one-paragraph descriptions.

## Functional Requirements

### Core Features (MVP)
Numbered list of features with one-sentence description + sub-bullets for sub-requirements.

### Future Features (Post-MVP)
Same shape; pulled from features tagged `phase: post-mvp`.

## Non-Functional Requirements
Performance, scalability, availability, security (high-level — defer details to SECURITY_AND_COMPLIANCE.md), accessibility, i18n.

## Technical Constraints
Pre-existing decisions, required integrations, budget limits.

## Success Metrics
How to measure if the project achieves its goals.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
