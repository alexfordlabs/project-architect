"""Tests for the `architect-brain ui` subcommand group."""

import io
import unittest
from contextlib import redirect_stdout

from architect_brain.__main__ import main


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    return code, buf.getvalue()


class TestUICLI(unittest.TestCase):

    def test_ui_banner(self):
        code, out = _run(["ui", "banner"])
        self.assertEqual(code, 0)
        self.assertIn("architect", out)

    def test_ui_phase_bar(self):
        code, out = _run(["ui", "phase-bar", "architecture"])
        self.assertEqual(code, 0)
        self.assertIn("3/11", out)
        self.assertIn("Architecture", out)

    def test_ui_phase_bar_unknown_is_empty(self):
        code, out = _run(["ui", "phase-bar", "bogus"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_ui_progress(self):
        code, out = _run(["ui", "progress", "5", "11", "Doc generation"])
        self.assertEqual(code, 0)
        self.assertIn("5/11", out)
        self.assertIn("Doc generation", out)

    def test_ui_progress_label_optional(self):
        code, out = _run(["ui", "progress", "1", "11"])
        self.assertEqual(code, 0)
        self.assertIn("1/11", out)


if __name__ == "__main__":
    unittest.main()
