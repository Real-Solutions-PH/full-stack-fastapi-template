# Deployment

## Principle: One Environment, Manual Promotion

Per constitution §3.5 there is exactly **one deployed environment at any time**, and per §3.2 **nothing deploys automatically on push or merge**. Promotion is always a deliberate human action.

- No per-environment branches, no auto-deploy from `main`/`master` (§3.2).
- No standing staging environment running alongside production.
- Production is always AWS, built during the production-targeting phase. When production goes live (cutover), the testing environment is torn down.

## Environments

| Env | Where | Purpose | How it gets deployed |
|-----|-------|---------|----------------------|
| Local | Docker Compose (this repo) | Day-to-day development | `docker compose watch` — never "deployed" anywhere |
| Testing | Vercel free tier: Next.js frontend + FastAPI as serverless functions; managed Postgres | Client-internal testing only — never real users | Deliberately, via the Vercel CLI or dashboard; never on push |
| Production | Always AWS | Real users | Built in the production-targeting phase; the testing env is torn down at cutover |

Only one of Testing or Production is deployed at a time — Testing exists before cutover, Production after.

## Promotion Path (Vercel → AWS)

Promotion to production is a deliberate manual act:

- A `workflow_dispatch`-only GitHub Actions workflow that deploys an explicitly chosen tag or commit SHA to AWS. This workflow will be added when the production environment is built.
- **Never** a `push:` or `release:` trigger. No deploy may be a side effect of merging or tagging.
- At cutover, the Vercel testing environment is torn down (§3.5).

## What This Template Deliberately Does NOT Include

Removed on purpose, per the constitution:

- **Self-hosted GitHub Actions runners** and VPS deploy workflows — no self-hosted clusters or servers for a 2-person team (§1).
- **Traefik reverse proxy** (`compose.traefik.yml` and all `traefik.*` labels) — there is no self-hosted server for it to front (§1, §3.5).
- **Standing staging environments** and auto-deploy on merge to `master` (§3.2, §3.5).
- **Railway or any third PaaS** — Vercel for testing, AWS for production; Hetzner only if EU data residency requires it (§3.5).

## Vercel Readiness Gaps (Documented, Not Yet Implemented)

Deploying this template's backend to Vercel free tier requires work that has deliberately not been done yet:

- **Serverless entrypoint**: FastAPI needs a Vercel-compatible entrypoint and a `vercel.json`; the current Docker-based backend image is not directly deployable to Vercel functions.
- **Managed service replacements**: the Compose stack's Postgres, Redis, MinIO, and Mailcatcher/SMTP containers must be replaced with managed equivalents (e.g. managed Postgres, hosted Redis, S3-compatible storage, a transactional email provider).
- **Migrations**: `prestart.sh` (which runs Alembic migrations) will not run in a serverless environment — migrations need an explicit story, e.g. run manually or from a one-off job before deploying.
- **Free-tier limits**: 60s max function duration (300s with Fluid compute) and ~4h active CPU per month — fine for CRUD APIs, unsuitable for WebSockets or long-running jobs (§3.5).

## ADR Escape Hatch

A project generated from this template may adopt a self-hosted Docker Compose + Traefik deployment **only** via an Architecture Decision Record in `docs/adr/` (per constitution §0.3; the ADR directory is being created in ticket #28). The old self-hosted deployment guide is preserved in git history: `deployment.md` at commit `d3a9c71`.

## Reference: Secrets and Environment Variables

### Generate secret keys

Some environment variables in the `.env` file have a default value of `changethis`.

You have to change them with a secret key, to generate secret keys you can run the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the content and use that as password / secret key. And run that again to generate another secure key.

### Environment variable reference

* `PROJECT_NAME`: The name of the project, used in the API for the docs and emails.
* `STACK_NAME`: The name of the stack used for Docker Compose labels and project name.
* `BACKEND_CORS_ORIGINS`: A list of allowed CORS origins separated by commas.
* `FIRST_SUPERUSER`: The email of the first superuser, this superuser will be the one that can create new users.
* `SMTP_HOST`: The SMTP server host to send emails, this would come from your email provider (E.g. Mailgun, Sparkpost, Sendgrid, etc).
* `SMTP_USER`: The SMTP server user to send emails.
* `SMTP_PASSWORD`: The SMTP server password to send emails.
* `EMAILS_FROM_EMAIL`: The email account to send emails from.
* `POSTGRES_SERVER`: The hostname of the PostgreSQL server. You can leave the default of `db`, provided by the same Docker Compose. You normally wouldn't need to change this unless you are using a third-party provider.
* `POSTGRES_PORT`: The port of the PostgreSQL server. You can leave the default. You normally wouldn't need to change this unless you are using a third-party provider.
* `POSTGRES_USER`: The Postgres user, you can leave the default.
* `POSTGRES_DB`: The database name to use for this application. You can leave the default of `app`.
* `SENTRY_DSN`: The DSN for Sentry, if you are using it.

## Runbook

See `docs/runbook.md` (ticket #28).
