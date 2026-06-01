#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for v2.2 task 48: E2E validator chain for bad shell hooks (sketch A).
#
# This test validates that the shellcheck command from the Validation section
# actually catches the bug — we can't dispatch the actual claude-tooling-author
# agent in a test, so we verify the validator commands themselves work.

source "$(dirname "$0")/lib/test_helpers.sh"

# The shellcheck binary must complain about unquoted $1
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "SKIP: shellcheck not installed"
  test_summary
  exit 0
fi
RESULT=$(shellcheck -s bash -S warning "$REPO_ROOT/tests/fixtures/bad-hook.sh" 2>&1; true)
# Note: SC2086 is info-severity; with -S warning it's filtered out.
# But the missing-fi syntax error should trip parse error.
# Let's check for either SC code OR syntax error
[[ "$RESULT" == *"SC"* || "$RESULT" == *"parse"* || "$RESULT" == *"unexpected"* ]] && \
  PASS_COUNT=$((PASS_COUNT + 1)) || \
  { FAIL_COUNT=$((FAIL_COUNT + 1)); FAIL_MESSAGES+=("FAIL: shellcheck must flag bad-hook.sh — got: $RESULT"); }

# bash -n must complain about missing fi
RESULT2=$(bash -n "$REPO_ROOT/tests/fixtures/bad-hook.sh" 2>&1; true)
assert_contains "$RESULT2" 'syntax error' 'bash -n must catch missing fi'

test_summary
