<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Agent common — runtime budget + scope discipline

Every project-architect subagent shares this trailing contract. Each agent prompt references this file instead of repeating it.

## Runtime budget

Your typical runtime budget is per the frontmatter `typical_minutes`; max is `max_minutes`.

**Surface a brief progress message** after each significant step:
```
[STEP N/M] <one-line description of what you just did>
```

If you anticipate exceeding `typical_minutes`: surface why and continue.
If you anticipate exceeding `max_minutes`: STOP and report:

```
PARTIAL_COMPLETION
- Done: <list>
- Remaining: <list>
- Reason: <one-line why this took longer than budget>
```

The orchestrator decides whether to extend, split, or escalate. Do NOT silently continue past `max_minutes`.

## Scope discipline

- Do ONLY what the dispatch envelope asks
- Do NOT audit unrelated docs/agents/decisions
- Treat out-of-scope findings as Phase 5 menu items (use `OUT_OF_SCOPE_FINDINGS:` block — see decision-revisor for canonical format)

## Reference & template paths

Every reference / template / catalog / playbook path in your INPUTS is **absolute** — the orchestrator expands `${CLAUDE_PLUGIN_ROOT}` before dispatching you. Read those paths exactly as given; do not prepend or reconstruct a relative form.

- A path into your OWN project workspace (`docs/…`) is relative to your cwd — read it relative.
- If you are handed a path INTO THE PLUGIN that is **bare / relative** (e.g. `skills/project-architect/references/…` with no absolute prefix), it is **unresolvable from your cwd** (you run in the user's project, not the plugin root) — do NOT guess, fabricate, or substitute a default. Treat it as a **BLOCKER**: return the informational error state (what you needed + the path you were given) and stop.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
