# ADR-0009 — Encryption at rest for MCP/tool connection config

- **Date:** 2026-09-04
- **Status:** accepted
- **Deciders:** maintainers

## Context

Connection config for MCP servers and tools (`mcpserver.config`,
`tool.config`) can hold connection secrets — bearer tokens, auth headers,
provider API keys. It was made write-only at the API boundary (never echoed;
ADR-0008) but was still stored as **plaintext JSONB**, so a database dump or a
read replica exposed every secret. ADR-0008 recorded this as an open
deviation from constitution §3 ("creds stored encrypted in DB").

The constitution's full ideal is envelope encryption: a **per-tenant data
key** encrypting the secret, with the **master key in a KMS / Supabase
Vault**. Neither exists yet — these catalogs are global (no tenant key) and no
KMS is wired — and building both is a larger, architecture-level change.

## Decision

Encrypt these config blobs at rest with **application-level symmetric
encryption**, keyed from settings:

1. **Encrypted column type.** `config` becomes a `bytea` holding a Fernet
   token (AES-128-CBC + HMAC-SHA256, authenticated) over the JSON of the dict.
   A SQLAlchemy `TypeDecorator` (`app/core/crypto.py::EncryptedJSON`) makes it
   transparent to the ORM — code still reads and writes a plain `dict`. The
   column is opaque, so it cannot be queried by content; it is only ever
   fetched whole by id, so nothing is lost.

2. **Key from settings, with rotation.** `CONFIG_ENCRYPTION_KEYS` is a
   comma-separated list of Fernet keys — the first encrypts, all decrypt
   (`MultiFernet`), so a key rotates by prepending the new one without a bulk
   re-encrypt. Required outside `local`; `local` falls back to a well-known
   insecure dev key with a warning so dev/tests run unconfigured.

3. **Migration.** A single revision converts `config` from JSONB to `bytea`,
   encrypting every existing row in place, and runs cleanly down (decrypting
   back to JSONB).

Key generation, rotation, and the local fallback are documented in
[22-data-protection.md](../22-data-protection.md).

## Constitution clause deviated from

- **§3 — "Creds stored encrypted in DB."** This **satisfies** the
  "encrypted in DB" requirement but **not** the fuller envelope-encryption
  model described in §3/§2.7 (per-tenant data key; master key in a
  KMS/Supabase Vault). The residual deviation: a single application-managed
  key (in settings/`.env`) rather than a KMS-held master key, and no
  per-tenant data key. Closing it depends on tenant scoping for these
  catalogs and a wired KMS — both out of scope here and tracked below.

## Consequences

**Positive:**

- A database dump, backup, or read replica no longer exposes connection
  secrets — they are ciphertext at rest.
- Key rotation is supported without downtime or a bulk re-encrypt pass.
- Transparent to callers; no service/repo/route changes.

**Negative / limitations:**

- The encryption key lives in settings/`.env`, not a KMS — anyone with both
  the DB dump and the environment can still decrypt. This is the accepted
  §3 gap above.
- No per-tenant data key; one key protects all rows.
- `config` is no longer queryable/indexable by content (acceptable — it is
  fetched only by id).
- Losing the key (with no entry still in `CONFIG_ENCRYPTION_KEYS`) makes
  existing config unrecoverable.

**Follow-ups:**

- Envelope encryption: per-tenant data key with the master key in a
  KMS/Supabase Vault, once these catalogs are tenant-scoped and a KMS is
  available.
