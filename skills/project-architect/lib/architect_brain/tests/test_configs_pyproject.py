"""Tests for architect_brain.configs.gen_pyproject."""

import unittest

from architect_brain.configs import gen_pyproject


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenPyproject(unittest.TestCase):

    def test_has_project_table(self):
        self.assertIn("[project]", gen_pyproject(_fi()))

    def test_default_name(self):
        self.assertIn('name = "app"', gen_pyproject(_fi()))

    def test_name_interpolated(self):
        self.assertIn('name = "my-thing"', gen_pyproject(_fi({"project.name": "my-thing"})))

    def test_has_ruff_and_pytest_tables(self):
        out = gen_pyproject(_fi())
        self.assertIn("[tool.ruff]", out)
        self.assertIn("[tool.ruff.lint]", out)
        self.assertIn("[tool.pytest.ini_options]", out)

    def test_requires_python(self):
        self.assertIn('requires-python = ">=3.11"', gen_pyproject(_fi()))

    def test_trailing_newline_and_deterministic(self):
        out = gen_pyproject(_fi())
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(gen_pyproject(_fi()), gen_pyproject(_fi()))

    # ── version-from-state: requires-python + ruff target track stack.versions.python ──
    def test_requires_python_uses_recorded_pin(self):
        out = gen_pyproject(_fi({"stack.versions.python": "3.13"}))
        self.assertIn('requires-python = ">=3.13"', out)

    def test_ruff_target_version_tracks_recorded_python(self):
        out = gen_pyproject(_fi({"stack.versions.python": "3.13"}))
        self.assertIn('target-version = "py313"', out)

    def test_python_version_falls_back_to_floor(self):
        out = gen_pyproject(_fi())
        self.assertIn('requires-python = ">=3.11"', out)
        self.assertIn('target-version = "py311"', out)

    def test_ruff_target_uses_major_minor_only_for_patch_pin(self):
        out = gen_pyproject(_fi({"stack.versions.python": "3.13.1"}))
        self.assertIn('target-version = "py313"', out)  # not py3131


if __name__ == "__main__":
    unittest.main()
