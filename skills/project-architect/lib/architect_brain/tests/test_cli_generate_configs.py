"""Tests for `architect-brain generate-configs`."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


def _setup(tmp: str, decisions: dict) -> tuple[Path, Path]:
    docs_dir = Path(tmp) / "docs"
    state_dir = docs_dir / "_architect_state"
    state_dir.mkdir(parents=True)
    (state_dir / "99-flat-index.json").write_text(
        json.dumps({"schema_version": "4.0", "decisions": decisions, "adrs": []}),
        encoding="utf-8",
    )
    out_dir = Path(tmp) / "out"
    out_dir.mkdir()
    return docs_dir, out_dir


class TestGenerateConfigsCLI(unittest.TestCase):

    def test_node_ts_postgres_monorepo_writes_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir, out_dir = _setup(tmp, {
                "stack.frontend.framework": "next.js",
                "stack.frontend.language": "typescript",
                "stack.database.engine": "postgres",
                "tooling.monorepo": True,
            })
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["generate-configs", "--docs-dir", str(docs_dir), "--out", str(out_dir)])
            self.assertEqual(code, 0)
            for fname in ["package.json", "biome.json", "tsconfig.json",
                          "Dockerfile", "docker-compose.yml", "turbo.json"]:
                self.assertTrue((out_dir / fname).exists(), f"missing {fname}")

    def test_python_writes_pyproject_not_package_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir, out_dir = _setup(tmp, {"stack.backend.language": "python"})
            with redirect_stdout(io.StringIO()):
                main(["generate-configs", "--docs-dir", str(docs_dir), "--out", str(out_dir)])
            self.assertTrue((out_dir / "pyproject.toml").exists())
            self.assertTrue((out_dir / "Dockerfile").exists())
            self.assertFalse((out_dir / "package.json").exists())

    def test_prints_written_filenames(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir, out_dir = _setup(tmp, {})
            buf = io.StringIO()
            with redirect_stdout(buf):
                main(["generate-configs", "--docs-dir", str(docs_dir), "--out", str(out_dir)])
            self.assertIn("Dockerfile", buf.getvalue())

    def test_minimal_state_writes_only_dockerfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_dir, out_dir = _setup(tmp, {})
            with redirect_stdout(io.StringIO()):
                main(["generate-configs", "--docs-dir", str(docs_dir), "--out", str(out_dir)])
            self.assertEqual([p.name for p in out_dir.iterdir()], ["Dockerfile"])


if __name__ == "__main__":
    unittest.main()
