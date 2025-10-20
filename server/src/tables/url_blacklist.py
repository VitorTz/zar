from asyncpg import Connection
from src.security import sha256_bytes
from typing import Optional


async def is_url_in_blacklist(url: str, conn: Connection) -> bool:
    r = await conn.fetchrow(
        "SELECT id FROM url_blacklist WHERE url_hash = $1",
        sha256_bytes(url)
    )
    return r is not None


async def add_url_to_blacklist(url: str, conn: Connection):
    await conn.execute(
        """
            INSERT INTO url_blacklist (
                url,
                url_hash
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (url_hash)
            DO NOTHING
        """,
        url,
        sha256_bytes(url.strip())
    )


async def delete_blacklisted_urls(url: str, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                urls
            WHERE
                original_url_hash = $1
        """,
        sha256_bytes(url.strip())
    )


async def remove_url_from_blacklist(url: str, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                url_blacklist
            WHERE
                url_hash = $1
        """,
        sha256_bytes(url.strip())
    )


async def get_blacklist(q: Optional[str], limit: int, offset: int, conn: Connection):
    if q:
        total: int = await conn.fetchval(
            """
                SELECT 
                    COUNT(*) as total
                FROM 
                    url_blacklist
                WHERE 
                    url ILIKE $1
            """,
            f"%{q}%",
        )
        r = await conn.fetch(
            """
                SELECT
                    id,
                    url,
                    url_hash::text,
                    similarity(url, $1) AS score,
                    TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at
                FROM 
                    url_blacklist
                WHERE 
                    url ILIKE $1
                ORDER BY 
                    score DESC
                LIMIT 
                    $2
                OFFSET
                    $3;
            """,
            f"%{q}%",
            limit,
            offset
        )
        return total, [dict(i) for i in r]

    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM url_blacklist")
    r = await conn.fetch(
        """
            SELECT 
                id,
                url,
                url_hash::text,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at
            FROM 
                url_blacklist
            LIMIT 
                $1
            OFFSET
                $2;
        """,
        limit,
        offset
    )
    return total, [dict(i) for i in r]