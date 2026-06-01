#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

C="$REPO_ROOT/skills/project-architect/references/document-catalog.md"
assert_file_exists "$C" "document-catalog.md must exist"

CONTENT=$(cat "$C")
for tpl in CLAUDE_MD_PLAN CLAUDE_TOOLING_PLAN SCAFFOLD_PLAN NEXT_STEP_PLAN; do
  assert_contains "$CONTENT" "$tpl" "catalog must register $tpl"
done

# Also verify generate_when expressions are mentioned for the conditional templates
assert_contains "$CONTENT" 'documentation_only' 'catalog must mention SCAFFOLD_PLAN generate_when condition'

test_summary
