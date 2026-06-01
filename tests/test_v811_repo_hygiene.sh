#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Repo-hygiene guard: the plugin must enforce on ITSELF what it preaches.
# (1) A CI workflow exists that runs the suite on a python matrix + shellcheck +
#     a release guard (a tag must match plugin.json's version) — for a plugin
#     whose whole value is enforcement discipline, "no CI" was the gap that let
#     __version__ drift and frozen-broken-command tests ship.
# (2) CONTRIBUTING.md carries no dead links / stale claims and names the real
#     (alexfordlabs/skills) marketplace.
# (3) README's Install path surfaces the hard Python prerequisite and the one
#     REQUIRED companion plugin's install command.
source "$(dirname "$0")/lib/test_helpers.sh"

CI="$REPO_ROOT/.github/workflows/ci.yml"
CONTRIB="$REPO_ROOT/CONTRIBUTING.md"
README="$REPO_ROOT/README.md"

# (1) CI workflow exists with the load-bearing pieces.
assert_file_exists "$CI" 'CI workflow (.github/workflows/ci.yml) exists'
CIC="$(cat "$CI" 2>/dev/null || true)"
assert_contains "$CIC" 'jobs:' 'CI declares jobs'
assert_contains "$CIC" 'matrix' 'CI uses a python version matrix'
assert_contains "$CIC" 'tests/run_all.sh' 'CI runs the full test suite'
assert_contains "$CIC" 'shellcheck' 'CI runs shellcheck'
assert_contains "$CIC" 'plugin.json' 'CI release-guard inspects plugin.json (tag == version)'

# (2) CONTRIBUTING.md hygiene.
CO="$(cat "$CONTRIB" 2>/dev/null || true)"
assert_not_contains "$CO" 'docs/superpowers/test-plans/2026-05-12-v2.0-manual-test-plan.md' \
  'no dead manual-test-plan link'
assert_not_contains "$CO" 'This repo is its own marketplace' \
  'no stale self-marketplace claim (distribution moved to alexfordlabs/skills)'
assert_not_contains "$CO" 'Markdown only. No code in this repo' \
  'no stale "markdown only" claim (the repo ships a Python package + bash suite)'
assert_contains "$CO" 'alexfordlabs/skills' 'CONTRIBUTING names the alexfordlabs/skills marketplace'

# (3) README Install surfaces the Python prereq + the required companion install.
RE="$(cat "$README" 2>/dev/null || true)"
assert_contains "$RE" 'Python 3.10+' 'README surfaces the Python 3.10+ runtime prerequisite'
assert_contains "$RE" 'commit-commands@claude-plugins-official' \
  'README shows the explicit commit-commands install command'

test_summary
