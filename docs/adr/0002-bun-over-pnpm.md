# ADR-0002 — bun instead of pnpm workspaces for JS package management

- **Date:** 2026-07-12
- **Status:** accepted
- **Deciders:** Kairus (RSPH), per #30 approval

## Context

Constitution §3.1 defaults JS tooling to pnpm workspaces. This template uses bun: a root `bun.lock` covering the `frontend` workspace, and a standalone bun project in `mobile/`. Every CI job, Dockerfile, and script already invokes bun; Dependabot runs the `bun` ecosystem for both directories.

## Decision

Keep **bun** as the JS package manager and lockfile of record everywhere. npm/yarn/pnpm lockfiles stay gitignored (a stale npm lockfile in `mobile/` already caused real dependency drift — see #32).

## Constitution clause deviated from

§3.1 — "Tooling: pnpm workspaces (TS)."

## Client sign-off

Internal template (RSPH-owned, §7.3) — founder approval on issue #30, 2026-07-12.

## Consequences

**Positive:**
- No migration churn across three workspaces, CI, and Docker; bun install speed benefits every pipeline run.

**Negative:**
- bun's workspace/lockfile semantics are younger than pnpm's; occasional ecosystem tooling assumes npm/pnpm (worked around case-by-case, e.g. license-checker at the workspace root).

**Follow-ups:**
- None.
