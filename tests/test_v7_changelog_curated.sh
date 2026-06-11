#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v7.0.0 clean-release: the published CHANGELOG.md is a CURATED, user-facing
# history (every version kept, but the internal development process scrubbed),
# while the full unabridged history is preserved verbatim on disk in the
# gitignored CHANGELOG.dev.md. This test pins both invariants: every version
# heading survives in the public file, the dev-process strings are absent, and
# CHANGELOG.dev.md exists on disk yet is untracked by git.
#
# SC1091: test_helpers.sh is sourced dynamically (every test does this).
# shellcheck disable=SC2016,SC1091
source "$(dirname "$0")/lib/test_helpers.sh"

PUBLIC="$REPO_ROOT/CHANGELOG.md"
DEV="$REPO_ROOT/CHANGELOG.dev.md"

# 1. The public CHANGELOG exists (tracked → present in every checkout).
assert_file_exists "$PUBLIC" "public CHANGELOG.md exists"
# CHANGELOG.dev.md is GITIGNORED: present in the author's working tree but absent
# from any fresh clone / CI checkout (git never tracked it). Its on-disk presence is
# a local-author convenience, NOT a portable repo invariant — only its UNTRACKED-ness
# is (asserted at the end, and it holds whether or not the file is on disk). So check
# existence only when it is present, to stay green in a clean checkout.
if [[ -f "$DEV" ]]; then
  assert_file_exists "$DEV" "full-history CHANGELOG.dev.md present in the author's tree"
fi

PUB="$(cat "$PUBLIC")"

# 2. Every version heading is retained in the public file (nothing trimmed).
#    Heading forms match the original: v2.1.5+ use '## vX.Y.Z', v2.1.4 and
#    earlier use '## [X.Y.Z]' — assert the real form for the v1.0.0 anchor.
assert_contains "$PUB" "## v6.0.0" "public CHANGELOG keeps the v6.0.0 heading"
assert_contains "$PUB" "## v5.0.0" "public CHANGELOG keeps the v5.0.0 heading"
assert_contains "$PUB" "## v4.0.1" "public CHANGELOG keeps the v4.0.1 heading"
assert_contains "$PUB" "## v4.0.0" "public CHANGELOG keeps the v4.0.0 heading"
assert_contains "$PUB" "## v3.1.0" "public CHANGELOG keeps the v3.1.0 heading"
assert_contains "$PUB" "## v3.0.0" "public CHANGELOG keeps the v3.0.0 heading"
assert_contains "$PUB" "## v2.3.0" "public CHANGELOG keeps the v2.3.0 heading"
assert_contains "$PUB" "## v2.2.1" "public CHANGELOG keeps the v2.2.1 heading"
assert_contains "$PUB" "## v2.2.0" "public CHANGELOG keeps the v2.2.0 heading"
assert_contains "$PUB" "## v2.1.5" "public CHANGELOG keeps the v2.1.5 heading"
assert_contains "$PUB" "## [2.1.4]" "public CHANGELOG keeps the [2.1.4] heading"
assert_contains "$PUB" "## [2.0.0]" "public CHANGELOG keeps the [2.0.0] heading"
assert_contains "$PUB" "## [1.0.0]" "public CHANGELOG keeps the [1.0.0] heading (original bracketed form)"

# 3. Keep-a-Changelog style header/intro convention preserved.
assert_contains "$PUB" "# Changelog" "public CHANGELOG keeps the '# Changelog' title"
assert_contains "$PUB" "Semantic Versioning" "public CHANGELOG keeps the SemVer intro note"

# 4. The internal development process is SCRUBBED (case-sensitive needles).
# NOTE: the deny-needles are assembled at runtime from fragments so this test file
# itself does not carry the exact contiguous identity-correlation strings that the
# repo-wide anti-regression scan (test_v600_version_bump.sh) searches for. That keeps
# this file out of that scan WITHOUT weakening either assertion.
PRIOR_ORG="alexander-ford""-ventures"  # prior GitHub org/repo name (fragmented on purpose)
assert_not_contains "$PUB" "whoami" "public CHANGELOG must not mention the internal test project"
assert_not_contains "$PUB" "pseudo-""lang" "public CHANGELOG must not expose the legacy author domain"
assert_not_contains "$PUB" "V""ladimir" "public CHANGELOG must not name the real person (cap)"
assert_not_contains "$PUB" "v""ladimir" "public CHANGELOG must not name the real person (lower)"
assert_not_contains "$PUB" "duke""lic" "public CHANGELOG must not expose the personal surname/email"
assert_not_contains "$PUB" "/Users/""v""ladimir" "public CHANGELOG must not contain absolute home paths"
assert_not_contains "$PUB" "$PRIOR_ORG" "public CHANGELOG must not name the prior org/repo"

# 5. CHANGELOG.dev.md is untracked (gitignored) — git knows nothing about it.
assert_eq "$(git -C "$REPO_ROOT" ls-files CHANGELOG.dev.md)" "" \
    "CHANGELOG.dev.md is gitignored/untracked"

test_summary
