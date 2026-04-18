# Testing Strategy

## Pyramid

| Layer | Tool | Target coverage | Speed |
|-------|------|-----------------|-------|
| Unit | pytest / vitest | 80% | ms |
| Integration | pytest + testcontainers | critical paths | s |
| E2E | Playwright | golden paths | min |
| Visual regression | Playwright screenshots | key surfaces | min |
| Load | k6 / locust | critical endpoints | per release |

## TDD Workflow

1. RED — write failing test.
2. GREEN — minimal code to pass.
3. REFACTOR.

## Coverage Gates

- PR fails if coverage drops > 1%.
- Min 80% lines, 70% branches.

## Test Data

- Factories (factory_boy / fishery).
- No prod data in tests.
- Reset DB per test class.

## Flaky Tests

- Quarantine, file issue, fix in 1 sprint.

## Environments

- Local: docker compose
- CI: ephemeral
- Staging: prod-like
