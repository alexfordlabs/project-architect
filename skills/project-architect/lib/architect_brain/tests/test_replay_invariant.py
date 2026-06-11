"""Property-based test for the replay invariant.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Invariant: replay(events) == fold(apply_event, events, empty_projections()).

This is the central correctness property of v8's state layer. The live-system
incremental-update path (apply_event mutating projections as events are
appended) must produce byte-identical projections to the "replay from scratch"
path (replay reading events.jsonl into empty projections).

Wave 5's check_31_resume_test will assert this invariant at every audit run,
so the live system fails loudly if the invariant ever drifts.

This file is hypothesis-gated — it skips gracefully when hypothesis is not
installed (an optional dependency for enhanced development). To run with
hypothesis enabled:
    pip install --user hypothesis
"""

import tempfile
import unittest
from pathlib import Path

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
    HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover - exercised only when dep missing
    HAS_HYPOTHESIS = False

    # Fallback no-op decorators so the @given(...)/@settings(...) lines below
    # remain syntactically valid at class-definition time even without
    # hypothesis installed. The @unittest.skipUnless decorator on the class
    # ensures the body never actually runs.
    def given(*_args, **_kwargs):  # type: ignore[no-redef]
        def _decorator(fn):
            return fn
        return _decorator

    def settings(*_args, **_kwargs):  # type: ignore[no-redef]
        def _decorator(fn):
            return fn
        return _decorator

    class _StFallback:
        @staticmethod
        def none():
            return None

    st = _StFallback()  # type: ignore[assignment]

from architect_brain.events import EventEnvelope, append_event
from architect_brain.projections import (
    CONCERN_NAMES,
    apply_event,
    empty_projections,
    replay,
)
from architect_brain.ulid import new_ulid


def _decision_events_strategy():
    """Hypothesis strategy: list of (key, value) pairs for DecisionMade events.

    Keys are sampled from a fixed set covering multiple concerns to ensure the
    routing table is exercised. Values are bool/int/str to verify projection
    handles heterogeneous types.
    """
    if not HAS_HYPOTHESIS:
        return None
    keys = st.sampled_from([
        "stack.frontend.framework",
        "stack.backend.language",
        "stack.database.engine",
        "architecture.style",
        "ai.enabled",
        "ai.agent",
        "api.public",
        "webhooks.outbound",
        "cost.budget",
        "identity.project_name",
        "vision.mission",
        "deployment.target",
    ])
    values = st.one_of(
        st.text(min_size=1, max_size=20),
        st.booleans(),
        st.integers(min_value=-1000, max_value=1000),
    )
    return st.lists(
        st.tuples(keys, values),
        min_size=0,
        max_size=30,
    )


@unittest.skipUnless(HAS_HYPOTHESIS, "hypothesis not installed; skipping property test")
class TestReplayInvariant(unittest.TestCase):

    @given(_decision_events_strategy() if HAS_HYPOTHESIS else st.none())
    @settings(max_examples=50, deadline=None)
    def test_replay_equals_incremental_fold(self, kv_pairs):
        """For any sequence of DecisionMade events, replay equals fold.

        Hypothesis generates up to 30 random (key, value) pairs and asserts the
        invariant holds for the full projection set.
        """
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "events.jsonl"
            incremental = empty_projections()
            for key, value in kv_pairs:
                event = EventEnvelope(
                    id=new_ulid(),
                    ts="2026-05-27T15:23:11Z",
                    by="orchestrator",
                    phase="stack",
                    type="DecisionMade",
                    payload={"key": key, "value": value},
                )
                append_event(log_path, event)
                apply_event(event, incremental)

            replayed = replay(log_path)

            # Compare every concern projection — they must be byte-identical
            # in semantic content (concern routing + decisions + flat-index).
            for concern_name in CONCERN_NAMES:
                self.assertEqual(
                    replayed[concern_name],
                    incremental[concern_name],
                    f"Replay drift in concern {concern_name!r}",
                )
            # Also verify the flat-index projection.
            self.assertEqual(
                replayed["_flat_index"],
                incremental["_flat_index"],
                "Replay drift in flat-index projection",
            )


if __name__ == "__main__":
    unittest.main()
