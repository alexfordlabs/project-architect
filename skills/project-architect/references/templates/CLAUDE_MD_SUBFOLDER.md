---
template_name: CLAUDE_MD_SUBFOLDER
generate_when: "subfolder meets gating triggers (see claude-md-author system prompt)"
required_decisions:
  - subfolder.path
  - subfolder.purpose
optional_decisions:
  - subfolder.language
  - subfolder.framework
  - subfolder.test_framework
  - subfolder.build_command
depends_on: [CLAUDE_MD_ROOT]
revision_triggers:
  - subfolder.language
  - subfolder.framework
  - subfolder.test_framework
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# {{subfolder.path}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🎯 Purpose](#purpose)
- [Local Tech Stack](#local-tech-stack)
- [Conventions Specific to This Area](#conventions-specific-to-this-area)
- [Local Development Commands](#local-development-commands)
- [Key Files In This Area](#key-files-in-this-area)
- [Cross-references](#cross-references)

## 🎯 Purpose
What this area is responsible for. How it relates to the rest of the project.

## Local Tech Stack
Only list what differs from the root CLAUDE.md.

## Conventions Specific to This Area
- {{convention}} — why
- {{convention}} — why

## Local Development Commands
Only commands that are different from root (test, build, run).

## Key Files In This Area
Path → purpose.

## Cross-references
- Root: `../CLAUDE.md` for project-wide conventions
- Related docs: {{relevant docs/ links}}

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
