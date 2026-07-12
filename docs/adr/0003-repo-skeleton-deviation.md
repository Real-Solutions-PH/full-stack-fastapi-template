# ADR-0003 — Keep backend/ frontend/ mobile/ layout instead of the §3.1 skeleton

- **Date:** 2026-07-12
- **Status:** accepted
- **Deciders:** Kairus (RSPH), per #30 approval

## Context

Constitution §3.1 defines the standard monorepo skeleton: `apps/` · `packages/` · `pipelines/` · `infra/` · `docs/` · `e2e/`. This template (a fork of tiangolo's full-stack-fastapi-template) uses `backend/` · `frontend/` · `mobile/` · `docs/` · `scripts/`. A tree-wide move would break every CI path, Docker build context, compose file, and import for zero functional gain on an existing codebase.

## Decision

Keep the current top-level layout **for this template**. The §3.1 skeleton remains the default for greenfield RSPH monorepos; this ADR covers only repositories derived from this template.

## Constitution clause deviated from

§3.1 — standard skeleton `apps/ packages/ pipelines/ infra/ docs/ e2e/`.

## Client sign-off

Internal template (RSPH-owned, §7.3) — founder approval on issue #30, 2026-07-12.

## Consequences

**Positive:**
- Zero churn; all CI/Docker/tooling paths stay valid.

**Negative:**
- Template-derived projects and greenfield projects have different top-level shapes; contributors moving between them must adjust.
- No dedicated `packages/` seam for shared types — the generated API clients fill that role today.

**Follow-ups:**
- The e2e location (`e2e/` at root per §3.1) is decided together with the Cypress migration — see ADR-0004.
