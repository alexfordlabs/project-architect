#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# PL-detection routing in questioning-flow.md (v8 phase placement).
# Verifies the reference documents a Vision-phase sub-section that routes a
# "designing a programming language" intent into one of the 6 PL sub_types
# and cross-references the follow-up Tech Stack (Phase 4) batches (pl.impl_strategy
# + pl.host_runtime) and Doc Generation (Phase 6) template generation.

source "$(dirname "$0")/lib/test_helpers.sh"

REF="$REPO_ROOT/skills/project-architect/references/questioning-flow.md"

assert_file_exists "$REF" 'questioning-flow.md must exist'

CONTENT=$(cat "$REF")

# The PL routing lives in the Vision phase's per-type drill-down.
assert_contains "$CONTENT" 'Programming language sub_type routing' 'questioning-flow.md must document the PL sub_type routing section'

# A dedicated Phase 1 PL routing section must exist. Title is flexible
# (the implementation may pick "Programming language sub_type routing"
# or similar), but it must combine a Phase 1 reference with PL routing intent.
assert_contains "$CONTENT" 'Phase 1' 'questioning-flow.md must reference Phase 1 in the PL routing section'
assert_contains "$CONTENT" 'programming language' 'questioning-flow.md must explicitly call out "programming language" intent detection'

# Detection signal: must mention triggering keywords the orchestrator
# should react to in earlier phases (compiler / interpreter / DSL / transpiler).
assert_contains "$CONTENT" 'compiler' 'questioning-flow.md must list "compiler" as a PL-intent signal'
assert_contains "$CONTENT" 'interpreter' 'questioning-flow.md must list "interpreter" as a PL-intent signal'
assert_contains "$CONTENT" 'DSL' 'questioning-flow.md must list "DSL" as a PL-intent signal'
assert_contains "$CONTENT" 'transpiler' 'questioning-flow.md must list "transpiler" as a PL-intent signal'

# All 6 PL sub_types must be named verbatim so the orchestrator can
# write them into state.decisions.project.sub_type unchanged.
for st in general_purpose_language domain_specific_language query_language configuration_language educational_language transpiler_target; do
  assert_contains "$CONTENT" "$st" "questioning-flow.md must name PL sub_type: $st"
done

# Routing rule: must explicitly persist the answer as the flat decision
# project.sub_type (v8 — no monolith state.decisions) so the reader knows where it lands.
assert_contains "$CONTENT" 'project.sub_type' 'questioning-flow.md must persist the PL sub_type as the flat decision project.sub_type'
assert_contains "$CONTENT" 'sub_type' 'questioning-flow.md must mention sub_type assignment for PL routing'

# Cross-reference to the Tech Stack (Phase 4) follow-up batches (pl.impl_strategy +
# pl.host_runtime are asked there, after Architecture).
assert_contains "$CONTENT" 'Tech Stack (Phase 4)' 'questioning-flow.md must cross-reference the Tech Stack phase (Phase 4) for PL follow-up batches'
assert_contains "$CONTENT" 'impl_strategy' 'questioning-flow.md must reference impl_strategy as the Phase 2 PL follow-up'
assert_contains "$CONTENT" 'host_runtime' 'questioning-flow.md must reference host_runtime as the Phase 2 PL follow-up'

# Cross-reference to Doc Generation (Phase 6) where the 7 PL templates generate.
assert_contains "$CONTENT" 'Doc Generation (Phase 6)' 'questioning-flow.md must cross-reference Doc Generation (Phase 6), where the 7 PL templates generate'

# Distinguishing one-liner cues for each sub_type — at least one well-known
# example or signal phrase per variant, so the user can self-classify.
assert_contains "$CONTENT" 'general-purpose' 'questioning-flow.md must describe general_purpose_language with a "general-purpose" phrase'
assert_contains "$CONTENT" 'embedded' 'questioning-flow.md must distinguish DSLs by an "embedded" / narrow-grammar cue'
assert_contains "$CONTENT" 'query' 'questioning-flow.md must distinguish query_language with the word "query"'
assert_contains "$CONTENT" 'configuration' 'questioning-flow.md must distinguish configuration_language with the word "configuration"'
assert_contains "$CONTENT" 'educational' 'questioning-flow.md must distinguish educational_language with the word "educational"'
assert_contains "$CONTENT" 'target language' 'questioning-flow.md must describe transpiler_target by the "target language" phrasing'

test_summary
