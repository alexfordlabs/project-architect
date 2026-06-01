#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Smoke-test: `architect-brain --help` returns 0 and mentions core subcommands.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCHITECT_BRAIN="$PLUGIN_ROOT/bin/architect-brain"

[ -x "$ARCHITECT_BRAIN" ] || { echo "FAIL: $ARCHITECT_BRAIN not executable"; exit 1; }

out=$("$ARCHITECT_BRAIN" --help 2>&1)
echo "$out" | grep -q "architect-brain" || { echo "FAIL: help output missing tool name"; exit 1; }
echo "$out" | grep -q "init"  || { echo "FAIL: help missing 'init'"; exit 1; }
echo "$out" | grep -q "audit" || { echo "FAIL: help missing 'audit'"; exit 1; }
echo "PASS: architect-brain --help shows expected output"
