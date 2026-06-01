<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- Repository: https://github.com/alexfordlabs/project-architect -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: SCAFFOLD_PLAN
generate_when: project.sub_type != "documentation_only"
required_decisions:
  - project.name
  - project.sub_type
  - stack.backend.language
  - stack.backend.language_edition
  - stack.license
optional_decisions:
  - stack.build_tool
  - stack.test_runner
  - stack.toolchain_version
  - stack.runtime_version
  - architecture.lib_vs_bin
  - copyright_holder
  - copyright_year
depends_on:
  - ARCHITECTURE.md
  - TECH_STACK.md
  - BUILD_AND_RUN.md
  - LICENSE_NOTICE.md
revision_triggers:
  - stack.backend.language
  - stack.backend.language_edition
  - stack.build_tool
  - stack.license
  - architecture.lib_vs_bin
---

# Scaffold plan — {{project.name}}

This document **describes** the exact files and commands needed to bootstrap the on-disk codebase for `{{project.name}}` once the design is locked. It is **not** the codebase itself — it is the recipe.

The plan is **consumed by `superpowers:writing-plans` (via `/scaffold`)**: Phase 9 (Tooling Execution) option (c) in `project-architect` hands the locked design off to superpowers, which turns this plan into a concrete `plans/<date>-scaffold.md` and runs SDD against it (TDD-driven, one verified file at a time).

## Why a plan, not the scaffold itself

Phase 6 (Document Generation) produces design + plan docs only. Generating scaffold contents (real `Cargo.toml`, `src/lib.rs`, license headers) in Phase 6 would:
- Conflate "what the codebase should look like" (design) with "creating it on disk" (execution).
- Make Phase 7 (Iteration) awkward — you'd be editing committed source code, not a plan.
- Bypass `superpowers:writing-plans` + SDD, which is where the actual scaffold belongs.

With a plan-first approach:
- Phase 7 (Iteration) lets you edit this plan and re-run the `architect-brain audit`
- Phase 9 (Tooling Execution) hands the plan to superpowers (`/scaffold`), which produces a real plan + executes it test-first
- The plan stays as a permanent record of the intended initial codebase, traceable back to ADRs

## 1. Build manifest

The future build manifest (`{{ if stack.backend.language == "rust" then "Cargo.toml" else if stack.backend.language == "javascript" or stack.backend.language == "typescript" then "package.json" else if stack.backend.language == "python" then "pyproject.toml" else if stack.backend.language == "go" then "go.mod" else "(language-appropriate manifest)" }}`) will encode dependencies, metadata, and build settings locked from the ADRs. Show the **full inline content** of the manifest here, with versions pinned per ADR.

### Language-conditional examples

{{ if stack.backend.language == "rust" then "" }}
```toml
# Cargo.toml — generated from TECH_STACK ADR {{stack.backend.language.adr}}
[package]
name = "{{project.name}}"
version = "0.1.0"
edition = "{{stack.backend.language_edition}}"
rust-version = "{{stack.toolchain_version}}"
license = "{{stack.license}}"
authors = ["{{copyright_holder}}"]
description = "{{project.elevator_pitch}}"

[dependencies]
# Each dep MUST cite the ADR that introduced it
{{stack.dependencies.runtime}}  # e.g., serde = { version = "1.0", features = ["derive"] }  # ADR 0004

[dev-dependencies]
{{stack.dependencies.test}}  # e.g., insta = "1.39"  # ADR 0005 (TESTING_STRATEGY)
```

{{ if stack.backend.language == "javascript" or stack.backend.language == "typescript" then "" }}
```json
{
  "name": "{{project.name}}",
  "version": "0.1.0",
  "description": "{{project.elevator_pitch}}",
  "license": "{{stack.license}}",
  "type": "module",
  "engines": { "node": "{{stack.runtime_version}}" },
  "scripts": {
    "build": "{{stack.build_tool}} build",
    "test": "{{stack.test_runner}}"
  },
  "dependencies": {},
  "devDependencies": {}
}
```

{{ if stack.backend.language == "python" then "" }}
```toml
# pyproject.toml — generated from TECH_STACK ADR {{stack.backend.language.adr}}
[project]
name = "{{project.name}}"
version = "0.1.0"
requires-python = ">={{stack.runtime_version}}"
license = { text = "{{stack.license}}" }
description = "{{project.elevator_pitch}}"
dependencies = []

[project.optional-dependencies]
dev = []

[build-system]
requires = ["{{stack.build_tool}}"]
build-backend = "{{stack.build_backend}}"
```

{{ if stack.backend.language == "go" then "" }}
```
module {{stack.module_path}}

go {{stack.runtime_version}}

require ()
```

For every dependency added, cite the ADR that mandates it. Do **not** add transitive sugar (test frameworks "everyone uses"); every line must be ADR-justified.

## 2. `src/` tree with per-file purpose statements

The future `src/` tree must be designed up-front so SDD has a concrete target. List **every initial file** with a one-line purpose statement tied to ARCHITECTURE.md or the relevant ADR. (Files added later during SDD belong in the superpowers plan, not here.)

> The directory/package layout below is the canonical `{{project_layout}}` decision recorded in the event-sourced state (`docs/_architect_state/` — the `project_layout` key in `99-flat-index.json`) — use those exact paths, do not invent a parallel layout. Pin dependency versions to the **newest-stable** resolved by research (no RC/beta/alpha on P0 deps); state a version family if research didn't pin an exact version.

### Example (Rust library + binary)

| File | Purpose | Source |
|---|---|---|
| `src/lib.rs` | Library entry point exposing public API per ADR-0003 | ARCHITECTURE §Module layout |
| `src/main.rs` | CLI entry point parsing args and dispatching to lib | ARCHITECTURE §Binaries |
| `src/error.rs` | Crate-wide error type (`thiserror`) per ADR-0006 | ARCHITECTURE §Error handling |
| `src/{{module.name}}/mod.rs` | {{module.purpose}} | ADR-{{module.adr}} |

### Example (Python package)

| File | Purpose | Source |
|---|---|---|
| `src/{{project.name}}/__init__.py` | Package root; re-exports public API | ARCHITECTURE §Public surface |
| `src/{{project.name}}/cli.py` | CLI entry (argparse / typer / click per ADR) | ARCHITECTURE §CLI |
| `src/{{project.name}}/core.py` | Pure-logic module — no I/O | ARCHITECTURE §Layering |
| `tests/test_core.py` | Test for `core.py` (TDD seed for SDD) | TESTING_STRATEGY §Unit tests |

### Example (TypeScript / Node)

| File | Purpose | Source |
|---|---|---|
| `src/index.ts` | Library entry — re-exports public API | ARCHITECTURE §Public surface |
| `src/cli.ts` | CLI entry (commander / yargs per ADR) | ARCHITECTURE §CLI |
| `src/{{module.name}}.ts` | {{module.purpose}} | ADR-{{module.adr}} |

For each row, the purpose statement must be **specific enough that an SDD agent could write the test first** without re-reading the entire design.

## 3. License files + NOTICE

The future repo will ship the canonical license text plus (if required) a `NOTICE` file for attribution. List the **full file content** here, with placeholders for year and author so Phase 9 (Tooling Execution) or `/scaffold` substitutes them deterministically.

### `LICENSE` ({{stack.license}})

The full text of `{{stack.license}}` will be written to `LICENSE` at repo root.

{{ if stack.license == "MIT" then "" }}
```
MIT License

Copyright (c) {{copyright_year}} {{copyright_holder}}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

{{ if stack.license == "Apache-2.0" then "" }}
For Apache-2.0, also write a `NOTICE` file with the attribution header (see LICENSE_NOTICE.md §NOTICE-file shape).

### `NOTICE` (if required by license)

```
{{project.name}}
Copyright (c) {{copyright_year}} {{copyright_holder}}

This product includes software developed at
{{copyright_holder}} ({{copyright_url}}).
```

### Per-source-file header (if mandated by LICENSE_NOTICE.md)

If the design requires per-file SPDX headers, document the exact header here:

```
// SPDX-License-Identifier: {{stack.license}}
// Copyright (c) {{copyright_year}} {{copyright_holder}}
```

## 4. Toolchain pin file

The future repo will pin its toolchain via a language-appropriate file so contributors get a reproducible environment without thinking about it.

### Language-conditional examples

{{ if stack.backend.language == "rust" then "" }}
```toml
# rust-toolchain.toml — pinned per TECH_STACK ADR {{stack.toolchain.adr}}
[toolchain]
channel = "{{stack.toolchain_version}}"
components = ["rustfmt", "clippy"]
profile = "minimal"
```

{{ if stack.backend.language == "javascript" or stack.backend.language == "typescript" then "" }}
```
# .nvmrc — pinned per TECH_STACK ADR {{stack.runtime.adr}}
{{stack.runtime_version}}
```

{{ if stack.backend.language == "python" then "" }}
```
# .python-version (pyenv / mise) — pinned per TECH_STACK ADR {{stack.runtime.adr}}
{{stack.runtime_version}}
```

{{ if stack.backend.language == "go" then "" }}
The `go` directive in `go.mod` (above) is the toolchain pin. Optionally pin via `// toolchain` line or `.tool-versions` (asdf / mise).

For each pin, cite the ADR that justifies the chosen version (LTS policy, language-feature gate, etc.).

## 5. Bootstrap commands

The exact, deterministic command sequence Phase 9 (Tooling Execution) — or `/scaffold` → `superpowers:writing-plans` — will run to materialize the scaffold. These run **before** any source content is written — they establish directory shape, VCS, and toolchain.

> **Important:** every destructive operation must be guarded. If a step would clobber an existing file, the executor must stop and surface a confirmation prompt. Use the `:*` glob form when listing patterns to avoid Semgrep / pre-commit false-positives (e.g., `Bash(rm:*)`, not the literal command).

### Example sequence (Rust library + binary)

```bash
# 1. Initialize project structure (no VCS yet — we add it explicitly below)
cargo init --lib --vcs none "{{project.name}}"
cd "{{project.name}}"

# 2. Overwrite Cargo.toml with the manifest from §1
#    (executor writes the file from this plan; no inline cat <<EOF here)

# 3. Write toolchain pin
#    (executor writes rust-toolchain.toml from §4)

# 4. Initialize VCS and seed history
git init
git branch -M main

# 5. Write LICENSE and (optionally) NOTICE from §3
#    (executor writes these files)

# 6. Stage everything and commit
git add .
git commit -m "chore(scaffold): bootstrap {{project.name}} v0.1.0"
```

### Example sequence (Python package with pyproject + src-layout)

```bash
mkdir -p "{{project.name}}/src/{{project.name}}" "{{project.name}}/tests"
cd "{{project.name}}"
# Executor writes pyproject.toml (§1), .python-version (§4), LICENSE (§3),
# and the empty src/ files from §2.
git init
git branch -M main
git add .
git commit -m "chore(scaffold): bootstrap {{project.name}} v0.1.0"
```

### Forbidden / guarded commands

The executor must **never** run, and `.claude/settings.json` should deny:

- `Bash(rm:*)` — no recursive deletes during scaffold
- `Bash(sudo:*)` — no privilege escalation
- `Bash(curl:*|sh)` — no piped remote execution

(These also live in `CLAUDE_TOOLING_PLAN.md` §`settings.json` — keep them in sync.)

## 6. Hand-off note

This plan is consumed by **`superpowers:writing-plans`** (via the `/scaffold` slash command generated in Phase 9 (Tooling Execution) when `claude-tooling-author` executes `CLAUDE_TOOLING_PLAN`).

Phase 9 (Tooling Execution) option (c) — "Hand off SCAFFOLD_PLAN to superpowers" — calls `/scaffold`, which:
1. Reads this `SCAFFOLD_PLAN.md` from the locked design.
2. Invokes `superpowers:writing-plans` to convert this plan into a concrete `plans/{{today}}-scaffold-{{project.name}}.md` (TDD-shaped phases).
3. Hands the produced plan to SDD (subagent-driven development) so each file in §2 is **test-first**: one file → one passing test → one verified commit.
4. Returns to the user at the end with a working, committed scaffold ready for `/implement <feature>`.

If `superpowers` is not installed on the contributor's machine, the manual fallback is documented in `NEXT_STEP_PLAN.md` § "If /scaffold fails because superpowers isn't installed" — execute §5 commands by hand, then write `src/` files from §2 stub-first, test-second.

## 7. Record the actual layout + self-check (single source of truth)

This is the closing step the executor runs **after the scaffold has materialized the tree** — it makes the `project_layout` decision honest and catches a partial scaffold immediately.

1. **Record the layout that was *actually* created back to the event-sourced state.** Once the bootstrap commands (§5) and the §2 files have run, build a small layout map from the directories/packages that now exist on disk — the real, post-scaffold tree, **not** the pre-scaffold plan in §2 — and record it as a single flat `project_layout` decision (a `DecisionMade` event). The value is a JSON object; `set-decision` JSON-parses it, so pass the dict literal directly:

   ```bash
   # The project_layout decision maps a friendly key → the actual relative path created, e.g.
   #   { "lib": "src/lib.rs", "cli": "src/main.rs", "core_pkg": "crates/<name>-core" }
   # Only include paths that were ACTUALLY created (verify each exists first).
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision project_layout \
     '{"lib":"src/lib.rs","cli":"src/main.rs","core_pkg":"crates/<name>-core"}'
   ```

   The `project_layout` decision must reflect what is **actually on disk** (the single source of truth), never the aspirational §2 plan — so the recorded layout can't drift from the real tree. The decision lands in `docs/_architect_state/events.jsonl` as a `DecisionMade` event and projects into `99-flat-index.json` (where the `scaffold_executed` check (26) reads it). If the scaffold created fewer paths than §2 listed (e.g. a module was deferred), record only what exists; `project_layout` describes reality.

2. **Self-check layout-vs-disk at scaffold-completion** — don't wait for the final handoff gate. Immediately after recording `project_layout`, confirm every path resolves on disk:

   ```bash
   # The same layout-vs-disk validation the scaffold_executed gate (check 26, BLOCKING)
   # runs at handoff — surfaced HERE so a partial/aborted scaffold is caught at the
   # cheapest possible moment instead of at the final re-gate.
   ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain audit --only 26 --verbose
   ```

   Every path recorded in the `project_layout` decision must exist on disk. A failure here means the scaffold only partially materialized (a `project_layout` path was never created) — stop and fix it now, while the context is fresh and the fix is one missing file, rather than discovering the drift at the final handoff gate.

## Notes for the executor

When `/scaffold` (via `superpowers:writing-plans`) consumes this plan:

1. Substitute every `{{...}}` placeholder from the flat decision map (`docs/_architect_state/99-flat-index.json`).
2. Resolve all language-conditional blocks (`{{ if stack.backend.language == "..." then "..." }}`) — keep only the branch that matches the project's language.
3. Pass the resolved plan to `superpowers:writing-plans`, which produces a TDD-shaped `plans/<date>-scaffold.md`.
4. Run that plan via `superpowers:executing-plans` + `subagent-driven-development` so every src file lands test-first.
5. Each commit subject follows project convention (e.g., `scaffold(<file>): <one-line purpose>`).
6. After the last commit, record the completion as flat decisions (events, never hand-edited state): `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision scaffold.executed true` and `${CLAUDE_PLUGIN_ROOT}/bin/architect-brain set-decision scaffold.commit <SHA>`. Both land as `DecisionMade` events in `docs/_architect_state/events.jsonl`.

If any bootstrap command in §5 fails, stop and surface to the user — do not retry destructively or rewrite history.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
