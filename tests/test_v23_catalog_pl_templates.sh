#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

C="$REPO_ROOT/skills/project-architect/references/document-catalog.md"
assert_file_exists "$C" "document-catalog.md must exist"

CONTENT=$(cat "$C")

# All 7 PL templates must be registered by name
for tpl in LANGUAGE_GRAMMAR SEMANTICS TYPE_SYSTEM STDLIB TOOLCHAIN BOOTSTRAP_PLAN STABILITY_AND_RFC; do
  assert_contains "$CONTENT" "$tpl" "catalog must register $tpl"
done

# Section must be discoverable as a "Programming language" / "PL" concept
# Match either spelling — we OR the two needles by checking each independently
if [[ "$CONTENT" == *"Programming language"* ]] || [[ "$CONTENT" == *"programming language"* ]]; then
  assert_contains "$CONTENT" "" "catalog mentions Programming language concept"
else
  # force a failure with a meaningful message via assert_contains on a sentinel needle
  assert_contains "$CONTENT" "Programming language" "catalog should mention 'Programming language' as a section concept"
fi

# At least 3 of the 6 PL sub_types must appear so readers can map gates back to sub_types
assert_contains "$CONTENT" "general_purpose_language" "catalog must reference general_purpose_language sub_type"
assert_contains "$CONTENT" "domain_specific_language" "catalog must reference domain_specific_language sub_type"
assert_contains "$CONTENT" "educational_language" "catalog must reference educational_language sub_type"

# v2.3 / Sketch F marker present so the section is locatable by version
if [[ "$CONTENT" == *"v2.3"* ]] || [[ "$CONTENT" == *"Sketch F"* ]]; then
  assert_contains "$CONTENT" "" "catalog carries a v2.3 / Sketch F marker"
else
  assert_contains "$CONTENT" "v2.3" "catalog should carry a 'v2.3' or 'Sketch F' marker"
fi

test_summary
