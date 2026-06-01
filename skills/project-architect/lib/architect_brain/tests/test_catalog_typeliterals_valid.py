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

_TYPE_LITERAL_RE = re.compile(r"project\.type\s*[=!]=\s*'([^']+)'")


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
            for lit in _TYPE_LITERAL_RE.findall(cond):
                if lit not in TOP_LEVEL_TYPES:
                    orphans.setdefault(lit, []).append(name)
        self.assertEqual(
            orphans,
            {},
            "catalog.json references project.type literals that are not in "
            f"TOP_LEVEL_TYPES (these docs can never fire): {orphans}",
        )


if __name__ == "__main__":
    unittest.main()
