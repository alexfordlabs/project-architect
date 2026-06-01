"""Tests for the `architect-brain audit` subcommand (Wave 5e — the auditor CLI).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from architect_brain.__main__ import main


def _run_audit(docs: Path, *extra: str) -> tuple[int, str, str]:
    """Run `audit` with the given extra args; return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["audit", "--docs-dir", str(docs), *extra])
    return code, out.getvalue(), err.getvalue()


class TestCLIAudit(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state(self) -> Path:
        return self.docs / "_architect_state"

    # --- exit codes + verdict ------------------------------------------------

    def test_only_passing_check_exits_zero(self):
        # check_05 (json_valid) passes on a fresh init.
        code, out, _ = _run_audit(self.docs, "--only", "05")
        self.assertEqual(code, 0)
        self.assertIn("05", out)
        self.assertIn("CLEAN", out)

    def test_full_run_blocks_on_missing_required_docs(self):
        # Fresh init has no design docs, so check_27 (required_docs_generated,
        # BLOCKING) fails → the full audit blocks LOCK.
        code, out, _ = _run_audit(self.docs)
        self.assertEqual(code, 1)
        self.assertIn("BLOCKED", out)

    def test_ack_downgrades_blocking(self):
        # The only blocker on fresh init is BLOCKING-tier (check_27), so --ack
        # downgrades it and the run no longer blocks.
        code, _, _ = _run_audit(self.docs, "--ack", "docs come later")
        self.assertEqual(code, 0)

    def test_ack_does_not_downgrade_fatal(self):
        # Corrupt a projection so check_29 (state_schema_valid, FATAL) fails;
        # --ack must NOT downgrade a FATAL failure.
        stack = self._state() / "stack.json"
        data = json.loads(stack.read_text())
        del data["concern"]  # 'concern' is a required schema field
        stack.write_text(json.dumps(data))
        code, _, _ = _run_audit(self.docs, "--ack", "nice try")
        self.assertEqual(code, 1)

    # --- --only filtering ----------------------------------------------------

    def test_only_filters_to_one_check(self):
        code, out, _ = _run_audit(self.docs, "--only", "05")
        # Exactly one check line is printed (one ✓/✗ glyph).
        glyph_lines = [ln for ln in out.splitlines() if ln.strip().startswith(("✓", "✗"))]
        self.assertEqual(len(glyph_lines), 1)
        self.assertIn("json_valid", glyph_lines[0])
        self.assertEqual(code, 0)

    def test_verbose_prints_findings(self):
        # A full --verbose run prints the failing check's findings (check_27).
        _, out, _ = _run_audit(self.docs, "--verbose")
        self.assertTrue(any(ln.strip().startswith("- ") for ln in out.splitlines()),
                        msg="expected an indented finding line under --verbose")

    # --- AuditCompleted event recording -------------------------------------

    def test_full_run_records_audit_event(self):
        _run_audit(self.docs)
        workflow = json.loads((self._state() / "workflow.json").read_text())
        self.assertEqual(len(workflow.get("audits", [])), 1)
        audit = workflow["audits"][0]
        self.assertEqual(audit["result"], "blocked")  # fresh init blocks on check_27
        self.assertEqual(audit["checks_failed"], 1)
        self.assertEqual(audit["checks_passed"], 34)  # 35 checks; check_27 fails, rest pass
        self.assertIn("ts", audit)

    def test_only_run_does_not_record_event(self):
        _run_audit(self.docs, "--only", "05")
        workflow = json.loads((self._state() / "workflow.json").read_text())
        self.assertEqual(workflow.get("audits", []), [])

    # --- --ack provenance (v8.0.1) ------------------------------------------
    # An acked-clean must be distinguishable from a genuinely-clean audit, and
    # the override reason — the accountability record — must survive in the ledger.

    def test_ack_reason_recorded_in_audit_event(self):
        _run_audit(self.docs, "--ack", "docs come later")
        workflow = json.loads((self._state() / "workflow.json").read_text())
        audit = workflow["audits"][-1]
        self.assertEqual(audit["result"], "clean")  # ack downgraded check_27
        self.assertEqual(audit["ack"], "docs come later")

    def test_ack_reason_in_emitted_event_payload(self):
        _run_audit(self.docs, "--ack", "waiving known gap")
        lines = (self._state() / "events.jsonl").read_text().strip().splitlines()
        audit_events = [json.loads(ln) for ln in lines if json.loads(ln)["type"] == "AuditCompleted"]
        self.assertEqual(audit_events[-1]["payload"]["ack"], "waiving known gap")

    def test_unacked_run_has_no_ack_key(self):
        _run_audit(self.docs)
        workflow = json.loads((self._state() / "workflow.json").read_text())
        self.assertNotIn("ack", workflow["audits"][-1])

    # --- worst_severity provenance (v8.0.1) ---------------------------------
    # Disambiguates two same-count audits: "N failed / clean" (all WARNING/INFO)
    # vs "N failed / blocked" (a BLOCKING/FATAL among them).

    def test_worst_severity_recorded_in_audit_event(self):
        _run_audit(self.docs)  # fresh init: check_27 (BLOCKING) fails
        workflow = json.loads((self._state() / "workflow.json").read_text())
        self.assertEqual(workflow["audits"][-1]["worst_severity"], "BLOCKING")

    def test_worst_severity_present_even_when_acked_clean(self):
        # Acked → result clean, but the worst FAILED severity is still BLOCKING:
        # together with `ack`, the ledger explains why a "clean" run had failures.
        _run_audit(self.docs, "--ack", "docs later")
        audit = json.loads((self._state() / "workflow.json").read_text())["audits"][-1]
        self.assertEqual(audit["result"], "clean")
        self.assertEqual(audit["worst_severity"], "BLOCKING")

    def test_audit_emit_preserves_resume_invariant(self):
        # After a full audit records its event, replay must still equal on-disk
        # projections (check_31's invariant) — i.e. the emit went through the
        # consistent append+project path.
        _run_audit(self.docs)
        code, _, _ = _run_audit(self.docs, "--only", "31")
        self.assertEqual(code, 0)

    # --- regression: incremental emit preserves the ADR ledger --------------
    # Pins the _read_projections_from_disk fix (it now restores _decisions_index
    # from disk). Before the fix, a second record-adr dropped the first ADR from
    # decisions/index.json, which check_30 (decisions_index_fresh) would flag.

    def test_incremental_emit_preserves_decisions_index(self):
        main(["record-adr", "--docs-dir", str(self.docs), "0001", "First", "Accepted"])
        main(["record-adr", "--docs-dir", str(self.docs), "0002", "Second", "Accepted"])
        index = json.loads((self._state() / "decisions" / "index.json").read_text())
        self.assertEqual([a["id"] for a in index["adrs"]], ["0001", "0002"])
        # And check_30 agrees the on-disk index matches replay.
        code, _, _ = _run_audit(self.docs, "--only", "30")
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
