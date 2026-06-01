"""Tests for the shared markdown-collector helper used by doc-scanning checks."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks._docscan import collect_markdown


def _make(tmp: str, files) -> Path:
    docs = Path(tmp) / "docs"
    for rel in files:
        p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
    docs.mkdir(parents=True, exist_ok=True)
    return docs


class TestDocscan(unittest.TestCase):

    def test_collects_toplevel_and_nested_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _make(tmp, ["b.md", "design/a.md", "design/z.md"])
            got = [p.relative_to(docs).as_posix() for p in collect_markdown(docs)]
            self.assertEqual(got, ["b.md", "design/a.md", "design/z.md"])

    def test_ignores_non_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _make(tmp, ["keep.md", "x.json", "y.txt"])
            got = [p.name for p in collect_markdown(docs)]
            self.assertEqual(got, ["keep.md"])

    def test_skips_vendor_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _make(tmp, ["keep.md", "node_modules/dep.md", "build/out.md"])
            got = [p.name for p in collect_markdown(docs)]
            self.assertEqual(got, ["keep.md"])

    def test_skips_architect_state_subtree(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _make(tmp, ["keep.md", "_architect_state/notes.md"])
            got = [p.name for p in collect_markdown(docs)]
            self.assertEqual(got, ["keep.md"])

    def test_extra_skip_dirs_excludes_versions_and_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _make(tmp, ["keep.md", "versions/v1/old.md", "research/note.md"])
            got = [p.name for p in collect_markdown(docs, extra_skip_dirs={"versions", "research"})]
            self.assertEqual(got, ["keep.md"])

    def test_default_does_not_skip_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _make(tmp, ["keep.md", "versions/v1/old.md"])
            got = sorted(p.name for p in collect_markdown(docs))
            self.assertEqual(got, ["keep.md", "old.md"])

    def test_missing_docs_root_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(collect_markdown(Path(tmp) / "nope"), [])

    def test_no_markdown_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = _make(tmp, ["only.json"])
            self.assertEqual(collect_markdown(docs), [])


if __name__ == "__main__":
    unittest.main()
