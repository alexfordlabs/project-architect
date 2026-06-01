---
adr_id: "0002"
title: "Adopt Textual as TUI framework"
status: accepted
date: 2026-05-13
decision_keys: ["cli_ux_libraries.tui_framework"]
affected_docs: ["CLI_UX_DESIGN.md"]
---

# Adopt Textual

Textual provides a modern reactive TUI framework on top of Rich, with widgets,
layout, async event handling, and CSS-like styling. Alternatives considered:
urwid (older, less ergonomic), prompt_toolkit alone (lower-level), and curses
(too primitive). Textual + rich + prompt_toolkit + typer compose well.
