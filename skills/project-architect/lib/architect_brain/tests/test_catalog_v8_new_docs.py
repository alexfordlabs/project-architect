"""Condition-firing tests for the Wave-7a v8 templates.

For each new must-ship template, a triggering decision-set must select it via
filter_applicable, and a greenfield (no decisions) state must NOT — this pins
each template's resolved catalog condition against the conditions DSL.
"""

import unittest
from pathlib import Path

from architect_brain.catalog import filter_applicable, load_catalog

_SKILL_ROOT = Path(__file__).resolve().parents[3]
_CATALOG = _SKILL_ROOT / "references" / "catalog.json"

# doc name -> a decision map that should make it APPLICABLE
_TRIGGERS = {
    "AGENT_DESIGN": {"ai.enabled": True, "ai.agent": True},
    "AGENT_EVALUATION": {"ai.enabled": True, "ai.agent": True},
    "CONTEXT_ENGINEERING": {"ai.enabled": True, "ai.agent": True},
    "AGENT_MEMORY": {"ai.agent": True, "ai.persistent_memory": True},
    "TOOL_PALETTE": {"ai.agent": True},
    "HUMAN_IN_THE_LOOP": {"ai.agent": True, "agent.autonomy": "low"},
    "AI_SAFETY": {"ai.enabled": True, "scale": "growth"},
    "WEBHOOK_DESIGN": {"api.enabled": True, "webhooks.outbound": True},
    "WEB_SECURITY_HEADERS": {"project.type": "web_app"},
    "POSTMORTEM_TEMPLATE": {"production_bound": True, "scale": "growth"},
    # --- Wave 7b consider-tier (conditional) ---
    "EVENT_TRACKING_PLAN": {"analytics.enabled": True},
    "FEATURE_FLAGS": {"feature_flags.enabled": True},
    "IDEMPOTENCY_DESIGN": {"api.enabled": True, "monetization.enabled": True},
    "RATE_LIMITING": {"api.enabled": True, "scale": "growth"},
    "API_VERSIONING": {"api.enabled": True, "api.public": True},
    "API_ERROR_MODEL": {"api.enabled": True},
    "SUPPLY_CHAIN_SECURITY": {"production_bound": True, "scale": "growth"},
    "LLM_OBSERVABILITY": {"ai.enabled": True, "scale": "growth"},
    "ENGINEERING_PRINCIPLES": {"scale": "growth"},
    "CODE_REVIEW": {"team_size": "small_team", "scm.host": "github"},
    "DATA_CONTRACT": {"data_pipeline.enabled": True, "data.contracts": True},
    "KUBERNETES_DEPLOYMENT": {"deployment.orchestrator": "kubernetes"},
    "CONTAINER_IMAGE_POLICY": {"deployment.containers": True},
    "PRIVACY_REVIEW": {"constraints.gdpr": True},
    "ON_CALL_GUIDE": {"production_bound": True, "team_size": "small_team", "scale": "growth"},
    # --- Wave 7c condition-gated ---
    "OPEN_SOURCE_GOVERNANCE": {"open_source": True, "community_size": "large"},
    "CONTRACT_TESTING": {"architecture.style": "microservices"},
    "GIT_BRANCHING": {"team_size": "small_team", "scm.host": "github"},
    "DEVELOPMENT_WORKFLOW": {"team_size": "small_team"},
    "GITOPS_DEPLOYMENT": {"deployment.gitops": True},
    "EDGE_COMPUTE_DESIGN": {"deployment.edge": True},
    "SERVERLESS_DESIGN": {"deployment.style": "serverless"},
    "THREAT_MODEL_LLM": {"ai.enabled": True, "constraints.regulated": True},
    "DOCUMENTATION_STRATEGY": {"open_source": True, "community_size": "medium"},
    "BOUNDED_CONTEXTS": {"project.ddd": True},
    "DOMAIN_EVENTS": {"project.ddd": True},
}

# WELL_ARCHITECTED_CHECKLIST is the one new ALWAYS doc — selected on every state,
# so it is asserted separately (it would (correctly) fail the greenfield-excludes test).
_ALWAYS_DOCS = ["WELL_ARCHITECTED_CHECKLIST"]


class TestV8NewDocConditions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(_CATALOG)

    def _applicable(self, decisions: dict) -> set:
        return set(filter_applicable(self.catalog, {"decisions": decisions}))

    def test_all_new_docs_present_in_catalog(self):
        docs = self.catalog["documents"]
        for name in _TRIGGERS:
            self.assertIn(name, docs, f"{name} not registered in catalog.json")

    def test_each_trigger_selects_its_doc(self):
        for name, decisions in _TRIGGERS.items():
            with self.subTest(doc=name):
                self.assertIn(name, self._applicable(decisions),
                              f"{name} not selected by its trigger {decisions}")

    def test_greenfield_excludes_all_new_docs(self):
        # No decisions → none of these condition-gated docs should be applicable.
        applicable = self._applicable({})
        for name in _TRIGGERS:
            with self.subTest(doc=name):
                self.assertNotIn(name, applicable,
                                 f"{name} wrongly applicable on a greenfield (empty) state")

    def test_always_docs_applicable_on_greenfield(self):
        # ALWAYS-conditioned docs (e.g. WELL_ARCHITECTED_CHECKLIST) are selected
        # regardless of decisions — including the empty greenfield state.
        applicable = self._applicable({})
        for name in _ALWAYS_DOCS:
            with self.subTest(doc=name):
                self.assertIn(name, self.catalog["documents"], f"{name} not in catalog")
                self.assertIn(name, applicable, f"{name} (ALWAYS) not applicable on greenfield")

    def test_agent_docs_excluded_when_not_an_agent(self):
        # ai.enabled but NOT an agent: the agent-only docs must not fire.
        applicable = self._applicable({"ai.enabled": True})
        for name in ("AGENT_EVALUATION", "AGENT_MEMORY", "HUMAN_IN_THE_LOOP"):
            with self.subTest(doc=name):
                self.assertNotIn(name, applicable)


if __name__ == "__main__":
    unittest.main()
