# Testing Strategy

## Pyramid

| Layer | Tool | Target coverage | Speed |
|-------|------|-----------------|-------|
| Unit | pytest / vitest | 80% | ms |
| Integration | pytest (compose/throwaway containers) | critical paths | s |
| E2E | Cypress (`e2e/`) | per user flow incl. edge cases | min |
| Visual regression | Cypress screenshots | key surfaces | min |
| Load | k6 / locust | critical endpoints | per release |

## TDD Workflow

1. RED — write failing test.
2. GREEN — minimal code to pass.
3. REFACTOR.

## Coverage Gates

- PR fails if coverage drops > 1%.
- Backend: min 90% lines, enforced in CI (`coverage report --fail-under=90`).

## Test Data

- No prod data in tests.
- Reset DB per test class.

## Flaky Tests

- Quarantine, file issue, fix in 1 sprint.

## Environments

- Local: docker compose
- CI: ephemeral
- Staging: prod-like
