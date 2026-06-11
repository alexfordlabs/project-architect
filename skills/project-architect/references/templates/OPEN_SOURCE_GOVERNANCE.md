---
template_name: OPEN_SOURCE_GOVERNANCE
generate_when: "conditional"
required_decisions:
  - workflow.open_source
  - workflow.governance_model
optional_decisions:
  - workflow.contribution_agreement
  - workflow.code_of_conduct
  - workflow.maintainer_roles
  - workflow.decision_process
  - workflow.fiscal_host
  - scm.host
  - project.license
  - team_size
depends_on: []
revision_triggers:
  - workflow.governance_model
  - workflow.contribution_agreement
  - workflow.code_of_conduct
  - workflow.maintainer_roles
  - workflow.decision_process
  - workflow.fiscal_host
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Open Source Governance: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This document defines how **{{project_name}}** is governed once it grows past its founders —
> who decides, how roles are earned, how contributions are legally accepted, and how disputes
> resolve. Its structure follows GitHub's **Open Source Guides — *[Leadership and Governance](https://opensource.guide/leadership-and-governance/)***,
> which frames governance as something you formalize *as your project grows* rather than up
> front. The governing rule from that guide: **"There is no right time to write down your
> project's governance, but it's much easier to define once you've seen your community dynamics
> play out."** Start with the lightest model that resolves your actual conflicts, and add
> formality only when contributor volume demands it.
> Two adjacent surfaces this template also covers — the **contribution agreement** and the
> **Code of Conduct** — fall *outside* the OSS-Guides governance chapter, so they are grounded
> in their own authoritative sources (the Developer Certificate of Origin and the Contributor
> Covenant) and cited as such below.

## Table of contents
- [🏛️ Governance Model](#governance-model)
- [🧑‍🔧 Roles & How They're Earned](#roles-how-theyre-earned)
- [✍️ Contribution Agreement (DCO vs. CLA)](#contribution-agreement-dco-vs-cla)
- [⚖️ Decision-Making & Conflict Resolution](#decision-making-conflict-resolution)
- [🚢 Release Sign-off & Maintainer Responsibilities](#release-sign-off-maintainer-responsibilities)
- [🤝 Code of Conduct](#code-of-conduct)
- [🏦 Legal Entity & Fiscal Hosting](#legal-entity-fiscal-hosting)
- [📁 Where Governance Lives](#where-governance-lives)
- [↻ Revision Log](#revision-log)

## 🏛️ Governance Model

The OSS Guides describe three common governance structures. Pick the one that matches how
decisions *actually* get made today, not the one that sounds most impressive.

| Model | OSS-Guides description | Best when | Canonical example |
|---|---|---|---|
| **BDFL** (Benevolent Dictator for Life) | *"One person (usually the initial author of the project) has final say on all major project decisions."* | Small project, one trusted driver, low contributor count | {{bdfl_example}} |
| **Meritocracy** | *"Active project contributors (those who demonstrate 'merit') are given a formal decision making role. Decisions are usually made based on pure voting consensus."* | Growing contributor base that wants a vote tied to demonstrated work | {{meritocracy_example}} |
| **Liberal contribution** | *"The people who do the most work are recognized as most influential… based on current work and not historic contributions. Major project decisions are made based on a consensus seeking process."* | Mature project that wants to avoid power calcifying around early contributors | {{liberal_contribution_example}} |

**Chosen model for {{project_name}}: `{{governance_model}}`.**

{{governance_model_rationale}}
*(Why this model fits {{project_name}}'s size, contributor count `{{contributor_count}}`, and
the kinds of decisions that recur. Note the trigger that would prompt a move to a heavier
model — e.g. "switch from BDFL to liberal-contribution when the bus factor reaches 1 and there
are ≥3 sustained outside contributors".)*

> The OSS Guides caution against over-engineering this. On the question *"Do I need governance
> docs when I launch my project?"* the guide answers that *"there is no right time to write down
> your project's governance, but it's much easier to define once you've seen your community
> dynamics play out"* — while adding that *"some early documentation will inevitably contribute
> to your project's governance, however, so start writing down what you can."* This document is
> that writing-down.

## 🧑‍🔧 Roles & How They're Earned

Per the guide's section *"What are examples of formal roles used in open source projects?"*,
formalizing roles can be *"as simple as adding their names to your README or a CONTRIBUTORS
text file"* for small projects, and graduating to *"a 'core team' of maintainers, or even
subcommittees"* as the project grows. Define the ladder explicitly so the path is legible.

| Role | Privileges | How it's earned | Current holders |
|---|---|---|---|
| **Contributor** | Open issues & PRs | Anyone — one merged PR | {{contributor_note}} |
| **Committer / Triager** | Triage, label, review; {{committer_write_scope}} | {{committer_criteria}} | {{committers}} |
| **Maintainer** | Merge rights, release authority, {{maintainer_scope}} | {{maintainer_criteria}} | {{maintainers}} |
| **{{steering_role_name}}** | Final say on cross-cutting / contested decisions | {{steering_criteria}} | {{steering_members}} |

**Commit-access policy** — the guide's section *"When should I give someone commit access?"*
notes that projects differ philosophically: some grant it freely to encourage investment,
others guard it closely. {{project_name}}'s stance: {{commit_access_policy}}

**Becoming a maintainer is a written, repeatable process** — per the guide, *"establish a
clear process for how someone can become a maintainer or join a subcommittee… and write it
into your GOVERNANCE.md."* The path here: {{maintainer_promotion_process}}
*(e.g. nominated by an existing maintainer after N sustained-quality contributions over M
months → lazy-consensus vote of current maintainers, 1 week, no sustained objection → added to
CODEOWNERS + org team + announced.)* Emeritus / step-down handling: {{emeritus_policy}}

> The guide favors letting *"people self-organize and volunteer for the roles they're most
> excited about, rather than assigning them."* Keep the ladder pull-based, not push-based.

## ✍️ Contribution Agreement (DCO vs. CLA)

Every inbound contribution needs a clear legal basis for the project to redistribute it under
its license (`{{project_license}}`). The OSS-Guides governance chapter does **not** prescribe a
mechanism, so this section is grounded in the two industry-standard instruments directly.

| Mechanism | What it is | Mechanics | Overhead | Use when |
|---|---|---|---|---|
| **DCO** — [Developer Certificate of Origin 1.1](https://developercertificate.org/) | A lightweight *attestation* (not copyright assignment): the contributor certifies they have the right to submit the code under the project license. | Each commit carries a `Signed-off-by: Name <email>` trailer (`git commit -s`); enforced by a [DCO bot](https://github.com/apps/dco) / `--signoff` CI check. | Very low — no account, no separate signature | Default for most community projects; keeps copyright with the author |
| **CLA** — Contributor License Agreement | A *signed agreement* granting the project (or its steward) explicit license — sometimes copyright assignment or a patent grant. | One-time signature via a CLA bot (e.g. [CLA Assistant](https://cla-assistant.io/)) before first merge; individual + corporate variants. | Higher — friction on first contribution; needs a legal entity to be the counterparty | Foundation-backed projects, relicensing flexibility, or strong patent-grant needs |

**Chosen mechanism for {{project_name}}: `{{contribution_agreement}}`.**

{{contribution_agreement_rationale}}
*(If DCO: confirm `git commit -s` is documented in CONTRIBUTING.md and the DCO check is a
required status check on `{{scm_host}}`. If CLA: name the legal counterparty, the bot, and
where signed agreements are stored. The two are not mutually exclusive but rarely combined.)*

> The DCO text is fixed and **must not be paraphrased** — link to `developercertificate.org`
> verbatim. The `Signed-off-by` line is the *only* artifact; it is not a place for extra prose.

## ⚖️ Decision-Making & Conflict Resolution

How {{project_name}} reaches a decision, and what happens when consensus fails.

| Decision class | Who decides | Mechanism |
|---|---|---|
| Routine (bugfix, docs, dep bump) | Any maintainer | {{routine_decision_rule}} (e.g. single-maintainer approval + green CI) |
| Significant (new feature, API change) | Maintainers | {{significant_decision_rule}} (e.g. lazy consensus: merge if no sustained objection in {{lazy_consensus_window}}) |
| Major / contested (license, governance, roadmap) | {{major_decision_body}} | {{major_decision_rule}} (e.g. formal vote, quorum {{quorum}}, threshold {{vote_threshold}}) |

- **Default mode:** {{default_decision_mode}}
  *(Meritocracy → "pure voting consensus" per the guide; Liberal contribution → "a consensus
  seeking process" where the burden is on objectors to propose an alternative, not just to
  block. BDFL → the dictator decides, ideally after soliciting input.)*
- **Recording decisions:** non-trivial choices are captured as ADRs ({{adr_location}}) so the
  rationale survives the people who made it.
- **Conflict resolution / escalation path:** {{conflict_resolution_process}}
  *(The OSS-Guides chapter is light on this; spell it out explicitly — e.g. "disagreement
  among maintainers escalates to {{steering_role_name}}; a tie is broken by {{tiebreaker}};
  Code-of-Conduct violations route to the separate CoC process below, never to the technical
  decision body.")*
- **Tie-breaker:** {{tiebreaker}}

## 🚢 Release Sign-off & Maintainer Responsibilities

Releases are the project's public promise; sign-off is the gate.

- **Who can cut a release:** {{release_authority}} (must hold the Maintainer role).
- **Release sign-off requirements:** {{release_sign_off_requirements}}
  *(e.g. CHANGELOG updated, version bumped, full test suite green, signed tag, ≥{{release_approvals}}
  maintainer approval(s), security review for any dependency change.)*
- **Versioning policy:** {{versioning_policy}} (e.g. SemVer; what constitutes a breaking change).
- **Release cadence:** {{release_cadence}}.
- **Signed releases:** {{signed_release_policy}} (GPG/Sigstore-signed tags & artifacts; publish
  the signing keys' provenance).

**Ongoing maintainer responsibilities** (the duties the role *owes* the community):

- [ ] Triage incoming issues & PRs within {{triage_sla}}.
- [ ] Uphold the Code of Conduct and act on reports per the process below.
- [ ] Keep dependencies patched; respond to security disclosures within {{security_sla}}.
- [ ] Mentor contributors toward the next rung of the role ladder.
- [ ] Step down gracefully (move to emeritus) rather than going silent — bus-factor hygiene.

## 🤝 Code of Conduct

A Code of Conduct is the social contract that makes the project safe to contribute to. The
OSS-Guides governance chapter does not specify one, so this section is grounded in the de-facto
standard: the **[Contributor Covenant](https://www.contributor-covenant.org/)** (latest version
is 3.0; the widely-adopted v2.1 below is the source of the four-tier enforcement ladder),
which is adopted by thousands of projects including the largest foundations.

- **Adopted CoC:** `{{code_of_conduct}}` (e.g. Contributor Covenant v2.1, verbatim).
- **File location:** `CODE_OF_CONDUCT.md` at repo root (so `{{scm_host}}` surfaces it in the
  community-health UI).
- **Scope:** applies in all project spaces and in public spaces when representing the project —
  per the Covenant's *Scope* clause.
- **Enforcement contact:** {{coc_contact}} — a private, monitored address **distinct** from
  public issue trackers. This is mandatory: an unenforced CoC is worse than none.
- **Enforcement Guidelines:** the Covenant v2.1 ships a four-tier ladder —
  **1. Correction → 2. Warning → 3. Temporary Ban → 4. Permanent Ban** — with a stated
  Community Impact and Consequence at each tier. {{project_name}} uses: {{coc_enforcement_ladder}}
- **Who handles reports:** {{coc_response_team}} *(deliberately separate from the technical
  decision body in § Decision-Making, so technical disagreements never get adjudicated as
  conduct issues, and vice versa.)*
- **Reporter protection:** {{coc_confidentiality_policy}} (confidentiality + anti-retaliation).

## 🏦 Legal Entity & Fiscal Hosting

Per the guide's section *"Do I need a legal entity to support my project?"*: **"You don't need
a legal entity to support your open source project unless you're handling money."** Decide only
if money, trademark, or liability is in play.

- **Does {{project_name}} handle money / need an entity?** {{needs_legal_entity}}
- **Fiscal host (if any):** {{fiscal_host}} — the guide notes *"a fiscal sponsor accepts
  donations on your behalf, usually in exchange for a percentage of the donation,"* and names
  *"Software Freedom Conservancy, Apache Foundation, Eclipse Foundation, Linux Foundation and
  Open Collective"* as examples.
- **Copyright / trademark holder:** {{copyright_holder}} *(the OSS-Guides chapter does not cover
  trademark; if the project name or logo matters, record who owns it and the usage policy
  separately.)*
- **Sponsorship / funding channels:** {{funding_channels}} (GitHub Sponsors, Open Collective, etc.).

## 📁 Where Governance Lives

Governance is only real if it's findable and version-controlled. Map each artifact to its file.

| Artifact | File | Status |
|---|---|---|
| This governance model + roles | `GOVERNANCE.md` | {{governance_md_status}} |
| Contribution mechanics (DCO/CLA, how to PR) | `CONTRIBUTING.md` | {{contributing_md_status}} |
| Code of Conduct | `CODE_OF_CONDUCT.md` | {{coc_md_status}} |
| Ownership → review routing | `CODEOWNERS` | {{codeowners_status}} |
| Maintainer roster / core team | {{maintainers_file}} | {{maintainers_file_status}} |
| Security disclosure process | `SECURITY.md` | {{security_md_status}} |
| License | `LICENSE` (`{{project_license}}`) | {{license_status}} |

> Keep the *model* in `GOVERNANCE.md` and the *mechanics* in `CONTRIBUTING.md` — don't duplicate.
> When this document and a root-level file disagree, the root-level file (which contributors
> actually read) is authoritative; update this doc to match in the same change.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
