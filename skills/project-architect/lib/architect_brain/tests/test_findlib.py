"""Tests for the shared _findlib.py project-tree walker."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks._findlib import walk_files


def _touch(root: Path, rels: list[str]) -> None:
    for rel in rels:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")


class TestFindlib(unittest.TestCase):

    def test_suffix_filter_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, ["b.sh", "a.sh", "keep.py", "nested/c.sh"])
            got = [p.relative_to(root).as_posix() for p in walk_files(root, suffixes={".sh"})]
            self.assertEqual(got, ["a.sh", "b.sh", "nested/c.sh"])

    def test_name_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, ["CLAUDE.md", "src/CLAUDE.md", "README.md"])
            got = sorted(p.relative_to(root).as_posix() for p in walk_files(root, names={"CLAUDE.md"}))
            self.assertEqual(got, ["CLAUDE.md", "src/CLAUDE.md"])

    def test_skips_vendor_and_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, [
                "real.sh",
                "node_modules/dep.sh",
                "tests/fixtures/sample.sh",
                ".git/hook.sh",
            ])
            got = [p.name for p in walk_files(root, suffixes={".sh"})]
            self.assertEqual(got, ["real.sh"])

    def test_max_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, ["top.md", "one/mid.md", "one/two/deep.md"])
            got = sorted(p.relative_to(root).as_posix()
                         for p in walk_files(root, suffixes={".md"}, max_depth=2))
            self.assertEqual(got, ["one/mid.md", "top.md"])

    def test_depth2_claude_md_only(self):
        # check_06's pattern: subfolder CLAUDE.md at depth exactly 2.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, ["CLAUDE.md", "src/CLAUDE.md", "a/b/CLAUDE.md"])
            depth2 = [p.relative_to(root).as_posix()
                      for p in walk_files(root, names={"CLAUDE.md"}, max_depth=2)
                      if len(p.relative_to(root).parts) == 2]
            self.assertEqual(depth2, ["src/CLAUDE.md"])

    def test_no_filter_returns_all_nonvendor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, ["a.txt", "node_modules/x.txt"])
            got = [p.name for p in walk_files(root)]
            self.assertEqual(got, ["a.txt"])

    def test_missing_root_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(walk_files(Path(tmp) / "nope"), [])


if __name__ == "__main__":
    unittest.main()
