# Data protection — deletion, retention, export

How the backend handles personal data: what it stores, how a record is
removed, how long anything is kept, and how a user's data is exported or
erased. Credentials are out of scope here — they live in Supabase Auth, never
in the application database.

## Personal data held

| Entity | Personal data | Where |
|--------|---------------|-------|
| `user` | email, full name | `user` table (a mirror of the Supabase Auth identity, keyed by the auth UID) |
| `item` | user-authored content | `item` table, `owner_id` → `user` |

## Two ways a record leaves the app

There are two distinct operations. They are not interchangeable — pick by
whether the removal must be reversible.

### Soft delete (reversible retention)

`deleted_at` (a nullable timestamp on `user` and `item`) is the soft-delete
marker. A non-null `deleted_at` means the row is **logically deleted but
retained**:

- It disappears from normal reads. `item` reads (`get_by_id`, `get_multi`)
  filter `deleted_at IS NULL`, so a soft-deleted item is a natural 404.
- The row and its data are kept until an explicit hard delete purges them.
- For a `user`, `soft_delete_user` also sets `is_active = False`, so the
  account is rejected at the auth boundary (the `is_active` gate) even while
  the row is retained.

Use it when a removal might need to be undone, or when a record must be kept
for a retention window before final purge.

Helpers: `items.repo.soft_delete`, `iam.users.services.soft_delete_user`.

### Hard delete / erasure (irreversible)

The existing delete path is a true erasure — it satisfies the GDPR right to
erasure:

- `delete_user` / `delete_user_me` revoke the Supabase Auth identity **first**
  (so a provider failure leaves nothing changed), then hard-delete the local
  row; the user's items cascade.
- `items.repo.delete` hard-deletes a single item.

Once erased, the data is gone. There is no undo.

## Retention posture

The template ships **no automatic purge**. Soft-deleted rows are retained
indefinitely until an operator runs an erasure. Choose a retention window for
your deployment and purge soft-deleted rows past it — e.g. a scheduled job
that hard-deletes `user`/`item` rows whose `deleted_at` is older than the
window. This is deliberately left to the deployer: retention duration is a
policy decision, not a code default.

## Data export (portability)

`iam.users.services.export_user_data(session, user_id)` returns a portable
dict of everything held about one user — their profile row plus **all** their
items, including retained soft-deleted ones (an export must return all data
still held). It contains no credentials.

```python
{
  "user":  { ... profile fields ... },
  "items": [ { ... }, ... ],
}
```

Serialize it to JSON to hand to the data subject.

## Audit trail

Every privileged/mutating action (user create/update/delete, MCP and tool
CRUD) writes an append-only row to `auditlog` — actor, action, target,
before/after snapshot, and timestamp — for account-takeover / privilege-
escalation forensics and accountability. Snapshots carry only non-secret
fields: connection secrets (MCP/tool `config`) are never captured. See
`app/modules/audit/`.

## Encryption at rest — connection secrets

Most credentials live in Supabase Auth, not the app DB. The exception is
**connection config for MCP servers and tools** (`mcpserver.config`,
`tool.config`), which can hold bearer tokens, auth headers, and provider API
keys. That config is write-only at the API (never echoed — see ADR-0008) and
is **encrypted at rest** so a database dump alone never exposes a secret.

**Scheme.** The `config` column is a `bytea` holding a Fernet token
(AES-128-CBC + HMAC-SHA256, authenticated) over the JSON of the config dict.
Encryption is transparent to the application: assign and read a plain `dict`;
the ciphertext only exists in the column. See `app/core/crypto.py`
(`EncryptedJSON`). Because the stored form is opaque, `config` cannot be
queried or indexed by its contents — it is only ever fetched whole by id, so
this costs nothing.

### Key management

`CONFIG_ENCRYPTION_KEYS` is a **comma-separated list of Fernet keys**. The
first key encrypts new writes; every key in the list can decrypt. Generate a
key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

- **Non-local (`ENVIRONMENT != local`)**: the key is **required** — the app
  refuses to start without it (`Settings` validation), so secrets are never
  written under a default key.
- **Local**: if unset, a well-known **insecure built-in dev key** is used and a
  warning is emitted, so dev and tests work unconfigured. Never rely on it for
  anything real.

Store the key in the team password manager (constitution §2.8), inject it via
`.env`, and **never commit it**.

### Rotation

1. Generate a new key and **prepend** it: `CONFIG_ENCRYPTION_KEYS=<new>,<old>`.
2. Redeploy. New writes use `<new>`; existing rows still decrypt under `<old>`.
3. Re-encrypt existing rows onto the new key with a one-off script that loads
   each row and re-saves it (loading decrypts under `<old>`; saving re-encrypts
   under the primary `<new>`). A no-op API update does **not** re-encrypt —
   `config` is only re-encrypted when it is written, and it can't be read back
   over the API to re-submit:

   ```python
   from sqlalchemy.orm.attributes import flag_modified
   from sqlmodel import Session, select
   from app.core.db import engine
   from app.modules.ai.mcp.models import MCPServer
   from app.modules.ai.tools.models import Tool

   with Session(engine) as s:
       for model in (MCPServer, Tool):
           for row in s.exec(select(model)).all():
               flag_modified(row, "config")  # force a re-write -> re-encrypt
               s.add(row)
       s.commit()
   ```

   (`flag_modified` is required — reassigning the same dict is not tracked as a
   change.)
4. Once every row is re-encrypted, drop `<old>` from the list.

### Known limitation (constitution §3 deviation)

This is application-level encryption with a key from settings — a step below
the constitution's envelope-encryption ideal (a **per-tenant data key** with
the **master key in a KMS / Supabase Vault**). These catalogs are global and
have no per-tenant key, and no KMS is wired. The residual gap is tracked in
ADR-0009.

## Account email changes

An account's email is the anchor for recovery and magic-link sign-in, so it
may only change once ownership of the new address is verified. Self-service
(`PATCH /users/me`) therefore **does not** change the email — it is refused
until a verified, double-confirmation change flow is available (see
ADR-0008). A superuser can still set a user's email through the admin update
path.
