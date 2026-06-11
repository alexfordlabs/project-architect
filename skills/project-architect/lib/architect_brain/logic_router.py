"""logic_router question-tree node evaluation (pure flow control).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

A ``logic_router`` node (spec §5.2) carries no user question — it branches the
question tree on a conditions-DSL ``condition`` evaluated against the current
flat-index. ``check_NN_router_decidable`` (Wave 5) asserts every router's
condition evaluates to a known boolean against current state. This reuses the
Wave-3 DSL evaluator (``catalog.eval_condition``) — one DSL, one semantics.
"""

from __future__ import annotations

from typing import Any

from architect_brain.catalog import eval_condition


class RouterError(Exception):
    """A logic_router node was malformed (wrong type or missing required field)."""


_REQUIRED = ("type", "condition", "if_true", "if_false")


def eval_router(node: dict[str, Any], flat_index: dict[str, Any]) -> str:
    """Evaluate a logic_router node → its ``if_true`` or ``if_false`` target.

    Raises RouterError if the node isn't a well-formed logic_router (wrong
    ``type`` or a missing required field).
    """
    for field in _REQUIRED:
        if field not in node:
            raise RouterError(f"logic_router node missing required field: {field!r}")
    if node["type"] != "logic_router":
        raise RouterError(f"not a logic_router node: type={node['type']!r}")
    return node["if_true"] if eval_condition(node["condition"], flat_index) else node["if_false"]
