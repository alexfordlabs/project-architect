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


class TestPlaybookCoherence(unittest.TestCase):
    """The revision-playbook is consumed by the decision-revisor agent, so no
    deterministic check guarded it — it silently drifted from the canonical
    decision-key namespace (tiger-panther: 73/89 recorded keys uncovered, and
    pre-rename spellings like ``monitoring.*`` / ``analytics.product`` lingered).
    These pin the two coherences a future edit must not break.
    """

    # UPPER_SNAKE refs in the affected-docs map that are NOT catalog documents
    # but ARE legitimate: the root/per-folder CLAUDE.md, the project README /
    # LICENSE, a pre-existing brand doc, and the prose word "ALL" ("ALL docs").
    _NON_CATALOG_DOCS = {
        "CLAUDE_MD_ROOT", "CLAUDE", "README", "LICENSE",
        "BRAND_AND_DESIGN_TOKENS", "ALL",
    }

    @staticmethod
    def _playbook() -> str:
        # Read at run time (not import time) so the playbook + catalog are read
        # together in one pass — an interleaved on-disk edit can't snapshot them
        # inconsistently.
        return (_REF / "revision-playbook.md").read_text(encoding="utf-8")

    @classmethod
    def _catalog_doc_names(cls) -> set:
        import json
        cat = json.loads((_REF / "catalog.json").read_text(encoding="utf-8"))
        return set(cat["documents"].keys())

    def _affected_docs_section(self) -> str:
        # Scope to the "Decision → affected docs map" — NOT the sibling "Affected
        # code areas" table (whose cells are code paths, not doc names).
        playbook = self._playbook()
        start = playbook.index("## Decision")
        end = playbook.index("## Affected code areas")
        return playbook[start:end]

    def test_every_playbook_affected_doc_is_a_real_catalog_document(self):
        # Each affected-docs cell names only docs the catalog can actually
        # generate — a renamed/typo'd doc ref would send decision-revisor to a
        # file that does not exist.
        import re
        catalog = self._catalog_doc_names() | self._NON_CATALOG_DOCS
        unknown = set()
        for line in self._affected_docs_section().splitlines():
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) != 2:
                continue  # not a 2-column map row
            key, docs = cells
            if key in ("decision_key", "Decision", "") or set(key) <= {"-"}:
                continue  # header / separator
            # Strip *(…)* annotations and `code` spans so only doc tokens remain.
            docs = re.sub(r"\*\([^)]*\)\*", "", docs)
            docs = re.sub(r"`[^`]*`", "", docs)
            for tok in re.findall(r"[A-Z][A-Z0-9_]{2,}", docs):
                if tok not in catalog:
                    unknown.add(tok)
        self.assertEqual(unknown, set(), f"playbook references non-catalog docs: {sorted(unknown)}")

    def test_canonical_keys_are_registered(self):
        # The keys the playbook was reconciled TO must exist in the canonical
        # registry — so the rename targeted real keys, not new drift.
        registry = (_REF / "decision-keys.md").read_text(encoding="utf-8")
        for key in (
            "observability.platform", "observability.stack", "testing.framework",
            "testing.strategy", "analytics.provider", "security.secrets_management",
            "stack.hosting.provider", "architecture.style", "stack.game.engine",
        ):
            self.assertIn(key, registry, f"{key} missing from decision-keys.md")
            self.assertIn(key, self._playbook(), f"{key} missing from revision-playbook.md")

    def test_pre_rename_spellings_are_gone_from_playbook(self):
        # Regression guard: the legacy drifted spellings must not reappear as
        # left-column keys in the affected-docs map.
        legacy = (
            "monitoring.error_tracking", "monitoring.apm", "monitoring.logging",
            "analytics.product", "testing.unit_framework", "security.secret_management",
            "project.subtype",
        )
        keys = set()
        for line in self._playbook().splitlines():
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) == 2:
                keys.add(cells[0].strip("`"))
        for stale in legacy:
            self.assertNotIn(stale, keys, f"legacy key {stale} still a playbook map row")


if __name__ == "__main__":
    unittest.main()
