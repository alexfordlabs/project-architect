"""check_23 -- dependency manifests must not pin pre-release / unstable versions.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Port of v7's check_23_dependency_freshness. Scans the common manifests under
the WHOLE project tree (v9.1 — previously top-level only, which let a nested
``web/package.json`` ship pre-release pins unaudited; third-party/build dirs
like ``node_modules``/``vendor``/``dist`` are pruned) for version specifiers
carrying a pre-release tag (-rc/-beta/-alpha/-canary/-next/-pre/-preview/-dev/
-nightly/-snapshot). Pinning a pre-release ships a moving target to users;
WARNING surfaces it for a human/research-scout to resolve a newest-stable
version (not mechanically auto-fixed). v8-ADAPTATION: there is no
schema-version gate anymore -- the check reads project manifests directly and
PASSES (nothing to verify) when none exist or none parse; json_valid
(check_05) / state_schema (check_29) own well-formedness.

KNOWN LIMITATION (carried from v7): package.json deps are matched as the joined
``name@version`` string, so a package whose NAME carries ``-<token>`` followed by
a digit/dot/hyphen boundary can false-positive even on a stable version (e.g.
``foo-rc2@1.0.0``). Blast radius is low: WARNING / surface / non-auto-fixable, so a
human reviews the flagged list.

OWN-VERSION EXCLUSION (carried from v7 v6.0.1): for TOML manifests (Cargo.toml,
pyproject.toml) a bare top-level ``version = "x"`` (the project's own version under
[package]/[project]) is dropped before matching, so a project's own legit
pre-release (e.g. 0.1.0-alpha.0) is not flagged. Real dependency pins carry a name.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "23"
NAME = "dependency_freshness"
SEVERITY = "WARNING"

# Leading hyphen before the pre-release token, then a ./digit/-/end boundary.
_PRERELEASE_RE = re.compile(
    r"-(rc|beta|alpha|canary|next|pre|preview|dev|nightly|snapshot)([.0-9-]|$)",
    re.IGNORECASE,
)

# A bare top-level `version = ...` line (the project's own version, not a dep).
_OWN_VERSION_RE = re.compile(r"^\s*version\s*=")

_LINE_MANIFESTS = ("requirements.txt", "go.mod", "Gemfile")
_TOML_MANIFESTS = ("Cargo.toml", "pyproject.toml")

# Directories that hold third-party / generated / historical code — not the
# user's own dependency declarations. Pruned from the tree walk.
_PRUNED_DIRS = frozenset({
    ".git", "node_modules", "vendor", "dist", "build", "target", "out",
    ".venv", "venv", "__pycache__", ".next", ".turbo", ".cache", "versions",
})


def _iter_manifests(proj: Path, name: str):
    """Yield every first-party ``<name>`` manifest in the tree (pruned walk)."""
    for root, dirs, files in os.walk(proj):
        dirs[:] = sorted(d for d in dirs if d not in _PRUNED_DIRS)
        if name in files:
            yield Path(root) / name


def _label(proj: Path, path: Path) -> str:
    """Project-root-relative posix label (``package.json``, ``web/package.json``)."""
    return path.relative_to(proj).as_posix()


def _scan_package_json(proj: Path, pkg_path: Path) -> list[Finding]:
    """Join dependencies + devDependencies as ``name@version`` and match each."""
    data = _state.load_json(pkg_path)
    if not isinstance(data, dict):
        # Malformed JSON defers to check_05 (json_valid); nothing to verify here.
        return []
    findings: list[Finding] = []
    deps: dict = {}
    for section in ("dependencies", "devDependencies"):
        block = data.get(section)
        if isinstance(block, dict):
            deps.update(block)
    for name, version in deps.items():
        dep = f"{name}@{version}"
        if _PRERELEASE_RE.search(dep):
            findings.append(
                Finding(
                    message=f"{_label(proj, pkg_path)}: {dep}",
                    location=str(pkg_path),
                )
            )
    return findings


def _scan_line_manifest(
    proj: Path, path: Path, *, drop_own_version: bool
) -> list[Finding]:
    """Match the manifest's lines, optionally dropping the own-version line."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    findings: list[Finding] = []
    for raw_line in text.splitlines():
        if drop_own_version and _OWN_VERSION_RE.match(raw_line):
            continue
        if _PRERELEASE_RE.search(raw_line):
            findings.append(
                Finding(
                    message=f"{_label(proj, path)}: {raw_line.strip()}",
                    location=str(path),
                )
            )
    return findings


def run(state_dir) -> CheckResult:
    """Flag any pre-release / unstable dependency pin in a project manifest."""
    proj = _state.project_root(state_dir)
    findings: list[Finding] = []

    for pkg_path in _iter_manifests(proj, "package.json"):
        findings.extend(_scan_package_json(proj, pkg_path))

    for manifest in _LINE_MANIFESTS:
        for path in _iter_manifests(proj, manifest):
            findings.extend(_scan_line_manifest(proj, path, drop_own_version=False))

    for manifest in _TOML_MANIFESTS:
        for path in _iter_manifests(proj, manifest):
            findings.extend(_scan_line_manifest(proj, path, drop_own_version=True))

    passed = not findings
    summary = (
        "no pre-release/unstable dependency pins detected"
        if passed
        else f"{len(findings)} pre-release/unstable dependency pin(s)"
    )
    return CheckResult(
        check_id=CHECK_ID,
        passed=passed,
        severity=SEVERITY,
        summary=summary,
        findings=tuple(findings),
    )
