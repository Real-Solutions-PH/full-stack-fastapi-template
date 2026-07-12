# CLAUDE.md

This repo is governed by the **Engineering Constitution v2.0**, pinned at [docs/constitution.md](docs/constitution.md) (master lives in Notion; the repo copy is never edited). Any deviation from a constitution default requires an ADR in [docs/adr/](docs/adr/) with client sign-off (§0.3).

## Repo map

- `backend/` — FastAPI + SQLModel, managed with `uv`.
- `frontend/` — Next.js 15 (App Router), a bun workspace member of the root `package.json`, linted with Biome.
- `mobile/` — Expo SDK 52, a **standalone** bun project **not** part of the root workspace — run bun commands from inside `mobile/`.
- `docs/` — numbered context pack + pinned constitution + `adr/` + `runbook.md`.
- `scripts/` — repo-level scripts (client generation, test runners).
- `Makefile` — task entry points for the above.

## Commands

| Workspace | Task | Command |
|---|---|---|
| backend | install deps | `uv sync` (from `backend/`) |
| backend | lint | `make backend-lint` (mypy + ty check + ruff check + ruff format --check) |
| backend | test | `make backend-test` (or `bash backend/scripts/test.sh`) |
| backend | migrate | `make backend-migrate` (upgrade head) / `make backend-revision MSG="..."` |
| frontend | install deps | `bun install` (root) |
| frontend | dev server | `bun run dev` |
| frontend | lint | `bun run lint` (Biome — **mutates**, runs `--write`) |
| frontend | test | `bun run test` (Playwright — needs the stack running) |
| mobile | install deps | `cd mobile && bun install` |
| mobile | typecheck | `bun run typecheck` (from `mobile/`) |
| mobile | lint | `bun run lint` (from `mobile/`, Biome) |

## Codegen rule

**Never hand-edit `frontend/src/client/`.** Regenerate it via `bash scripts/generate-client.sh` after any backend API change — a pre-commit hook enforces this. The mobile client is generated separately via `mobile/openapi-ts.config.ts`.

## Conventions

- Conventional commits (`feat:`, `fix:`, `chore:`, …).
- Every schema change goes through Alembic — no dashboard or manual DDL.
- Biome is the linter/formatter for TS — not ESLint, not Prettier.
- Backend type-checking is mypy **strict**.
- Docs use `YYYY-MM-DD` dates; update `docs/README.md`'s index when adding a doc.
- Backend tests run against the local DB and **wipe `User`/`Item` rows** — use the Docker-based test scripts (`make backend-test` / `bash backend/scripts/test.sh`), not an ad hoc run against a DB you care about.

## Pointers

- [development.md](development.md) — local dev setup.
- [docs/13-deployment.md](docs/13-deployment.md) — deployment story.
- [docs/runbook.md](docs/runbook.md) — operational runbook.
- [docs/adr/](docs/adr/) — architecture decision records.
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution workflow.
