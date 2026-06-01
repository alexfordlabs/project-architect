<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Claude Code Integration Recipes

The `claude-tooling-author` agent reads this file to decide which `.claude/` artifacts to write for the generated project. Stack-aware hooks, permissions, agents, commands, and plugin recommendations live here.

## Table of Contents
- [Universal recommendations (every project)](#universal-recommendations-every-project)
- [Stack-conditional recommendations](#stack-conditional-recommendations)
- [Project-type-conditional recommendations](#project-type-conditional-recommendations)
- [Quality / process recommendations](#quality--process-recommendations)
- [Hook templates](#hook-templates)
- [Permission allowlist templates](#permission-allowlist-templates)
- [Project-local agent templates](#project-local-agent-templates)
- [Slash command templates](#slash-command-templates)

---

## Universal recommendations (every project)

These go in every generated `recommended-plugins.md` regardless of stack:

| Plugin / skill | Why |
|---|---|
| `superpowers:brainstorming` | Any new feature should brainstorm first |
| `superpowers:writing-plans` | Multi-step task planning |
| `superpowers:executing-plans` | Plan execution discipline |
| `superpowers:test-driven-development` | TDD discipline |
| `superpowers:systematic-debugging` | Bug investigation |
| `superpowers:verification-before-completion` | Prevent premature "done" claims |
| `superpowers:requesting-code-review` | Before merges |
| `superpowers:using-git-worktrees` | Isolation for feature work |
| `claude-md-management:revise-claude-md` | Keep CLAUDE.md current |
| `claude-md-management:claude-md-improver` | Audit CLAUDE.md quality |
| `commit-commands:commit` | Quick commit workflow |

## Stack-conditional recommendations

Selected when `decisions.<key>` matches.

### Hosting / cloud

| Stack signal | Recommended plugins |
|---|---|
| Cloudflare (Workers / Pages / D1 / R2 / KV / Durable Objects / Queues) | `cloudflare:cloudflare`, `cloudflare:wrangler`, `cloudflare:durable-objects`, `cloudflare:workers-best-practices` |
| Cloudflare + AI agents | + `cloudflare:agents-sdk`, `cloudflare:sandbox-sdk` |
| Cloudflare + email | + `cloudflare:cloudflare-email-service` |
| Cloudflare + perf concerns | + `cloudflare:web-perf` |
| Vercel + Next.js | `vercel:nextjs`, `vercel:vercel-cli`, `vercel:next-cache-components`, `vercel:react-best-practices` |
| Vercel + shadcn/ui | + `vercel:shadcn` |
| Vercel + AI | + `vercel:ai-sdk`, `vercel:ai-gateway`, `vercel:chat-sdk` |
| Vercel + auth | + `vercel:auth` |
| AWS | `aws-dev-toolkit:aws-architect`, `aws-dev-toolkit:aws-plan` + service-specific (`lambda`, `ec2`, `eks`, `ecs`, `s3`, `dynamodb`, `bedrock`, `rds-aurora`, `iam`, `networking`, `observability`) |
| AWS serverless | `aws-serverless:aws-lambda`, `aws-serverless:api-gateway`, `aws-serverless:aws-serverless-deployment` |
| Azure | `azure:azure-prepare`, `azure:azure-deploy` + service-specific (`azure-compute`, `azure-kubernetes`, `azure-storage`, `azure-ai`) |
| GCP / Firebase | `plugin_firebase:firebase`, `cloud-sql-postgresql:*` |
| Netlify | `netlify-skills:netlify-deploy`, `netlify-skills:netlify-functions`, `netlify-skills:netlify-edge-functions` |
| Fastly | `fastly-agent-toolkit:fastly`, `fastly-agent-toolkit:fastly-cli` |

### Databases / data

| Stack signal | Recommended plugins |
|---|---|
| Supabase (any product) | `supabase:supabase`, `supabase:supabase-postgres-best-practices` |
| Postgres (any host) | `supabase:supabase-postgres-best-practices` |
| CockroachDB | `cockroachdb:*` (start with `cockroachdb-sql`, `setting-up-local-cluster`) |
| MongoDB | `mongodb:mongodb-schema-design`, `mongodb:mongodb-query-optimizer`, `mongodb:mongodb-natural-language-querying` |
| Pinecone / vector DB | `pinecone:quickstart`, `pinecone:cli`, `pinecone:docs` |
| Qdrant | `qdrant:qdrant-clients-sdk`, `qdrant:qdrant-performance-optimization` |
| Zilliz / Milvus | `zilliz:quickstart`, `zilliz:vector` |
| Snowflake | `snowflake-cortex-code:cortex-setup`, `snowflake-cortex-code:cortex-router` |
| Airflow / Astronomer | `astronomer-data:airflow`, `astronomer-data:authoring-dags`, `astronomer-data:debugging-dags` |
| AlloyDB | `alloydb:alloydb-postgres-admin`, `alloydb:alloydb-postgres-optimize` |

### Frontend

| Stack signal | Recommended plugins |
|---|---|
| Figma design hand-off | `figma:figma-use`, `figma:figma-implement-design`, `figma:figma-code-connect` |
| Tailwind CSS | implicit via vercel:shadcn or figma recommendations |
| Frontend (any) | `document-skills:frontend-design`, `chrome-devtools-mcp:debug-optimize-lcp` |

### Mobile

| Stack signal | Recommended plugins |
|---|---|
| Expo / React Native | `expo:building-native-ui`, `expo:expo-deployment`, `expo:upgrading-expo`, `expo:native-data-fetching`, `expo:expo-cicd-workflows` |
| Expo + Tailwind | + `expo:expo-tailwind-setup` |
| Expo + native modules | + `expo:expo-module` |

### Auth

| Stack signal | Recommended plugins |
|---|---|
| Auth0 (any) | `auth0:auth0-quickstart` |
| Auth0 + Next.js | + `auth0:auth0-nextjs` |
| Auth0 + React | + `auth0:auth0-react` |
| Auth0 + Express | + `auth0:auth0-express` or `auth0:express-oauth2-jwt-bearer` |
| Auth0 + Vue | + `auth0:auth0-vue` |
| Auth0 + Angular | + `auth0:auth0-angular` |
| Auth0 + iOS / macOS | + `auth0:auth0-swift` |
| Auth0 + Android | + `auth0:auth0-android` |
| Auth0 + React Native / Expo | + `auth0:auth0-react-native` or `auth0:auth0-expo` |
| Auth0 + FastAPI | + `auth0:auth0-fastapi-api` |
| Auth0 + Flask | + `auth0:auth0-flask` |
| Auth0 + Spring Boot | + `auth0:auth0-springboot-api` |
| Auth0 + ASP.NET Core | + `auth0:auth0-aspnetcore-api` |
| Auth0 + MFA needs | + `auth0:auth0-mfa` |
| Auth0 + custom universal login | + `auth0:acul-screen-generator` |

### Payments / billing

| Stack signal | Recommended plugins |
|---|---|
| Stripe | `stripe:stripe-best-practices`, `stripe:test-cards`, `stripe:explain-error` |
| MercadoPago | `mercadopago:mp-setup`, `mercadopago:mp-checkout-online`, `mercadopago:mp-subscriptions` |

### Notifications / messaging

| Stack signal | Recommended plugins |
|---|---|
| Twilio (SMS / voice / WhatsApp) | `twilio-developer-kit:*` (start with `twilio-cli-reference`) |
| Twilio SendGrid (email) | `twilio-developer-kit:twilio-sendgrid-email-send`, `twilio-developer-kit:twilio-sendgrid-deliverability-advisor` |
| Slack integration | `slack:slack-messaging`, `slack:slack-search` |
| Telegram bot | `telegram:configure`, `telegram:access` |
| iMessage | `imessage:configure`, `imessage:access` |
| Discord | `discord:configure`, `discord:access` |
| Zoom | `zoom-plugin:plan-zoom-product`, `zoom-plugin:choose-zoom-approach` + product-specific |

### Testing

| Stack signal | Recommended plugins |
|---|---|
| Playwright (E2E) | `playwright-cli:playwright-cli`, `document-skills:webapp-testing` |
| Chrome DevTools debugging | `chrome-devtools-mcp:chrome-devtools`, `chrome-devtools-mcp:a11y-debugging`, `chrome-devtools-mcp:memory-leak-debugging` |

### AI / ML

| Stack signal | Recommended plugins |
|---|---|
| HuggingFace ecosystem | `huggingface-skills:hf-cli`, `huggingface-skills:huggingface-best`, `huggingface-skills:huggingface-llm-trainer` |
| HuggingFace + vision | + `huggingface-skills:huggingface-vision-trainer`, `transformers-js` |
| HuggingFace + Gradio app | + `huggingface-skills:huggingface-gradio` |
| Anthropic API integration | `claude-api` |
| Sentence-transformers | `huggingface-skills:train-sentence-transformers` |
| FiftyOne (computer vision) | `fiftyone:quickstart`, `fiftyone:fiftyone-dataset-curation` |
| Pydantic-AI agents | `ai:building-pydantic-ai-agents` |
| Vercel AI Gateway | `vercel:ai-gateway`, `vercel:ai-sdk` |

### Observability

| Stack signal | Recommended plugins |
|---|---|
| Sentry (errors) | `sentry:sentry-sdk-setup`, `sentry:sentry-workflow`, `sentry:seer` |
| Datadog | `datadog:ddsetup`, `datadog:ddconfig`, `datadog:ddtoolsets` |
| Logfire | `logfire:instrument`, `logfire:logfire-query`, `logfire:dev-session` |
| PostHog | `posthog:llma-cc-setup`, `posthog:instrument-product-analytics` + use-case specific |
| Amplitude | `amplitude:add-analytics-instrumentation`, `amplitude:create-dashboard` |
| FullStory | `fullstory:general-analysis` |
| PagerDuty | `pagerduty:pre-commit-risk-scoring` |

### Quality / security

| Stack signal | Recommended plugins |
|---|---|
| CodeRabbit | `coderabbit:code-review`, `coderabbit:autofix` |
| Semgrep | `semgrep:setup-semgrep-plugin` |
| SonarQube | `sonarqube:sonar-analyze`, `sonarqube:sonar-quality-gate` |
| Aikido | `aikido:setup`, `aikido:scan` |
| NightVision (DAST) | `nightvision:scan-configuration`, `nightvision:api-discovery` |
| 42Crunch (API security) | `api-security-testing:42crunch-setup`, `api-security-testing:42crunch-scan` |
| Vanta (compliance) | `vanta:list-tests`, `vanta:test-remediation` |
| JFrog | `jfrog:jfrog` |

### Documentation sites

| Stack signal | Recommended plugins |
|---|---|
| Mintlify | `mintlify:mintlify` |
| Generic doc co-authoring | `document-skills:doc-coauthoring`, `document-skills:internal-comms` |

### Project management / collaboration

| Stack signal | Recommended plugins |
|---|---|
| Atlassian (Jira / Confluence) | `atlassian:search-company-knowledge`, `atlassian:spec-to-backlog`, `atlassian:triage-issue` |
| Notion | `Notion:search`, `Notion:create-page`, `Notion:tasks:setup` |
| Linear | *(no first-party skill yet — recommend manual)* |
| Miro | `miro:miro-diagram`, `miro:miro-doc` |

### Code intelligence

| Stack signal | Recommended plugins |
|---|---|
| Sourcegraph | `sourcegraph:searching-sourcegraph` |

---

## Project-type-conditional recommendations

| Project type | Recommended plugins |
|---|---|
| Claude Code plugin | `plugin-dev:create-plugin`, `plugin-dev:plugin-structure`, `plugin-dev:skill-development`, `plugin-dev:command-development`, `plugin-dev:agent-development`, `plugin-dev:hook-development`, `plugin-dev:mcp-integration`, `plugin-dev:plugin-settings` |
| MCP server | `mcp-server-dev:build-mcp-server`, `mcp-server-dev:build-mcp-app`, `mcp-server-dev:build-mcpb`, `document-skills:mcp-builder` |
| Skill development | `skill-creator:skill-creator`, `document-skills:skill-creator` |
| Heavy UI / dashboards | `document-skills:frontend-design`, `document-skills:web-artifacts-builder`, `document-skills:theme-factory`, `document-skills:brand-guidelines` |
| Browser extension | *(no first-party plugin yet — manual)* |
| Game | *(no first-party plugin yet — manual)* |
| Documentation-heavy | `document-skills:doc-coauthoring`, `document-skills:internal-comms`, `mintlify:mintlify` |
| Web3 / smart contracts | *(no first-party plugin yet — recommend Foundry / Hardhat manuals)* |
| Embedded / firmware | *(no first-party plugin yet — manual)* |

---

## Quality / process recommendations

Recommend for any production-bound project:

| Plugin | Why |
|---|---|
| `coderabbit:code-review` | AI code review before merge |
| `semgrep:setup-semgrep-plugin` | Static analysis + secret scanning |
| `pr-review-toolkit:review-pr` | Specialized PR review agents |
| `code-review:code-review` | Default code-review skill |
| `superpowers:dispatching-parallel-agents` | Parallel work patterns |
| `superpowers:subagent-driven-development` | Plan execution with subagents |
| `feature-dev:feature-dev` | Guided feature development |
| `update-config` | Configure Claude Code via settings.json |
| `fewer-permission-prompts` | Reduce permission prompts |
| `hookify:hookify` | Create hooks from conversation |

---

## Hook templates

The agent writes these to `<generated-project>/.claude/hooks/` and wires them in `.claude/settings.json` under the `hooks` key.

### `post-tool-use.sh` — format on save

```bash
#!/usr/bin/env bash
# Format files after Edit/Write tool use.
# Stack-specific: if project uses Prettier / Biome / rustfmt / gofmt / black / etc.,
# the architect picks the right formatter at generation time.

set -e

# Read tool output from stdin (Claude Code hook protocol)
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  exit 0
fi

case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.md)
    # if Prettier / Biome present
    pnpm exec biome format --write "$FILE" 2>/dev/null \
      || pnpm exec prettier --write "$FILE" 2>/dev/null \
      || true
    ;;
  *.rs)
    rustfmt "$FILE" 2>/dev/null || true
    ;;
  *.go)
    gofmt -w "$FILE" 2>/dev/null || true
    ;;
  *.py)
    ruff format "$FILE" 2>/dev/null \
      || black "$FILE" 2>/dev/null \
      || true
    ;;
esac
```

### `stop.sh` — ensure tests green before stopping

```bash
#!/usr/bin/env bash
# Run quick test suite before Claude declares "done."
# Stack-specific: command is filled in by claude-tooling-author at generation time.

set -e

# Example for a pnpm + Vitest project:
if pnpm test:quick --silent 2>&1 | tail -5; then
  exit 0
else
  echo "Tests failing — fix before claiming task complete." >&2
  exit 2
fi
```

### `pre-tool-use.sh` — block dangerous commands

```bash
#!/usr/bin/env bash
# Block obviously-dangerous commands from the Bash tool.

set -e

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ "$TOOL" != "Bash" ]]; then exit 0; fi

DANGEROUS=(
  'rm -rf /'
  'rm -rf ~'
  'git push --force.*main'
  'git push --force.*master'
  'git reset --hard origin'
)

for pattern in "${DANGEROUS[@]}"; do
  if echo "$CMD" | grep -qE "$pattern"; then
    echo "Blocked dangerous command: $CMD" >&2
    exit 2
  fi
done

exit 0
```

### `session-start.sh` — print recent commits + open TODOs

```bash
#!/usr/bin/env bash
# Greet a new session with recent project state.

echo "=== Recent commits ==="
git log --oneline -10 2>/dev/null || true
echo
echo "=== Open TODOs ==="
rg -n "TODO|FIXME" --max-count=5 2>/dev/null | head -20 || true
```

The `claude-tooling-author` agent customizes commands and patterns to match the chosen stack.

---

## Permission allowlist templates

The agent writes these to `<generated-project>/.claude/settings.json` under `permissions.allow`. Pick the rows that match the stack.

| Stack | Allow rules |
|---|---|
| Any project | `Bash(git status)`, `Bash(git diff:*)`, `Bash(git log:*)`, `Bash(git branch:*)`, `Bash(ls:*)`, `Bash(pwd)`, `Bash(cat:*)`, `Bash(rg:*)`, `Bash(find:*)`, `Bash(echo:*)` |
| Node / TypeScript | `Bash(pnpm install)`, `Bash(pnpm dev)`, `Bash(pnpm build)`, `Bash(pnpm test:*)`, `Bash(pnpm lint:*)`, `Bash(pnpm typecheck)`, `Bash(node:*)`, `Bash(npx:*)` |
| Rust | `Bash(cargo build:*)`, `Bash(cargo test:*)`, `Bash(cargo check:*)`, `Bash(cargo clippy:*)`, `Bash(cargo fmt:*)`, `Bash(cargo run:*)` |
| Python | `Bash(uv:*)`, `Bash(pip install:*)`, `Bash(pytest:*)`, `Bash(ruff:*)`, `Bash(black:*)`, `Bash(mypy:*)`, `Bash(python:*)` |
| Go | `Bash(go build:*)`, `Bash(go test:*)`, `Bash(go run:*)`, `Bash(go mod:*)`, `Bash(gofmt:*)`, `Bash(go vet:*)` |
| Wrangler (Cloudflare) | `Bash(wrangler:*)` |
| Vercel | `Bash(vercel:*)` |
| Supabase | `Bash(supabase:*)` |
| GitHub | `Bash(gh pr:*)`, `Bash(gh issue:*)`, `Bash(gh repo view)`, `Bash(gh auth status)` |
| Docker | `Bash(docker ps)`, `Bash(docker logs:*)`, `Bash(docker compose up:*)`, `Bash(docker compose down)` |
| Test browsers | `mcp__plugin_playwright_playwright__*` |

---

## Project-local agent templates

The agent writes these to `<generated-project>/.claude/agents/<name>.md`. Each agent knows the project's specific commands.

### `test-runner.md`
```markdown
---
name: test-runner
description: Run the project's test suite and report failures. Use when the user asks to "run tests", or proactively before declaring a task complete.
tools: [Bash, Read, Grep]
model: opus
---

# Test Runner

Run the test suite for this project using the project's standard command:

```
{{stack-specific test command — e.g., pnpm test, cargo test, pytest, go test ./...}}
```

If tests fail, do NOT attempt fixes. Return a structured report:
- Total tests, passed, failed, skipped
- For each failure: file:line, error message, last-N lines of context
- Suggested next steps for the orchestrator (debug? skip? mark blocked?)
```

### `migration-checker.md` (when database present)
```markdown
---
name: migration-checker
description: Validate that database migrations are forward and backward compatible. Use before applying any migration in production.
tools: [Bash, Read, Grep, Glob]
model: opus
---

# Migration Checker

Check the latest migration for:
1. **Forward-compat**: does the migration run cleanly against a fresh DB at HEAD?
2. **Backward-compat**: can the prior app version run against the new schema (no breaking column drops, no NOT NULL without default)?
3. **Rollback**: does the down-migration exist and reverse cleanly?
4. **Lock pressure**: does it acquire long locks on hot tables?
5. **Data backfills**: are large UPDATEs batched?

Return a structured report with PASS/FAIL per check.
```

### `deploy-verifier.md` (when production-bound)
```markdown
---
name: deploy-verifier
description: Smoke-test a deployment after it lands. Use after `wrangler deploy` / `vercel --prod` / equivalent.
tools: [Bash, Read]
model: opus
---

# Deploy Verifier

Run smoke tests against the deployed environment:
1. Health endpoint returns 200
2. Auth flow completes
3. Critical user paths complete (paste-in or framework-specific)
4. Error tracker shows no new spike
5. APM shows no new latency regression

Return PASS/FAIL with citations from logs / metrics.
```

---

## Slash command templates

The agent writes these to `<generated-project>/.claude/commands/<name>.md`.

### `feature.md`
```markdown
---
description: Start a new feature with brainstorming → plan → implementation workflow
---

# /feature

Start a new feature in this project.

## Workflow
1. Invoke `superpowers:brainstorming` to refine the idea.
2. Invoke `superpowers:writing-plans` to write an implementation plan.
3. Decide subagent-driven vs inline execution.
4. Invoke `superpowers:subagent-driven-development` or `superpowers:executing-plans`.

Project stack:
{{stack summary}}

Project conventions:
- {{key conventions from CLAUDE.md}}

Begin by asking the user: "What feature do you want to build?"
```

### `run-tests.md`
```markdown
---
description: Run the project test suite
---

# /run-tests

Dispatch the `test-runner` project agent. Summarize failures (if any) and offer to investigate the first one.
```

### `deploy-preview.md` (web projects)
```markdown
---
description: Deploy a preview to {{platform}} for the current branch
---

# /deploy-preview

Run:
```
{{stack-specific preview deploy command}}
```

Report the preview URL when the deploy completes.
```

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
