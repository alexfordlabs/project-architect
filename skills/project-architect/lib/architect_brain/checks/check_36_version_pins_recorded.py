"""check_36 -- generated artifacts must ride researched pins, not plugin floors.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

NEW in v9.1 — the enforcement that closes the tiger-panther-game gap: the
config generators fall back to a plugin-baked floor whenever the corresponding
``stack.versions.<token>`` decision was never recorded, and that fallback used
to be SILENT (the shipped biome.json sat a full major behind newest-stable and
nothing flagged it). This check makes the fallback visible: for every pin token
the chosen stack makes applicable (``configs.applicable_pin_tokens`` — the SAME
predicates ``generate-configs`` emits by, so obligation and emission cannot
diverge), if the consuming artifact exists on disk and the pin is missing from
the flat index, emit a WARNING finding naming the exact ``set-decision`` to run.

PASS when nothing was generated yet (pre-scaffold: nothing to verify), when the
stack makes no tokens applicable, or when every applicable+generated token has
a recorded pin. WARNING (house convention for new checks: observe, then
promote): the artifact still works on the floor version — it is just not
newest-stable, which research-scout § 1a was supposed to resolve.
"""

from __future__ import annotations

from architect_brain.checks import _state
from architect_brain.configs import applicable_pin_tokens, usable_pin
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "36"
NAME = "version_pins_recorded"
SEVERITY = "WARNING"


def run(state_dir) -> CheckResult:
    """Flag generated artifacts whose version pin was never recorded in state."""
    proj = _state.project_root(state_dir)
    flat_index = _state.load_flat_index(state_dir)

    findings: list[Finding] = []
    for token, artifact in sorted(applicable_pin_tokens(flat_index).items()):
        artifact_path = proj / artifact
        if not artifact_path.is_file():
            continue  # not generated yet — nothing shipped on a floor
        if usable_pin(flat_index, token) is not None:
            continue  # shared predicate with _pin — recorded ⇒ emitted, no divergence
        findings.append(
            Finding(
                message=(
                    f"stack.versions.{token} not recorded — {artifact} was "
                    f"generated from the plugin's baked floor (stale on the "
                    f"plugin's release cadence). Resolve the newest-stable "
                    f"version (research-scout § 1a) and record it: "
                    f"architect-brain set-decision stack.versions.{token} "
                    f"'<resolved-pin>'"
                ),
                location=str(artifact_path),
            )
        )

    passed = not findings
    summary = (
        "all applicable version pins recorded (or nothing generated yet)"
        if passed
        else f"{len(findings)} generated artifact(s) riding a plugin-floor version"
    )
    return CheckResult(
        check_id=CHECK_ID,
        passed=passed,
        severity=SEVERITY,
        summary=summary,
        findings=tuple(findings),
    )
