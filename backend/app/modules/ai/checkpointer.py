from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.core.config import settings


async def get_checkpointer() -> AsyncPostgresSaver:
    """Create and initialise a PostgreSQL checkpointer for LangGraph.

    Uses the same database as the application.  The checkpointer manages
    its own tables via ``setup()``.
    """
    conn_string = str(settings.SQLALCHEMY_DATABASE_URI).replace(
        "postgresql+psycopg", "postgresql"
    )
    conn = await AsyncConnection.connect(
        conn_string, autocommit=True, row_factory=dict_row
    )
    checkpointer = AsyncPostgresSaver(conn)
    await checkpointer.setup()
    return checkpointer
