---
template_name: AGENT_DESIGN
generate_when: "conditional"
required_decisions:
  - ai.enabled
  - ai.agent
  - project.type
optional_decisions:
  - ai.framework
  - ai.orchestration
  - ai.long_running
  - ai.persistent_memory
  - agent.autonomy
  - agent.execution
  - agent.memory
  - agent.hitl
  - agent.tools.sandbox
depends_on: []
revision_triggers:
  - ai.agent
  - ai.framework
  - ai.orchestration
  - agent.autonomy
  - agent.execution
  - agent.memory
  - agent.hitl
  - agent.tools.sandbox
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Agent Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

> This is the root agentic-system design doc for **{{project_name}}**. Its structure and
> guidance follow Anthropic's *[Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)*.
> The governing rule from that guidance: **find the simplest solution possible, and only
> increase complexity when needed** — when added complexity demonstrably improves outcomes.
> Every choice below is justified against that bar.

## Table of contents
- [🤖 Workflow vs. Agent: Which Are We Building?](#workflow-vs-agent-which-are-we-building)
- [🧱 The Augmented LLM (Foundational Block)](#the-augmented-llm-foundational-block)
- [🧩 Chosen Building-Block Pattern](#chosen-building-block-pattern)
- [♻️ The Agent Loop](#the-agent-loop)
- [🔧 Tool & Environment Design (ACI)](#tool-environment-design-aci)
- [🎚️ Autonomy & Stopping Conditions](#autonomy-stopping-conditions)
- [🧠 Memory & Context](#memory-context)
- [🛡️ Guardrails & Safety](#guardrails-safety)
- [👁️ Transparency & Observability](#transparency-observability)
- [📈 When to Add Complexity](#when-to-add-complexity)
- [↻ Revision Log](#revision-log)

## 🤖 Workflow vs. Agent: Which Are We Building?

Anthropic draws a sharp line between two architectures, distinguished by *who controls
the execution path*:

- **Workflow** — "systems where LLMs and tools are orchestrated through predefined code
  paths." The path is fixed by the engineer; the model fills in steps. Offers
  *predictability and consistency for well-defined tasks*.
- **Agent** — "systems where LLMs dynamically direct their own processes and tool usage,
  maintaining control over how they accomplish tasks." Better when *flexibility and
  model-driven decision-making are needed at scale*.

**{{project_name}} is built as a:** `{{chosen_pattern}}`
**(workflow / agent / single augmented LLM call).**

**Why this and not something simpler:** {{simplicity_justification}}

> Anthropic's framing of the decision: an **agent** is warranted for *open-ended problems
> where it's difficult or impossible to predict the required number of steps, and where you
> can't hardcode a fixed path.* If the task decomposes into known steps, prefer a workflow.
> If a single augmented LLM call with retrieval and good examples suffices, build that —
> "this might mean not building agentic systems at all." Agentic systems *trade latency and
> cost for better task performance*; record below why that trade is worth it here.

| Property | This project |
|---|---|
| Path predictability | {{path_predictability}} |
| Steps known in advance? | {{steps_predictable}} |
| Latency/cost tolerance | {{latency_cost_tolerance}} |
| Decision: simplest sufficient design | `{{chosen_pattern}}` |

## 🧱 The Augmented LLM (Foundational Block)

Per the guidance, the *augmented LLM* is the basic building block of every agentic system —
an LLM enhanced with **retrieval**, **tools**, and **memory**, where the model "actively
uses these capabilities — generating its own search queries, selecting appropriate tools,
and determining what information to retain."

| Augmentation | Decision for {{project_name}} |
|---|---|
| Base model | `{{primary_model}}` (fallback: `{{fallback_model}}`) |
| Retrieval | {{retrieval_approach}} — what external info the model can search (see RAG / AI&ML docs if applicable) |
| Tools | {{tool_set_summary}} — see [Tool & Environment Design](#tool-environment-design-aci) |
| Memory | {{memory_summary}} — see [Memory & Context](#memory-context) |

## 🧩 Chosen Building-Block Pattern

Anthropic catalogs five composable patterns, in roughly increasing order of autonomy.
State which one(s) {{project_name}} uses and why. Compose them rather than reaching for a
single monolithic agent.

| Pattern | What it is | Use when | Used here? |
|---|---|---|---|
| **Prompt chaining** | Decompose into sequential steps; each call processes the prior output (optionally with a gate check between steps). | The task cleanly decomposes into *fixed* subtasks; trade latency for accuracy. | {{uses_prompt_chaining}} |
| **Routing** | Classify the input, then dispatch to a specialized downstream prompt/model. | Distinct input categories are better handled separately (e.g. triage, model-size routing). | {{uses_routing}} |
| **Parallelization** | Run LLM calls concurrently and aggregate. *Sectioning* = independent subtasks; *Voting* = same task run multiple times for diverse outputs. | Subtasks parallelize for speed, or multiple perspectives/attempts raise confidence. | {{uses_parallelization}} |
| **Orchestrator-workers** | A central LLM *dynamically* breaks down the task, delegates to worker LLMs, and synthesizes. | Complex tasks where you *can't predict* the subtasks (e.g. multi-file edits, multi-source search). | {{uses_orchestrator_workers}} |
| **Evaluator-optimizer** | One LLM generates; a second evaluates and feeds back, in a loop. | Clear evaluation criteria exist and *iterative refinement provides measurable value*. | {{uses_evaluator_optimizer}} |

**Primary pattern:** `{{chosen_pattern}}`
**Composition / topology:** {{pattern_composition}}
*(Describe how the patterns combine — e.g. "router selects a worker; orchestrator fans out;
evaluator gates the final answer." Reference the C4 / component diagram if one exists.)*

## ♻️ The Agent Loop

> Applies when `{{chosen_pattern}}` is an autonomous agent or orchestrator. Omit the loop
> specifics if {{project_name}} is a pure predefined workflow (the path *is* the loop).

Anthropic's mechanic: "Agents are typically just LLMs using tools based on environmental
feedback in a loop." The agent begins with a command or discussion with the human; once the
task is clear, it plans and operates independently, returning to the human for information
or judgement as needed. The loop shape for {{project_name}}:

```
{{agent_loop_diagram}}

  1. GATHER CONTEXT   — receive task; pull state/retrieval; understand the goal
  2. PLAN / DECIDE    — reason about the next step, select the tool
  3. ACT (via tools)  — call the tool / execute code in the environment
  4. OBSERVE          — read the *ground truth* the environment returns
  5. VERIFY           — did the action move us toward the goal? error? blocker?
       ├─ progress  → loop back to step 2
       ├─ done      → return result
       └─ blocked   → escalate to human (see Stopping Conditions)
```

> **Ground truth from the environment is non-negotiable.** Anthropic: "it's crucial for the
> agents to gain 'ground truth' from the environment at each step (such as tool call results
> or code execution)." Document below exactly what feedback signal closes each loop iteration —
> a real tool result, a test run, a type check, a search hit — not the model's own assertion
> that it succeeded.

| Loop element | Decision |
|---|---|
| Trigger / entry | {{loop_trigger}} |
| Ground-truth signal per step | {{ground_truth_signal}} |
| Verification step | {{verification_step}} |
| Iteration state carried between steps | {{loop_state}} |

## 🔧 Tool & Environment Design (ACI)

Anthropic: "invest just as much effort in creating good *agent*-computer interfaces (ACI)"
as in human-computer interfaces — they "actually spent more time optimizing our tools than
the overall prompt." Design the tool surface deliberately.

**Tool catalog**

| Tool | Purpose | Input format | Returns (ground truth) |
|---|---|---|---|
| {{tool_1_name}} | {{tool_1_purpose}} | {{tool_1_input}} | {{tool_1_output}} |
| {{tool_2_name}} | {{tool_2_purpose}} | {{tool_2_input}} | {{tool_2_output}} |
| {{additional_tools}} | … | … | … |

**ACI design rules** (apply each to the catalog above):

- **Give the model room to think.** Allow enough tokens *before* the model commits to an
  action so it doesn't "write itself into a corner." {{thinking_budget}}
- **Use natural formats.** Keep tool inputs/outputs close to what the model has seen in
  training text; avoid formats with bookkeeping overhead (line counts, heavy string-escaping).
  Chosen format: {{tool_format}}
- **Write tool docs as if for a junior engineer.** Each definition includes example usage,
  edge cases, input-format requirements, and clear boundaries from neighboring tools.
- **Poka-yoke (mistake-proof) the arguments.** Shape parameters so wrong usage is hard —
  Anthropic's canonical example: requiring *absolute* filepaths instead of relative ones
  eliminated a whole class of errors. Poka-yoke measures here: {{poka_yoke_measures}}

**Environment** (where the agent acts): {{agent_environment}}
*(local FS, sandboxed VM, browser, API surface, MCP servers, etc. — and the blast radius
each tool can touch.)*

## 🎚️ Autonomy & Stopping Conditions

**Autonomy level:** `{{agent_autonomy}}`
*(e.g. fully autonomous / supervised-step / suggest-only / human-approves-each-action.)*
**Execution mode:** `{{agent_execution}}`  ·  **Long-running?** {{long_running}}

Because "the autonomous nature of agents means higher costs, and the potential for
compounding errors," every loop needs explicit brakes. Define them:

| Stopping condition | Value |
|---|---|
| Natural completion criterion | {{completion_criterion}} |
| Max iterations / turn budget | {{max_iterations}} |
| Cost / token ceiling | {{cost_ceiling}} |
| Human-in-the-loop checkpoints | {{hitl_checkpoints}} |
| Blocker → escalate to human | {{escalation_policy}} |

> Human review remains crucial — "particularly in coding contexts" — for ensuring solutions
> align with broader system requirements. Specify above where {{project_name}} pauses for
> judgement (`agent.hitl`).

## 🧠 Memory & Context

What the agent retains across steps and across sessions, and where it lives.

- **Within-loop (working) memory:** {{working_memory}}
- **Cross-session / persistent memory:** {{persistent_memory}} (`ai.persistent_memory`)
- **Context-window management:** {{context_management}} — truncation / summarization /
  retrieval-on-demand strategy as the trajectory grows.
- **State store:** {{state_store}} — where trajectory + intermediate results are persisted
  (needed for long-running or resumable agents).

## 🛡️ Guardrails & Safety

Anthropic recommends "extensive testing in sandboxed environments, along with the
appropriate guardrails."

- **Sandboxing:** {{sandbox_policy}} (`agent.tools.sandbox`) — isolation level for tool
  execution and the blast radius cap.
- **Input/output filtering:** {{io_guardrails}} — prompt-injection screening on
  tool-returned content, output moderation, PII handling.
- **Compounding-error containment:** {{error_containment}} — how a bad step is detected and
  prevented from cascading (verify-before-act, write-then-read-back, dry-run modes).
- **Destructive-action policy:** {{destructive_action_policy}} — which actions require
  confirmation, are reversible, or are forbidden.
- **Test strategy:** {{agent_test_strategy}} — trajectory replay, golden-task suite,
  adversarial inputs, sandboxed end-to-end runs gating releases.

## 👁️ Transparency & Observability

Anthropic's second core principle: "Prioritize *transparency* by explicitly showing the
agent's planning steps." Make the trajectory legible.

- **Plan visibility:** {{plan_visibility}} — surface the agent's reasoning/plan to the
  operator (not just the final answer).
- **Trace & logging:** {{trace_logging}} — per-step record of tool calls, inputs, ground-truth
  results, and decisions (tool/SDK: {{observability_tool}}).
- **Evaluation harness:** {{eval_harness}} — how trajectories and outcomes are scored over time.

## 📈 When to Add Complexity

The three principles to revisit at every iteration (Anthropic's conclusion): **maintain
simplicity**, **prioritize transparency**, and **carefully craft the ACI** through thorough
tool documentation and testing.

| Trigger to escalate | Current design | Next step if triggered |
|---|---|---|
| Single call no longer accurate enough | `{{chosen_pattern}}` | {{escalation_to_workflow}} |
| Fixed path can't cover real inputs | — | {{escalation_to_agent}} |
| Latency/cost unacceptable | — | {{simplify_step}} |

**Open questions / deferred decisions:** {{open_questions}}

> Frameworks (`{{ai_framework}}`) can speed the start, but "don't hesitate to reduce
> abstraction layers and build with basic components as you move to production." Add an agent
> framework only when it earns its abstraction here.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
