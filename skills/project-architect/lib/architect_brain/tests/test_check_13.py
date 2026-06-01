"""Tests for the check_13_state_drift auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_13_state_drift
from architect_brain.checks.check_13_state_drift import CHECK_ID, NAME, SEVERITY, run

_HAVE_GIT = shutil.which("git") is not None


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    project_root = state_dir.parent.parent = ``<tmp>``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_events(state_dir: Path, lines: list[str]) -> None:
    (state_dir / "events.jsonl").write_text(
        "".join(line + "\n" for line in lines), encoding="utf-8"
    )


def _event_line(ts: str, *, ulid: str = "01J0000000000000000000000A") -> str:
    """A minimal well-formed PhaseAdvanced event JSONL line with the given ts."""
    return (
        '{"id":"%s","ts":"%s","by":"orchestrator","phase":"vision",'
        '"type":"PhaseAdvanced","payload":{"from":null,"to":"vision"}}'
        % (ulid, ts)
    )


def _git(state_dir: Path, *args: str, env_extra: dict | None = None) -> None:
    proj = state_dir.parent.parent
    env = {
        "GIT_AUTHOR_NAME": "T",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "T",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    if env_extra:
        env.update(env_extra)
    import os

    full_env = {**os.environ, **env}
    subprocess.run(
        ["git", "-C", str(proj), *args],
        check=True,
        capture_output=True,
        env=full_env,
    )


def _git_commit_at(state_dir: Path, epoch: int) -> None:
    """Make a commit whose committer (and author) date is the given unix epoch."""
    proj = state_dir.parent.parent
    (proj / "afile.txt").write_text("x", encoding="utf-8")
    iso = f"{epoch} +0000"
    _git(state_dir, "add", "-A")
    _git(
        state_dir,
        "commit",
        "-m",
        "c",
        env_extra={"GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso},
    )


class TestCheck13Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "13")
        self.assertEqual(NAME, "state_drift")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertEqual(check_13_state_drift.CHECK_ID, "13")
        self.assertTrue(callable(check_13_state_drift.run))


class TestCheck13Degraded(unittest.TestCase):
    def test_not_a_git_repo_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_event_line("2026-05-27T15:23:11Z")])
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "13")
            self.assertEqual(result.findings, ())

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_no_events_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            _git_commit_at(state, 2_000_000_000)
            # No events.jsonl at all.
            result = run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_empty_events_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            _git_commit_at(state, 2_000_000_000)
            _write_events(state, [])
            result = run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_no_commits_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            _write_events(state, [_event_line("2026-05-27T15:23:11Z")])
            # No commit made → git log -1 returns empty.
            result = run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_unparseable_newest_ts_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            _git_commit_at(state, 2_000_000_000)
            bad = (
                '{"id":"01J0000000000000000000000A","ts":"not-a-timestamp",'
                '"by":"orchestrator","phase":"vision","type":"PhaseAdvanced",'
                '"payload":{"from":null,"to":"vision"}}'
            )
            _write_events(state, [bad])
            result = run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_malformed_event_line_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            _git_commit_at(state, 2_000_000_000)
            _write_events(state, ["{not json at all"])
            # Must NOT raise; defers to check_12/json_valid.
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck13Pass(unittest.TestCase):
    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_event_after_head_passes(self):
        # Newest event is more recent than HEAD → delta negative → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            head_epoch = 2_000_000_000
            _git_commit_at(state, head_epoch)
            # event ts 100s AFTER head
            ev_epoch = head_epoch + 100
            from datetime import datetime, timezone

            iso = datetime.fromtimestamp(ev_epoch, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            _write_events(state, [_event_line(iso)])
            result = run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_within_grace_passes(self):
        # Event lags HEAD by exactly the grace window → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            head_epoch = 2_000_000_000
            _git_commit_at(state, head_epoch)
            from datetime import datetime, timezone

            ev_epoch = head_epoch - 60  # delta == 60, not > 60
            iso = datetime.fromtimestamp(ev_epoch, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            _write_events(state, [_event_line(iso)])
            result = run(state)
            self.assertTrue(result.passed)

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_offset_form_ts_passes(self):
        # +00:00 offset form should parse identically to the Z form.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            head_epoch = 2_000_000_000
            _git_commit_at(state, head_epoch)
            ev_iso = "2033-05-18T03:33:20+00:00"  # == 2_000_000_000
            line = _event_line(ev_iso)
            _write_events(state, [line])
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck13Fail(unittest.TestCase):
    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_lags_head_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            head_epoch = 2_000_000_000
            _git_commit_at(state, head_epoch)
            from datetime import datetime, timezone

            ev_epoch = head_epoch - 3600  # 1 hour behind HEAD
            iso = datetime.fromtimestamp(ev_epoch, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            _write_events(state, [_event_line(iso)])
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "13")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("lags HEAD commit by 3600s", result.findings[0].message)

    @unittest.skipUnless(_HAVE_GIT, "git not available")
    def test_newest_of_many_is_used(self):
        # The LAST (newest) event is the one compared, even if an earlier
        # event would be within grace.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _git(state, "init")
            head_epoch = 2_000_000_000
            _git_commit_at(state, head_epoch)
            from datetime import datetime, timezone

            recent_iso = datetime.fromtimestamp(
                head_epoch - 10, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            stale_iso = datetime.fromtimestamp(
                head_epoch - 500, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            # newest (last) line is the STALE one
            _write_events(
                state,
                [
                    _event_line(recent_iso, ulid="01J0000000000000000000000A"),
                    _event_line(stale_iso, ulid="01J0000000000000000000000B"),
                ],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertIn("lags HEAD commit by 500s", result.findings[0].message)


if __name__ == "__main__":
    unittest.main()
