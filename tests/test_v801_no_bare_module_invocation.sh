#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Guard (v8.0.1): no agent prompt may invoke the bare `python3 -m architect_brain`
# module form. A dispatched subagent runs in a fresh shell with no PYTHONPATH, so
# the bare form raises `ModuleNotFoundError: No module named architect_brain`.
# Agents MUST use the ${CLAUDE_PLUGIN_ROOT}/bin/architect-brain wrapper, which sets
# PYTHONPATH before exec'ing the module.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

hits=$(grep -rnE 'python3[[:space:]]+-m[[:space:]]+architect_brain' "$PLUGIN_ROOT/agents" 2>/dev/null || true)
if [ -n "$hits" ]; then
  echo "FAIL: bare 'python3 -m architect_brain' found in agent prompt(s) — use the wrapper:"
  echo "$hits"
  exit 1
fi
echo "PASS: no bare 'python3 -m architect_brain' invocation in agents/"
