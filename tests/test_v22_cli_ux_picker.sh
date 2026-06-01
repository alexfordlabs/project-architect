#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

QF="$REPO_ROOT/skills/project-architect/references/questioning-flow.md"
assert_file_exists "$QF" "questioning-flow.md must exist"

CONTENT=$(cat "$QF")
assert_contains "$CONTENT" 'Per-language CLI-UX' 'must have Per-language CLI-UX picker section'

# Each language listed with its libraries
assert_contains "$CONTENT" 'ratatui' 'Rust libraries must include ratatui'
assert_contains "$CONTENT" 'inquire' 'Rust must include inquire'
assert_contains "$CONTENT" 'indicatif' 'Rust must include indicatif'
assert_contains "$CONTENT" 'bubbletea' 'Go must include bubbletea'
assert_contains "$CONTENT" 'lipgloss' 'Go must include lipgloss'
assert_contains "$CONTENT" 'textual' 'Python must include textual'
assert_contains "$CONTENT" 'rich' 'Python must include rich'
assert_contains "$CONTENT" 'prompt_toolkit' 'Python must include prompt_toolkit'
assert_contains "$CONTENT" 'typer' 'Python must include typer'
assert_contains "$CONTENT" 'ink' 'Node must include ink'
assert_contains "$CONTENT" 'clack' 'Node must include @clack/prompts'
assert_contains "$CONTENT" 'listr2' 'Node must include listr2'
assert_contains "$CONTENT" 'TTY' 'Ruby must include TTY toolkit'
assert_contains "$CONTENT" 'Spectre.Console' 'C# must include Spectre.Console'
assert_contains "$CONTENT" 'Terminal.Gui' 'C# must include Terminal.Gui'

# Routing logic
assert_contains "$CONTENT" 'cli.experience_model' 'must reference the cli.experience_model gate (flat key)'
assert_contains "$CONTENT" 'stack.backend.language' 'routing must condition on stack.backend.language (flat key)'

test_summary
