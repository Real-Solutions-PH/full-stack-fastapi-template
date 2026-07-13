import logging

from sqlalchemy import text

from app.core.db import engine

logger = logging.getLogger(__name__)


def warn_if_rls_dormant() -> None:
    """Log when the app connection bypasses row-level security.

    Superusers and table owners skip RLS entirely, so the RLS policies are a
    dormant second wall until the app engine is flipped to the non-owner
    ``app_user`` role. Non-fatal by design: purely a startup breadcrumb.
    """
    try:
        with engine.connect() as conn:
            # Table OWNERS also bypass plain ENABLE RLS — on managed Postgres
            # the app role is often a non-superuser schema owner, so checking
            # rolsuper/rolbypassrls alone gives a false all-clear.
            bypasses = conn.execute(
                text(
                    "SELECT (SELECT rolbypassrls OR rolsuper FROM pg_roles"
                    "        WHERE rolname = current_user)"
                    " OR EXISTS (SELECT 1 FROM pg_tables"
                    "            WHERE schemaname = 'public'"
                    "            AND tablename = 'item'"
                    "            AND pg_catalog.pg_has_role("
                    "                current_user, tableowner, 'MEMBER'))"
                )
            ).scalar()
            current_role = conn.execute(text("SELECT current_user")).scalar()
        if bypasses:
            logger.warning(
                "RLS is DORMANT: app connection runs as %s which bypasses row"
                " security via superuser/BYPASSRLS or table ownership"
                " (expected until the engine is flipped to app_user)",
                current_role,
            )
    except Exception:  # pragma: no cover - visibility only, never fatal
        logger.warning("Could not determine RLS posture of the app connection")
