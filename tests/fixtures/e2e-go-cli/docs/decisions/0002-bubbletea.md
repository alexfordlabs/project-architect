---
adr_id: "0002"
title: "Adopt Bubble Tea for interactive prompts"
status: accepted
date: 2026-05-13
decision_keys: ["cli_ux_libraries.tui_framework"]
affected_docs: ["CLI_UX_DESIGN.md"]
---

# Adopt Bubble Tea

Bubble Tea (with lipgloss styling and huh form builder) gives ergonomic
Elm-style interactive prompts on top of standard subcommand flow. mpb covers
progress bars for long-running operations. The stack composes well and is
widely adopted across modern Go CLIs (gh, glow, soft-serve).
