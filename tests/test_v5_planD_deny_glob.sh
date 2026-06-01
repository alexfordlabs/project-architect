#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
CTA="$(cat "$REPO_ROOT/agents/claude-tooling-author.md")"

assert_contains "$CTA" 'Bash(curl* | sh)' 'tooling-author must show the parser-valid deny glob'
assert_not_contains "$CTA" 'Bash(curl:* | sh)' 'tooling-author must NOT show the failed-open mid-pattern glob'
assert_contains "$CTA" 'fails open' 'tooling-author must explain why mid-pattern :* fails open'
assert_contains "$CTA" 'settings_permissions_valid' 'tooling-author must self-validate vs the B21 rule'

test_summary
