<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Contributing to project-architect

Thank you for considering a contribution! This project is open source under the [MIT License](LICENSE).

## How to contribute

1. **Open an issue first** for substantial changes. Quick bugfixes or doc tweaks can go straight to a PR.
2. **Fork**, branch from `main`, make your change.
3. **Bump version** per the [versioning policy](README.md#versioning-policy).
4. **Update CHANGELOG.md** with a new `[X.Y.Z]` entry.
5. **Add author attribution** to any new file (HTML comment block — see existing files for the pattern).
6. **Run `claude plugin validate`** before opening the PR.
7. **Open the PR** using the [PR template](.github/pull_request_template.md).

## Code style

- Markdown only. No code in this repo.
- YAML frontmatter on all skill / agent / template files.
- Every file ends with a Revision Log section (templates only) and a "Skillfully made with…" footer (templates only).
- Author attribution at the top of every text file.

## Local development

This repo is its own marketplace. To install your in-progress changes locally:

```bash
claude plugin marketplace update alexfordlabs
claude plugin uninstall project-architect@alexfordlabs
claude plugin install project-architect@alexfordlabs
/reload-plugins
```

To run the manual test plan, see [`docs/superpowers/test-plans/2026-05-12-v2.0-manual-test-plan.md`](docs/superpowers/test-plans/2026-05-12-v2.0-manual-test-plan.md).

## Reporting bugs

Use the [bug report issue template](.github/ISSUE_TEMPLATE/bug_report.yml). Include the plugin version, Claude Code version, and reproduction steps.

## Suggesting features

Use the [feature request issue template](.github/ISSUE_TEMPLATE/feature_request.yml) or open a [Discussion](https://github.com/alexfordlabs/project-architect/discussions) for open-ended ideas.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
