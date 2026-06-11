"""MADR 4 + structured-MADR frontmatter parsing for project-architect v8.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Provides parse_frontmatter(text) which extracts YAML frontmatter (between ---
delimiters at the top of markdown text) into a dict.

Two implementations:

- stdlib-only path: handles the simple key:value subset that v8's structured-
  MADR frontmatter uses — strings, quoted strings, booleans, ints, null,
  inline empty lists ([]), and block lists of scalars (- item). It does NOT
  handle nested mappings, anchors, multi-line scalars, or flow-style maps.
  When the stdlib path encounters a nested-mapping construct (an indented
  ``key: value`` under another key) it ignores the inner key and continues
  with the next top-level key; this is the known limitation documented at
  the spec level.

- optional pyyaml-enhanced path: when ``pyyaml`` IS installed, the parser
  uses ``yaml.safe_load`` for full YAML 1.2 support including nested
  mappings (e.g., the ``audit: {required_review_at: null}`` field). When
  ``pyyaml`` is NOT installed, the stdlib fallback is sufficient for every
  flat key/value in the v8 MADR-4 + structured-MADR shape; only nested
  mappings are silently dropped.

``emit_frontmatter`` (the inverse) is the canonical writer: it emits keys
in the v8 spec canonical order, double-quotes strings (via ``json.dumps``,
so embedded ``"`` / backslashes / newlines are properly escaped into valid
YAML 1.2 flow scalars), leaves ints/bools/null unquoted, inlines empty
lists, and uses block-list form for non-empty lists. Output round-trips
through ``parse_frontmatter`` (modulo nested mappings, which require pyyaml
on both ends). NOTE: a value containing an embedded double-quote requires
the pyyaml path to round-trip — the stdlib subset parser strips the outer
quotes but does NOT un-escape ``\"``, so such values come back with the
backslash intact under the stdlib fallback. This is the same documented
"pyyaml on both ends" limitation that already applies to nested mappings.

``parse_madr_4_body`` extracts the MADR 4 section bodies (Context and
Problem Statement, Considered Options, Decision Outcome, Confirmation,
Consequences, Rejected alternatives) from the markdown body below the
frontmatter. Missing sections are omitted from the returned dict;
``Confirmation`` is reported both as a standalone key and inside
``Decision Outcome``'s body (since H3 sub-headings under H2 in MADR 4
are part of the parent section).
"""

from __future__ import annotations

import json
import re
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
    HAS_YAML = True
except ImportError:  # pragma: no cover - exercised only when pyyaml absent
    yaml = None  # type: ignore[assignment]
    HAS_YAML = False


_FRONTMATTER_OPEN = "---\n"


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown text.

    The frontmatter is the block between two ``---`` delimiter lines that
    begins on the first line of the document (a leading UTF-8 BOM is
    tolerated). Returns an empty dict if no frontmatter is present or the
    frontmatter block is malformed (e.g., missing closing ``---``).

    When pyyaml is available it is used for full YAML 1.2 parsing (including
    nested mappings). Otherwise the stdlib subset parser is used; see the
    module docstring for the supported subset.
    """
    if not text:
        return {}

    # Tolerate a leading UTF-8 BOM.
    stripped = text.lstrip("﻿")
    if not stripped.startswith(_FRONTMATTER_OPEN):
        return {}

    remainder = stripped[len(_FRONTMATTER_OPEN):]

    closing_match = re.search(r"^---\s*$", remainder, re.MULTILINE)
    if not closing_match:
        return {}

    frontmatter_text = remainder[: closing_match.start()]

    if HAS_YAML and yaml is not None:
        try:
            parsed = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            # Fall through to stdlib path if pyyaml errors (defensive).
            pass
        else:
            if isinstance(parsed, dict):
                return parsed
            return {}

    return _parse_frontmatter_stdlib(frontmatter_text)


def _parse_frontmatter_stdlib(text: str) -> dict[str, Any]:
    """Parse a subset of YAML using only stdlib.

    Supports:

    - Simple ``key: value`` where value is a string, quoted string, int,
      bool, null, or inline empty list (``[]``).
    - Block list of scalars::

          key:
            - item
            - "quoted item"

    Does NOT support nested mappings, anchors, multi-line scalars, or
    flow-style mappings. Nested keys under another key are silently dropped
    (only top-level keys are returned).
    """
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        # Only consume top-level (column-0) ``key: value`` lines. Lines that
        # start with whitespace are either block-list items (handled by the
        # parent-key loop below) or nested-mapping entries (ignored).
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not match:
            i += 1
            continue

        key, raw_value = match.group(1), match.group(2).strip()

        if raw_value == "":
            # Empty value: look ahead for a block list of scalars.
            list_items: list[Any] = []
            j = i + 1
            while j < n:
                if not lines[j].strip():
                    # Blank line inside a block list ends the list.
                    break
                item_match = re.match(r"^\s+-\s+(.*)$", lines[j])
                if not item_match:
                    break
                list_items.append(_parse_scalar(item_match.group(1).strip()))
                j += 1

            if list_items:
                result[key] = list_items
                i = j
                continue

            # No block list followed: it's either a nested mapping (which
            # we silently skip past) or a genuinely empty value. Detect a
            # nested mapping by an indented ``subkey:`` follow-up line and
            # skip those lines; otherwise record None.
            if i + 1 < n and re.match(r"^\s+[A-Za-z_][A-Za-z0-9_]*\s*:", lines[i + 1]):
                # Nested mapping — skip its indented block; do not record key.
                j = i + 1
                while j < n and (lines[j].startswith((" ", "\t")) or not lines[j].strip()):
                    j += 1
                i = j
                continue

            result[key] = None
            i += 1
            continue

        result[key] = _parse_scalar(raw_value)
        i += 1

    return result


def _parse_scalar(s: str) -> Any:
    """Parse a YAML-ish scalar: quoted string, int, bool, null, or bare string."""
    s = s.strip()

    # Inline empty list.
    if s == "[]":
        return []

    # Quoted string — strip the surrounding quotes (single or double).
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]

    # null
    if s.lower() in ("null", "~"):
        return None

    # bool
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False

    # int
    try:
        return int(s)
    except ValueError:
        pass

    # float (only if it actually looks float-y — avoids eating version strings,
    # though those should be quoted anyway in our schema).
    if "." in s:
        try:
            return float(s)
        except ValueError:
            pass

    # Bare string.
    return s


# Canonical key order for v8 structured-MADR frontmatter
_CANONICAL_KEYS: tuple[str, ...] = (
    "type",
    "schema_version",
    "id",
    "title",
    "status",
    "date",
    "decision_makers",
    "tags",
    "phase",
    "plugin_version",
    "supersedes",
    "superseded_by",
    "related",
    "risk",
    "audit",
)


def emit_frontmatter(metadata: dict[str, Any]) -> str:
    """Produce a structured-MADR YAML frontmatter string with deterministic ordering.

    Canonical keys are emitted first in the v8 spec order; other keys go after
    in alphabetical order. Strings are double-quoted; ints/bools/null unquoted;
    empty lists inline; non-empty lists as block lists.

    Output round-trips through `parse_frontmatter` (modulo nested mappings if
    the stdlib path is used without pyyaml).
    """
    lines = ["---"]

    # Emit canonical keys first
    for key in _CANONICAL_KEYS:
        if key in metadata:
            lines.extend(_emit_field(key, metadata[key]))

    # Then any remaining keys in alphabetical order
    extra_keys = sorted(k for k in metadata if k not in _CANONICAL_KEYS)
    for key in extra_keys:
        lines.extend(_emit_field(key, metadata[key]))

    lines.append("---")
    return "\n".join(lines) + "\n"


def _emit_field(key: str, value: Any) -> list[str]:
    """Emit a single key:value (or key + block-list) as a list of lines."""
    if value is None:
        return [f"{key}: null"]
    if isinstance(value, bool):
        return [f"{key}: {'true' if value else 'false'}"]
    if isinstance(value, int):
        return [f"{key}: {value}"]
    if isinstance(value, list):
        if not value:
            return [f"{key}: []"]
        out = [f"{key}:"]
        for item in value:
            out.append(f"  - {_emit_scalar(item)}")
        return out
    if isinstance(value, dict):
        # Nested mapping — emit inline JSON-style for v8 audit field
        # (pyyaml-enhanced path will parse it back; stdlib path silently drops)
        return [f"{key}: {json.dumps(value)}"]
    # Default: string as a double-quoted scalar. json.dumps produces a valid
    # YAML 1.2 flow scalar with proper escaping (embedded " → \", backslashes,
    # newlines, etc.) — JSON string syntax is a subset of YAML 1.2's
    # double-quoted style. A naive f'"{value}"' would emit invalid YAML for
    # any value containing a double-quote.
    return [f"{key}: {json.dumps(str(value))}"]


def _emit_scalar(value: Any) -> str:
    """Emit a scalar value for use in a list item."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    # Double-quoted scalar via json.dumps — valid YAML 1.2 with proper quote
    # escaping (see _emit_field for the rationale).
    return json.dumps(str(value))


# Canonical MADR 4 H2 section headings, mapped to their normalized keys.
# Matched case-insensitively (and tolerant of a trailing colon on the heading).
_MADR_H2_SECTIONS: dict[str, str] = {
    "context and problem statement": "context_and_problem_statement",
    "considered options": "considered_options",
    "decision outcome": "decision_outcome",
    "consequences": "consequences",
    "rejected alternatives": "rejected_alternatives",
}

# H3 sub-sections inside ``Decision Outcome`` that we surface as their own
# top-level keys (the H3 content STAYS inside its parent H2 body too).
_MADR_H3_SUBSECTIONS: dict[str, str] = {
    "confirmation": "confirmation",
}


_HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")


def parse_madr_4_body(text: str) -> dict[str, str]:
    """Extract MADR 4 sections from the markdown body of an ADR.

    Skips a leading YAML frontmatter block (``---``/``---``). Then scans
    H2 (``## ``) headings; the body of each recognised H2 section is the
    text between that heading and the next H2 heading (any intervening H3
    sub-sections are part of the parent H2 body). The recognised H2
    sections are:

    - ``Context and Problem Statement`` → ``context_and_problem_statement``
    - ``Considered Options`` → ``considered_options``
    - ``Decision Outcome`` → ``decision_outcome``
    - ``Consequences`` → ``consequences``
    - ``Rejected alternatives`` → ``rejected_alternatives``

    H3 sub-headings (``### …``) and any unrecognised H2 headings stay
    as content of the current parent H2 section — so ``### Remix`` and
    ``### Astro`` inside ``Rejected alternatives`` are part of that
    section's body.

    The H3 sub-section ``### Confirmation`` (nested under ``Decision
    Outcome``) is ALSO returned as its own key ``confirmation`` — but
    its content stays inside ``decision_outcome`` too (MADR 4 treats it
    as a sub-section of the parent H2).

    Missing sections are omitted from the returned dict (no empty
    entries). Heading matching is case-insensitive and tolerates a
    trailing colon (``Context and Problem Statement:`` is recognised).

    Returns ``{}`` for empty input or a body with no recognised sections.
    """
    if not text:
        return {}

    # Skip the YAML frontmatter block if present.
    body = _strip_frontmatter(text)

    # Pass 1: collect each recognised H2 section's body. H3 sub-headings
    # within an H2 stay as content of the parent H2.
    result: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        match = _HEADING_RE.match(line)
        if match is not None and len(match.group(1)) == 2:
            heading_text = match.group(2).strip().rstrip(":").strip()
            normalised = heading_text.lower()
            section_key = _MADR_H2_SECTIONS.get(normalised)
            if section_key is not None:
                # Boundary: flush previous section, start new.
                if current_key is not None:
                    result[current_key] = "\n".join(current_lines).strip()
                current_key = section_key
                current_lines = []
                continue
            # Unrecognised H2 → fall through and treat the heading line
            # as content of the current section.
        # Any non-heading line, or an H3, or an unrecognised H2 → content.
        if current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        result[current_key] = "\n".join(current_lines).strip()

    # Pass 2: pull out the Confirmation sub-section from Decision Outcome.
    # We scan the SAME body (not the captured decision_outcome) so that
    # the parsing is independent of pass 1's flushing behaviour.
    confirmation_body = _extract_h3_subsection(body, "confirmation")
    if confirmation_body is not None:
        result[_MADR_H3_SUBSECTIONS["confirmation"]] = confirmation_body

    return result


def _strip_frontmatter(text: str) -> str:
    """Return ``text`` with any leading ``---``/``---`` frontmatter removed."""
    stripped = text.lstrip("﻿")
    if not stripped.startswith(_FRONTMATTER_OPEN):
        return text
    remainder = stripped[len(_FRONTMATTER_OPEN):]
    closing = re.search(r"^---\s*$", remainder, re.MULTILINE)
    if closing is None:
        return text
    # Skip past the closing delimiter (and any following newline).
    cut = closing.end()
    if cut < len(remainder) and remainder[cut] == "\n":
        cut += 1
    return remainder[cut:]


def _extract_h3_subsection(body: str, heading_lower: str) -> str | None:
    """Return the body of an ``### <heading>`` H3 sub-section, or None.

    The sub-section body runs from the H3 heading until the next H2 OR
    H3 heading (whichever comes first). Matching is case-insensitive and
    tolerates a trailing colon on the heading.
    """
    in_section = False
    captured: list[str] = []
    for line in body.splitlines():
        match = _HEADING_RE.match(line)
        if match is not None:
            heading_text = match.group(2).strip().rstrip(":").strip().lower()
            if in_section:
                # Any subsequent H2 or H3 closes the sub-section.
                return "\n".join(captured).strip()
            if len(match.group(1)) == 3 and heading_text == heading_lower:
                in_section = True
            continue
        if in_section:
            captured.append(line)

    if in_section:
        return "\n".join(captured).strip()
    return None
