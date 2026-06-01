"""Deterministic Mermaid C4 diagram generators.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Each ``gen_c4_*`` function takes a flat-index projection and returns a Mermaid
C4 diagram block (context / container / component). Output is DETERMINISTIC:
the same flat-index produces byte-identical text. Wave 4 builds out all three
C4 levels; the ``generate-diagram`` CLI (later task) emits them on demand.
"""

from __future__ import annotations

from typing import Any


def _dec(flat_index: dict[str, Any], key: str, default: Any = None) -> Any:
    """Read a decision value from the flat index by dotted key."""
    if not isinstance(flat_index, dict):
        return default
    return flat_index.get("decisions", {}).get(key, default)


def gen_c4_context(flat_index: dict[str, Any]) -> str:
    """Emit a Mermaid C4Context (system-context) diagram (deterministic)."""
    name = _dec(flat_index, "project.name") or "System"
    db = _dec(flat_index, "stack.database.engine")
    lines = [
        "C4Context",
        f"    title System Context diagram for {name}",
        '    Person(user, "User", "End user of the system")',
        f'    System(app, "{name}", "The application")',
        '    Rel(user, app, "Uses")',
    ]
    if db:
        lines.append(f'    System_Ext(db, "Database", "{db}")')
        lines.append('    Rel(app, db, "Reads from and writes to")')
    return "\n".join(lines) + "\n"


def gen_c4_container(flat_index: dict[str, Any]) -> str:
    """Emit a Mermaid C4Container diagram (deterministic)."""
    name = _dec(flat_index, "project.name") or "System"
    framework = _dec(flat_index, "stack.frontend.framework") or "Application"
    db = _dec(flat_index, "stack.database.engine")
    lines = [
        "C4Container",
        f"    title Container diagram for {name}",
        '    Person(user, "User", "End user")',
        f'    Container(app, "{name}", "{framework}", "Main application")',
    ]
    if db:
        lines.append(f'    ContainerDb(db, "Database", "{db}", "Stores application data")')
    lines.append('    Rel(user, app, "Uses")')
    if db:
        lines.append('    Rel(app, db, "Reads from and writes to")')
    return "\n".join(lines) + "\n"


def gen_c4_component(flat_index: dict[str, Any]) -> str:
    """Emit a Mermaid C4Component diagram for the app's internal layers (deterministic)."""
    name = _dec(flat_index, "project.name") or "System"
    db = _dec(flat_index, "stack.database.engine")
    lines = [
        "C4Component",
        f"    title Component diagram for {name}",
        f'    Container_boundary(app, "{name}") {{',
        '        Component(api, "API Layer", "Controllers", "Handles inbound requests")',
        '        Component(svc, "Service Layer", "Domain logic", "Business rules")',
    ]
    if db:
        lines.append('        Component(repo, "Data Access", "Repository", "Persists data")')
    lines.append("    }")
    lines.append('    Rel(api, svc, "Calls")')
    if db:
        lines.append('    Rel(svc, repo, "Uses")')
    return "\n".join(lines) + "\n"
