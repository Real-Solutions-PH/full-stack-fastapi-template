"""encrypt mcp/tool config at rest

Converts the plaintext JSONB ``config`` column on ``mcpserver`` and ``tool``
into an encrypted opaque blob (``bytea``), encrypting every existing row in
place. Runs cleanly up and down; the down path decrypts back to JSONB.

Requires the encryption key to be resolvable (CONFIG_ENCRYPTION_KEYS, or the
local dev fallback) — the same key the application uses at runtime.

Revision ID: f0c9a7b3e124
Revises: b952011f1fff
Create Date: 2026-09-04 09:10:00.000000

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.crypto import decrypt_json, encrypt_json

# revision identifiers, used by Alembic.
revision = "f0c9a7b3e124"
down_revision = "b952011f1fff"
branch_labels = None
depends_on = None

_TABLES = ("mcpserver", "tool")


def _as_dict(value: object) -> dict:
    # psycopg returns JSONB as a dict already; tolerate a raw text form too.
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    return json.loads(value)  # type: ignore[arg-type]


def upgrade() -> None:
    conn = op.get_bind()
    for table in _TABLES:
        op.add_column(table, sa.Column("config_enc", sa.LargeBinary(), nullable=True))
        rows = (
            conn.execute(
                sa.text(f"SELECT id, config FROM {table}")  # noqa: S608
            )
            .mappings()
            .all()
        )
        for row in rows:
            conn.execute(
                sa.text(
                    f"UPDATE {table} SET config_enc = :enc WHERE id = :id"  # noqa: S608
                ),
                {"enc": encrypt_json(_as_dict(row["config"])), "id": row["id"]},
            )
        op.drop_column(table, "config")
        op.alter_column(table, "config_enc", new_column_name="config", nullable=False)


def downgrade() -> None:
    conn = op.get_bind()
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column(
                "config_jsonb",
                postgresql.JSONB(),
                server_default="{}",
                nullable=True,
            ),
        )
        rows = (
            conn.execute(
                sa.text(f"SELECT id, config FROM {table}")  # noqa: S608
            )
            .mappings()
            .all()
        )
        for row in rows:
            blob = row["config"]
            cfg = decrypt_json(bytes(blob)) if blob is not None else {}
            conn.execute(
                sa.text(
                    f"UPDATE {table} SET config_jsonb = CAST(:c AS jsonb) "  # noqa: S608
                    "WHERE id = :id"
                ),
                {"c": json.dumps(cfg), "id": row["id"]},
            )
        op.drop_column(table, "config")
        op.alter_column(
            table,
            "config_jsonb",
            new_column_name="config",
            nullable=False,
            server_default="{}",
        )
