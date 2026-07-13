# ADR-0005 — Supabase (Auth + RLS) over self-managed Postgres + custom JWT

- **Date:** 2026-07-12
- **Status:** accepted
- **Deciders:** maintainers

## Context

The template inherited a self-managed Postgres container with a hand-rolled JWT auth stack (password hashing, token issuance, email recovery, FIRST_SUPERUSER bootstrap) and a single-tenant data model. Constitution §4.1 defaults Data/Auth/Storage to Supabase with RLS by tenant and a client-owned org from day one; §1 mandates multi-tenancy from day one.

Deciding factors: Supabase is the standard data/auth/storage platform; scalability, reliability, backups, and partition readiness are managed by the platform rather than a small team (§1 lean-team principle); the client-owned-org model (§2.5) falls out naturally.

## Decision

Adopt **Supabase** as the template default: Supabase Auth replaces the custom JWT stack, Postgres moves to the client's Supabase org, and tenant isolation is enforced with **RLS policies** on all user-facing tables. Migration is decomposed into child changes (tenant model → auth migration → RLS + per-tenant rate-limit seam → runbook), sequenced so each lands independently.

## Constitution clause deviated from

None — this aligns the template with §4.1 and §1. (The interim state — self-managed Postgres + JWT until the child changes land — is the transitional deviation this ADR authorizes.)

## Consequences

**Positive:**
- No self-operated database: scaling, HA, backups, PITR are Supabase's problem.
- Auth (sessions, recovery, MFA headroom) maintained by the platform; the custom crypto surface disappears.
- Multi-tenant enforcement moves into the database (RLS) instead of query discipline.

**Negative:**
- Local/dev and CI flows must run against the Supabase CLI local stack (or a shim) instead of a bare Postgres container.
- Alembic's role narrows (Supabase CLI migrations per §2.6 note) — migration tooling story must be decided in the tenant-model child ticket.
- Vendor coupling on the auth layer; exit path is standard Postgres + GoTrue-compatible JWTs (documented, per §1's adapter/exit-path rule).

**Follow-ups:**
- Child changes: tenant model + scoping, auth migration, RLS + rate-limit seam, runbook client-org setup.
