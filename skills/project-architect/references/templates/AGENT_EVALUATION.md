---
template_name: AGENT_EVALUATION
generate_when: "conditional"
required_decisions:
  - ai.enabled
  - ai.agent
optional_decisions:
  - ai.framework
  - ai.orchestration
  - ai.model
  - agent.execution
  - agent.tools.sandbox
  - agent.hitl
depends_on:
  - AGENT_DESIGN
revision_triggers:
  - ai.agent
  - ai.framework
  - ai.model
  - agent.execution
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Agent Evaluation: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}
>
> This document defines how the agent described in [`AGENT_DESIGN.md`](AGENT_DESIGN.md) is measured for quality, correctness, and regression-safety. The structure follows the [LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts): an **experiment** is the result of running a **target** (an application version) over a **dataset** of **examples**, scored by one or more **evaluators**. We use that vocabulary throughout even when the runtime harness is something other than LangSmith ({{eval_harness}}).

## Table of contents
- [Why we evaluate this agent](#why-we-evaluate-this-agent)
- [Evaluation harness](#evaluation-harness)
- [Datasets & examples](#datasets-examples)
- [What we evaluate (the four levels)](#what-we-evaluate-the-four-levels)
- [🔧 Evaluators](#evaluators)
- [📊 Success metrics & scoring](#success-metrics-scoring)
- [Offline vs. online evaluation](#offline-vs-online-evaluation)
- [Pairwise & regression evaluation](#pairwise-regression-evaluation)
- [👤 Human review & annotation queues](#human-review-annotation-queues)
- [🚦 Evaluation in CI / quality gates](#evaluation-in-ci-quality-gates)
- [Eval cadence & ownership](#eval-cadence-ownership)
- [↻ Revision Log](#revision-log)

## Why we evaluate this agent

A statement of the quality bar this agent must clear before shipping and the failure modes evaluation is designed to catch. Because the agent (`ai.agent == true`) makes multi-step decisions — tool selection, argument formatting, looping — a single end-to-end pass/fail score hides where it breaks. This document commits to measuring the agent at multiple levels so a regression in *how* it solves a task is caught even when the *final answer* still happens to be right.

- **Primary quality bar:** {{primary_quality_bar}} (e.g., "≥ {{target_pass_rate}}% correctness on the core dataset before any prompt or model change ships").
- **Failure modes we explicitly test for:** {{tracked_failure_modes}} (e.g., wrong tool selected, malformed tool arguments, infinite/over-long loops, hallucinated facts, unsafe actions, ignoring retrieved context).
- **Out of scope here:** raw model benchmarking and infra/load testing — see the relevant ops docs.

## Evaluation harness

The concrete tooling that runs experiments and stores results.

| Aspect | Choice |
|---|---|
| Harness / platform | {{eval_harness}} (e.g., LangSmith, Braintrust, Anthropic Console evals, custom pytest + JSON) |
| Agent framework under test | {{ai_framework}} |
| Model(s) under test | {{primary_model}} (+ fallbacks: {{fallback_models}}) |
| Where datasets live | {{dataset_location}} (e.g., LangSmith dataset `{{eval_dataset}}`, versioned JSONL in `evals/datasets/`) |
| Where results live | {{results_location}} (experiment store, dashboard, CI artifact) |
| SDK / invocation | {{eval_sdk}} (e.g., LangSmith Python/TS SDK, in-repo runner) |

The **target** is a thin wrapper that takes an example's `inputs` and returns the agent's output (and, where supported, its intermediate steps / run tree) so trajectory-aware evaluators can inspect the path, not just the final response.

## Datasets & examples

Following LangSmith's model, a **dataset** is a curated collection of **examples**, and each example carries:

- **Inputs** — the dictionary of variables handed to the agent (`{{example_inputs_shape}}`).
- **Reference outputs** *(optional)* — the expected answer and/or expected trajectory. Per LangSmith, reference outputs are consumed **only by evaluators** and are never passed to the agent.
- **Metadata** *(optional)* — labels for filtered views (difficulty, feature area, customer segment, `{{example_metadata_keys}}`).

### Datasets in this project

| Dataset | Purpose | Size (target) | Split(s) |
|---|---|---|---|
| `{{eval_dataset}}` | Core correctness / regression suite | {{core_dataset_size}} | {{dataset_splits}} (e.g., smoke / full / edge-cases) |
| {{secondary_dataset}} | {{secondary_dataset_purpose}} | {{secondary_dataset_size}} | — |

We use **splits** (not just metadata) to separate, e.g., a fast `smoke` subset for every PR from the `full` suite run nightly, mirroring an ML train/validation/test partition.

### How examples are created

Per LangSmith's three strategies, this project sources examples from:

1. **Manual curation** — start with {{manual_example_count}} (LangSmith suggests 10–20) high-quality examples spanning common scenarios **and** edge cases. Owner: {{dataset_owner}}.
2. **Historical traces** — promote real production/staging runs into examples (filtered by user feedback or heuristics): {{trace_promotion_policy}}.
3. **Synthetic data** — generate variations from templates for coverage breadth: {{synthetic_data_policy}} (or "not used").

For trajectory examples we additionally record, per LangSmith's agent guidance, **an ordered list of the steps we expect the agent to take** — node names and tool invocations — stored as `{{expected_trajectory_field}}`.

## What we evaluate (the four levels)

LangSmith distinguishes several agent-evaluation strategies. We declare which we use and why.

### 1. Final-response evaluation
Evaluate the agent's **final output** against a reference response. Best for "did it ultimately get the right answer?" using LLM-as-judge (factual accuracy vs. ground truth) or binary correctness.
- **In use:** {{final_response_eval}} (yes/no). **Evaluators:** {{final_response_evaluators}}.

### 2. Single-step evaluation
Evaluate **one agent step in isolation** — e.g., "does it select the appropriate first tool?" or "does the intent classifier route to the right subagent?". Great for debugging a component before full end-to-end runs. Datasets capture intermediate states / single decision points with expected outputs.
- **In use:** {{single_step_eval}} (yes/no). **Steps under test:** {{single_step_targets}}.

### 3. Trajectory evaluation
Evaluate **whether the agent took the expected path** of tool calls to reach the answer. We use subsequence matching with **partial credit** (LangSmith): score based on how many expected steps appear, in order, within the actual trajectory — so an agent that takes some correct steps still scores above zero.
- **In use:** {{trajectory_eval}} (yes/no). **Match policy:** {{trajectory_match_policy}} (exact / ordered-subsequence / unordered / LLM-judged).

### 4. End-to-end task success
The composite "did the whole task succeed" signal that {{end_to_end_definition}} — typically a combination of (1) and (3) gated together.

> **Decision:** for {{project_name}} the binding levels are **{{evaluation_levels_in_use}}**. Rationale: {{evaluation_levels_rationale}}.

## 🔧 Evaluators

Each evaluator is a scoring function returning **feedback** — a `key`, a `score` (numeric) or `value` (categorical), and an optional `comment`. We mark each as **reference-based** (needs an expected output) or **reference-free** (judges criteria directly).

### LLM-as-judge
An LLM scores the output, either reference-free (criteria adherence) or reference-based (vs. expected output). Requires prompt tuning; few-shot examples improve reliability.

| Evaluator | Judges | Ref-based? | Judge model | Output (score/value) |
|---|---|---|---|---|
| {{judge_eval_name}} | {{judge_eval_criteria}} | {{judge_ref_based}} | {{judge_model}} | {{judge_output_shape}} |

Judge-prompt source of truth: {{judge_prompt_location}}. We **validate the judge** against human labels before trusting it ({{judge_validation_policy}}).

### Heuristic / code-based
Deterministic, rule-based checks for structural correctness — JSON-schema compliance, exact match, tool-argument validity, latency/step-count bounds.

| Evaluator | Checks | Output |
|---|---|---|
| {{heuristic_eval_name}} | {{heuristic_eval_check}} | {{heuristic_output_shape}} |

### Human
Manual review via annotation queues or inline annotation against a rubric (see [Human review](#human-review-annotation-queues)).
- **In use:** {{human_eval}} (yes/no). **Rubric:** {{human_rubric_location}}.

### Pairwise
Compares **two outputs** (heuristic, LLM, or human judge) — used when directly scoring is hard but comparing is easy (see [Pairwise & regression](#pairwise-regression-evaluation)).

## 📊 Success metrics & scoring

The feedback keys we track, their type, and the threshold that defines success.

| Metric (feedback `key`) | Type | Level | Target / gate |
|---|---|---|---|
| {{metric_correctness}} | continuous (0–1) / categorical | final-response | ≥ {{target_correctness}} |
| {{metric_trajectory}} | continuous (0–1) | trajectory | ≥ {{target_trajectory}} |
| {{metric_tool_selection}} | binary | single-step | ≥ {{target_tool_selection}} |
| {{metric_safety}} | categorical | reference-free | {{target_safety}} (e.g., 0 unsafe actions) |
| {{metric_latency}} | continuous | operational | ≤ {{target_latency}} |
| {{metric_cost}} | continuous | operational | ≤ {{target_cost_per_run}} |

- **Aggregation:** experiment-level rollup is {{aggregation_method}} (mean / pass-rate / min over the dataset).
- **Repetitions:** because LLM agents are non-deterministic, each example is run {{eval_repetitions}}× and scores are averaged to reduce variance.
- **Primary gate metric:** {{primary_gate_metric}} — the single number a release is judged on.

## Offline vs. online evaluation

| Aspect | Offline (pre-deploy) | Online (post-deploy) |
|---|---|---|
| Target | the `{{eval_dataset}}` dataset of examples | live production runs / threads |
| Data available | inputs **+ reference outputs** | inputs + outputs only (no ground truth) |
| Timing | batch, before merge/release | real-time / sampled, continuously |
| Use here | {{offline_use}} (benchmarking, regression, unit-style checks) | {{online_use}} (quality patterns, safety, anomaly detection) |
| Evaluators | {{offline_evaluators}} | {{online_evaluators}} (reference-free only) |

Online evaluation runs automatically via {{online_eval_trigger}} (e.g., LangSmith Rules sampling N% of production traces) and surfaces drift that offline suites can't see because production inputs aren't in any dataset.

## Pairwise & regression evaluation

**Regression testing (offline):** every candidate version is scored on `{{eval_dataset}}` and must not drop below the current baseline on {{regression_guard_metrics}}. Baseline source: {{regression_baseline}}. A drop beyond {{regression_tolerance}} blocks the change.

**Pairwise evaluation:** when a metric is hard to score absolutely (tone, helpfulness, format quality), we compare the **candidate vs. baseline** output on the same input and pick a winner (LLM or human judge). Used for: {{pairwise_use_cases}}. Decision rule: candidate must win ≥ {{pairwise_win_threshold}} of comparisons to ship.

## 👤 Human review & annotation queues

Where human judgment enters the loop (LangSmith annotation queues):

- **Single-run queue** — reviewers score runs against the rubric ({{human_rubric_location}}); supports free-form acceptance-criteria assertions.
- **Pairwise queue** — reviewers pick A vs. B for the pairwise metrics above.
- **Reviewers / cadence:** {{human_reviewers}}, {{human_review_cadence}}.
- **Feedback loop:** human labels feed back as (a) new dataset examples and (b) the validation set that calibrates the LLM-as-judge.
- **HITL note:** {{hitl_eval_note}} — if the running agent itself has human-in-the-loop (`agent.hitl`), those approval/rejection signals are also captured as online feedback.

## 🚦 Evaluation in CI / quality gates

How evaluation blocks bad changes from shipping.

- **Trigger:** {{ci_eval_trigger}} (e.g., on every PR touching `prompts/`, `agents/`, or model config; nightly full run).
- **Runner:** {{ci_eval_runner}} (LangSmith SDK invoked from {{ci_platform}}; results pushed to the experiment store).
- **Gate:** the PR fails if {{ci_gate_condition}} (e.g., primary gate metric < target, or any regression beyond tolerance vs. baseline).
- **Suite tiering:** `smoke` split on every PR (fast); `full` + trajectory + pairwise nightly/pre-release.
- **Artifacts:** experiment link + per-example diffs attached to the PR for reviewer inspection.
- **Required-decision change → re-eval:** any change to `ai.model`, `ai.framework`, or the agent's prompt/tooling MUST re-run offline eval before merge.

## Eval cadence & ownership

| Activity | Cadence | Owner |
|---|---|---|
| Smoke suite | per PR | CI ({{eval_owner}}) |
| Full offline suite | {{eval_cadence}} (e.g., nightly + pre-release) | {{eval_owner}} |
| Online eval review | {{online_review_cadence}} | {{online_eval_owner}} |
| Dataset curation / growth | {{dataset_review_cadence}} | {{dataset_owner}} |
| Judge re-validation vs. humans | {{judge_validation_cadence}} | {{eval_owner}} |

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
