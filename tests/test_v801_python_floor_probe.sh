#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# bin/architect-brain must reject Python < 3.10 with a CLEAN message (not a raw
# traceback or ModuleNotFoundError) — the Preflight floor the SKILL promises. The
# first architect-brain call (the Preflight banner) is where a missing/too-old
# python3 first bites, so the wrapper itself guards it.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCHITECT_BRAIN="$PLUGIN_ROOT/bin/architect-brain"

[ -x "$ARCHITECT_BRAIN" ] || { echo "FAIL: $ARCHITECT_BRAIN not executable"; exit 1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# A fake python3 that fails the wrapper's `version_info >= (3, 10)` floor probe
# (emulating an old interpreter) and otherwise no-ops.
cat > "$tmp/python3" <<'PY'
#!/usr/bin/env bash
for a in "$@"; do
  case "$a" in
    *"version_info >= (3, 10)"*) exit 1 ;;   # floor probe: too old
    *"version_info[:3]"*) echo "3.9.0"; exit 0 ;;
  esac
done
exit 0
PY
chmod +x "$tmp/python3"

set +e
out=$(PATH="$tmp:$PATH" "$ARCHITECT_BRAIN" --version 2>&1)
rc=$?
set -e

[ "$rc" -ne 0 ] || { echo "FAIL: old python3 not rejected (rc=$rc); out: $out"; exit 1; }
echo "$out" | grep -qiE '3\.10|too old|required' || {
  echo "FAIL: expected a clean Python-floor message, got: $out"; exit 1;
}
echo "PASS: wrapper rejects Python < 3.10 cleanly (rc=$rc)"
