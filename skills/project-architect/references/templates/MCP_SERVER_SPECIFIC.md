---
template_name: MCP_SERVER_SPECIFIC
generate_when: "decisions.project.type == 'mcp_server'"
required_decisions: [mcp.host_environment, mcp.surface]
optional_decisions: [mcp.auth_model, mcp.statefulness, mcp.language]
depends_on: []
revision_triggers: [mcp.host_environment, mcp.surface, mcp.auth_model]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# MCP Server Specific: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [⚙️ Host Environment (stdio / HTTP+SSE / Cloudflare Workers / Vercel)](#host-environment-stdio-httpsse-cloudflare-workers-vercel)
- [🔧 Surface (tools / resources / prompts)](#surface-tools-resources-prompts)
- [🔐 Auth Model](#auth-model)
- [Statefulness (durable per-user vs stateless)](#statefulness-durable-per-user-vs-stateless)
- [Language & SDK Choice](#language-sdk-choice)
- [🗄️ Tool Schema Strategy](#tool-schema-strategy)
- [🧪 Testing the Server](#testing-the-server)
- [↻ Revision Log](#revision-log)

## ⚙️ Host Environment (stdio / HTTP+SSE / Cloudflare Workers / Vercel)
Transport / host model: local stdio for Claude Desktop / Claude Code, HTTP+SSE for remote clients, deployed on Cloudflare Workers, Vercel Functions, Fly.io, AWS Lambda, or self-hosted.

## 🔧 Surface (tools / resources / prompts)
MCP capabilities exposed (tools — verbs, resources — readable URIs, prompts — parameterized templates) and the user-facing problem each surface solves.

## 🔐 Auth Model
Authentication model (none for local stdio, OAuth 2.1 with PKCE for remote, API key / bearer token, signed user JWT, per-tenant credentials passthrough) and refresh / rotation handling.

## Statefulness (durable per-user vs stateless)
Statefulness posture: stateless request-response, ephemeral per-session memory, durable per-user state (Cloudflare Durable Objects, Postgres-backed sessions), and consistency model.

## Language & SDK Choice
Implementation language and MCP SDK (TypeScript `@modelcontextprotocol/sdk`, Python SDK, Rust SDK, custom transport) with rationale around deployment target and library ecosystem.

## 🗄️ Tool Schema Strategy
Tool input/output schema discipline (Zod / Pydantic / JSON Schema), naming and description conventions for high agent recall, examples in descriptions, and breaking-change policy.

## 🧪 Testing the Server
Testing approach (MCP Inspector for manual smoke, contract tests against schemas, integration tests in Claude Code, fuzzing tool inputs) and CI gates.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
