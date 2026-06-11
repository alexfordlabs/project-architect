"""architect_brain — project-architect v8 Python module.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json as _json
from pathlib import Path as _Path


def _resolve_version() -> str:
    """Single source of truth for the plugin version: read .claude-plugin/plugin.json.

    Walk up from this file to the plugin manifest so the brain's ``__version__``
    can never drift from ``plugin.json`` (the published version) — and so a
    release bump propagates everywhere automatically (CLI ``--version``, the ADR
    ``plugin_version`` stamp, the migrator's doc/ADR re-stamp). Falls back to a
    sentinel only if the manifest is genuinely unreadable (an odd packaging
    context); in-repo and in an installed plugin it is always present.
    """
    for _parent in _Path(__file__).resolve().parents:
        _manifest = _parent / ".claude-plugin" / "plugin.json"
        if _manifest.is_file():
            try:
                _v = _json.loads(_manifest.read_text())["version"]
            except (ValueError, KeyError, OSError):
                break
            if isinstance(_v, str) and _v:
                return _v
            break  # manifest present but version missing/null/non-string → sentinel
    return "0.0.0+unknown"


__version__ = _resolve_version()
