---
template_name: POSTMORTEM_TEMPLATE
generate_when: "conditional"
required_decisions:
  - production_bound
  - scale
optional_decisions:
  - team_size
  - scm.host
depends_on: []
revision_triggers: []
---

# Incident Postmortem — {{project_name}}

> A **blameless** incident postmortem template for {{project_name}}, grounded in
> [Google SRE — Postmortem Culture](https://sre.google/sre-book/postmortem-culture/).
> Copy this per incident. The guiding principle: **"the cost of failure is education."**
> Assume everyone involved acted with good intent and the best information they had —
> investigate the *system and process* gaps that let the incident happen, never the people.
> Naming an individual as a root cause is a smell; ask what made the failure *possible*.

## When to write one (trigger criteria)

Open a postmortem when any of these hold (a stakeholder may also request one):
- User-visible downtime or degradation beyond {{slo_or_threshold}}.
- Any data loss.
- On-call intervention (rollback, traffic reroute, manual mitigation).
- Time-to-resolution exceeded {{resolution_threshold}}.
- A monitoring/alerting gap meant the issue was found manually.

---

## Metadata

| Field | Value |
|---|---|
| Incident ID | {{incident_id}} |
| Title | {{incident_title}} |
| Severity | {{severity}} |
| Status | {{status}} (draft / in-review / final) |
| Authors | {{authors}} |
| Date of incident | {{incident_date}} |
| Date of postmortem | {{postmortem_date}} |

## Summary

{{one_or_two_sentence_summary}} — what broke, who/what was affected, for how long, and the root cause in a sentence.

## Impact

- **User impact:** {{user_impact}} (who, what they experienced, how many).
- **Duration:** {{impact_start}} → {{impact_end}} ({{impact_duration}}).
- **Scope / blast radius:** {{blast_radius}}.
- **Business/data impact:** {{business_or_data_impact}} (revenue, SLA/SLO burn, data loss).

## Timeline (UTC)

Reconstruct the sequence — detection, escalation, mitigation, resolution. Be specific.

| Time (UTC) | Event |
|---|---|
| {{ts}} | {{event}} |
| {{ts}} | {{event}} |
| … | … |

## Root cause(s)

{{root_cause_analysis}} — go deep enough (e.g. 5-whys / contributing-factors). Capture the
**contributing factors**, not just the proximate trigger. There is often more than one cause.

## Trigger

{{trigger}} — the specific change/event/condition that set the incident in motion
(deploy, config change, traffic spike, dependency failure, …).

## Detection

{{detection}} — how was it detected (alert / customer report / manual)? How long until
detection? If detection was slow or manual, that itself is an action item.

## Resolution / mitigation

{{resolution}} — what actions stopped the bleeding and restored service, and in what order.

## Lessons learned

- **What went well:** {{what_went_well}}.
- **What went wrong:** {{what_went_wrong}}.
- **Where we got lucky:** {{where_we_got_lucky}}.

## Action items

Track every follow-up to completion. Each item is **specific, owned, and tracked**, prioritised
by severity, and aimed at a *systemic* fix (prevention, faster detection, safer mitigation) —
not "be more careful." Prefer items that make the failure structurally impossible or auto-detected.

| Action item | Type (prevent / detect / mitigate / process) | Owner | Tracking ref | Priority | Due |
|---|---|---|---|---|---|
| {{action_item}} | {{type}} | {{owner}} | {{ticket}} | {{priority}} | {{due}} |

## Supporting information

{{links}} — dashboards, logs, traces, alerts, related incidents, chat transcript.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
