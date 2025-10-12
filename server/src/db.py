from asyncpg import create_pool, Pool, Connection
from src.migrate import db_migrate
import os


db_pool: Pool = None


async def db_init() -> None:
    global db_pool
    db_pool = await create_pool(os.getenv("DATABASE_URL"), min_size=5, max_size=20)
    async with db_pool.acquire() as conn:
        await db_migrate(conn)


def get_db_pool() -> Pool:
    global db_pool
    return db_pool


async def db_close() -> None:
    await db_pool.close()


async def get_db():
    async with db_pool.acquire() as conn:
        yield conn


async def db_count(table: str, conn: Connection) -> int:
    r = await conn.fetchrow(f"SELECT COUNT(*) AS total FROM {table};")
    return dict(r)['total']


async def db_version(conn: Connection) -> str:
    r = await conn.fetchrow("SELECT version()")    
    return r['version']