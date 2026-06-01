---
template_name: CODE_REVIEW
generate_when: "conditional"
required_decisions: [team_size, scm.host]
optional_decisions:
  - scm.provider
  - team.structure
  - workflow.branching
  - workflow.pr_required
  - workflow.merge_strategy
  - ci.provider
  - constraints.regulated
depends_on: []
revision_triggers:
  - team_size
  - scm.host
  - team.structure
  - workflow.pr_required
  - workflow.merge_strategy
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Code Review & Ownership: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document defines how changes to **{{project_name}}** are reviewed, who owns which
> paths, and how ownership is enforced mechanically. The ownership layer is grounded in the
> **[GitHub CODEOWNERS specification](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)**
> — the authoritative reference for path-based review routing. Even on a non-GitHub host
> (`{{scm_host}}`), the CODEOWNERS *model* (gitignore-style pattern → owner, last-match-wins)
> is the lingua franca and is supported with minor dialect differences by GitLab, Bitbucket,
> and Gitea. This doc records the project's review *policy* and the concrete CODEOWNERS file
> that implements it.

## Table of contents
- [👥 Team & Reviewer Roster](#team-reviewer-roster)
- [📋 Review Policy](#review-policy)
- [🗂️ Ownership Map (CODEOWNERS)](#ownership-map-codeowners)
- [📐 CODEOWNERS Syntax Rules](#codeowners-syntax-rules)
- [🔒 Branch Protection & Required Review](#branch-protection-required-review)
- [✅ Review Checklist & Standards](#review-checklist-standards)
- [🤖 Automated Review (CI gates & bots)](#automated-review-ci-gates-bots)
- [⏱️ Review SLAs & Escalation](#review-slas-escalation)
- [↻ Revision Log](#revision-log)

## 👥 Team & Reviewer Roster

| Role | Identifier (handle / team) | Owns | Notes |
|---|---|---|---|
| {{role_1}} | `{{handle_1}}` | {{owns_1}} | {{notes_1}} |
| {{role_2}} | `{{handle_2}}` | {{owns_2}} | {{notes_2}} |
| {{additional_reviewers}} | … | … | … |

- **Team size:** `{{team_size}}` (this doc generates because the team is not solo).
- **SCM host:** `{{scm_host}}` · **Provider/org:** `{{scm_provider}}`
- **Team structure on the host:** {{team_structure}} — name the org teams (e.g. `@{{org}}/backend`,
  `@{{org}}/frontend`) used as owners below.

> **Owner eligibility (GitHub rule).** Every code owner — whether a `@username` or an
> `@{{org}}/team` — MUST have explicit **write** access to the repository. For a *team* to be
> usable as an owner, the team must be **visible** and hold **write** permission, even when the
> individual members already have access through other means. List owners that don't yet meet
> this bar so access can be granted before the CODEOWNERS file is committed.

## 📋 Review Policy

| Policy dimension | Decision for {{project_name}} |
|---|---|
| Pull request required to merge? | {{pr_required}} (`workflow.pr_required`) |
| Minimum approvals | {{min_approvals}} |
| Code-owner approval required? | {{codeowner_review_required}} |
| Branching model | {{branching_model}} (`workflow.branching`) — e.g. trunk-based / GitHub Flow / GitFlow |
| Merge strategy | {{merge_strategy}} (`workflow.merge_strategy`) — squash / merge commit / rebase |
| Self-review allowed? | {{self_review_policy}} |
| Stale-approval dismissal on new commits | {{dismiss_stale_approvals}} |

**Review philosophy:** {{review_philosophy}}
*(One paragraph: what reviewers optimize for — correctness, design coherence, security, or
velocity — and how disagreements are resolved.)*

## 🗂️ Ownership Map (CODEOWNERS)

The file lives at **`{{codeowners_path}}`**. Per the GitHub spec, GitHub searches three
locations *in this order* and uses the **first** file it finds:

1. `.github/CODEOWNERS`  ← recommended; keeps repo root clean
2. `CODEOWNERS` (repository root)
3. `docs/CODEOWNERS`

> The review request always uses the CODEOWNERS file from the **base branch** of the PR, and
> different branches may carry different CODEOWNERS files.

This project's intended ownership (translate the rows into the file shown below):

| Path / glob | Owner(s) | Why |
|---|---|---|
| `*` | `{{default_owner}}` | catch-all fallback owner |
| `{{path_1}}` | `{{owner_1}}` | {{reason_1}} |
| `{{path_2}}` | `{{owner_2}}` | {{reason_2}} |
| `{{path_3}}` | `{{owner_3}}` | {{reason_3}} |

**Generated `CODEOWNERS` file:**

```gitignore
# CODEOWNERS for {{project_name}}
# Syntax: <pattern>  <owner1> <owner2> ...
# Order matters — the LAST matching pattern wins for a given file.
# Comments start with '#'. Inline comments are supported.

# --- Default owner: matches everything not matched by a later, more specific line ---
*                       {{default_owner}}

# --- Area ownership (more specific lines below override the catch-all) ---
{{path_1}}              {{owner_1}}
{{path_2}}              {{owner_2}}

# --- Multiple owners share a pattern: put them ALL on ONE line ---
{{shared_path}}         {{owner_a}} {{owner_b}}

# --- "Carve-out": a subdirectory with NO required owner.
#     Negation ('!') is NOT supported, so leave the owner field empty instead.
{{parent_path}}         {{parent_owner}}
{{carved_out_subpath}}
```

> **Last-match-wins, not first-match.** Because precedence runs top-to-bottom with the *last*
> matching line winning, order specific rules **after** general ones. The `*` catch-all goes at
> the **top**; the most specific paths go at the **bottom**.

## 📐 CODEOWNERS Syntax Rules

These are the binding rules from the GitHub spec — violating them silently drops review
routing, so encode them in CI (see [Automated Review](#automated-review-ci-gates-bots)).

| Rule | Detail |
|---|---|
| **Pattern style** | gitignore-style globs. `*` = everything; `*.js` = JS files; `/build/logs/` = that dir + subdirs; `docs/*` = direct children of `docs` (not nested); `**/logs` = a `logs` dir at any depth; `/docs/` = root `docs` + all subdirs. |
| **Owner types** | `@username`, `@{{org}}/team-name`, or a bare `user@example.com` email. *(Email owners do **not** work for managed/Enterprise-managed user accounts.)* |
| **Multiple owners** | All owners for one pattern MUST be on the **same line**, space-separated. |
| **Precedence** | The **last** matching pattern takes precedence. |
| **Comments** | Lines starting with `#` are comments; inline comments after a rule are allowed. Backslash-escaping a literal `#` does **not** work. |
| **Negation** | `!` negation is **NOT supported**. To exclude a subpath, give the parent an owner and leave the subpath's owner field empty. |
| **Character ranges** | `[ ]` ranges are **NOT supported**. |
| **Case sensitivity** | Paths are **case-sensitive** (GitHub uses a case-sensitive filesystem). |
| **Invalid lines** | Any line with invalid syntax is **silently skipped** — so a typo can disable an entire ownership rule. Lint before commit. |
| **File size** | The file must be **under 3 MB**; a larger file is **not loaded at all**, and *no* code owners are requested. |

**Host-dialect note (`{{scm_host}}`):** {{host_dialect_notes}}
*(GitLab supports `[Section]` headers and `^[Optional]` sections; Bitbucket and Gitea diverge
on glob anchoring. If not on GitHub, record the exact deltas that affect the file above.)*

## 🔒 Branch Protection & Required Review

How ownership becomes *enforcement* rather than mere notification.

| Setting | Value |
|---|---|
| Protected branch(es) | {{protected_branches}} |
| "Require a pull request before merging" | {{require_pr}} |
| "Require approvals" (count) | {{required_approval_count}} |
| "Require review from Code Owners" | {{require_codeowner_review}} |
| "Dismiss stale approvals" | {{dismiss_stale}} |
| "Require status checks to pass" | {{required_status_checks}} |
| "Require linear history" | {{require_linear_history}} |
| "Require conversation resolution" | {{require_conversation_resolution}} |
| Admins exempt from rules? | {{admin_bypass}} |

> When **"Require review from Code Owners"** is enabled, an approval from **any one** of the
> matched owners is sufficient — not every listed owner. Owners are auto-requested on regular
> PRs but **not** on **draft** PRs; the request fires when the draft is marked ready for review.

## ✅ Review Checklist & Standards

What every reviewer verifies before approving. Keep it short enough to actually run.

- [ ] **Correctness** — the change does what the PR description claims; edge cases considered.
- [ ] **Tests** — new behavior is covered; tests fail without the change and pass with it
      (per the project's `superpowers:test-driven-development` discipline if adopted).
- [ ] **Scope** — the diff is focused; no unrelated drive-by changes; size ≤ {{max_pr_size}} where practical.
- [ ] **Security** — no secrets committed; inputs validated; authz checks present (cross-ref
      the security threat model if one exists).
- [ ] **Design coherence** — consistent with the architecture docs / ADRs; new public surface is justified.
- [ ] **Docs & changelog** — user-visible changes update README/CHANGELOG; ADR filed if a
      decision changed.
- [ ] **Conventions** — {{coding_conventions}} (lint/format clean, naming, commit-message style).
- [ ] **Backwards compatibility** — {{compat_policy}} (migrations, API versioning, deprecations).

**Approval semantics in this project:** {{approval_semantics}}
*(e.g. "Approve = I'd ship this"; "Request changes = blocking"; "Comment = non-blocking nit".
Define nit-vs-blocker convention so authors know what must be addressed.)*

## 🤖 Automated Review (CI gates & bots)

Mechanical checks that run *before* a human looks, on `{{ci_provider}}`:

| Gate | Tool | Blocking? |
|---|---|---|
| Lint / format | {{lint_tool}} | {{lint_blocking}} |
| Type check | {{typecheck_tool}} | {{typecheck_blocking}} |
| Tests | {{test_runner}} | {{tests_blocking}} |
| Security / secret scan | {{security_scan}} | {{security_blocking}} |
| CODEOWNERS validity | {{codeowners_linter}} | {{codeowners_lint_blocking}} |
| Dependency / supply-chain | {{dependency_scan}} | {{dependency_blocking}} |

- **Auto-review bots:** {{review_bots}} (e.g. CodeRabbit, GitHub Copilot review, Reviewdog) —
  advisory unless explicitly promoted to a required status check.
- **CODEOWNERS lint in CI is strongly recommended** because invalid lines are silently skipped
  by GitHub: validate that every owner exists and has write access, and that no pattern is
  dropped. Tool: {{codeowners_linter}}.

## ⏱️ Review SLAs & Escalation

| Concern | Policy |
|---|---|
| Target time-to-first-review | {{review_sla}} |
| Reviewer load-balancing | {{load_balancing}} (round-robin / auto-assign / CODEOWNERS-only) |
| Stale / unreviewed PR escalation | {{escalation_path}} |
| Out-of-office / single-owner risk (bus factor) | {{bus_factor_mitigation}} |
| Emergency / hotfix bypass | {{hotfix_policy}} — who can override branch protection and how it's audited |

> **Bus-factor watch.** Any path owned by a *single* `@username` (rather than a team) is a
> review bottleneck and a continuity risk. Prefer team owners (`@{{org}}/team`) for any path on
> the critical merge path; list single-owner paths above so they get a backup before that owner
> is unavailable.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
