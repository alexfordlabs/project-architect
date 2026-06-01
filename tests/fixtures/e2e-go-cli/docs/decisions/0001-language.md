---
adr_id: "0001"
title: "Choose Go as primary language"
status: accepted
date: 2026-05-13
decision_keys: ["tech_stack.language"]
affected_docs: ["TECH_STACK.md"]
---

# Choose Go

Go 1.22 is well-suited for gh-style CLIs with subcommands: single static binary,
fast cold start, mature CLI ecosystem (cobra, urfave/cli) and a strong TUI
toolkit (charmbracelet: bubbletea, lipgloss, huh). We considered Rust (great
perf but slower iteration) and Python (worse single-binary distribution); Go
wins on the ergonomics-to-distribution trade-off.
