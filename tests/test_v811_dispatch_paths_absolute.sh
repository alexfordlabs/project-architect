#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Guard: every plugin-relative reference/template path handed to a DISPATCHED
# subagent as an INPUT must be absolute (${CLAUDE_PLUGIN_ROOT}/...). A dispatched
# agent runs with cwd = the USER's project, not the plugin root, so a bare
# `skills/project-architect/...` INPUT path is unresolvable — the agent silently
# fails to Read its template/catalog/playbook and fabricates structure the
# auditor passes on structure alone. (This is the documented "subagent has no
# plugin base-dir" defect, fixed in reverse-engineer but historically never
# applied to project-architect itself.) State paths under `docs/...` stay
# relative — those ARE relative to the agent's user-project cwd.
source "$(dirname "$0")/lib/test_helpers.sh"

DP="$REPO_ROOT/skills/project-architect/references/dispatch-prompts.md"
AC="$REPO_ROOT/skills/project-architect/references/agent-common.md"
DA="$REPO_ROOT/agents/document-author.md"
CT="$REPO_ROOT/agents/claude-tooling-author.md"

assert_file_exists "$DP" 'dispatch-prompts.md exists'
D="$(cat "$DP" 2>/dev/null || true)"

# Each plugin-relative INPUT path (incl. the new catalog_path) is an absolute
# ${CLAUDE_PLUGIN_ROOT} path the orchestrator expands at dispatch time.
for key in template_path template_root_path template_subfolder_path integration_path playbook_path catalog_path; do
  assert_contains "$D" "${key}: \${CLAUDE_PLUGIN_ROOT}/skills/project-architect/" \
    "INPUT '${key}' is an absolute \${CLAUDE_PLUGIN_ROOT} path"
done

# No bare plugin-relative INPUT path survives anywhere in the dispatch bodies.
BARE="$(grep -nE '^[a-z_]+_path: skills/project-architect/' "$DP" || true)"
assert_eq "$BARE" "" 'no INPUT path is a bare (unresolvable) plugin-relative skills/... path'

# agent-common.md carries the absolute-path contract + BLOCKER discipline.
A="$(cat "$AC" 2>/dev/null || true)"
assert_contains "$A" 'absolute' 'agent-common states reference/template INPUT paths are absolute'
assert_contains "$A" 'BLOCKER' 'agent-common treats a bare relative reference path as a BLOCKER'

# document-author reads the catalog via its absolute INPUT, not a self-built path.
DAC="$(cat "$DA" 2>/dev/null || true)"
assert_not_contains "$DAC" 'Open `skills/project-architect/references/catalog.json`' \
  'document-author does not self-construct an unresolvable catalog path'
assert_contains "$DAC" 'catalog_path' 'document-author reads the catalog via the catalog_path INPUT'

# claude-tooling-author reads the SLASH_* templates via the absolute template_root_path INPUT.
CTC="$(cat "$CT" 2>/dev/null || true)"
assert_not_contains "$CTC" 'Read `references/templates/SLASH_SCAFFOLD.md`' \
  'claude-tooling-author does not self-construct an unresolvable SLASH template path'
assert_contains "$CTC" 'template_root_path' 'claude-tooling-author reads SLASH templates via template_root_path'

test_summary
