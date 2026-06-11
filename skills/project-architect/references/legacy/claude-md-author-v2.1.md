<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

> Archived v2.1 CLAUDE.md authoring workflow — superseded by the plan-driven v2.2 flow. Kept for archaeology / bare-Phase-4 fallback.

## Workflow (v2.1 — legacy, superseded by v2.2)

### Step 1: Write the root CLAUDE.md

1. Read `template_root_path`.
2. Read `state_path`.
3. Fill in the template sections:
   - **Project Overview**: one sentence from `decisions.project.elevator_pitch` + link to `docs/PROJECT_OVERVIEW.md`.
   - **Tech Stack**: concise table from `language.*`, `frontend.*`, `backend.*`, `database.*`, `auth.*`, `hosting.*`.
   - **Project Structure**: directory tree (top 2 levels only). Mark which subdirs have their own CLAUDE.md.
   - **Development Commands**: stack-specific (`pnpm install`, `cargo build`, etc.).
   - **Code Conventions**: pulled from tech-stack defaults (e.g., TypeScript → Biome/Prettier, Rust → rustfmt+clippy, Python → ruff+black).
   - **Architecture Notes**: 5–10 one-line decisions with `(see ADR NNNN)` references.
   - **Key Files**: ~10 most-important paths with one-line purposes.
4. Write to `<user-project>/CLAUDE.md`.
5. Invoke `Skill` tool with `claude-md-management:claude-md-improver`. The improver will read the file and suggest improvements.
6. Apply suggested improvements (if any) and re-audit until the improver returns "passes."

### Step 2: Identify subdirectories that warrant their own CLAUDE.md

Apply these gating triggers (any one means write a sub-CLAUDE.md):
- Different primary language vs root (e.g., root is TypeScript, `packages/crypto/` is Rust).
- Different test framework.
- Different deploy target (e.g., `apps/web/` deploys to Vercel; `services/api/` deploys to Cloudflare Workers).
- Explicit conventions in state (`subfolder_overrides` key in state).
- Substantial enough to warrant its own context — heuristic: ≥10 expected source files OR a clearly distinct subsystem.

Skip:
- Trivial dirs (`utils/`, `helpers/`, `types/`, `node_modules/`, `target/`, `dist/`).
- Generated dirs.

### Step 3: For each qualifying subdirectory, write a CLAUDE.md

1. Read `template_subfolder_path`.
2. Fill in:
   - **Purpose**: one paragraph — what this area is responsible for, how it relates to the rest.
   - **Local Tech Stack**: only what DIFFERS from root.
   - **Conventions Specific to This Area**: only differences.
   - **Local Development Commands**: only different ones.
   - **Key Files In This Area**: 3–8 most-important.
   - **Cross-references**: back to root + relevant `docs/*.md`.
3. Write to `<subdir>/CLAUDE.md`.
4. Run `claude-md-improver` audit; iterate until pass.

### Step 4: Return summary

Return to the orchestrator:
```
CLAUDE.md WRITTEN
- /CLAUDE.md (audited: PASS, N improvements applied)
- apps/web/CLAUDE.md (audited: PASS)
- packages/crypto/CLAUDE.md (audited: PASS)
- services/api/CLAUDE.md (audited: PASS)
Total files: 4
```

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
