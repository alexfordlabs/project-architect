#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

# Regression guard (v4.0.1): no PUBLISHED, EXECUTABLE source file may contain an
# absolute home path (/Users/... or /home/<user>/...). Such paths ship broken to
# every other user (the path only exists on the author's machine) AND leak the
# author's username into a published artifact. Portable forms are required:
#   ~/.claude/...   ${CLAUDE_PLUGIN_ROOT}/...   <user>/<project-id> placeholders (no /Users/).
# Scope = the surfaces that ship + execute. docs/ (historical specs/plans),
# CHANGELOG.md and HANDOFF.md (historical record) are intentionally excluded.

source "$(dirname "$0")/lib/test_helpers.sh"

# Exclude gitignored build caches: CPython __pycache__/*.pyc embed the absolute
# build path in bytecode, and Hypothesis seeds .hypothesis/constants/ with absolute
# paths in comments — both are untracked + gitignored, so they must not trip this
# scan of the SHIPPED source (a local Python run would otherwise cause a false fail).
hits="$(grep -rnE '/Users/|/home/[a-z]' \
  --exclude-dir=__pycache__ --exclude-dir=.hypothesis --exclude='*.pyc' \
  "$REPO_ROOT/agents" \
  "$REPO_ROOT/skills" \
  "$REPO_ROOT/.claude-plugin" \
  "$REPO_ROOT/README.md" \
  "$REPO_ROOT/CONTRIBUTING.md" 2>/dev/null || true)"

assert_eq "$hits" "" "no absolute home paths (/Users/... or /home/<user>/...) in published source"

test_summary
