# Onboarding (Devs + AI Agents)

## Day 0 — Access

- [ ] GitHub repo
- [ ] Cloud accounts (read-only first)
- [ ] Sentry, Stripe, etc.
- [ ] Secrets via 1Password / vault
- [ ] On-call rotation (later)

## Day 1 — Local Setup

```bash
# clone
git clone <repo> && cd full-stack-fastapi-template

# env
cp .env.example .env

# spin up
docker compose up -d

# backend
cd backend && uv sync && uv run pytest

# frontend
cd frontend && bun install && bun run dev
```

URLs:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- MinIO: http://localhost:9001

## Day 2 — Repo Tour

| Path | What |
|------|------|
| `backend/` | FastAPI app |
| `frontend/` | Next.js app |
| `compose.yml` | service definitions |
| `docs/` | this folder |
| `scripts/` | one-off ops |
| `hooks/` | git/claude hooks |

## Workflow

1. Branch from `master`.
2. TDD — see [11-testing-strategy.md](11-testing-strategy.md).
3. PR with description, screenshots, test plan.
4. Reviewer + CI green -> squash merge.
5. Auto-deploy to staging.

## AI Agent Context

When starting session, agents should read in order:
1. [README.md](README.md)
2. [00-vision.md](00-vision.md)
3. [06-architecture.md](06-architecture.md)
4. [07-tech-stack.md](07-tech-stack.md)
5. [10-implementation-plan.md](10-implementation-plan.md)
6. Task-specific doc (e.g. [09-api-spec.md](09-api-spec.md) for API work)

## Common Commands

| Task | Command |
|------|---------|
| Run tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Migrate | `uv run alembic upgrade head` |
| New migration | `uv run alembic revision --autogenerate -m "msg"` |

## Troubleshooting

- DB connection refused -> `docker compose up -d db`
- Port in use -> `lsof -i :PORT`
- Stale deps -> `uv sync --reinstall` / `bun install --force`
