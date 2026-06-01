#!/usr/bin/env bash
# Intentionally bad — for testing check_04_shellcheck.
# Triggers multiple shellcheck findings at warning severity:
#   - SC2164: unchecked `cd` (warning)
#   - SC2086: unquoted $1 (info — only visible at default severity)
#   - SC2154: undeclared variable usage (warning)
cd /tmp/some/path/that/may/not/exist
if [ -z $1 ]; then
  echo "missing arg: $undeclared_var"
fi
