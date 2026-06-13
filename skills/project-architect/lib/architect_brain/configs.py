"""Deterministic config-as-code generators.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Each ``gen_*`` function takes a flat-index projection (``{"decisions": {...}}``)
and returns a config file's full text. Every generator is DETERMINISTIC: the
same flat-index produces byte-identical output (sort_keys + fixed templates),
so re-running scaffolding never churns the tree. Wave 4 builds these out
(package.json, tsconfig, biome, pyproject, Dockerfile, docker-compose, turbo);
the ``generate-configs`` CLI (Task 4.8) emits all applicable ones.

Version pins (v8.0.1, hardened v9.1): dependency/runtime versions are read from
``stack.versions.<package>`` decisions via ``_pin`` when present — so the
manifests track the versions research-scout resolved as newest-stable — and
fall back to the plugin-baked ``FLOORS`` otherwise. FLOORS are refreshed to the
newest stable release at every plugin release (release-workflow step; see
``bin/floor-check``), and audit check 36 (``version_pins_recorded``) flags any
generated artifact whose token has no recorded pin, so a floor fallback is
never silent. Pin-token applicability is computed by the SAME predicates the
``generate-configs`` CLI uses (``js_stack`` / ``dockerfile_language`` /
``applicable_pin_tokens``) — obligation and emission cannot diverge.
"""

from __future__ import annotations

import json
import re
from typing import Any

# Plugin-baked fallback versions, used ONLY when no ``stack.versions.<token>``
# decision is recorded. Policy: newest stable (Active-LTS for node) at the
# plugin's release date — REFRESH AT EVERY RELEASE (run ``bin/floor-check``).
# Last refreshed: 2026-06-13.
FLOORS: dict[str, str] = {
    "next": "^16.0.0",
    "react": "^19.0.0",
    "node": "24",
    "python": "3.14",
    "postgres": "18",
    "redis": "8",
    "biome": "2.5.0",
    "typescript": "^6.0.0",
}


def _dec(flat_index: dict[str, Any], key: str, default: Any = None) -> Any:
    """Read a decision value from the flat index by dotted key."""
    if not isinstance(flat_index, dict):
        return default
    return flat_index.get("decisions", {}).get(key, default)


def _pin(flat_index: dict[str, Any], package: str) -> str:
    """Resolve a dependency/runtime version: a researched state pin, else FLOORS.

    Prefers a ``stack.versions.<package>`` decision recorded in state (what
    research-scout § 1a resolves as newest-stable and the orchestrator records),
    so generated manifests track current versions WITHOUT a plugin release. The
    ``FLOORS`` constant is only a fallback; check 36 flags artifacts generated
    from it. Still deterministic: same state in, same text out.
    """
    val = _dec(flat_index, f"stack.versions.{package}")
    return val if isinstance(val, str) and val else FLOORS[package]


def _bare_version(pin: str) -> str:
    """Strip a range operator prefix (``^``/``~``/``>=``/…) off a pin."""
    return pin.lstrip("^~><=v ")


def _major(pin: str) -> str | None:
    """The leading major-version integer of a pin, or None if unparseable."""
    m = re.match(r"(\d+)", _bare_version(pin))
    return m.group(1) if m else None


def _stack_languages(flat_index: dict[str, Any]) -> set[Any]:
    return {
        _dec(flat_index, "stack.frontend.language"),
        _dec(flat_index, "stack.backend.language"),
    }


def js_stack(flat_index: dict[str, Any]) -> bool:
    """Whether the stack gets a JS/TS toolchain (package.json/biome/tsconfig).

    The ONE predicate shared by the ``generate-configs`` emission, the pin
    obligation (check 36), and the agents' prose — keep them from diverging.
    """
    langs = _stack_languages(flat_index)
    return (
        _dec(flat_index, "stack.frontend.framework") is not None
        or "typescript" in langs
        or "javascript" in langs
    )


def dockerfile_language(flat_index: dict[str, Any]) -> str | None:
    """Which runtime the generated Dockerfile is based on, or None for none.

    The backend language wins (it is the deploy artifact); a JS/TS front end
    implies node. Languages we have no honest template for (rust, go, …) and
    stacks with no language decided yield None — the v9.1 fix for the old
    behaviour of silently defaulting every project to a node Dockerfile.
    """
    backend = _dec(flat_index, "stack.backend.language")
    if backend == "python":
        return "python"
    if backend in ("typescript", "javascript"):
        return "node"
    if backend is None and js_stack(flat_index):
        return "node"
    return None


def applicable_pin_tokens(flat_index: dict[str, Any]) -> dict[str, str]:
    """Map every ``stack.versions.<token>`` the generators would consume for
    this stack to the artifact filename that consumes it.

    Mirrors the generators exactly; check 36 uses this to flag artifacts that
    shipped on a floor fallback.
    """
    tokens: dict[str, str] = {}
    if js_stack(flat_index):
        tokens["biome"] = "biome.json"
        tokens["typescript"] = "package.json"
        tokens["node"] = "package.json"
        if _dec(flat_index, "stack.frontend.framework") == "next.js":
            tokens["next"] = "package.json"
            tokens["react"] = "package.json"
    lang = dockerfile_language(flat_index)
    if lang == "python":
        tokens["python"] = "Dockerfile"
    elif lang == "node":
        tokens["node"] = "Dockerfile"
    if "python" in _stack_languages(flat_index):
        tokens.setdefault("python", "pyproject.toml")
    if _dec(flat_index, "stack.database.engine") in ("postgres", "postgresql"):
        tokens["postgres"] = "docker-compose.yml"
    if _dec(flat_index, "stack.cache.engine") == "redis":
        tokens["redis"] = "docker-compose.yml"
    return tokens


def _json(obj: Any) -> str:
    """Serialise to deterministic JSON text (sorted keys, 2-space, trailing newline)."""
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def gen_package_json(flat_index: dict[str, Any]) -> str:
    """Emit package.json for the project's JS/TS stack (deterministic).

    Every tool the scripts invoke (tsc, biome) is declared as a pinned
    devDependency — never assumed global (the v9.1 fix for scripts that
    referenced an undeclared toolchain).
    """
    name = _dec(flat_index, "project.name") or "app"
    framework = _dec(flat_index, "stack.frontend.framework")
    pkg: dict[str, Any] = {
        "name": name,
        "version": "0.1.0",
        "private": True,
        "type": "module",
    }
    node_major = _major(_pin(flat_index, "node")) or FLOORS["node"]
    dev: dict[str, str] = {
        "@biomejs/biome": _pin(flat_index, "biome"),  # exact pin (Biome convention)
        "typescript": _pin(flat_index, "typescript"),
        "@types/node": f"^{node_major}.0.0",
    }
    if framework == "next.js":
        pkg["scripts"] = {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "biome check .",
        }
        react = _pin(flat_index, "react")  # react + react-dom move in lockstep
        pkg["dependencies"] = {
            "next": _pin(flat_index, "next"),
            "react": react,
            "react-dom": react,
        }
        dev["@types/react"] = react
        dev["@types/react-dom"] = react
    else:
        pkg["scripts"] = {
            "build": "tsc -p tsconfig.json",
            "test": "node --test",
            "lint": "biome check .",
        }
        pkg["dependencies"] = {}
    pkg["devDependencies"] = dev
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
    """Emit biome.json with the recommended ruleset + formatter (deterministic).

    The config SHAPE tracks the pinned major: Biome 2.0 moved import organizing
    from the top-level ``organizeImports`` key to ``assist.actions.source``
    (emitting the 1.x shape against a 2.x binary is a hard config error — the
    v9.1 fix; previously the 1.x shape was emitted unconditionally). The linter
    block stays on ``rules.recommended: true``, which every 1.x AND 2.x accepts
    — the newer ``rules.preset`` alias is 2.5-only (live-validated: a 2.4.15
    binary rejects ``preset`` as an unknown key).
    """
    pin = _pin(flat_index, "biome")
    schema_version = _bare_version(pin)
    major = _major(pin)
    legacy_1x = major is not None and int(major) < 2
    cfg: dict[str, Any] = {
        "$schema": f"https://biomejs.dev/schemas/{schema_version}/schema.json",
        "formatter": {
            "enabled": True,
            "indentStyle": "space",
            "indentWidth": 2,
            "lineWidth": 100,
        },
        "linter": {"enabled": True, "rules": {"recommended": True}},
    }
    if legacy_1x:
        cfg["organizeImports"] = {"enabled": True}
    else:
        cfg["assist"] = {"actions": {"source": {"organizeImports": "on"}}}
    return _json(cfg)


def gen_pyproject(flat_index: dict[str, Any]) -> str:
    """Emit pyproject.toml for a Python project (deterministic TOML text).

    Hand-built TOML string (no tomllib dependency — the repo targets 3.10+).
    """
    name = _dec(flat_index, "project.name") or "app"
    # requires-python floor + ruff target track the researched python pin
    # (stack.versions.python), so pyproject agrees with the Dockerfile instead of
    # frozen 3.11. ``py`` is major.minor (e.g. "3.13"); ruff wants "py313".
    py = _pin(flat_index, "python")
    # ruff target-version is pyMAJORMINOR (no dots, major.minor only) — tolerate a
    # pin that carries a patch component (e.g. "3.13.1" -> "py313").
    ruff_target = "py" + "".join(py.split(".")[:2])
    return (
        "[project]\n"
        f'name = "{name}"\n'
        'version = "0.1.0"\n'
        f'requires-python = ">={py}"\n'
        "dependencies = []\n"
        "\n"
        "[tool.ruff]\n"
        "line-length = 100\n"
        f'target-version = "{ruff_target}"\n'
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
    Raises ``ValueError`` for stacks ``dockerfile_language`` can't honestly
    base — the caller (``generate-configs``) skips emission instead of the old
    silent default to a node image.
    """
    language = dockerfile_language(flat_index)
    if language is None:
        raise ValueError(
            "no Dockerfile template for this stack "
            "(dockerfile_language() returned None)"
        )
    distroless = bool(_dec(flat_index, "constraints.supply_chain_security"))
    if language == "python":
        py_tag = _pin(flat_index, "python")
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
    node_tag = _pin(flat_index, "node")
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
            f"    image: postgres:{_pin(flat_index, 'postgres')}-alpine",
            "    environment:",
            "      POSTGRES_PASSWORD: postgres",
            "    ports:",
            '      - "5432:5432"',
        ]
    if cache == "redis":
        depends.append("cache")
        extra += [
            "  cache:",
            f"    image: redis:{_pin(flat_index, 'redis')}-alpine",
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
