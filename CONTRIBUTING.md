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

(convention documented in ticket #32)
