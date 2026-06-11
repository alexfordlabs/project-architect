#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Meta-test (Wave 1.13): tests/run_all.sh must integrate the architect_brain
# Python unittest suite + must pre-clean __pycache__/.hypothesis caches so
# test_v401_no_absolute_home_paths.sh stays green between development runs.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_ALL="$PLUGIN_ROOT/tests/run_all.sh"

[[ -f "$RUN_ALL" ]] || { echo "FAIL: $RUN_ALL not found"; exit 1; }

# Assert 1: run_all.sh references __pycache__ cleanup OR PYTHONDONTWRITEBYTECODE
if ! grep -qE "(__pycache__|PYTHONDONTWRITEBYTECODE)" "$RUN_ALL"; then
  echo "FAIL: run_all.sh missing __pycache__/PYTHONDONTWRITEBYTECODE hygiene"
  exit 1
fi

# Assert 2: run_all.sh integrates the architect_brain Python unittest suite
if ! grep -qE "(architect_brain\.tests|python3 -m unittest discover.*architect_brain)" "$RUN_ALL"; then
  echo "FAIL: run_all.sh missing architect_brain Python suite integration"
  exit 1
fi

# Assert 3: run_all.sh also cleans .hypothesis caches (Wave 1.7 property test)
if ! grep -q "\.hypothesis" "$RUN_ALL"; then
  echo "FAIL: run_all.sh missing .hypothesis cache hygiene (Wave 1.7 artifact)"
  exit 1
fi

echo "PASS: run_all.sh integrates Python brain suite + handles pyc/.hypothesis hygiene"
