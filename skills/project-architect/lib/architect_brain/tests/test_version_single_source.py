"""Single-source-of-truth guard for the plugin version.

``architect_brain.__version__`` MUST equal the version declared in
``.claude-plugin/plugin.json``. This pins the drift that motivated the fix: the
brain hardcoded ``"8.0.0"`` while ``plugin.json`` had moved to ``8.1.0``, and
``migration.py`` stamped that stale literal into migrated user docs' frontmatter
(a silent stale-provenance bug on every migration). Resolving the version from
the manifest makes a future bump propagate everywhere automatically.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import unittest
from pathlib import Path

import architect_brain


def _find_plugin_manifest() -> Path:
    """Walk up from this test file to the repo's .claude-plugin/plugin.json."""
    for parent in Path(__file__).resolve().parents:
        manifest = parent / ".claude-plugin" / "plugin.json"
        if manifest.is_file():
            return manifest
    raise AssertionError(".claude-plugin/plugin.json not found above the test file")


class TestVersionSingleSource(unittest.TestCase):
    def test_brain_version_matches_plugin_manifest(self):
        manifest = _find_plugin_manifest()
        declared = json.loads(manifest.read_text())["version"]
        self.assertEqual(
            architect_brain.__version__,
            declared,
            "architect_brain.__version__ must equal .claude-plugin/plugin.json "
            f"version ({declared!r}) — single source of truth, no hardcoded drift",
        )

    def test_version_is_semverish(self):
        self.assertRegex(architect_brain.__version__, r"^\d+\.\d+\.\d+")

    def test_version_is_resolved_dynamically(self):
        # Guard against a future contributor re-hardcoding `__version__ = "x.y.z"`
        # and staying green: the resolver must actually read the manifest.
        import inspect

        src = inspect.getsource(architect_brain._resolve_version)
        self.assertIn("plugin.json", src)


if __name__ == "__main__":
    unittest.main()
