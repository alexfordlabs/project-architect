"""Tests for `architect-brain generate-diagram <type>`."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


def _run(dtype: str):
    with tempfile.TemporaryDirectory() as tmp:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["generate-diagram", dtype, "--docs-dir", str(Path(tmp) / "docs")])
        return code, buf.getvalue()


class TestGenerateDiagramCLI(unittest.TestCase):

    def test_context(self):
        code, out = _run("context")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("C4Context"))

    def test_container(self):
        code, out = _run("container")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("C4Container"))

    def test_component(self):
        code, out = _run("component")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("C4Component"))

    def test_invalid_type_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                main(["generate-diagram", "bogus", "--docs-dir", str(Path(tmp) / "docs")])


if __name__ == "__main__":
    unittest.main()
