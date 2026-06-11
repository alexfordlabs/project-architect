<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Research Prompts

Prompt templates the orchestrator hands to the `research-scout` agent. The agent substitutes `{{...}}` placeholders with values from `state.decisions` and the current phase summary.

## Table of Contents
- [Universal research checklist](#universal-research-checklist)
- [Phase-level prompts](#phase-level-prompts)
- [Ad-hoc red-flag prompts](#ad-hoc-red-flag-prompts)
- [Output format the scout returns](#output-format-the-scout-returns)
- [Recency policy per phase](#recency-policy-per-phase)

---

## Universal research checklist

This checklist applies to **every dispatch** — phase-level (Kickoff / Vision / Architecture / Stack / Cost — phases 1–5) and ad-hoc red-flag alike. Every research-scout dispatch MUST cover these four bases before topic-specific work begins:

1. **Latest official docs.** For each vendor / tool / framework / service / API / schema in scope, locate the **latest official** docs (latest stable release; canary/nightly if emerging features are in question). Cite docs URL + version + page last-updated date.
2. **`llms.txt` and `llms-full.txt`.** Probe `<docs-root>/llms.txt` and `<docs-root>/llms-full.txt` as the FIRST `WebFetch` for every tool — the [`llms.txt` standard](https://llmstxt.org/) is widely supported by modern vendors (Anthropic, Cloudflare, Supabase, Vercel, Next.js, etc.) and provides markdown content formatted specifically for LLM consumption. Fall back to the docs sitemap if not published; note absence in findings.
3. **Current best practices.** Search the open web for `<topic> best practices 2026`, `<topic> production patterns`, `<topic> postmortems`. Pull from engineering blogs, conference talks, advocacy posts. Cite URLs.
4. **Similar projects / prior art.** 3–5 commercial or OSS projects building something analogous, with one-line summary + link each.

The phase-specific prompts below ADD topic-specific questions ON TOP of this universal floor. The scout's findings file MUST cite the official-docs URL plus any `llms.txt` source for each tool researched. The orchestrator's review of every dispatch confirms the universal checklist was honoured before reading topic-specific findings.

---

## Phase-level prompts

> **v8 phase ladder** (the order the orchestrator dispatches these): Kickoff (1) → Vision (2) → Architecture (3) → Tech Stack (4) → Cost (5). Architecture (pattern validation) is researched **before** the stack — domain shape first, infrastructure second. The headings below follow that order.

### Kickoff (Phase 1) — Domain research
> Research the project domain. Find: **(1)** 3–5 similar existing projects (commercial or OSS) with one-line summaries and links. **(2)** Common pitfalls developers hit when building a `{{decisions.project.subtype}}` `{{decisions.project.type}}` for `{{decisions.project.target_users}}`. **(3)** Regulatory implications given target users and domain (privacy, accessibility, financial, healthcare, etc.). **(4)** Market context — is this space crowded / emerging / niche? **(5)** What's *actually hard* about this kind of project that newcomers underestimate? Cite URLs. Market data must be < 12 months old; foundational pitfalls can be older. Write findings to `{{output_path}}`. End with an "Implications for this project" section listing concrete follow-up questions for the architect to consider.

### Vision (Phase 2) — Scope realism
> For an MVP with features `{{decisions.features}}` at `{{decisions.scale}}` scale built by a `{{decisions.team_size}}` team in a `{{decisions.timeline}}` timeframe, research: **(1)** Which of these features are typically v1 vs deferred to v2 in similar projects (cite examples). **(2)** Which features are over-scoped — commonly cut in similar projects. **(3)** Which features are under-scoped — typically need supporting features that aren't listed. **(4)** Realistic timeline benchmarks for similar feature sets. **(5)** Where similar projects most often fail (technical, market, ops). Cite specific projects and post-mortems. Write findings to `{{output_path}}`.

### Architecture (Phase 3) — Pattern validation
> For this architecture: `{{architecture_summary}}`, find: **(1)** Prior-art projects using similar patterns and how they scaled (or didn't). **(2)** Anti-patterns to avoid for this combination. **(3)** Open-source reference implementations worth studying. **(4)** Common production failure modes — cite real incidents and post-mortems where possible. **(5)** Whether any pattern in this architecture is considered outdated by current industry consensus. Write findings to `{{output_path}}`.

### Tech Stack (Phase 4) — Stack combination gotchas + current-version resolution
> For this stack: `{{stack_summary}}`, find: **(1)** Known integration gotchas between these specific tools (cite docs and GitHub issues). **(2)** Version compatibility issues to watch for. **(3)** Production issues reported in the last 12 months. **(4)** Emerging alternatives gaining traction the user might want to know about. **(5)** Any tool in this stack that is deprecated, sunsetting, or has had a major maintainer change. **(6)** Per the universal checklist § 1a, the **newest-stable version** of each P0 dependency (cite the registry/release page + date), delivered as `stack.versions.<package>` values for the orchestrator to record (they flow into the generated `package.json` / `Dockerfile`). Be specific about versions. Write findings to `{{output_path}}`.

### Cost (Phase 5) — Pricing research
> For these managed services `{{services_with_tiers}}` at expected `{{decisions.scale}}` usage, find: **(1)** Base tier costs from official pricing pages. **(2)** Per-unit costs (egress, requests, storage, compute-time, function invocations). **(3)** Commonly-forgotten line items (data transfer between regions, log retention, snapshot storage, IP addresses, etc.). **(4)** Free-tier limits and what triggers paid tiers. **(5)** Pricing changes in the last 6 months. Cite official pricing pages only — no third-party calculators unless verifying against official sources. Estimate $/month at MVP / growth / enterprise tiers in a table. Write findings to `{{output_path}}`.

---

## Ad-hoc red-flag prompts

The orchestrator dispatches the scout on these triggers mid-phase. Each is shorter and more targeted than phase-level prompts.

| Trigger | Prompt |
|---|---|
| Deprecated tool mentioned | "Is `{{tool}}` deprecated, sunsetting, or has it had a recent major maintainer change? What's the recommended successor? Migration cost / breaking changes? Cite official announcements and recent GitHub activity." |
| Regulated industry + non-compliant default | "What specific `{{regulation}}` requirements does an architecture using `{{component}}` typically violate? List the precise remediations needed and any OSS or commercial compliance helpers." |
| Critical-path vendor lock | "What is the migration cost off `{{vendor}}` if the project needs to switch? Portability patterns? Has anyone documented such a migration?" |
| Scaling ceiling concern | "What are the known scaling limits for `{{tool}}` at `{{scale}}`? Cite known production deployments at similar scale and any horror stories." |
| Novel security architecture | "Are there known cryptographic or security weaknesses in this approach: `{{approach}}`? Audit findings? Academic critique?" |
| Cost outlier | "Why is `{{service}}` significantly more expensive than `{{alternative}}` at `{{scale}}` scale? What's included that the alternative lacks?" |

---

## Output format the scout returns

The scout writes a markdown file at the path the orchestrator specified, with this structure:

```markdown
---
phase: {{phase_number}}
topic: {{topic_slug}}
dispatched_at: {{ISO8601}}
queries: [...]                  # list of search queries the scout actually ran
recency_floor: {{YYYY-MM-DD}}   # oldest acceptable source date
---

# Research: {{Topic}}

## Summary
{{3-5 sentence executive summary — the architect reads this first}}

## Similar projects / prior art
- [Project](url) — what they did, what worked, what didn't

## Known gotchas / issues
- {{issue}} — citation

## Production issues (last 12 months)
- {{issue}} — date, severity, status, citation

## Emerging alternatives
- {{alternative}} — why it's gaining traction

## Implications for this project          ← architect reads this second
- {{actionable implication}} — drives question Y or revisits decision Z

## Sources
- [Title](url) — accessed {{YYYY-MM-DD}}
```

The scout's return value to the orchestrator is a short text summary (≤20 lines) — NOT the full file. The full file lives on disk for the user and future iterations.

---

## Recency policy per phase

| Phase | Recency floor |
|---|---|
| Kickoff (1) — Domain | 12 months for market context; foundational pitfalls can be older |
| Vision (2) — Scope realism | 12 months |
| Architecture (3) — Pattern validation | 24 months for foundational papers; 12 months for production reports |
| Tech Stack (4) — Stack gotchas + versions | 12 months for production issues; tool deprecation status + newest-stable versions as-of-today |
| Cost (5) — Pricing | 6 months; cite "as of `{{date}}`" |
| Ad-hoc | depends on trigger; default 12 months unless specified |

Tune these per project if the user has unusual stability or recency requirements.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
