from src.util import execute_sql_file
from asyncpg import Connection
from pathlib import Path


async def db_migrate(conn: Connection) -> None:
    print("[DATABASE MIGRATE START]")
    await execute_sql_file(Path("db/tables.sql"), conn)
    print("[DATABASE MIGRATE END]")