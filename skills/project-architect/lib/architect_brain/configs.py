"""Deterministic config-as-code generators.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Each ``gen_*`` function takes a flat-index projection (``{"decisions": {...}}``)
and returns a config file's full text. Every generator is DETERMINISTIC: the
same flat-index produces byte-identical output (sort_keys + fixed templates),
so re-running scaffolding never churns the tree. Wave 4 builds these out
(package.json, tsconfig, biome, pyproject, Dockerfile, docker-compose, turbo);
the ``generate-configs`` CLI (Task 4.8) emits all applicable ones.

Version pins (v8.0.1): dependency/runtime versions are read from
``stack.versions.<package>`` decisions via ``_pin`` when present — so the
manifests track the versions research-scout resolved as newest-stable — and
fall back to a conservative plugin-baked floor otherwise. The floor goes stale
on the plugin's release cadence; recording the researched pin keeps generated
configs fresh without a plugin release.
"""

from __future__ import annotations

import json
from typing import Any


def _dec(flat_index: dict[str, Any], key: str, default: Any = None) -> Any:
    """Read a decision value from the flat index by dotted key."""
    if not isinstance(flat_index, dict):
        return default
    return flat_index.get("decisions", {}).get(key, default)


def _pin(flat_index: dict[str, Any], package: str, floor: str) -> str:
    """Resolve a dependency/runtime version: a researched state pin, else a floor.

    Prefers a ``stack.versions.<package>`` decision recorded in state (what
    research-scout § 1a resolves as newest-stable and the orchestrator records),
    so generated manifests track current versions WITHOUT a plugin release. The
    ``floor`` is a conservative constant baked into the plugin — it is only a
    fallback and goes stale on the plugin's own release cadence, so a real run
    should record the researched pin. Still deterministic: same state in, same
    text out.
    """
    val = _dec(flat_index, f"stack.versions.{package}")
    return val if isinstance(val, str) and val else floor


def _json(obj: Any) -> str:
    """Serialise to deterministic JSON text (sorted keys, 2-space, trailing newline)."""
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def gen_package_json(flat_index: dict[str, Any]) -> str:
    """Emit package.json for the project's JS/TS stack (deterministic)."""
    name = _dec(flat_index, "project.name") or "app"
    framework = _dec(flat_index, "stack.frontend.framework")
    pkg: dict[str, Any] = {
        "name": name,
        "version": "0.1.0",
        "private": True,
        "type": "module",
    }
    if framework == "next.js":
        pkg["scripts"] = {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "biome check .",
        }
        react = _pin(flat_index, "react", "^19.0.0")  # react + react-dom move in lockstep
        pkg["dependencies"] = {
            "next": _pin(flat_index, "next", "^15.0.0"),
            "react": react,
            "react-dom": react,
        }
    else:
        pkg["scripts"] = {
            "build": "tsc -p tsconfig.json",
            "test": "node --test",
            "lint": "biome check .",
        }
        pkg["dependencies"] = {}
    return _json(pkg)


def gen_tsconfig(flat_index: dict[str, Any]) -> str:
    """Emit a strict, modern tsconfig.json (deterministic; stack-independent base)."""
    return _json({
        "compilerOptions": {
            "target": "ES2022",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "strict": True,
            "noUncheckedIndexedAccess": True,
            "noImplicitOverride": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "verbatimModuleSyntax": True,
            "lib": ["ES2022", "DOM", "DOM.Iterable"],
            "outDir": "dist",
            "rootDir": "src",
        },
        "include": ["src"],
        "exclude": ["node_modules", "dist"],
    })


def gen_biome_json(flat_index: dict[str, Any]) -> str:
    """Emit biome.json with the recommended ruleset + formatter (deterministic)."""
    return _json({
        "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
        "organizeImports": {"enabled": True},
        "linter": {"enabled": True, "rules": {"recommended": True}},
        "formatter": {
            "enabled": True,
            "indentStyle": "space",
            "indentWidth": 2,
            "lineWidth": 100,
        },
    })


def gen_pyproject(flat_index: dict[str, Any]) -> str:
    """Emit pyproject.toml for a Python project (deterministic TOML text).

    Hand-built TOML string (no tomllib dependency — the repo targets 3.10+).
    """
    name = _dec(flat_index, "project.name") or "app"
    return (
        "[project]\n"
        f'name = "{name}"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        "dependencies = []\n"
        "\n"
        "[tool.ruff]\n"
        "line-length = 100\n"
        'target-version = "py311"\n'
        "\n"
        "[tool.ruff.lint]\n"
        'select = ["E", "F", "I", "UP", "B"]\n'
        "\n"
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
    )


def gen_dockerfile(flat_index: dict[str, Any]) -> str:
    """Emit a multi-stage Dockerfile (deterministic).

    Distroless runtime base when ``constraints.supply_chain_security`` is set.
    """
    language = (
        _dec(flat_index, "stack.backend.language")
        or _dec(flat_index, "stack.frontend.language")
        or "node"
    )
    distroless = bool(_dec(flat_index, "constraints.supply_chain_security"))
    if language == "python":
        py_tag = _pin(flat_index, "python", "3.11")
        runtime = "gcr.io/distroless/python3-debian12" if distroless else f"python:{py_tag}-slim"
        return (
            "# syntax=docker/dockerfile:1\n"
            f"FROM python:{py_tag}-slim AS build\n"
            "WORKDIR /app\n"
            "COPY . .\n"
            "RUN pip install --no-cache-dir .\n"
            "\n"
            f"FROM {runtime}\n"
            "WORKDIR /app\n"
            "COPY --from=build /app /app\n"
            'CMD ["python", "-m", "app"]\n'
        )
    node_tag = _pin(flat_index, "node", "22")
    runtime = f"gcr.io/distroless/nodejs{node_tag}-debian12" if distroless else f"node:{node_tag}-slim"
    return (
        "# syntax=docker/dockerfile:1\n"
        f"FROM node:{node_tag}-slim AS build\n"
        "WORKDIR /app\n"
        "COPY package*.json ./\n"
        "RUN npm ci\n"
        "COPY . .\n"
        "RUN npm run build\n"
        "\n"
        f"FROM {runtime}\n"
        "WORKDIR /app\n"
        "COPY --from=build /app /app\n"
        'CMD ["node", "dist/index.js"]\n'
    )


def gen_docker_compose(flat_index: dict[str, Any]) -> str:
    """Emit docker-compose.yml (deterministic).

    Always an ``app`` service; adds ``db`` (postgres) and ``cache`` (redis)
    services + ``depends_on`` when those engines are selected.
    """
    db = _dec(flat_index, "stack.database.engine")
    cache = _dec(flat_index, "stack.cache.engine")
    app = ["services:", "  app:", "    build: .", "    ports:", '      - "3000:3000"']
    depends: list[str] = []
    extra: list[str] = []
    if db in ("postgres", "postgresql"):
        depends.append("db")
        extra += [
            "  db:",
            "    image: postgres:17-alpine",
            "    environment:",
            "      POSTGRES_PASSWORD: postgres",
            "    ports:",
            '      - "5432:5432"',
        ]
    if cache == "redis":
        depends.append("cache")
        extra += [
            "  cache:",
            "    image: redis:7-alpine",
            "    ports:",
            '      - "6379:6379"',
        ]
    if depends:
        app.append("    depends_on:")
        app += [f"      - {name}" for name in depends]
    return "\n".join(app + extra) + "\n"


def gen_turbo_json(flat_index: dict[str, Any]) -> str:
    """Emit turbo.json for a monorepo (Turbo 2.x `tasks` schema; deterministic)."""
    return _json({
        "$schema": "https://turbo.build/schema.json",
        "tasks": {
            "build": {"dependsOn": ["^build"], "outputs": ["dist/**", ".next/**"]},
            "lint": {},
            "test": {"dependsOn": ["build"]},
            "dev": {"cache": False, "persistent": True},
        },
    })
