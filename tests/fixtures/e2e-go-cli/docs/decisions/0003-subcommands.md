---
adr_id: "0003"
title: "gh-style subcommand structure"
status: accepted
date: 2026-05-13
decision_keys: ["cli_experience_model"]
affected_docs: ["CLI_UX_DESIGN.md"]
---

# gh-style subcommands with interactive_prompts

The CLI uses noun-verb subcommands (e.g., `tool widget create`) with optional
interactive prompts via Bubble Tea + huh when a required argument is missing.
This pattern (popularised by gh, kubectl, docker) gives both scriptable
non-interactive use and a friendly first-run experience.
