<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: CLI_UX_DESIGN
generate_when: project.sub_type in ["cli_tool", "cli_with_subcommands", "tui_app", "interactive_cli"]
required_decisions:
  - project.name
  - project.sub_type
  - tech_stack.language
  - cli_experience_model
optional_decisions:
  - cli_ux_libraries
depends_on:
  - PROJECT_REQUIREMENTS.md
  - CLI_REFERENCE.md
  - ARCHITECTURE.md
  - TECH_STACK.md
revision_triggers:
  - cli_experience_model
  - cli_ux_libraries
---

# CLI/TUI UX design — {{project.name}}

This document specifies the user-facing behavior of {{project.name}} as a {{project.sub_type}}: what it looks like, how users interact, and which libraries deliver that experience. It complements `CLI_REFERENCE.md` (which lists commands/flags) by describing the *experience* of using those commands.

## 1. Interaction model

How does the user drive the tool?

- **Mode:** {{cli_experience_model}}  (one of: `one_shot` / `interactive_prompts` / `full_tui` / `hybrid`)
- **Entry point:** {{project.name}} `{{cli.default_subcommand}}` or no-arg shows {{ if cli_experience_model == "one_shot" then "help" else "interactive picker" }}

Detail per mode:
- `one_shot` — emits text and exits; no spinner, no prompts.
- `interactive_prompts` — single-screen prompts (yes/no, multi-select, text input) before doing work.
- `full_tui` — keyboard-driven multi-pane interface (modal navigation, focus management).
- `hybrid` — `one_shot` by default; `--interactive` flag triggers prompts.

## 2. Key bindings

For `full_tui` or `interactive_prompts` modes, define standard key mappings:

| Action | Default key | Notes |
|---|---|---|
| Quit | `q`, `Esc`, `Ctrl+C` | All three respected per `cli_experience_model` |
| Move down/up | `j`/`k`, `Down`/`Up` | Vim + arrow keys both supported |
| Select / confirm | `Enter`, `Space` | |
| Help | `?` | Shows in-app keybinding overlay |
| Search | `/` | Vim-style |

{{ if cli_experience_model == "one_shot" then "(One-shot mode: no key bindings — non-interactive)." else "Document per-screen overrides in CLI_REFERENCE.md." }}

## 3. Visual design

- **Color usage:** {{decisions.cli_ux.color_scheme}}  (e.g., "ANSI 16-color minimal, no truecolor required")
- **Unicode usage:** {{decisions.cli_ux.unicode_level}}  (e.g., "Box-drawing + spinner glyphs OK; emoji avoided for legibility")
- **Spinner / progress style:** {{decisions.cli_ux.progress_style}}
- **Theming:** light/dark/auto-detect; respect `NO_COLOR` env var, `COLORFGBG`, `TERM=dumb`

## 4. Output formats

- **Default:** human-readable, paged through `less` if `stdout` is a TTY.
- **Machine-readable:** `--json` flag emits NDJSON or JSON-array (one or the other — pick).
- **TSV/CSV:** `--format tsv` for grep/awk piping.
- **Quiet mode:** `--quiet` suppresses progress + status, keeps fatal errors.
- **Verbosity:** `-v` / `-vv` / `-vvv` (or `--log-level debug`).

## 5. Error conventions

- **Exit codes:** `0` success, `1` general error, `2` invalid usage, `3+` per-domain (document each).
- **Format:** stderr lines prefixed with `error:` / `warning:` (color-aware).
- **Recoverable vs fatal:** recoverable surfaces inline, fatal aborts with non-zero exit.
- **No silent failures:** any error must produce stderr output unless `--quiet` AND non-fatal.

## 6. Accessibility

- **Screen reader-friendly:** `NO_COLOR=1` env-var disables color (de-facto standard).
- **Reduced motion:** `--no-spinner` flag for users with vestibular sensitivity OR when stdout isn't a TTY.
- **High contrast:** test at color depth 4 (basic ANSI 16-color) — must remain readable.
- **Cognitive load:** prefer text + symbol redundancy ("✓ done" not just "✓").

## 7. Help text

- **`{{project.name}} --help`:** one-page synopsis (usage + brief description + `--help <command>` pointer).
- **`{{project.name}} <cmd> --help`:** per-subcommand detail (flags, examples, exit codes).
- **`{{project.name}} help <topic>`:** longer-form topic pages (concepts, recipes).
- All help text auto-generated from {{decisions.cli_ux.help_source}} (e.g., clap derive macros, click decorators).

## 8. Library inventory

Per the Phase 2 picker, this project will use:

| Concern | Library | Why |
|---|---|---|
| {{cli_ux_libraries[0].concern}} | {{cli_ux_libraries[0].name}} | {{cli_ux_libraries[0].rationale}} |
| {{cli_ux_libraries[1].concern}} | {{cli_ux_libraries[1].name}} | {{cli_ux_libraries[1].rationale}} |
| {{cli_ux_libraries[2].concern}} | {{cli_ux_libraries[2].name}} | {{cli_ux_libraries[2].rationale}} |
| {{cli_ux_libraries[3].concern}} | {{cli_ux_libraries[3].name}} | {{cli_ux_libraries[3].rationale}} |

(Empty/missing rows are dropped at template-execution time when state doesn't supply that concern.)

## Notes for the executor

This is a design doc (not a plan). It's generated in Phase 4 like any other architecture doc, NOT in Phase 7. Substitute `{{...}}` placeholders from `state.decisions` and `state.decisions.cli_ux_libraries`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
