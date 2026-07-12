# ADR-0004 — Cypress for E2E testing (migrate from Playwright)

- **Date:** 2026-07-12
- **Status:** accepted
- **Deciders:** Kairus (RSPH), per #30 decision

## Context

Constitution §3.1/§3.4 default E2E to Cypress in `e2e/`, per user flow including edge cases. The template inherited a Playwright suite (62 tests in `frontend/tests/`, 4-way sharded in CI). Deciding factors for aligning to Cypress: a matured, higher-ownership E2E infrastructure over a larger low-ownership test surface; the E2E suite is client-facing (demos/UAT evidence), where Cypress's interactive runner presents better; built-in component testing gives headroom for future client requests without new tooling.

Trade-offs were surfaced explicitly before deciding (§1 "no silent decisions"):

- **Parallelization:** Cypress gates parallel runs behind Cypress Cloud (paid); OSS alternatives (sorry-cypress/Currents) mean self-hosted services (§1 tension). Accepted: CI runs the suite serially (or split by spec-file batching) until a client engagement justifies Cloud.
- **Browser engines:** Cypress has no production WebKit/Safari coverage. Accepted; revisit if a client requires Safari E2E.

## Decision

Adopt **Cypress** as the E2E framework, located at `e2e/` per §3.1. The existing Playwright suite keeps CI green until the migration lands; Playwright is removed in the same change that brings Cypress coverage to parity (per user flow including edge cases, §3.4). Migration is tracked as its own ticket.

## Constitution clause deviated from

None — this aligns the template with the §3.1/§3.4 default. (The interim state, Playwright until migration completes, is the transitional deviation this ADR authorizes.)

## Client sign-off

Internal template (RSPH-owned, §7.3) — founder decision on issue #30, 2026-07-12.

## Consequences

**Positive:**
- Constitution-aligned default; no standing ADR debt for E2E.
- Client-facing interactive runner; built-in component testing available on request.

**Negative:**
- Serial CI runs until a paid/hosted parallelization path is justified — longer E2E wall-clock than today's 4 shards.
- No WebKit/Safari engine coverage.
- One-time migration cost for 62 existing tests + CI workflow + the Playwright compose service/Dockerfile.

**Follow-ups:**
- Migration ticket with §3.4 coverage AC (see issue linked from #30).
