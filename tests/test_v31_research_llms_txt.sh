#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Asserts the universal-research-floor rule:
# Every research-scout dispatch MUST cover the four bases —
#   1. latest official docs
#   2. llms.txt + llms-full.txt (per llmstxt.org standard)
#   3. best practices
#   4. similar projects / prior art
# — before topic-specific work.

source "$(dirname "$0")/lib/test_helpers.sh"

SCOUT="$REPO_ROOT/agents/research-scout.md"
PROMPTS="$REPO_ROOT/skills/project-architect/references/research-prompts.md"

assert_file_exists "$SCOUT" "research-scout agent prompt must exist"
assert_file_exists "$PROMPTS" "research-prompts reference must exist"

SCOUT_CONTENT=$(cat "$SCOUT")
PROMPTS_CONTENT=$(cat "$PROMPTS")

# ── research-scout.md: agent prompt encodes the rule ────────────────────────
assert_contains "$SCOUT_CONTENT" 'llms.txt' \
    'research-scout must mention llms.txt'
assert_contains "$SCOUT_CONTENT" 'llms-full.txt' \
    'research-scout must mention llms-full.txt'
assert_contains "$SCOUT_CONTENT" 'llmstxt.org' \
    'research-scout must cite the llms.txt standard URL'
assert_contains "$SCOUT_CONTENT" 'latest official' \
    'research-scout must mandate latest official docs'
assert_contains "$SCOUT_CONTENT" 'best practices' \
    'research-scout must mandate best-practices research'
assert_contains "$SCOUT_CONTENT" 'similar projects' \
    'research-scout must mandate similar-projects research'
assert_contains "$SCOUT_CONTENT" 'Universal first-pass' \
    'research-scout must have a Universal first-pass section'

# ── research-prompts.md: orchestrator templates carry the same floor ────────
assert_contains "$PROMPTS_CONTENT" 'Universal research checklist' \
    'research-prompts must have a Universal research checklist section'
assert_contains "$PROMPTS_CONTENT" 'every dispatch' \
    'research-prompts must explicitly say the checklist applies to every dispatch'
assert_contains "$PROMPTS_CONTENT" 'llms.txt' \
    'research-prompts checklist must include llms.txt'
assert_contains "$PROMPTS_CONTENT" 'llms-full.txt' \
    'research-prompts checklist must include llms-full.txt'
assert_contains "$PROMPTS_CONTENT" 'llmstxt.org' \
    'research-prompts checklist must cite the llms.txt standard URL'
assert_contains "$PROMPTS_CONTENT" 'latest official' \
    'research-prompts checklist must mandate latest official docs'
assert_contains "$PROMPTS_CONTENT" 'best practices' \
    'research-prompts checklist must include best-practices research'
assert_contains "$PROMPTS_CONTENT" 'similar projects' \
    'research-prompts checklist must include similar-projects research'

test_summary
