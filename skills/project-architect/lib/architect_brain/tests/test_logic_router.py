"""Tests for architect_brain.logic_router.eval_router."""

import unittest

from architect_brain.logic_router import RouterError, eval_router


_NODE = {
    "id": "skip_stack_if_pre_filled",
    "type": "logic_router",
    "condition": "stack.frontend.framework != null AND stack.backend.language != null",
    "if_true": "phase_4_cost",
    "if_false": "phase_3_stack_frontend",
}


def _fi(decisions):
    return {"schema_version": "4.0", "decisions": decisions, "adrs": []}


class TestEvalRouter(unittest.TestCase):

    def test_true_branch_when_both_keys_present(self):
        fi = _fi({"stack.frontend.framework": "next.js", "stack.backend.language": "typescript"})
        self.assertEqual(eval_router(_NODE, fi), "phase_4_cost")

    def test_false_branch_when_keys_absent(self):
        self.assertEqual(eval_router(_NODE, _fi({})), "phase_3_stack_frontend")

    def test_partial_state_is_false(self):
        # only frontend set → the AND is false → if_false
        fi = _fi({"stack.frontend.framework": "next.js"})
        self.assertEqual(eval_router(_NODE, fi), "phase_3_stack_frontend")

    def test_non_router_type_raises(self):
        # Well-formed EXCEPT for `type` — so only the type check can raise here
        # (a fixture also missing condition/if_true/if_false would be caught by
        # the required-field loop first, leaving the type check untested).
        bad = {"id": "q", "type": "question",
               "condition": "ALWAYS", "if_true": "a", "if_false": "b"}
        with self.assertRaises(RouterError):
            eval_router(bad, _fi({}))

    def test_missing_required_field_raises(self):
        bad = {"id": "r", "type": "logic_router", "condition": "ALWAYS"}  # no if_true/if_false
        with self.assertRaises(RouterError):
            eval_router(bad, _fi({}))

    def test_deterministic(self):
        fi = _fi({"stack.frontend.framework": "next.js", "stack.backend.language": "typescript"})
        self.assertEqual(eval_router(_NODE, fi), eval_router(_NODE, fi))


if __name__ == "__main__":
    unittest.main()
