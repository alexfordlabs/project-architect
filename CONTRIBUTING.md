<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
-->

# Contributing to project-architect

Thank you for considering a contribution! This project is open source under the [Apache License 2.0](LICENSE).

## How to contribute

1. **Open an issue first** for substantial changes. Quick bugfixes or doc tweaks can go straight to a PR.
2. **Fork**, branch from `main`, make your change.
3. **Bump the version** in `.claude-plugin/plugin.json` (semver: patch for fixes, minor for additive features, major for breaking changes).
4. **Update CHANGELOG.md** with a new `[X.Y.Z]` entry.
5. **Add author attribution** to any new file (HTML comment block — see existing files for the pattern).
6. **Run `claude plugin validate`** before opening the PR.
7. **Open the PR** using the [PR template](.github/pull_request_template.md).

## Code style

- The orchestration surface is **Markdown** (the skill, agents, templates, references); the deterministic engine is a **Python package** (`skills/project-architect/lib/architect_brain/`) with a **bash test harness** (`tests/`).
- **TDD is required.** Every change to a check, template, agent, or `SKILL.md` ships with a test. Run `bash tests/run_all.sh` (the bash harness + the `architect_brain` Python suite) — it must end with `All tests passed.` and `Test files failed: 0`.
- `shellcheck` clean on `bin/architect-brain` + `tests/*.sh`; `python3 -m py_compile` clean on the brain package.
- YAML frontmatter on all skill / agent / template files.
- Templates end with a Revision Log section and a "Skillfully made with…" footer.
- Author attribution at the top of every source file.

## Local development

The plugin is distributed from the shared **`alexfordlabs`** marketplace (the [`alexfordlabs/skills`](https://github.com/alexfordlabs/skills) repo). To install your in-progress changes locally:

```bash
claude plugin marketplace update alexfordlabs
claude plugin uninstall project-architect@alexfordlabs
claude plugin install project-architect@alexfordlabs
/reload-plugins
```

Run the test suite before opening a PR:

```bash
bash tests/run_all.sh
```

## Reporting bugs

Use the [bug report issue template](.github/ISSUE_TEMPLATE/bug_report.yml). Include the plugin version, Claude Code version, and reproduction steps.

## Suggesting features

Use the [feature request issue template](.github/ISSUE_TEMPLATE/feature_request.yml) or open a [Discussion](https://github.com/alexfordlabs/project-architect/discussions) for open-ended ideas.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
