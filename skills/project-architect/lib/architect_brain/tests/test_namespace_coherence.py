"""Integration: a Golden Path's decisions must flow end-to-end.

This pins the cross-component coherence that the Wave-4 e2e smoke found broken:
golden-paths use the canonical ``stack.*`` decision-key namespace, so the
catalog conditions + config/diagram generators MUST read the same keys. With
the real ``modern_saas_2026`` path applied, the web-app + database documents
must be selected and the database-driven artifacts must materialise.
"""

import unittest
from pathlib import Path

from architect_brain.catalog import filter_applicable, load_catalog
from architect_brain.configs import gen_docker_compose
from architect_brain.diagrams import gen_c4_container
from architect_brain.golden_paths import decisions_for, load_golden_paths

# parents[0]=tests/, [1]=architect_brain/, [2]=lib/, [3]=project-architect/
_REF = Path(__file__).resolve().parents[3] / "references"


class TestNamespaceCoherence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(_REF / "catalog.json")
        cls.gp = load_golden_paths(_REF / "golden-paths.json")
        decisions = decisions_for("modern_saas_2026", cls.gp)
        cls.flat = {"schema_version": "4.0", "decisions": decisions, "adrs": []}

    def test_golden_path_selects_frontend_and_database_docs(self):
        applicable = filter_applicable(self.catalog, self.flat)
        self.assertIn("UI_UX_DESIGN", applicable)      # gated on stack.frontend.framework
        self.assertIn("DATABASE_DESIGN", applicable)   # gated on stack.database.engine

    def test_golden_path_selects_deployment_and_auth_docs(self):
        applicable = filter_applicable(self.catalog, self.flat)
        self.assertIn("DEPLOYMENT", applicable)             # stack.hosting.provider
        self.assertIn("AUTHENTICATION_SYSTEM", applicable)  # stack.auth.provider (compound)

    def test_golden_path_drives_docker_compose_db(self):
        out = gen_docker_compose(self.flat)
        self.assertIn("db:", out)         # stack.database.engine = postgresql → db service

    def test_golden_path_drives_c4_database(self):
        out = gen_c4_container(self.flat)
        self.assertIn("postgresql", out)  # stack.database.engine value rendered


if __name__ == "__main__":
    unittest.main()
