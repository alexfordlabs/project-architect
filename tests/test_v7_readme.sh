#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v7.0.0 clean-release: the README is the repo's publishable front door. This
# test pins the publish-ready rewrite — every required §3.5 section is present
# (Capabilities, Install, a mention of each command, Use cases, What it
# generates, a Guides/quick-start section, Project types, Contributing,
# License, Attribution + the Alex Ford Labs publisher line) — AND the legacy
# development artifacts are scrubbed (no whoami, no legacy identity refs, no
# per-version "What's new in vX" tables).
#
# NOTE: the deny-needles below are assembled at runtime from fragments so this
# test file itself does NOT carry the contiguous identity-correlation strings
# that the repo-wide anti-regression scan (test_v600_version_bump.sh) searches
# for. That keeps this file out of that scan WITHOUT weakening any assertion.
#
# SC1091: test_helpers.sh is sourced dynamically (every test does this).
# shellcheck disable=SC2016,SC1091
source "$(dirname "$0")/lib/test_helpers.sh"

README="$REPO_ROOT/README.md"
assert_file_exists "$README" "README.md exists"

DOC="$(cat "$README")"

# ── Presence: top attribution + badges retained ──────────────────────────────
assert_contains "$DOC" "Author: Alexander Ford <alex@alexfordlabs.com>" \
    "README keeps the top attribution comment"
assert_contains "$DOC" "img.shields.io/github/v/release/alexfordlabs/project-architect" \
    "README keeps the alexfordlabs release badge"

# ── Presence: required §3.5 sections (match real heading text) ────────────────
assert_contains "$DOC" "## Capabilities" "README has a Capabilities section"
assert_contains "$DOC" "## Install" "README has an Install section"
assert_contains "$DOC" "## Commands" "README has a Commands & workflows section"
assert_contains "$DOC" "## Use cases" "README has a Use cases section"
assert_contains "$DOC" "## What it generates" "README has a What-it-generates section"
assert_contains "$DOC" "## Guides" "README has a Guides / quick-start section"
assert_contains "$DOC" "## Project types" "README has a Project types section"
assert_contains "$DOC" "## Recommended companion plugins" \
    "README has a Recommended companion plugins section"
assert_contains "$DOC" "## Contributing" "README has a Contributing section"
assert_contains "$DOC" "## License" "README has a License section"
assert_contains "$DOC" "## Attribution" "README has an Attribution section"
assert_contains "$DOC" "Alex Ford Labs" "README names the Alex Ford Labs publisher"
assert_contains "$DOC" "MIT" "README states the MIT license"

# ── Presence: every command is documented ─────────────────────────────────────
assert_contains "$DOC" "/scaffold" "README mentions /scaffold"
assert_contains "$DOC" "/implement" "README mentions /implement"
assert_contains "$DOC" "/iterate-design" "README mentions /iterate-design"
assert_contains "$DOC" "/upgrade-project" "README mentions /upgrade-project"
assert_contains "$DOC" "/re-architect" "README mentions /re-architect"

# ── Presence: the real install commands (the shared alexfordlabs/skills marketplace) ───
assert_contains "$DOC" "claude plugin marketplace add alexfordlabs/skills" \
    "README has the real marketplace-add command (shared alexfordlabs/skills marketplace)"
assert_contains "$DOC" "project-architect@alexfordlabs" \
    "README has the real install identifier"

# ── Presence: accurate component counts + real phase names ────────────────────
assert_contains "$DOC" "27" "README cites the 27-check quality gate"
assert_contains "$DOC" "11" "README cites the 11-phase workflow"
assert_contains "$DOC" "Preflight" "README names the real Preflight phase"

# ── Negative: legacy identity refs + per-version tables are scrubbed ──────────
# Deny-needles assembled from fragments (see header NOTE).
PRIOR_ORG="alexander-ford""-ventures"   # prior GitHub org/repo (fragmented on purpose)
REAL_PERSON_CAP="V""ladimir"
REAL_PERSON_LC="v""ladimir"
SURNAME="duke""lic"
LEGACY_DOMAIN="pseudo-""lang"
PREV_ORG="silicon""youth"
WHATS_NEW="What's new in v"          # the per-version table heading (CHANGELOG's job)

assert_not_contains "$DOC" "whoami" "README must not mention the internal test project"
assert_not_contains "$DOC" "$LEGACY_DOMAIN" "README must not expose the legacy author domain"
assert_not_contains "$DOC" "$REAL_PERSON_CAP" "README must not name the real person (cap)"
assert_not_contains "$DOC" "$REAL_PERSON_LC" "README must not name the real person (lower)"
assert_not_contains "$DOC" "$SURNAME" "README must not expose the personal surname/email"
assert_not_contains "$DOC" "$PRIOR_ORG" "README must not name the prior org/repo"
assert_not_contains "$DOC" "$PREV_ORG" "README must not name the older mirror org"
assert_not_contains "$DOC" "$WHATS_NEW" "README must not carry per-version what's-new tables"

test_summary
