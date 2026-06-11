"""Run-UI rendering (banner, progress bar, phase ladder) — ported from v7 bin/architect-ui.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Pure stdout text, NO ANSI escapes (the Claude Code transcript is append-only
markdown, not a TTY). The "beauty" is the Unicode block-char wordmark, the
✓/→/✗ status glyphs, and a clean monospace layout. Wave 4c ports banner +
progress + phase_bar from the bash original; the `architect-brain ui ...` CLI
wires them.
"""

from __future__ import annotations


def banner() -> str:
    """Return the project-architect wordmark banner + tagline (deterministic).

    The block-char art spells ARCHITECT; the plain-text tagline guarantees the
    literal substring "architect"/"project-architect" for any caller + the test
    contract (carried over from v7's bin/architect-ui).
    """
    return (
        "   ▄▀█ █▀█ █▀▀ █░█ █ ▀█▀ █▀▀ █▀▀ ▀█▀\n"
        "   █▀█ █▀▄ █▄▄ █▀█ █ ░█░ ██▄ █▄▄ ░█░\n"
        "\n"
        "   project-architect · design-first project bootstrapping\n"
        "   ─────────────────────────────────────────────────────\n"
    )


_BAR_WIDTH = 20


def progress(current: int, total: int, label: str = "") -> str:
    """Render an advancing block-char progress bar line (ported from v7).

    No ANSI: the transcript is append-only markdown, not a TTY. A non-positive
    ``total`` clamps to 0%/empty (divide-by-zero guard); an over-count clamps to
    100%/full.
    """
    if total <= 0:
        filled = 0
        pct = 0
    else:
        filled = current * _BAR_WIDTH // total
        pct = current * 100 // total
        if filled > _BAR_WIDTH:
            filled = _BAR_WIDTH
        if pct > 100:
            pct = 100
    empty = _BAR_WIDTH - filled
    bar = "█" * filled + "░" * empty
    return f"  Phase {current}/{total}  [{bar}] {pct:3d}%  {label}\n"


def step(symbol: str, text: str) -> str:
    """Render a single status line: ``<symbol> <text>`` (symbol ∈ ✓ → ✗)."""
    return f"{symbol} {text}\n"


# The v8 user-facing phase ladder. NOTE the v8 reorder vs v7: Architecture (3)
# comes BEFORE Tech stack (4), and Cost (5) is its own phase. Preflight is the
# banner-only opener (no bar). Unknown/empty keys are chain-safe no-ops.
_PHASE_LADDER: dict[str, tuple[int, str] | None] = {
    "preflight": None,
    "kickoff": (1, "Universal kickoff"),
    "vision": (2, "Vision & requirements"),
    "architecture": (3, "Architecture"),
    "stack": (4, "Tech stack"),
    "cost": (5, "Cost model"),
    "docs": (6, "Doc generation"),
    "iteration": (7, "Iteration"),
    "lock": (8, "Lock"),
    "tooling": (9, "Tooling execution"),
    "handoff": (10, "Handoff"),
    "complete": (11, "Complete"),
}
_PHASE_TOTAL = 11


def phase_bar(phase_key: str) -> str:
    """Render the ladder row for a v8 phase key, or "" for banner-only/unknown keys."""
    entry = _PHASE_LADDER.get(phase_key)
    if entry is None:
        return ""
    current, label = entry
    return progress(current, _PHASE_TOTAL, label)
