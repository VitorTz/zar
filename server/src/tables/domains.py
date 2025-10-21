from asyncpg import Connection
from typing import Optional


async def get_domain_id(url: str, conn: Connection, is_secure: bool = True) -> int:
    domain_id: int = conn.fetchval(
        """
            WITH ins AS (
                INSERT INTO domains (
                    url, 
                    url_hash,
                    is_secure
                )
                VALUES 
                    (TRIM($1), decode(md5(TRIM($2)), 'hex'), $3)
                ON CONFLICT
                    (url_hash)
                DO NOTHING
                RETURNING 
                    id
            )
            SELECT 
                id FROM ins UNION
            SELECT 
                id 
            FROM
                domains 
            WHERE 
                url_hash = decode(md5(TRIM($2)), 'hex')
        """,
        url,
        url,
        is_secure
    )
    return domain_id


async def is_safe_domain(url: str, conn: Connection) -> bool:
    r = await conn.fetchrow(
        "SELECT is_secure FROM domains WHERE url_hash = decode(md5(TRIM($1))",
        url
    )
    return r['is_secure'] if r else None


async def create_domain(url: str, is_secure: bool, conn: Connection):
    await conn.execute(
        """
            INSERT INTO domains (
                url,
                url_hash,
                is_secure
            )
            VALUES
                ($1, decode(md5(TRIM($2)), $3)
            ON CONFLICT
                (url_hash)
            DO NOTHING
        """,
        url,
        url,
        is_secure
    )


async def delete_domain_by_id(domain_id, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                domains
            WHERE
                id = $1
        """,
        domain_id
    )


async def get_domains(
    url: Optional[str],
    is_secure: Optional[bool],
    limit: int,
    offset: int,
    conn: Connection
):
    if url:
        total = await conn.fetchval(
            """
            SELECT COUNT(*) 
            FROM domains
            WHERE url ILIKE $1
              AND ($2 IS NULL OR is_secure = $2)
            """,
            f"%{url}%",
            is_secure
        )
        rows = await conn.fetch(
            """
            SELECT
                id,
                url,
                url_hash::text,
                similarity(url, $1) AS score,
                is_secure
            FROM domains
            WHERE url ILIKE $1
              AND ($2 IS NULL OR is_secure = $2)
            ORDER BY score DESC
            LIMIT $3
            OFFSET $4
            """,
            f"%{url}%",
            is_secure,
            limit,
            offset
        )
        return total, [dict(r) for r in rows]

    total = await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM domains
        WHERE ($1 IS NULL OR is_secure = $1)
        """,
        is_secure
    )
    rows = await conn.fetch(
        """
        SELECT
            id,
            url,
            url_hash::text,
            is_secure
        FROM domains
        WHERE ($1 IS NULL OR is_secure = $1)
        LIMIT $2
        OFFSET $3
        """,
        is_secure,
        limit,
        offset
    )
    return total, [dict(r) for r in rows]