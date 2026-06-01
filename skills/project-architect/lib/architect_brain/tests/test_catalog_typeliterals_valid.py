"""Guard test: every project.type literal used in catalog conditions must be a
real member of the project-type registry (TOP_LEVEL_TYPES).

Regression test for the v8 defect where catalog.json conditions referenced
type literals (``ai_ml``/``desktop``/``embedded``/``mobile`` typos, plus
``web3``/``scientific``/``ar_vr`` which were advertised but never registered).
A doc gated on a literal that matches no registry type can NEVER fire, so those
project archetypes silently received a smaller doc set. This pins the
catalog<->registry contract so a future condition (or a registry rename) that
re-introduces an orphan literal fails CI deterministically ($0).
"""

import json
import re
import unittest
from pathlib import Path

from architect_brain.project_types import TOP_LEVEL_TYPES

# parents[0]=tests/, [1]=architect_brain/, [2]=lib/, [3]=project-architect/
_CATALOG = Path(__file__).resolve().parents[3] / "references" / "catalog.json"

# project.type literals appear two ways in the conditions DSL: equality
# (`project.type == 'x'` / `!= 'x'`) and list-membership (`project.type IN
# ['a', 'b']` / `NOT IN [...]`). Both must be scanned — a typo inside an IN-list
# would otherwise slip past the guard while the doc silently never fires.
_EQ_RE = re.compile(r"project\.type\s*[=!]=\s*'([^']+)'")
_IN_RE = re.compile(r"project\.type\s+(?:NOT\s+)?IN\s*\[([^\]]*)\]", re.IGNORECASE)
_LIST_LITERAL_RE = re.compile(r"'([^']+)'")


def _type_literals(cond):
    """Every project.type literal in a condition string (== / != and IN / NOT IN)."""
    lits = list(_EQ_RE.findall(cond))
    for list_body in _IN_RE.findall(cond):
        lits.extend(_LIST_LITERAL_RE.findall(list_body))
    return lits


def _iter_conditions(documents):
    """Yield (doc_name, condition_string) for every condition in the catalog."""
    for name, doc in documents.items():
        conds = doc.get("conditions", [])
        if isinstance(conds, str):
            conds = [conds]
        for cond in conds:
            yield name, cond if isinstance(cond, str) else json.dumps(cond)


class TestCatalogTypeLiteralsValid(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.documents = json.loads(_CATALOG.read_text(encoding="utf-8"))["documents"]

    def test_every_project_type_literal_is_a_registry_member(self):
        orphans = {}
        for name, cond in _iter_conditions(self.documents):
            for lit in _type_literals(cond):
                if lit not in TOP_LEVEL_TYPES:
                    orphans.setdefault(lit, []).append(name)
        self.assertEqual(
            orphans,
            {},
            "catalog.json references project.type literals that are not in "
            f"TOP_LEVEL_TYPES (these docs can never fire): {orphans}",
        )

    def test_extractor_covers_in_list_membership_form(self):
        # Pins that the guard sees IN-list literals (not just ==/!=), so an orphan
        # typo inside `project.type IN [...]` cannot slip past green.
        lits = _type_literals("x == 1 OR project.type IN ['mcp_server', 'agentic_system']")
        self.assertEqual(set(lits), {"mcp_server", "agentic_system"})
        self.assertEqual(
            _type_literals("project.type NOT IN ['web_app']"), ["web_app"]
        )


if __name__ == "__main__":
    unittest.main()
