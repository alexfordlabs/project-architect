"""Canonical project-type registry (v8 adds the agentic_system type).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

The single machine-readable source of valid top-level project types + the
agentic_system sub-types (spec §5.7). The catalog conditions, golden paths, and
(Wave 5) the auditor's project-type check all key off this list. Adding a type
is a one-tuple edit here.
"""

from __future__ import annotations


class ProjectTypeError(Exception):
    """A project.type value is not in the canonical registry."""


# Canonical top-level project types. ``agentic_system`` was the v8 addition
# (spec §5.7); the trailing ``web3``/``scientific``/``ar_vr`` were registered in
# v8.2 to match the advertised type set + their catalog docs; the rest carry
# forward v7's set.
TOP_LEVEL_TYPES: tuple[str, ...] = (
    "web_app",
    "mobile_app",
    "api_service",
    "cli",
    "library",
    "desktop_app",
    "game",
    "data_pipeline",
    "ml_project",
    "programming_language",
    "browser_extension",
    "claude_code_plugin",
    "mcp_server",
    "embedded_system",
    "infrastructure",
    "static_site",
    "documentation_only",
    "agentic_system",
    # Advertised in plugin.json + the SKILL frontmatter and carrying their own
    # catalog docs (WEB3_SPECIFIC / SCIENTIFIC_COMPUTING / AR_VR_SPECIFIC) plus
    # interview drill-downs (web3 / scientific in questioning-flow.md), but
    # previously absent from this registry — so those docs could never fire.
    # Registered here so the catalog<->registry contract holds
    # (tests/test_catalog_typeliterals_valid.py pins it).
    "web3",
    "scientific",
    "ar_vr",
)


# Sub-types for the agentic_system top-level type (spec §5.7).
AGENTIC_SUBTYPES: tuple[str, ...] = (
    "single_agent",
    "multi_agent_orchestrator",
    "agentic_tool",
)


def is_valid_project_type(value: str) -> bool:
    """Return True if ``value`` is a known top-level project type."""
    return value in TOP_LEVEL_TYPES


def is_valid_agentic_subtype(value: str) -> bool:
    """Return True if ``value`` is a known agentic_system sub-type."""
    return value in AGENTIC_SUBTYPES


def validate_project_type(value: str) -> None:
    """Raise ProjectTypeError if ``value`` is not a known top-level type."""
    if value not in TOP_LEVEL_TYPES:
        raise ProjectTypeError(
            f"unknown project type {value!r} (not in {len(TOP_LEVEL_TYPES)} known types)"
        )
