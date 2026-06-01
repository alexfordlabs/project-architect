---
template_name: ON_CALL_GUIDE
generate_when: "conditional"
required_decisions:
  - production_bound
  - team_size
  - scale
optional_decisions:
  - ops.observability
  - ops.slo_defined
  - ops.incident_tooling
  - ops.runbooks
  - team.distribution
  - constraints.labor_law
depends_on: []
revision_triggers:
  - production_bound
  - team_size
  - scale
  - team.distribution
  - ops.slo_defined
  - ops.incident_tooling
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# On-Call Guide: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the on-call operations guide for **{{project_name}}** — a production-bound system run by a team of **{{team_size}}** at **{{scale}}** scale. Its structure and guidance follow the **[Google SRE Workbook — On-Call](https://sre.google/workbook/on-call/)**, the current authoritative reference for running a sustainable, humane on-call rotation. The governing principle: on-call exists to keep the service reliable *without burning out the humans who run it*. Every section below records THIS project's concrete policy, not a generic aspiration. Where a value is project-specific, it is a `{{placeholder}}` to be filled at lock time.

## Table of contents
- [👥 Rotation Model & Staffing](#rotation-model-staffing)
- [⏱️ Shift Structure & Handoff](#shift-structure-handoff)
- [🔔 Alert Taxonomy: Page vs. Ticket vs. Info](#alert-taxonomy-page-vs-ticket-vs-info)
- [📟 Pager Response SLOs](#pager-response-slos)
- [🚦 Escalation Paths](#escalation-paths)
- [📚 Playbooks & On-Caller Resources](#playbooks-on-caller-resources)
- [📉 Pager Load Targets & Operational Balance](#pager-load-targets-operational-balance)
- [🔁 Flexibility: Swaps, Breaks & Part-Time](#flexibility-swaps-breaks-part-time)
- [💰 Compensation](#compensation)
- [🤝 Team Dynamics & Psychological Safety](#team-dynamics-psychological-safety)
- [🎓 Onboarding to the Rotation](#onboarding-to-the-rotation)
- [📊 Pager Load Tracking & Review Cadence](#pager-load-tracking-review-cadence)
- [↻ Revision Log](#revision-log)

## 👥 Rotation Model & Staffing

The Workbook warns that "24 hours of on-call duty without reprieve isn't a sustainable setup" and sets concrete minimum-staffing floors so that **each rotation leaves enough headroom for project work**. Pick the model that matches `team.distribution` and record the staffing math.

| Model | Workbook minimum | Use when |
|---|---|---|
| Single-site, 24/7 | **9 people** (8 + 1 buffer) | One location must cover the full day |
| Multi-site / follow-the-sun | **6 per site** (5 + 1 buffer) | Two paired sites cover each other's night |

**{{project_name}}'s rotation model:** `{{rotation_model}}`
**Sites in rotation:** {{rotation_sites}} (`team.distribution`)
**Engineers in rotation:** {{rotation_headcount}} — _the "+1 buffer" exists specifically to absorb long-term breaks; do not staff to the bare minimum._

> If the team is below the Workbook floor for the chosen model, this is a flagged risk: document the compensating measure (reduced coverage hours, a shared rotation with a sibling team, or accepting that an absence collapses the rotation). State it here: {{understaffing_mitigation}}

## ⏱️ Shift Structure & Handoff

The Workbook recommends **limiting shift lengths to 12 hours** as the sustainable optimum, with day/night splits inside a single site or 3-days-on / 4-days-off cadences as alternatives.

| Property | Decision for {{project_name}} |
|---|---|
| Shift length | {{shift_length}} (≤ 12h recommended) |
| Rotation cadence | {{rotation_cadence}} (e.g. weekly, 3-on/4-off) |
| Primary on-caller | {{primary_role}} — first responder to every page |
| Secondary on-caller | {{secondary_role}} — backup + escalation point; covers extended incidents and missed pages |

**Handoff procedure** (the Workbook makes this a hard ritual, not an optional courtesy):

1. **Start of shift** — the incoming on-caller reads the handoff from the previous shift before doing anything else.
2. **During shift** — the on-caller minimizes user impact *first*, then ensures issues are *fully* addressed (no "it fixed itself" closures).
3. **End of shift** — the outgoing on-caller sends a handoff note to the next engineer covering: open incidents, in-flight mitigations, flapping alerts, and anything the next person must watch.

**Handoff channel / template:** {{handoff_channel}} (`ops.incident_tooling`)

## 🔔 Alert Taxonomy: Page vs. Ticket vs. Info

The single most important alert rule from the Workbook: **"All alerts should be immediately actionable. There should be an action we expect a human to take immediately after they receive the page that the system is unable to take itself."** A low signal-to-noise ratio causes alert fatigue, which is the root cause of missed real incidents.

Adopt the three-tier model (Evernote's P1/P2/P3, as cited in the Workbook):

| Tier | Channel | Criteria | This project's examples |
|---|---|---|---|
| **P1 — Page** | Wakes the on-caller | Immediately actionable **and** SLO-impacting | {{p1_examples}} |
| **P2 — Ticket** | Email / queue, work-hours | Not customer-facing or limited scope; needs human action but not *now* | {{p2_examples}} |
| **P3 — Info** | Dashboards / passive email | Awareness only; no action expected | {{p3_examples}} |

**Alerting philosophy:** {{alerting_philosophy}} — state whether {{project_name}} uses **SLO-based / symptom-based alerting** (paging on error-budget burn) (`ops.slo_defined`) or threshold/cause-based alerting, and why. The Workbook is blunt: under SLO-based alerting, "relaxing alert thresholds is rarely an appropriate response to being paged" — fix the cause, don't silence the symptom.

**New-alert discipline:** every new alert (a) ships with a corresponding playbook entry and (b) runs in **test mode for ~1 week** to experience typical periodic production conditions before it can page a human.

## 📟 Pager Response SLOs

Response-time expectations follow from the user-facing impact of the alert, not from how the alert was built. Mirror the Workbook's Table 8-1 tiers and set the constraint each tier places on the on-caller.

| Impact tier | Target response | On-caller constraint |
|---|---|---|
| Revenue / availability-critical outage | {{p1_response_target}} (e.g. **5 min**) | Within arm's reach of a charged, authenticated laptop with network access at all times during the shift |
| Degraded but bounded (e.g. batch failure) | {{p2_response_target}} (e.g. **30 min**) | Free to run a short errand; must stay reachable |
| Non-urgent | Next business hours (ticket) | No paging; handled during work hours |

**Acknowledgement vs. resolution.** {{ack_vs_resolve_policy}} — define the *acknowledge* deadline (the on-caller has seen it) separately from any *mitigation* target. If acknowledgement lapses, auto-escalate (see below).

## 🚦 Escalation Paths

Psychological safety depends on the on-caller *never being stuck alone*. "On-call engineers should be fully supported by a series of procedures and escalation paths to make their lives easier." Define the full ladder explicitly so escalation is a documented action, not a judgement call made at 3 a.m.

| Step | Who | Trigger to escalate to this level |
|---|---|---|
| 1 | Primary on-caller | The page fires |
| 2 | Secondary on-caller | Primary doesn't ack within {{secondary_escalation_window}}, or needs a second pair of hands |
| 3 | {{escalation_l3}} (e.g. service owner / domain expert) | Incident exceeds {{l3_trigger}} (duration, blast radius, or expertise gap) |
| 4 | {{escalation_l4}} (e.g. eng manager / incident commander) | {{l4_trigger}} — customer-facing major incident, security event, or needs cross-team coordination |

**Cross-team / vendor escalation:** {{external_escalation}} — how to reach upstream dependency owners, cloud-provider support, and the contacts/SLAs for each (`ops.incident_tooling`).
**It is always OK to escalate.** State the cultural norm plainly: {{escalation_culture}}.

## 📚 Playbooks & On-Caller Resources

The Workbook: "whenever an alert is created, a corresponding playbook entry is usually created. These guides reduce stress, the mean time to repair (MTTR), and the risk of human error." An on-caller's effectiveness is bounded by the resources handed to them.

The on-caller for {{project_name}} must have, before their first shift:

- **Per-alert playbooks** — {{playbook_location}} (`ops.runbooks`). Every P1 alert links directly to its playbook entry; the entry covers diagnosis steps, known causes, and the standard mitigations below.
- **Standard mitigations available** — {{standard_mitigations}} (roll back a release — *preferred over a quick fix*; drain traffic away from the affected component; flip a feature flag; rate-limit; add capacity).
- **Monitoring consoles** — {{monitoring_consoles}} (`ops.observability`). Pages link to the relevant console, and the console highlights where the system is operating out of spec.
- **Access & credentials** — {{oncall_access}} — production access, break-glass procedure, and how credentials are obtained without delay during an incident.
- **Change timeline** — {{change_timeline}} — a searchable log of recent deploys/config changes, so a page can be correlated to "what changed."

## 📉 Pager Load Targets & Operational Balance

The Workbook's hard ceiling: **"We target a maximum of two incidents per on-call shift"** (one *problem* per 12-hour shift, regardless of how many individual alerts fired). Exceeding this consistently means **"corrective action is warranted"** — the fix is to reduce load, not to ask people to endure more.

| Target | Value |
|---|---|
| Max paging incidents per shift | **2** (Workbook standard) |
| Project-work floor | **≥ 50%** of engineering time on project work (Workbook standard) — protects the time needed to *fix* the things that page |
| Current measured load | {{current_pager_load}} (pages/shift, 21-day trailing average) |

**When over budget:** {{over_budget_policy}} — the Workbook's three load drivers are (1) production bugs, (2) alerting configuration, and (3) human follow-up rigor. Name which driver dominates here and the standing commitment to drive it down (e.g. "any shift exceeding 2 pages produces a load-reduction action item in the next production review").

> **Follow-up rigor.** "Explaining away a page as 'transient,' or taking no action because the system 'fixed itself'… invites the bug to happen again." Every page gets a root cause — and root causes "extend out of the machine and into the team's processes." Post-incident review for {{project_name}}: {{postmortem_policy}}.

## 🔁 Flexibility: Swaps, Breaks & Part-Time

A humane rotation bends without breaking. Document the mechanisms:

- **Short-term swaps:** {{swap_policy}} — peer-reviewed shift swaps with a documented process for both urgent and planned cases.
- **Schedule immutability:** once a schedule is published, the tooling **never silently rewrites an already-generated schedule** — changes happen via explicit, recorded swaps.
- **Long-term breaks (leave, sabbatical):** {{long_break_policy}} — the "+1 buffer" per site is what absorbs a temporarily-reduced roster.
- **Part-time integration:** {{part_time_policy}} — part-time engineers carry a *proportionately smaller* share of on-call (reduced full days, or split/shorter shifts), never an equal share.
- **Scheduling tool:** {{scheduling_tool}} — rebalances load fairly using personal preferences and historical load.

## 💰 Compensation

On-call work **should be compensated** — both to reward the burden and to ensure "engineers do not take on too many on-call shifts for economic reasons."

| Aspect | Decision for {{project_name}} |
|---|---|
| Model | {{compensation_model}} (time-off-in-lieu / cash / both) |
| Cap | {{compensation_cap}} — capped at some proportion of overall salary (per Workbook) |
| Legal basis | {{labor_law_basis}} — must conform to local labor law and regulations (`constraints.labor_law`) |

> If {{project_name}} cannot offer cash compensation at its current stage, state the explicit alternative (time-off-in-lieu, reduced shift frequency) — *uncompensated, unbounded on-call is the anti-pattern this section exists to prevent.*

## 🤝 Team Dynamics & Psychological Safety

"Psychological safety is vital for effective on-call rotations." The failure mode the Workbook names is the **"survive the week" mentality** — high volume, duplicate-page fatigue, new features prioritized over follow-up, ownership eroding. Counter it deliberately:

- **Blameless culture:** {{blameless_culture}} — postmortems target processes and systems, never individuals. The question is "how do we prevent this class of bug," not "who broke it."
- **Ownership:** {{ownership_model}} — whoever runs the rotation owns the reliability roadmap, drives full resolution, and maintains the monitoring rules — and is empowered to *implement* fixes, not just file them.
- **Team cohesion:** {{team_cohesion}} — co-locating (physically or virtually) everyone in the rotation regardless of title, plus deliberate team-bonding investment, measurably improves on-call.

## 🎓 Onboarding to the Rotation

No engineer joins the rotation cold. Define the path to "first solo shift":

- **Pre-on-call checklist:** {{oncall_readiness_checklist}} — the focus areas a new on-caller must be fluent in: administering production jobs, traffic draining, rollback, rate-limiting, capacity increases, the monitoring stack, and the system's architecture & dependencies.
- **Training methods:** {{training_methods}} — shadowing outgoing on-callers, hands-on labs for "muscle memory" on debugging/mitigation, and **"Wheel of Misfortune"** disaster role-plays of recent incidents.
- **Shadow → primary timeline:** {{shadow_timeline}} — e.g. shadow for the first month(s), then become primary with an experienced backup before going fully solo.

## 📊 Pager Load Tracking & Review Cadence

"The quality of the data you collect will determine the quality of the decisions either humans or automata can make." Track the load and review it on a regular cadence so problems surface as trends, not as burnout.

**Metrics tracked for {{project_name}}:** {{tracked_metrics}}
- Pages per shift (target: ≤ 2)
- 21-day trailing average of pager load
- MTTR (mean time to repair)
- % of shifts exceeding the pager budget
- Root-cause identification rate
- Bug-to-page correlation (which bugs/components cause the most pages)

**Review cadence:** {{review_cadence}} — a recurring production / service review where pager-load trends are discussed openly as "a barometer of team health," and over-budget shifts generate concrete load-reduction action items.
**Data store / tooling:** {{load_data_store}} (`ops.incident_tooling`) — structured data linking each paging incident to its bug ticket, so the analysis above is possible.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
