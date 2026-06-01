"""check_25 -- privacy/anonymity-sensitive projects must not silently depend on
deanonymizing/centralized backend services.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Two-stage TRIGGER-then-SCAN. The check only applies when the project is
privacy/anonymity-sensitive -- either the ``project.privacy_sensitive`` decision
is truthy, or the ``docs/`` corpus matches anonymity-domain keywords. Once
triggered, each dependency manifest is scanned for a fixed blocklist of
deanonymizing/centralized services (Firebase, Google Analytics, Sentry,
Mixpanel, etc.) and every distinct hit is surfaced for human reconsideration.
WARNING (not blocking): swapping such a backend for a metadata-resistant
alternative is an architecture decision, not an auto-fixable defect.

v8-ADAPTATION of v7's check_25_anonymity_threat_preflight.sh: the privacy flag
now comes from the flat decision index (``_state.load_decisions``) instead of
``jq .decisions[...]`` on a monolithic state.json, and the keyword corpus is the
``collect_markdown`` doc scan (which skips the ``_architect_state`` machine-state
subtree) instead of v7's ``read_md_corpus``. Absent data => PASS (a fresh
project is not privacy-sensitive => preflight not applicable).
"""

from __future__ import annotations

import re
from pathlib import Path

from architect_brain.checks import _state
from architect_brain.checks._docscan import collect_markdown
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "25"
NAME = "anonymity_threat_preflight"
SEVERITY = "WARNING"

# Manifests scanned (at the project root, not recursively). Mirrors v7.
_MANIFESTS: tuple[str, ...] = (
    "package.json",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "pyproject.toml",
)

# Anonymity-domain keywords that put a project in scope. ``\bTor\b`` keeps Tor
# from matching "factory"/"vendor"; the rest are plain substrings.
_TRIGGER_RE = re.compile(
    r"anonymous|anonymity|\bTor\b|onion service|zero-knowledge"
    r"|end-to-end encrypt|threat model|metadata-resistant",
    re.IGNORECASE,
)

# Deanonymizing/centralized services. Distinct hit per manifest is surfaced.
# Benign crypto/privacy libs (libsodium, age, openpgp, cryptography) are NOT here.
_BLOCKLIST_TERMS: tuple[str, ...] = (
    "firebase",
    "firebase-admin",
    "google-analytics",
    "googleapis",
    "gtag",
    "google-tag-manager",
    "@sentry",
    "sentry-sdk",
    "mixpanel",
    "segment",
    "amplitude",
    "fullstory",
    "hotjar",
    "datadog",
    "aws-amplify",
    "cognito",
    "onesignal",
    "@vercel/analytics",
)
# Order longest-first so an alternative is tried before any term that is a
# prefix of it (Python re is leftmost-FIRST, not POSIX leftmost-LONGEST): this
# keeps ``firebase-admin`` from being swallowed by the ``firebase`` alternative,
# matching v7's ``grep -ioE`` (POSIX leftmost-longest) intent of reporting it as
# its own distinct service.
_BLOCKLIST_RE = re.compile(
    "|".join(re.escape(term) for term in sorted(_BLOCKLIST_TERMS, key=len, reverse=True)),
    re.IGNORECASE,
)


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def _is_privacy_flag_set(decisions) -> bool:
    """The ``project.privacy_sensitive`` decision, accepting bool True or "true"."""
    value = decisions.get("project.privacy_sensitive")
    return value is True or value == "true"


def _docs_mention_anonymity(state_dir: Path) -> bool:
    """Whether any design ``.md`` doc matches an anonymity-domain keyword."""
    for md in collect_markdown(_state.docs_root(state_dir)):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        if _TRIGGER_RE.search(text):
            return True
    return False


def _scan_manifest(proj: Path, name: str) -> list[Finding]:
    """Return one Finding per DISTINCT blocklisted service in ``proj/name``."""
    manifest = proj / name
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return []
    # Preserve first-seen order; dedupe by lowercased canonical service term.
    seen: set[str] = set()
    findings: list[Finding] = []
    for match in _BLOCKLIST_RE.finditer(text):
        svc = match.group(0).lower()
        if svc in seen:
            continue
        seen.add(svc)
        findings.append(
            Finding(message=f"{name} references '{svc}'", location=str(manifest))
        )
    return findings


def run(state_dir) -> CheckResult:
    """Trigger on privacy-sensitivity, then surface deanonymizing services."""
    state_dir = Path(state_dir)
    decisions = _state.load_decisions(state_dir)

    triggered = _is_privacy_flag_set(decisions) or _docs_mention_anonymity(state_dir)
    if not triggered:
        return _pass("not privacy/anonymity-sensitive; preflight not applicable")

    proj = _state.project_root(state_dir)
    findings: list[Finding] = []
    for name in _MANIFESTS:
        findings.extend(_scan_manifest(proj, name))

    if not findings:
        return _pass(
            "privacy-sensitive project; no deanonymizing/centralized services detected"
        )

    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=f"{len(findings)} deanonymizing/centralized service(s) in a privacy-sensitive project",
        findings=tuple(findings),
    )
