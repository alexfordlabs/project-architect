---
template_name: GIT_BRANCHING
generate_when: "conditional"
required_decisions:
  - workflow.branching
  - team_size
optional_decisions:
  - workflow.merge_strategy
  - workflow.pr_required
  - workflow.feature_flags
  - workflow.release_branching
  - ci.provider
  - scm.host
  - deployment.cadence
depends_on: []
revision_triggers:
  - workflow.branching
  - workflow.merge_strategy
  - workflow.feature_flags
  - workflow.release_branching
  - team_size
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Git Branching Model: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document records the branching model **{{project_name}}** uses, why it was chosen, and
> the concrete rules the team follows. The recommended model and its guidance are grounded in
> **[Trunk-Based Development](https://trunkbaseddevelopment.com/)** (Paul Hammant et al.) — the
> authoritative reference for the trunk-based model, defined there as *"a source-control
> branching model, where developers collaborate on code in a single branch called 'trunk' and
> resist any pressure to create other long-lived development branches by employing documented
> techniques."* GitFlow is presented below as the contrast, not the recommendation.

## Table of contents
- [🌳 Chosen Model](#chosen-model)
- [⚖️ Trunk-Based vs. GitFlow (the contrast)](#trunk-based-vs-gitflow-the-contrast)
- [📏 Small-Team vs. Scaled Trunk-Based](#small-team-vs-scaled-trunk-based)
- [🔀 Short-Lived Feature Branches](#short-lived-feature-branches)
- [🚩 Feature Flags & Branch by Abstraction](#feature-flags-branch-by-abstraction)
- [🏷️ Release Strategy](#release-strategy)
- [🔧 Merge vs. Rebase Policy](#merge-vs-rebase-policy)
- [✅ Operating Rules (the contract)](#operating-rules-the-contract)
- [↻ Revision Log](#revision-log)

## 🌳 Chosen Model

**{{project_name}} uses:** `{{branching_model}}` (`workflow.branching`)
*(trunk-based / scaled trunk-based / GitHub Flow / GitFlow / custom.)*

**Trunk branch name:** `{{trunk_branch_name}}` *(e.g. `main`.)*
**Team size driving this choice:** `{{team_size}}` (`team_size`).

**Why this model:** {{branching_rationale}}
*(One paragraph. If trunk-based: the goal per the standard is to* never break the build, and
*always be release ready, avoiding "merge hell." If GitFlow or another long-lived-branch model
was chosen instead, justify it against the standard's explicit recommendation to the contrary
— see the contrast table below.)*

> **The standard's headline guidance:** *"You should do Trunk-Based Development instead of
> GitFlow and other branching models that feature multiple long-running branches."* The single
> non-negotiable invariant of trunk-based development is that the trunk stays **"release
> ready" at all times** — every developer clones the trunk, pulls from it *"many times a
> day,"* and runs the build locally *"to prove that they did not break anything with the
> commit before the commit is pushed."*

## ⚖️ Trunk-Based vs. GitFlow (the contrast)

The two models differ chiefly in **how many long-running branches exist** and **how long
work lives away from the trunk before integration**.

| Dimension | Trunk-Based Development (recommended) | GitFlow (the contrast) |
|---|---|---|
| Long-running branches | One: the **trunk**. Resist creating others. | Several persistent branches (`main` + `develop`, plus `release/*`, `hotfix/*`). |
| Feature branches | Short-lived (≤ **a couple of days**), or none (commit straight to trunk). | Long-lived `feature/*` branches merged into `develop`. |
| Integration cadence | Continuous — teammates' commits integrated *"on an hour-by-hour basis."* | Deferred until a feature branch is "done," inviting merge conflicts. |
| Continuous Integration | Native — trunk is always green and releasable. | Harder — `develop` and feature branches drift apart. |
| Release path | Cut a release branch from trunk just-in-time, or release straight from trunk. | Promote `develop` → `release/*` → `main`, with back-merges. |
| Best fit | Teams practising CI/CD and frequent deploys. | Scheduled, versioned releases with parallel maintenance lines. |
| The standard's verdict | *"resist any pressure to create other long-lived development branches."* | A "Gitflow" practitioner will find TBD *"very different."* |

**This project's reasoning on the trade-off:** {{model_tradeoff_reasoning}}
*(If the project has versioned, parallel-maintenance releases (e.g. supporting v1.x and v2.x
simultaneously) GitFlow-style release lines may be defensible; otherwise prefer trunk-based.)*

## 📏 Small-Team vs. Scaled Trunk-Based

The standard splits trunk-based development into two execution styles, the dividing line
being *"subject to team size and commit rate consideration."*

| Style | What developers do | When the standard recommends it |
|---|---|---|
| **Commit straight to trunk** | Each dev runs a pre-integration build locally, then *"commit/push straight to trunk."* No PR branch. | Small teams / low commit rate. |
| **Scaled Trunk-Based Development** | Work on **short-lived feature branches** that come back as pull requests with CI verification, but each branch is still *"the product of a single dev-workstation"* (solo, pair, or mob). | Larger teams — the standard cites this as a productivity improvement for teams of **16+ developers** vs. committing directly. |

**This project's style:** `{{trunk_style}}` *(commit-straight-to-trunk / scaled-with-PRs.)*
**PR required to land on trunk?** {{pr_required}} (`workflow.pr_required`)
**Why this style for a team of `{{team_size}}`:** {{style_rationale}}

> Even in the scaled style, the goal is unchanged: branches exist only to run code review and
> CI *"in advance of commits landing in the trunk."* They are not a place where multiple
> developers collaborate over time — that is what makes them *short-lived*, not long-lived.

## 🔀 Short-Lived Feature Branches

Applies when `{{trunk_style}}` is scaled-with-PRs. The standard's concrete rules:

| Rule | The standard's value | This project |
|---|---|---|
| Maximum branch lifetime | *"the branch should only last a couple of days. Any longer than two days, and there is a risk of the branch becoming a long-lived feature branch."* | {{branch_lifetime}} |
| Developers per branch | *"the developer count should stay at one (or two if pair-programming)."* | {{devs_per_branch}} |
| Destination | Branches *"are destined to come back as 'pull requests' into the main/trunk."* | {{pr_target}} |
| CI on the branch | *"corresponding CI daemons verifying those in advance of commits landing in the trunk."* — `{{ci_provider}}` | {{branch_ci}} |
| Delete after merge | The PR platform *"may … even go as far as to delete the short-lived feature branch"* — deletion is standard practice post-merge. | {{delete_after_merge}} |
| Branch naming | — (project convention) | `{{branch_naming_convention}}` |

**Review policy (cross-ref `CODE_REVIEW.md` if generated):** {{review_policy_pointer}}

> **The two-day rule is the line that keeps "short-lived" honest.** A branch that outlives a
> couple of days *is* a long-lived branch by another name, and re-introduces the merge-hell
> the model exists to avoid. If a change can't land within that window, split it (see Feature
> Flags & Branch by Abstraction below) rather than letting the branch age.

## 🚩 Feature Flags & Branch by Abstraction

These are the standard's two named techniques for shipping large or incomplete work to trunk
*without* a long-lived branch — they let teams *"hedge on the order of releases."*

**Strategy chosen for incomplete/large changes:** `{{incomplete_work_strategy}}`
*(feature-flags / branch-by-abstraction / both / none.)*
**Feature flags in use?** {{feature_flags_enabled}} (`workflow.feature_flags`)

| Technique | What it is (per the standard) | How {{project_name}} applies it |
|---|---|---|
| **[Feature Flags](https://trunkbaseddevelopment.com/feature-flags/)** | Merge incomplete code to trunk behind a flag that keeps it dormant in production until ready; decouples deploy from release. | {{feature_flag_approach}} |
| **[Branch by Abstraction](https://trunkbaseddevelopment.com/branch-by-abstraction/)** | Introduce an abstraction layer, migrate callers behind it incrementally on trunk, then remove the old implementation — a large refactor with no long-lived branch. | {{branch_by_abstraction_approach}} |

- **Flag tooling / mechanism:** {{flag_tooling}} *(config, env var, LaunchDarkly/Unleash/OpenFeature, build-time, etc.)*
- **Flag lifecycle / cleanup:** {{flag_cleanup_policy}} — flags are technical debt; record who removes a flag once its feature is fully rolled out and how stale flags are tracked.

> Feature flags are the trunk-based answer to *"this feature isn't done, but I don't want a
> branch open for a week."* The cost is flag-management discipline: an un-retired flag is a
> permanent conditional in production code. Track and prune them like any other debt.

## 🏷️ Release Strategy

How a releasable artifact is cut from a perpetually-green trunk. The standard offers two
models; pick one.

**Chosen release model:** `{{release_model}}` (`workflow.release_branching`)
*(branch-for-release / release-from-trunk.)*  ·  **Deploy cadence:** {{deploy_cadence}}

| Model | The standard's description | Fix workflow |
|---|---|---|
| **[Branch for Release](https://trunkbaseddevelopment.com/branch-for-release/)** | Cut a release branch from trunk just-in-time (the standard cuts it *"a few days before the release"*), harden it, ship, then *"release branches are deleted some time after release."* Fixes are reproduced/fixed on trunk and **cherry-picked** onto the release branch. | {{release_branch_fix_flow}} |
| **[Release from Trunk](https://trunkbaseddevelopment.com/release-from-trunk/)** | High-throughput teams tag/deploy straight from trunk and *"fix forward"* — roll the fix forward on trunk rather than patching a side branch. | {{fix_forward_flow}} |

- **Release branch naming / tagging:** {{release_naming}} *(e.g. `release/X.Y` branches, `vX.Y.Z` tags.)*
- **Cherry-pick vs. fix-forward decision:** {{cherrypick_vs_fixforward}}
- **Hotfix path for production:** {{hotfix_path}} — who can cut it and how it lands back on trunk.

> A key trunk-based property: fixes originate on **trunk** and flow *to* a release branch
> (cherry-pick), never the reverse. The release branch is a short-lived, disposable hardening
> lane — not a parallel line of development. This is the inverse of GitFlow's `release/*` →
> `develop` back-merge.

## 🔧 Merge vs. Rebase Policy

How commits from a branch (or a PR) are integrated onto the trunk. This is independent of the
branching model but must be decided once and enforced for a clean, bisectable history.

**Chosen integration strategy:** `{{merge_strategy}}` (`workflow.merge_strategy`)

| Strategy | History shape | Trade-off |
|---|---|---|
| **Squash and merge** | One commit per PR on trunk. | Cleanest linear trunk; loses intra-PR commit granularity. Pairs well with short-lived branches. |
| **Rebase and merge** | PR commits replayed linearly onto trunk; no merge commit. | Linear, no merge bubbles; rewrites SHAs (force-push on the branch). |
| **Merge commit (no-ff)** | Preserves branch topology with an explicit merge node. | Full history retained; trunk graph is non-linear. |

- **Rationale for `{{merge_strategy}}`:** {{merge_rationale}}
- **Require linear history on trunk?** {{require_linear_history}}
- **Rebase-before-merge to stay current with trunk?** {{rebase_before_merge}}
- **Commit-message / Conventional-Commits convention:** {{commit_message_convention}}
- **"Don't rewrite published history" rule:** {{public_history_rule}} *(never rebase commits others have pulled; rebase only un-pushed local work or your own un-merged branch.)*

## ✅ Operating Rules (the contract)

The concrete day-to-day rules every contributor to {{project_name}} follows. Keep these
short enough to actually obey.

- [ ] **Trunk is always releasable.** Never push a commit that breaks the build; run the build
      locally *before* pushing — *"prove that they did not break anything … before the commit
      is pushed."*
- [ ] **Pull trunk frequently** — *"many times a day,"* so you integrate teammates' work *"on
      an hour-by-hour basis"* and conflicts stay small.
- [ ] **Keep branches short.** {{branch_lifetime}} max; one (or two, if pairing) developer per
      branch; delete after merge.
- [ ] **Land via `{{merge_strategy}}`** with CI green on `{{ci_provider}}`; {{pr_required}} for PR-gated landing.
- [ ] **Hide unfinished work behind {{incomplete_work_strategy}}**, never behind a long-lived branch.
- [ ] **Releases come from trunk** via `{{release_model}}`; fixes originate on trunk.
- [ ] **Protected-branch settings on `{{trunk_branch_name}}`:** {{branch_protection_summary}}
      *(cross-ref `CODE_REVIEW.md § Branch Protection` if generated.)*

**Open questions / deferred decisions:** {{open_questions}}

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
