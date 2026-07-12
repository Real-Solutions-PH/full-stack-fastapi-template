# Contributing

Internal contribution guide for this repository.

## Workflow

1. Branch from `master`.
2. Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.
3. Before pushing, run:
   - `pre-commit run --all-files`
   - `make backend-lint`
   - The relevant test suites (backend and/or frontend).
4. Open a PR against `master`. PRs require CI to be green before merge.

For development environment setup, see the [Development Guide](development.md).

## Dependency update PRs

Dependabot opens weekly grouped PRs per ecosystem: bun (root + `mobile/`), uv, docker (`backend/` + `frontend/`), docker-compose, and github-actions. Maintainers may self-merge these once CI is green — no second review is required (§3.7).

Exceptions that need a human look before merge:

- Any PR failing CI.
- Major-version bumps of core frameworks (`fastapi`, `next`, `react`, `expo`, `react-native`), especially `expo-*` / `react-native-*` bumps — these are version-coupled and there is no mobile CI gate yet (see ticket #26).
