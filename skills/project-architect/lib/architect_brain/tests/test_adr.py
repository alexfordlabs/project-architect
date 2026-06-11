"""Tests for architect_brain.adr — MADR 4 + structured-MADR frontmatter parsing.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import unittest

from architect_brain.adr import parse_frontmatter


class TestParseFrontmatter(unittest.TestCase):

    def test_empty_text_returns_empty_dict(self):
        self.assertEqual(parse_frontmatter(""), {})

    def test_no_frontmatter_returns_empty_dict(self):
        text = "# Title\n\nNo frontmatter here.\n"
        self.assertEqual(parse_frontmatter(text), {})

    def test_simple_string_values(self):
        text = """---
title: Use Next.js 15
status: Accepted
---

# Body
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["title"], "Use Next.js 15")
        self.assertEqual(result["status"], "Accepted")

    def test_quoted_string_values(self):
        """Quoted strings have their quotes stripped."""
        text = """---
title: "Use Next.js 15"
status: "Accepted"
---
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["title"], "Use Next.js 15")
        self.assertEqual(result["status"], "Accepted")

    def test_int_value_parsed(self):
        text = """---
schema_version: 4
priority: 2
---
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["schema_version"], 4)
        self.assertEqual(result["priority"], 2)

    def test_quoted_int_stays_string(self):
        """Quoted ints are strings (e.g., version "4.0")."""
        text = """---
schema_version: "4.0"
---
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["schema_version"], "4.0")

    def test_bool_values(self):
        text = """---
deprecated: true
draft: false
---
"""
        result = parse_frontmatter(text)
        self.assertIs(result["deprecated"], True)
        self.assertIs(result["draft"], False)

    def test_null_value(self):
        text = """---
superseded_by: null
---
"""
        result = parse_frontmatter(text)
        self.assertIsNone(result["superseded_by"])

    def test_empty_list_inline(self):
        text = """---
supersedes: []
---
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["supersedes"], [])

    def test_block_list_with_dash_items(self):
        text = """---
tags:
  - stack
  - frontend
  - architecture
---
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["tags"], ["stack", "frontend", "architecture"])

    def test_block_list_with_quoted_dash_items(self):
        text = """---
decision_makers:
  - "Alexander Ford"
  - "Other Person"
---
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["decision_makers"], ["Alexander Ford", "Other Person"])

    def test_full_structured_madr_frontmatter(self):
        """End-to-end test against the v8 structured-MADR shape from the spec."""
        text = """---
type: adr
schema_version: "4.0"
id: "0007"
title: "Use Next.js 15 over Remix"
status: "Accepted"
date: "2026-05-27"
decision_makers:
  - "Alexander Ford"
tags:
  - "stack"
  - "frontend"
phase: "stack"
plugin_version: "8.0.0"
supersedes: []
superseded_by: []
related:
  - "0003"
risk: "low"
---

# ADR Body
"""
        result = parse_frontmatter(text)
        self.assertEqual(result["type"], "adr")
        self.assertEqual(result["schema_version"], "4.0")
        self.assertEqual(result["id"], "0007")
        self.assertEqual(result["title"], "Use Next.js 15 over Remix")
        self.assertEqual(result["status"], "Accepted")
        self.assertEqual(result["date"], "2026-05-27")
        self.assertEqual(result["decision_makers"], ["Alexander Ford"])
        self.assertEqual(result["tags"], ["stack", "frontend"])
        self.assertEqual(result["phase"], "stack")
        self.assertEqual(result["plugin_version"], "8.0.0")
        self.assertEqual(result["supersedes"], [])
        self.assertEqual(result["superseded_by"], [])
        self.assertEqual(result["related"], ["0003"])
        self.assertEqual(result["risk"], "low")

    def test_no_closing_delimiter_returns_empty_dict(self):
        """Malformed frontmatter (no closing ---) returns empty dict."""
        text = """---
title: Use Next.js 15
status: Accepted
"""
        # No closing --- — partial frontmatter is treated as no frontmatter
        result = parse_frontmatter(text)
        self.assertEqual(result, {})

    def test_handles_trailing_whitespace_in_values(self):
        # Build the text programmatically so trailing whitespace on the value
        # line survives editor save-time strip-trailing-whitespace settings.
        text = "---\n" + "title: Use Next.js 15   \n" + "---\n"
        result = parse_frontmatter(text)
        self.assertEqual(result["title"], "Use Next.js 15")


from architect_brain.adr import emit_frontmatter


class TestEmitFrontmatter(unittest.TestCase):

    def test_emit_empty_dict_produces_minimal_frontmatter(self):
        result = emit_frontmatter({})
        self.assertTrue(result.startswith("---\n"))
        self.assertTrue(result.endswith("---\n"))

    def test_emit_simple_string_value(self):
        result = emit_frontmatter({"title": "Use Next.js 15"})
        self.assertIn('title: "Use Next.js 15"', result)

    def test_emit_canonical_key_order(self):
        """v8 spec key order: type, schema_version, id, title, status, date, ..."""
        metadata = {
            "audit": {"required_review_at": None},
            "id": "0007",
            "type": "adr",
            "title": "Test",
            "schema_version": "4.0",
        }
        result = emit_frontmatter(metadata)
        # Find positions of each key in the output
        pos_type = result.index("type:")
        pos_schema = result.index("schema_version:")
        pos_id = result.index("id:")
        pos_title = result.index("title:")
        pos_audit = result.index("audit:")
        # Order: type < schema_version < id < title < audit
        self.assertLess(pos_type, pos_schema)
        self.assertLess(pos_schema, pos_id)
        self.assertLess(pos_id, pos_title)
        self.assertLess(pos_title, pos_audit)

    def test_emit_full_canonical_key_sequence(self):
        """All canonical keys present in metadata emit in exact spec order."""
        import re
        from architect_brain.adr import _CANONICAL_KEYS
        metadata = {k: ("adr" if k == "type" else "4.0" if k == "schema_version"
                        else [] if k in ("supersedes", "superseded_by", "related", "tags", "decision_makers")
                        else {} if k == "audit" else "x")
                    for k in _CANONICAL_KEYS}
        result = emit_frontmatter(metadata)
        emitted_keys = re.findall(r"^([a-z_]+):", result, re.MULTILINE)
        canonical_present = [k for k in _CANONICAL_KEYS if k in metadata]
        self.assertEqual(emitted_keys, canonical_present)

    def test_emit_int_value_unquoted(self):
        result = emit_frontmatter({"priority": 5})
        self.assertIn("priority: 5", result)
        # Should not be quoted
        self.assertNotIn('priority: "5"', result)

    def test_emit_bool_value(self):
        result = emit_frontmatter({"deprecated": True, "draft": False})
        self.assertIn("deprecated: true", result)
        self.assertIn("draft: false", result)

    def test_emit_null_value(self):
        result = emit_frontmatter({"superseded_by": None})
        self.assertIn("superseded_by: null", result)

    def test_emit_empty_list_inline(self):
        result = emit_frontmatter({"supersedes": []})
        self.assertIn("supersedes: []", result)

    def test_emit_list_of_strings_as_block(self):
        result = emit_frontmatter({"tags": ["stack", "frontend"]})
        self.assertIn("tags:", result)
        self.assertIn('  - "stack"', result)
        self.assertIn('  - "frontend"', result)

    def test_emit_unknown_keys_alphabetical_after_canonical(self):
        """Keys not in the canonical list go AFTER canonical keys, alphabetically."""
        metadata = {
            "title": "Test",
            "zebra": "z",
            "alpha": "a",
        }
        result = emit_frontmatter(metadata)
        pos_title = result.index("title:")
        pos_alpha = result.index("alpha:")
        pos_zebra = result.index("zebra:")
        self.assertLess(pos_title, pos_alpha)
        self.assertLess(pos_alpha, pos_zebra)

    def test_emit_full_structured_madr_round_trips_via_parse(self):
        """emit then parse → equivalent dict (modulo ordering)."""
        original = {
            "type": "adr",
            "schema_version": "4.0",
            "id": "0007",
            "title": "Use Next.js 15",
            "status": "Accepted",
            "date": "2026-05-27",
            "decision_makers": ["Alexander Ford"],
            "tags": ["stack", "frontend"],
            "phase": "stack",
            "plugin_version": "8.0.0",
            "supersedes": [],
            "superseded_by": [],
            "related": ["0003"],
            "risk": "low",
        }
        emitted = emit_frontmatter(original)
        # Round-trip through parse_frontmatter (which the prior test class exercised)
        from architect_brain.adr import parse_frontmatter
        reparsed = parse_frontmatter(emitted + "\n# body\n")
        self.assertEqual(reparsed, original)

    def test_emit_is_deterministic(self):
        """Same input → byte-identical output."""
        metadata = {"id": "0007", "title": "Test", "supersedes": ["0001", "0002"]}
        a = emit_frontmatter(metadata)
        b = emit_frontmatter(metadata)
        self.assertEqual(a, b)

    def test_emit_escapes_embedded_quotes(self):
        """Strings with embedded double-quotes must emit valid, parseable YAML."""
        result = emit_frontmatter({"title": 'He said "hi" loudly'})
        # Round-trip must recover the original
        from architect_brain.adr import parse_frontmatter
        reparsed = parse_frontmatter(result + "\n# body")
        self.assertEqual(reparsed["title"], 'He said "hi" loudly')

    def test_emit_escapes_quotes_in_list_items(self):
        result = emit_frontmatter({"tags": ['has "quote"', "plain"]})
        from architect_brain.adr import parse_frontmatter
        reparsed = parse_frontmatter(result + "\n# body")
        self.assertEqual(reparsed["tags"], ['has "quote"', "plain"])

    def test_emit_with_embedded_quotes_is_strictly_valid_yaml(self):
        """The emitted frontmatter must parse under a STRICT YAML parser.

        This is the genuine regression guard for the quote-escaping defect:
        ``parse_frontmatter`` has a defensive stdlib fallback that masks
        malformed pyyaml output, so a round-trip through it can succeed even
        on invalid YAML. Parsing the emitted block with ``yaml.safe_load``
        directly (no fallback) fails loudly on the unescaped ``"`` and
        succeeds once the values are JSON-escaped.

        Skipped when pyyaml is not installed (the strict path is unavailable).
        """
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:  # pragma: no cover - exercised only when pyyaml absent
            self.skipTest("pyyaml not installed; strict-YAML guard not applicable")

        metadata = {
            "title": 'He said "hi" loudly',
            "tags": ['has "quote"', "plain"],
            "decision_makers": ['O\'Brien said "go"'],
        }
        result = emit_frontmatter(metadata)
        # Strip the ``---`` delimiter lines to obtain the bare YAML mapping,
        # then parse it with pyyaml directly (no stdlib fallback).
        body = result[len("---\n"):]
        body = body[: body.rindex("---")]
        parsed = yaml.safe_load(body)
        self.assertEqual(parsed["title"], 'He said "hi" loudly')
        self.assertEqual(parsed["tags"], ['has "quote"', "plain"])
        self.assertEqual(parsed["decision_makers"], ['O\'Brien said "go"'])


from architect_brain.adr import parse_madr_4_body


class TestParseMadr4Body(unittest.TestCase):

    SAMPLE_MADR = """---
type: adr
id: "0007"
title: "Use Next.js 15"
status: "Accepted"
---

# ADR-0007: Use Next.js 15

## Context and Problem Statement

We need a React framework. Should we use Next.js or Remix?

The team prefers SSR and ISR for SEO.

## Considered Options

- **Next.js 15** — App Router + RSC + Vercel hosting
- **Remix** — Web Standards focus, but smaller community
- **Astro** — Content-first, weaker for SaaS

## Decision Outcome

Chosen: **Next.js 15** — biggest community, best Vercel integration.

### Confirmation

We'll know this decision is working if:
- Lighthouse scores stay above 90
- Build times stay under 2 minutes

## Consequences

- ✅ Vercel deployment is trivial
- ⚠️ Tied to Vercel's roadmap for some features

## Rejected alternatives

### Remix

Remix's Web Standards approach is elegant but the community is 10× smaller.

### Astro

Astro is content-first; we need full SaaS app capabilities.
"""

    def test_extracts_context_section(self):
        result = parse_madr_4_body(self.SAMPLE_MADR)
        self.assertIn("context_and_problem_statement", result)
        self.assertIn("React framework", result["context_and_problem_statement"])
        self.assertIn("SSR and ISR", result["context_and_problem_statement"])

    def test_extracts_considered_options(self):
        result = parse_madr_4_body(self.SAMPLE_MADR)
        self.assertIn("considered_options", result)
        self.assertIn("Next.js 15", result["considered_options"])
        self.assertIn("Remix", result["considered_options"])
        self.assertIn("Astro", result["considered_options"])

    def test_extracts_decision_outcome(self):
        result = parse_madr_4_body(self.SAMPLE_MADR)
        self.assertIn("decision_outcome", result)
        self.assertIn("Next.js 15", result["decision_outcome"])

    def test_extracts_confirmation_subsection(self):
        result = parse_madr_4_body(self.SAMPLE_MADR)
        self.assertIn("confirmation", result)
        self.assertIn("Lighthouse", result["confirmation"])

    def test_extracts_consequences(self):
        result = parse_madr_4_body(self.SAMPLE_MADR)
        self.assertIn("consequences", result)
        self.assertIn("Vercel deployment", result["consequences"])

    def test_extracts_rejected_alternatives(self):
        result = parse_madr_4_body(self.SAMPLE_MADR)
        self.assertIn("rejected_alternatives", result)
        self.assertIn("Remix", result["rejected_alternatives"])

    def test_skips_frontmatter(self):
        """Frontmatter should not appear in any section."""
        result = parse_madr_4_body(self.SAMPLE_MADR)
        for section_text in result.values():
            self.assertNotIn("schema_version", section_text)
            self.assertNotIn("type: adr", section_text)

    def test_parse_madr_case_insensitive_headings(self):
        text = "## CONTEXT AND PROBLEM STATEMENT\n\nThe context.\n"
        result = parse_madr_4_body(text)
        self.assertIn("context_and_problem_statement", result)

    def test_parse_madr_trailing_colon_heading(self):
        text = "## Context and Problem Statement:\n\nThe context.\n"
        result = parse_madr_4_body(text)
        self.assertIn("context_and_problem_statement", result)

    def test_empty_text_returns_empty_dict(self):
        self.assertEqual(parse_madr_4_body(""), {})

    def test_no_sections_returns_empty_dict(self):
        text = """---
type: adr
---

# Title

Just a body, no sections.
"""
        result = parse_madr_4_body(text)
        self.assertEqual(result, {})

    def test_missing_section_omitted_from_result(self):
        """If a section is absent, the key is omitted (not present with empty value)."""
        text = """---
type: adr
---

## Context and Problem Statement

The context.

## Decision Outcome

The decision.
"""
        result = parse_madr_4_body(text)
        self.assertIn("context_and_problem_statement", result)
        self.assertIn("decision_outcome", result)
        self.assertNotIn("consequences", result)
        self.assertNotIn("rejected_alternatives", result)


if __name__ == "__main__":
    unittest.main()
