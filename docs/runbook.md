# Runbook

Operational reference for this project. Skeleton per ticket #28 — sections get filled in as the relevant ticket lands.

## Overview & environments

Single deployed environment at any time (testing → production at cutover). See [13-deployment.md](13-deployment.md) for the full environment story and promotion path.

## Deploy

Deployment is a deliberate, manual promotion — single environment, no auto-deploy on push/merge. Full detail lives in [13-deployment.md](13-deployment.md); not duplicated here.

## Rollback

- **App (Vercel/AWS):** redeploy the prior tag or commit SHA — never forward-fix under pressure. Vercel supports instant rollback to a previous deployment.
- **Database (Alembic):** `make backend-downgrade` to step back one migration.

## Backup & restore

- **Postgres:** data lives in the `app-db-data` Docker volume. Back up / restore with `pg_dump` / `pg_restore` (or `psql < dump.sql`).
- **MinIO (object storage):** back up the `app-minio-data` volume or mirror buckets with the MinIO client (`mc mirror`).
- **Redis:** cache only — data loss is acceptable; no backup required.

## Common operations

- `make up` / `make down` / `make logs` / `make ps` — start, stop, tail logs, list containers.
- Run migrations: `make backend-migrate` (upgrade head) or `make backend-revision MSG="..."` to create one.
- Regenerate the API client after a backend change: `bash scripts/generate-client.sh` (enforced by a pre-commit hook).
- First superuser is created by `backend/scripts/prestart.sh` (`FIRST_SUPERUSER` env var) — runs automatically via the `prestart` compose service.
- Mailcatcher (dev SMTP inbox): `http://localhost:1080`.

## Error monitoring & uptime

### GlitchTip (error monitoring, Sentry-SDK compatible)

**Per-client setup:** one GlitchTip organization per client, with three projects: `{client}-backend`, `{client}-frontend`, `{client}-mobile`. Each project issues its own DSN.

**Where each DSN goes** (all surfaces no-op silently when their DSN is unset):

| Surface | Variable | How it's applied |
|---------|----------|------------------|
| Backend | `SENTRY_DSN` | Runtime env var (`.env` / deploy environment) — picked up by FastAPI on boot. |
| Frontend | `FRONTEND_SENTRY_DSN` → `NEXT_PUBLIC_SENTRY_DSN` | Docker **build arg** (see `compose.yml`), inlined into the Next.js bundle at build time. Setting it only at runtime silently no-ops — rebuild the image after changing it. |
| Mobile | `EXPO_PUBLIC_SENTRY_DSN` | EAS environment variable, or `mobile/.env` for local builds. Build-time inlined, same caveat as frontend. |

**Verification:** after wiring a DSN, trigger a test error on each surface and confirm it appears in the matching GlitchTip project:
- Backend: raise an exception from any endpoint (or temporarily add a `/sentry-debug` route that raises).
- Frontend: throw inside a page component — the `error.tsx` / `global-error.tsx` boundaries report it.
- Mobile: call `Sentry.captureException(new Error("test"))` from a dev build with the DSN set.

**Alerts:** in each GlitchTip project, set alert rules to email the on-call address (e.g. notify on any new issue; tune noise later).

### Better Stack (uptime)

One Better Stack account per client (free tier: 10 monitors, 3-minute checks, status page).

- **Monitors:** backend health check `https://api.{domain}/api/v1/utils/health-check/` and the frontend URL `https://{domain}/`.
- **Escalation:** alert the on-call email/phone per the incident severities below (SEV1 path for prod-down).
- **Status page:** publish a Better Stack status page for the client with both monitors.

### DSN rotation at offboarding

When a client engagement ends: rotate (regenerate) all three GlitchTip DSNs — or delete the projects — and remove the old values from deploy env, build args, and EAS. Hand the GlitchTip org and Better Stack account over to the client or tear them down per contract.

## Client-owned org setup

Placeholder — TBD, ticket #25.

## Incidents & escalation

Per constitution §4: SEV1 (prod down / data breach) ack < 4 PH business hours (best effort < 24h any calendar day); SEV2 (major feature degraded) ack < 8 working hours; SEV3 (minor) ack next business day. First move is rollback, not forward-fix. SEV1 gets a written postmortem within 5 business days.
