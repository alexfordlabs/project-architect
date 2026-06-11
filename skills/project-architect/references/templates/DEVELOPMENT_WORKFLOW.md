---
template_name: DEVELOPMENT_WORKFLOW
generate_when: "conditional"
required_decisions: [team_size, scm.host]
optional_decisions:
  - scm.provider
  - team.structure
  - workflow.branching
  - workflow.pr_required
  - workflow.merge_strategy
  - workflow.commit_convention
  - ci.provider
  - deployment.trigger
depends_on: []
revision_triggers:
  - team_size
  - workflow.branching
  - workflow.pr_required
  - workflow.merge_strategy
  - deployment.trigger
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Development Workflow: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document is the **day-in-the-life dev loop** for the **{{project_name}}** team: how a
> change travels from an idea to running in production, and the team norms at every step. It is
> grounded in **[GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)**
> — described by GitHub as *"a lightweight, branch-based workflow"* — and adapts its six steps
> to this project's host (`{{scm_host}}`), team size (`{{team_size}}`), and deploy model.
> Two sibling docs own the details this one only summarizes: branch mechanics and naming live
> in **[GIT_BRANCHING.md](./GIT_BRANCHING.md)**; the reviewer's checklist, ownership map, and
> approval semantics live in **[CODE_REVIEW.md](./CODE_REVIEW.md)**. This doc is the *spine* that
> ties them together into one repeatable loop.

## Table of contents
- [🔁 The Loop at a Glance](#the-loop-at-a-glance)
- [① Create a Branch](#1-create-a-branch)
- [② Make Changes & Commit](#2-make-changes-commit)
- [③ Open a Pull Request](#3-open-a-pull-request)
- [④ Review](#4-review)
- [⑤ CI Checks](#5-ci-checks)
- [⑥ Merge](#6-merge)
- [⑦ Deploy](#7-deploy)
- [⑧ Delete the Branch](#8-delete-the-branch)
- [🚑 Hotfix Path](#hotfix-path)
- [📓 Norms Cheat-Sheet](#norms-cheat-sheet)
- [↻ Revision Log](#revision-log)

## 🔁 The Loop at a Glance

GitHub flow's premise is that the **default branch (`{{default_branch}}`) is always deployable**.
Every change is made on a short-lived branch, reviewed via a pull request, gated by CI, then
merged back — at which point it becomes a candidate to deploy. The full cycle for
{{project_name}}:

```
{{default_branch}} (always deployable)
   │
   ├─▶ ① branch ─▶ ② commit/push ─▶ ③ open PR ─▶ ④ review ──┐
   │                                      ▲                  │
   │                                      └── address comments┘
   │                                                          ▼
   │                                              ⑤ CI checks pass
   │                                                          ▼
   └──────────────────◀───── ⑥ merge ──────────────────◀─────┘
                               │
                               ▼
                         ⑦ deploy ({{deploy_trigger}})
                               │
                               ▼
                         ⑧ delete branch
```

| Step | Who acts | What "done" looks like |
|---|---|---|
| ① Branch | Author | A branch named per the convention exists off `{{default_branch}}`. |
| ② Commit | Author | Isolated, complete commits pushed; commit messages follow {{commit_convention}}. |
| ③ PR | Author | PR opened with a filled-out description; reviewers + labels assigned. |
| ④ Review | Reviewer(s) | {{min_approvals}} approval(s); all blocking comments resolved. |
| ⑤ CI | Automation | All required checks green on the PR head. |
| ⑥ Merge | {{who_merges}} | Branch merged into `{{default_branch}}` via {{merge_strategy}}. |
| ⑦ Deploy | {{deploy_actor}} | Change live in {{deploy_target}} via {{deploy_trigger}}. |
| ⑧ Cleanup | Author / auto | Merged branch deleted. |

> **Branching model in use:** `{{branching_model}}` (`workflow.branching`). This template assumes
> a GitHub-flow-style trunk model. If `{{branching_model}}` is GitFlow or a release-train variant,
> record the deltas (long-lived `develop`/`release/*` branches, cherry-pick rules) in
> [GIT_BRANCHING.md](./GIT_BRANCHING.md) and treat the steps below as the *PR loop* within it.

## ① Create a Branch

> GitHub flow step 1 — *"Create a branch in your repository"* with *"a short, descriptive branch
> name"* (their example: `increase-test-timeout`). Branching means *"changes you make on your
> branch don't affect the default branch."*

- **Cut from:** the latest `{{default_branch}}` (`git switch {{default_branch}} && git pull`).
- **Naming convention:** `{{branch_naming_convention}}`
  *(e.g. `<type>/<issue-id>-<slug>` → `feat/142-rate-limit`, `fix/198-null-deref`. The exact
  scheme is owned by [GIT_BRANCHING.md](./GIT_BRANCHING.md); restate the one-liner here so the
  loop is self-contained.)*
- **One concern per branch.** Keep branches short-lived so they merge before `{{default_branch}}`
  drifts. Target lifetime: {{branch_lifetime_target}}.

## ② Make Changes & Commit

> GitHub flow step 2 — *"On your branch, make any desired changes to the repository."* The
> guidance: *"Ideally, each commit contains an isolated, complete change,"* which makes reverting
> individual commits straightforward.

- **Commit discipline:** {{commit_convention}} (`workflow.commit_convention`)
  *(e.g. Conventional Commits — `feat:` / `fix:` / `chore:` — or a plain imperative-mood
  one-liner. State the rule and whether CI lints it.)*
- **Test-first:** {{test_discipline}}
  *(If the project adopts TDD, the failing test lands with — or before — the change. Reference
  the testing strategy doc if one exists.)*
- **Push early, push often.** Push to the remote branch as you go so the PR (next step) updates
  automatically and teammates see progress: `git push -u origin {{branch_name}}`.
- **Pre-commit gate:** {{precommit_hooks}}
  *(lint / format / secret-scan hooks that must pass locally before a commit lands.)*

## ③ Open a Pull Request

> GitHub flow step 3 — *"Create a pull request to ask collaborators for feedback on your
> changes."* Include *"a summary of the changes and what problem they solve"* and link related
> issues.

- **Pull request required to merge?** {{pr_required}} (`workflow.pr_required`).
- **PR template (`{{pr_template_path}}`):** every PR fills out —
  - **What & why** — a summary of the change and the problem it solves.
  - **Linked issue** — `Closes #{{issue_ref}}` (auto-closes on merge).
  - **How to test / verify** — reproduction or test steps for the reviewer.
  - **Risk & rollout** — migrations, feature flags, backwards-compat notes.
  - **Checklist** — tests added, docs updated, changelog touched (mirrors the
    [CODE_REVIEW.md](./CODE_REVIEW.md) checklist).
- **Draft PRs** for work-in-progress: open as **Draft** to run CI and gather early eyes without
  requesting formal review; mark **Ready for review** to trigger reviewer auto-request.
- **Reviewer assignment:** {{reviewer_assignment}} — auto-routed via `CODEOWNERS` (see
  [CODE_REVIEW.md](./CODE_REVIEW.md)) and/or {{load_balancing}}.
- **PR size norm:** keep diffs reviewable — target ≤ {{max_pr_size}} changed lines; split larger
  work into stacked PRs.

## ④ Review

> GitHub flow step 4 — *"Reviewers should leave questions, comments, and suggestions."* The
> author *"can continue to commit and push changes in response to the reviews. Your pull request
> will update automatically."*

| Norm | Value for {{project_name}} |
|---|---|
| Minimum approvals to merge | {{min_approvals}} |
| Code-owner approval required? | {{codeowner_review_required}} |
| Who reviews | {{reviewer_pool}} |
| Target time-to-first-review | {{review_sla}} |
| Self-approval allowed? | {{self_review_policy}} |
| Stale approvals dismissed on new push? | {{dismiss_stale_approvals}} |

- **Respond, don't re-open.** Push fixups onto the same branch; the PR updates in place. Resolve
  each conversation once addressed.
- **Approval semantics, nit vs. blocker, and the full reviewer checklist** are defined in
  **[CODE_REVIEW.md](./CODE_REVIEW.md)** — that doc is authoritative; this loop just sequences it.
- **Solo-team note:** when `{{team_size}}` is effectively one, replace human review with a
  self-review pass + the CI gate as the de-facto second opinion. {{solo_review_substitute}}

## ⑤ CI Checks

Mechanical gates run on every PR push on `{{ci_provider}}` (`ci.provider`). These run *before
and during* human review so reviewers spend their time on judgement, not on catching lint.

| Gate | Tool | Required to merge? |
|---|---|---|
| Lint / format | {{lint_tool}} | {{lint_blocking}} |
| Type check | {{typecheck_tool}} | {{typecheck_blocking}} |
| Unit / integration tests | {{test_runner}} | {{tests_blocking}} |
| Build | {{build_tool}} | {{build_blocking}} |
| Security / secret scan | {{security_scan}} | {{security_blocking}} |
| {{extra_gate}} | {{extra_gate_tool}} | {{extra_gate_blocking}} |

- **Required status checks** are enforced via branch protection on `{{default_branch}}` — see the
  protection matrix in [CODE_REVIEW.md](./CODE_REVIEW.md). A PR cannot merge with a failing
  required check.
- **Keep the default branch deployable:** because `{{default_branch}}` is always shippable, a red
  required check is a hard stop, not a warning.

## ⑥ Merge

> GitHub flow step 5 — *"Once your pull request is approved, merge your pull request. This will
> automatically merge your branch so that your changes appear on the default branch."*

- **Who merges:** {{who_merges}} *(author after approvals / a maintainer / merge queue / auto-merge
  once all gates pass).*
- **Merge strategy:** `{{merge_strategy}}` (`workflow.merge_strategy`) —
  - **Squash** → one tidy commit per PR (default for clean history; pairs well with
    Conventional-Commit PR titles).
  - **Merge commit** → preserves the full branch history with a merge node.
  - **Rebase** → linear history, no merge node.
  Pick one and enforce it in repo settings so the button can't drift.
- **Merge queue / auto-merge:** {{merge_queue_policy}} — if enabled, PRs are merged serially after
  re-validating against the latest `{{default_branch}}`, preventing "green-then-broken" races.
- **Linear-history requirement:** {{require_linear_history}}.

## ⑦ Deploy

> Beyond GitHub flow's six core steps, this team defines *when a merge becomes a deploy*. Because
> `{{default_branch}}` is always deployable, deploy can be continuous or gated.

| Deploy dimension | Decision for {{project_name}} |
|---|---|
| Trigger | {{deploy_trigger}} (`deployment.trigger`) — on-merge / tag push / manual promotion / scheduled |
| Target(s) | {{deploy_target}} (e.g. staging → production) |
| Pipeline | {{deploy_pipeline}} — the CD job/workflow that runs |
| Approval to ship to prod | {{prod_deploy_approval}} |
| Rollback mechanism | {{rollback_mechanism}} |
| Environment promotion | {{promotion_flow}} |

- **Deploy-then-validate vs. validate-then-deploy:** {{deploy_validation_order}}
  *(GitHub flow allows deploying the branch *before* merge to validate in a real environment; if
  this team does that, document it here — otherwise deploy happens post-merge.)*
- **Observability after deploy:** {{post_deploy_checks}} — health checks, error-rate watch, and
  who's on point if the deploy regresses.

## ⑧ Delete the Branch

> GitHub flow step 6 — *"After you merge your pull request, delete your branch. This indicates
> that the work on the branch is complete."* Note that *"your pull request and commit history
> will not be deleted."*

- **Auto-delete on merge:** {{auto_delete_branches}} *(recommended: enable repo setting so merged
  branches are pruned automatically).*
- **Local cleanup:** `git switch {{default_branch}} && git pull && git branch -d {{branch_name}}`.

## 🚑 Hotfix Path

Urgent production fixes follow the *same* loop on a compressed timeline — they do **not** skip
review or CI, they fast-track them.

| Hotfix dimension | Decision for {{project_name}} |
|---|---|
| Branch source | {{hotfix_branch_source}} (off `{{default_branch}}` for trunk models) |
| Expedited review | {{hotfix_review_policy}} — who can approve under time pressure |
| Required checks under hotfix | {{hotfix_required_checks}} — which gates stay mandatory |
| Branch-protection bypass | {{hotfix_bypass_policy}} — who may override and how it's audited |
| Post-hotfix follow-up | {{hotfix_followup}} — backport / postmortem / ADR if a process gap caused it |

## 📓 Norms Cheat-Sheet

The one-screen summary a new contributor pins next to their editor:

- **Default branch is always deployable** — never push directly to `{{default_branch}}`.
- **Branch name:** {{branch_naming_convention}}.
- **Commit style:** {{commit_convention}}.
- **PR needs:** filled template + linked issue + {{min_approvals}} approval(s) + green CI.
- **Merge via:** {{merge_strategy}}, performed by {{who_merges}}.
- **Deploy when:** {{deploy_trigger}}.
- **After merge:** branch is deleted ({{auto_delete_branches}}).
- **Reviewer rules → [CODE_REVIEW.md](./CODE_REVIEW.md). Branch mechanics → [GIT_BRANCHING.md](./GIT_BRANCHING.md).**

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
