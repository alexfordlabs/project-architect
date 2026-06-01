#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

# Shared test helpers for project-architect tests.
# Source this file in every test:  source "$(dirname "$0")/lib/test_helpers.sh"

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export REPO_ROOT

PASS_COUNT=0
FAIL_COUNT=0
FAIL_MESSAGES=()

# assert_eq <actual> <expected> <message>
assert_eq() {
  local actual="$1"
  local expected="$2"
  local msg="${3:-(no message)}"
  if [[ "$actual" == "$expected" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MESSAGES+=("FAIL: $msg — expected '$expected', got '$actual'")
    return 1
  fi
}

# assert_contains <haystack> <needle> <message>
assert_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-(no message)}"
  if [[ "$haystack" == *"$needle"* ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MESSAGES+=("FAIL: $msg — '$needle' not found in haystack")
    return 1
  fi
}

# assert_not_contains <haystack> <needle> <message>
assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-(no message)}"
  if [[ "$haystack" != *"$needle"* ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MESSAGES+=("FAIL: $msg — '$needle' found in haystack but should not be present")
    return 1
  fi
}

# assert_file_exists <path> <message>
assert_file_exists() {
  local path="$1"
  local msg="${2:-(no message)}"
  if [[ -f "$path" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MESSAGES+=("FAIL: $msg — file '$path' does not exist")
    return 1
  fi
}

# assert_dir_exists <path> <message>
assert_dir_exists() {
  local path="$1"
  local msg="${2:-(no message)}"
  if [[ -d "$path" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MESSAGES+=("FAIL: $msg — directory '$path' does not exist")
    return 1
  fi
}

# assert_executable <path> <message>
assert_executable() {
  local path="$1"
  local msg="${2:-(no message)}"
  if [[ -x "$path" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MESSAGES+=("FAIL: $msg — file '$path' is not executable")
    return 1
  fi
}

# assert_exit_code <expected_code> <command...>
assert_exit_code() {
  local expected="$1"
  shift
  "$@" >/dev/null 2>&1
  local actual=$?
  if [[ "$actual" == "$expected" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MESSAGES+=("FAIL: $* — expected exit code $expected, got $actual")
    return 1
  fi
}

# Print summary at end-of-test. Call this last.
test_summary() {
  echo ""
  echo "──────────────────────────────"
  echo "PASSED: $PASS_COUNT"
  echo "FAILED: $FAIL_COUNT"
  if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo ""
    echo "FAILURES:"
    for m in "${FAIL_MESSAGES[@]}"; do
      echo "  $m"
    done
    exit 1
  fi
  exit 0
}
