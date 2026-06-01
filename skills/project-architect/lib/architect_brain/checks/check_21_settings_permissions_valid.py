"""check_21 -- .claude/settings.json permission rules must not fail open.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

A Claude Code permission rule of the form ``Tool(inner)`` matches via prefix
glob; a TRAILING ``:*`` (e.g. ``Bash(rm:*)``) is the valid form meaning "any
args after this colon". When ``:*`` appears MID-pattern (e.g.
``Bash(curl:* | sh)``) the rule silently fails to match the command it meant
to deny -- the deny rule fails OPEN, leaving a dangerous command permitted.

v8-ADAPTATION: v7 gated this behind a ``schema_version == "3.0"`` state check
and read state via jq. v8 drops that gate entirely -- it reads
``.claude/settings.json`` directly (it's the artifact being validated, not the
architect state) and never consults the flat index. Graceful degradation:
absent or unparseable settings (deferred to json_valid) => pass.
"""

from __future__ import annotations

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "21"
NAME = "settings_permissions_valid"
SEVERITY = "WARNING"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def run(state_dir) -> CheckResult:
    """Flag any permission rule whose inner pattern has a mid-pattern ``:*``."""
    settings_path = _state.project_root(state_dir) / ".claude" / "settings.json"
    settings = _state.load_json(settings_path)
    if settings is None:
        # Absent or unparseable -> nothing to verify (json_valid owns validity).
        return _pass("no .claude/settings.json (nothing to verify)")
    if not isinstance(settings, dict):
        return _pass(".claude/settings.json is not an object (deferred)")

    perms = settings.get("permissions") or {}
    if not isinstance(perms, dict):
        return _pass("permissions is not an object (nothing to verify)")

    rules: list = []
    for key in ("deny", "allow", "ask"):
        bucket = perms.get(key, [])
        if isinstance(bucket, list):
            rules.extend(bucket)

    if not rules:
        return _pass("no permission rules (nothing to verify)")

    findings: list[Finding] = []
    for rule in rules:
        if not isinstance(rule, str):
            continue
        # inner = text between the FIRST "(" and the LAST ")".
        open_idx = rule.find("(")
        close_idx = rule.rfind(")")
        if open_idx == -1 or close_idx == -1 or close_idx < open_idx:
            continue
        inner = rule[open_idx + 1 : close_idx]
        # Fails open: contains ":*" but does NOT end with ":*" (mid-pattern).
        if ":*" in inner and not inner.endswith(":*"):
            findings.append(
                Finding(
                    message=f"{rule} -- ':*' mid-pattern; fails open",
                    location=rule,
                )
            )

    if not findings:
        return _pass(
            f"{len(rules)} permission rule(s) valid (no mid-pattern ':*')"
        )

    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=f"{len(findings)} permission rule(s) fail open (mid-pattern ':*')",
        findings=tuple(findings),
    )
