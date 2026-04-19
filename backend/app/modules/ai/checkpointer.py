from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import settings


async def get_checkpointer() -> AsyncPostgresSaver:
    """Create and initialise a PostgreSQL checkpointer for LangGraph.

    Uses the same database as the application.  The checkpointer manages
    its own tables via ``setup()``.
    """
    conn_string = str(settings.SQLALCHEMY_DATABASE_URI).replace(
        "postgresql+psycopg", "postgresql"
    )
    checkpointer = AsyncPostgresSaver.from_conn_string(conn_string)
    await checkpointer.setup()
    return checkpointer
