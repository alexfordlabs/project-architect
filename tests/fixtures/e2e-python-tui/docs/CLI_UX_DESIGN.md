# CLI UX Design

Experience model: full_tui — Textual app is the primary surface.

## Libraries

- tui_framework: textual (reactive widgets, layout, CSS-like styling)
- colors: rich (color & text rendering)
- prompts: prompt_toolkit (line editing & readline-style input)
- cli: typer (one-shot subcommand entry points, --help routing)

See ADR-0002 (textual choice) and ADR-0003 (full-TUI model).
