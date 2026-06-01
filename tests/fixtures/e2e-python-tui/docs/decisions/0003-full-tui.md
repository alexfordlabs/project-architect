---
adr_id: "0003"
title: "Full-TUI experience model"
status: accepted
date: 2026-05-13
decision_keys: ["cli_experience_model"]
affected_docs: ["CLI_UX_DESIGN.md"]
---

# Full-TUI experience model

The primary user surface is a full-screen interactive Textual app, not a
one-shot flag-driven CLI. This decision drives library choices (textual for
layout, rich for colors, prompt_toolkit for line editing) and informs the
keyboard-driven navigation model documented in CLI_UX_DESIGN.md.
