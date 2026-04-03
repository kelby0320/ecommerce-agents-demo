from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager

import psycopg
import psycopg.rows

_superuser_dsn: str = ""
_agent_dsn: str = ""


def init_db(dsn: str) -> None:
    global _superuser_dsn, _agent_dsn
    _superuser_dsn = dsn
    _agent_dsn = dsn.replace(
        "postgresql://postgres:postgres@",
        "postgresql://agent_reader:agent_password@",
    )


@contextmanager
def get_connection():
    """Sync superuser connection. Bypasses RLS. For REST API."""
    conn = psycopg.connect(_superuser_dsn, row_factory=psycopg.rows.dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@asynccontextmanager
async def get_agent_connection(user_id: str):
    """Async agent_reader connection with RLS session var. SELECT only."""
    conn = await psycopg.AsyncConnection.connect(
        _agent_dsn, row_factory=psycopg.rows.dict_row, autocommit=True
    )
    try:
        if user_id:
            await conn.execute(
                "SELECT set_config('app.current_user_id', %s, FALSE)", [user_id]
            )
        yield conn
    finally:
        await conn.close()
