<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Runtime Budgets Reference

Per-agent budget catalog and the orchestrator's observer-wrapper logic.

## Per-agent budget table

| Agent | typical_minutes | max_minutes | Notes |
|---|---|---|---|
| research-scout | 5 | 15 | Web fetches dominate; bounded by `max_results` |
| architecture-specialist | 6 | 15 | Phase-3 style/boundaries questioning + research |
| document-author | 3 | 10 | Single template fill; well-bounded |
| claude-md-author | 3 | 8 | Hierarchy of small files |
| claude-tooling-author | 10 | 20 | Many small files (settings, hooks, commands) |
| decision-revisor | 5 | 12 | Surgical patch; touches ≤4 docs |
| design-recovery | 6 | 15 | Reconstructs an existing project's design (re-architect) |

> The quality gate is **not** a subagent in v8 — it is the in-process `architect-brain audit` (35 checks), run by the orchestrator as a direct Bash call, so it has no dispatch budget.

## Observer wrapper

The orchestrator wraps every `Agent({...})` dispatch with observation logic. The observer **never blocks** — it only surfaces telemetry.

### What the observer does

```
when dispatching agent X with budget {typical, max}:
  start_time = now()
  log "dispatching X (budget: typical={typical}min, max={max}min)"

while X is running:
  on each progress message from X:
    last_progress = now()
    log "X: <progress message>"
  if (now() - last_progress) > (typical / 3) minutes:
    log "X silent for too long; agent may be stuck"
  if (now() - start_time) > max minutes:
    log "X over max budget — consider Esc + re-dispatch with tighter scope"
    # Do NOT auto-kill — some work legitimately takes longer

when X returns:
  elapsed = now() - start_time
  agent_work_time = elapsed   # total includes user-wait if user was prompted; for cleaner accounting, use elapsed during dispatch only
  log "X returned in {elapsed}min (budget: {typical}/{max})"
  if elapsed > typical:
    record telemetry: { agent: X, elapsed, scope: <dispatch_envelope_summary> }
    flag for the Iteration-phase menu: "agent X cost {elapsed}min (typical {typical}min) — review scope"
```

### Why observation, not enforcement

Auto-killing an agent is risky: some legitimate work takes longer (large input, complex revision, network slowness). The observer model:
- Surfaces cost overruns in real time (so user can intervene)
- Records telemetry for tuning (which agents repeatedly overrun?)
- Pre-populates the Iteration-phase menu with "review scope of agent X" items
- Never silently kills work-in-progress

### Timer attribution

The visible elapsed time for an agent dispatch can include **user-wait time** (architect blocked on `AskUserQuestion`). For cost analysis, the observer SHOULD subtract user-wait intervals to compute `agent_work_time`. For user transparency, show `total_elapsed`. Detailed user-wait attribution is an optional refinement.

## Telemetry — inline, not persisted

v8 state is event-sourced (`docs/_architect_state/`) and has **no agent-dispatch event type**, so the observer's timing telemetry is **inline only**: it surfaces overruns in the transcript and seeds the Iteration-phase menu. It is never written to the event log — dispatch timing is non-deterministic and would break the `replay(events) == projections` invariant. A surfaced overrun reads, e.g.:

```
agent decision-revisor returned in 31.5min (budget: 5/12) — over max; review scope in the Iteration menu
```

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
