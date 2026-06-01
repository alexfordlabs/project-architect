#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

source "$(dirname "$0")/lib/test_helpers.sh"

PLUGIN_JSON="$REPO_ROOT/.claude-plugin/plugin.json"
CHANGELOG="$REPO_ROOT/CHANGELOG.md"

PLUGIN_VERSION=$(jq -r '.version' "$PLUGIN_JSON")
assert_eq "$PLUGIN_VERSION" "8.1.0" "plugin.json version must be 8.1.0"

CHANGELOG_CONTENT=$(cat "$CHANGELOG")
assert_contains "$CHANGELOG_CONTENT" 'v6.0.0' 'CHANGELOG must have a v6.0.0 entry'
assert_contains "$CHANGELOG_CONTENT" 're-architect' 'CHANGELOG v6.0.0 must describe /re-architect'
assert_contains "$CHANGELOG_CONTENT" 'preserve mode' 'CHANGELOG v6.0.0 must describe the folded-in preserve mode'
assert_contains "$CHANGELOG_CONTENT" 'reconcile-adrs' 'CHANGELOG v6.0.0 must mention reconcile-adrs'

# v7.0.0 entry (this release)
assert_contains "$CHANGELOG_CONTENT" 'v7.0.0' 'CHANGELOG must have a v7.0.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'set-decision' 'CHANGELOG v7.0.0 must mention the set-decision ledger command'

# v7.1.0 entry
assert_contains "$CHANGELOG_CONTENT" 'v7.1.0' 'CHANGELOG must have a v7.1.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'banner' 'CHANGELOG v7.1.0 must describe the inline banner/progress-bar UI'

# v7.1.1 entry
assert_contains "$CHANGELOG_CONTENT" 'v7.1.1' 'CHANGELOG must have a v7.1.1 entry'
assert_contains "$CHANGELOG_CONTENT" 'transition contract' 'CHANGELOG v7.1.1 must describe the NARRATE step wired into the transition contract'

# v7.1.2 entry
assert_contains "$CHANGELOG_CONTENT" 'v7.1.2' 'CHANGELOG must have a v7.1.2 entry'
assert_contains "$CHANGELOG_CONTENT" 'alexfordlabs/skills' 'CHANGELOG v7.1.2 must describe the move to the alexfordlabs/skills marketplace'

# v7.2.0 entry
assert_contains "$CHANGELOG_CONTENT" 'v7.2.0' 'CHANGELOG must have a v7.2.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'phase-bar' 'CHANGELOG v7.2.0 must describe the architect-ui phase-bar / run-the-binary UI fix'

# v8.0.0 entry
assert_contains "$CHANGELOG_CONTENT" 'v8.0.0' 'CHANGELOG must have a v8.0.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'architect-brain' 'CHANGELOG v8.0.0 must describe the architect-brain binary'
assert_contains "$CHANGELOG_CONTENT" 'event-sourced' 'CHANGELOG v8.0.0 must describe the event-sourced state'

# v8.1.0 entry (this release)
assert_contains "$CHANGELOG_CONTENT" 'v8.1.0' 'CHANGELOG must have a v8.1.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'user_provenance' 'CHANGELOG v8.1.0 must describe the user_provenance check'
assert_contains "$CHANGELOG_CONTENT" 'mechanical' 'CHANGELOG v8.1.0 must describe the mechanical LOCK gate'
assert_contains "$CHANGELOG_CONTENT" 'stack.versions' 'CHANGELOG v8.1.0 must describe the stack.versions.* namespace'

# Regression: prior entries retained (CURATED, not trimmed — all versions kept)
assert_contains "$CHANGELOG_CONTENT" 'v5.0.0' 'CHANGELOG must retain the v5.0.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'v4.0.1' 'CHANGELOG must retain the v4.0.1 entry'
assert_contains "$CHANGELOG_CONTENT" 'v4.0.0' 'CHANGELOG must retain the v4.0.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'v3.1.0' 'CHANGELOG must retain the v3.1.0 entry'
assert_contains "$CHANGELOG_CONTENT" 'v2.2.1' 'CHANGELOG must retain the v2.2.1 entry'

# Curated public CHANGELOG must be clean of dev-process + legacy identity (v7 clean release)
assert_not_contains "$CHANGELOG_CONTENT" 'whoami' 'public CHANGELOG must not contain whoami'
assert_not_contains "$CHANGELOG_CONTENT" 'pseudo-''lang' 'public CHANGELOG must not contain the legacy author domain'
assert_not_contains "$CHANGELOG_CONTENT" 'V''ladimir' 'public CHANGELOG must not contain the real-identity name'

# Manifest identity unchanged since v4.0.0
assert_eq "$(jq -r '.author.email' "$PLUGIN_JSON")" "alex@alexfordlabs.com" \
    "plugin.json author.email must remain alex@alexfordlabs.com"
assert_eq "$(jq -r '.repository' "$PLUGIN_JSON")" \
    "https://github.com/alexfordlabs/project-architect" \
    "plugin.json repository must remain alexfordlabs"

# Anti-regression: no legacy identity strings in tracked files outside historical-preservation areas.
# NOTE: the search needles below are CHAR-CLASS fragmented (e.g. `[v]ladimir`) so this file itself
# carries no grep-able real-identity literal (clean-history republish goal), while the regex still
# matches the real strings in any scanned file. The self-exclusion of this file + .gitleaks.toml is
# belt-and-suspenders. The published v4.x release history retains the legacy email and is untouched.
LEAKS=$(
    cd "$REPO_ROOT" && git ls-files | \
    grep -v -E '^(\.gitleaks\.toml|tests/test_v80_version_bump\.sh)$' | \
    grep -v -E '^(docs/superpowers/(plans|specs|test-plans)|docs/tests|tests/fixtures|.*_archive)/' | \
    xargs -I {} grep -lE '[p]seudo-lang\.com|[a]lexander-ford-ventures|[v]ladimir@[d]ukelic|[V]ladimir [D]ukelic' {} 2>/dev/null \
    || true
)
assert_eq "$LEAKS" "" "no legacy identity strings should remain in tracked files outside historical-preservation areas"

test_summary
