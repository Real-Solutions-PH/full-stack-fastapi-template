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

Placeholder — detail lands with ticket #31.

## Client-owned org setup

Placeholder — TBD, ticket #25.

## Incidents & escalation

Per constitution §4: SEV1 (prod down / data breach) ack < 4 PH business hours (best effort < 24h any calendar day); SEV2 (major feature degraded) ack < 8 working hours; SEV3 (minor) ack next business day. First move is rollback, not forward-fix. SEV1 gets a written postmortem within 5 business days.
