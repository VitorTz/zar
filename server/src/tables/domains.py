from src.schemas.domain import Domain, DomainCreate, DomainUpdate
from src.schemas.pagination import Pagination
from asyncpg import Connection
from typing import Optional


async def get_domain(url: str, conn: Connection) -> Optional[Domain]:
    r = await conn.fetchrow(
        """
            SELECT
                id,
                url,
                url_hash,
                is_secure
            FROM
                domains
            WHERE
                url_hash = decode(md5(TRIM($1)), 'hex')
        """,
        url
    )
    return Domain(**dict(r)) if r else None


async def get_domain(url: str, conn: Connection) -> Domain:
    r = await conn.fetchrow(
        """
        WITH ins AS (
            INSERT INTO domains (
                url, 
                url_hash
            )
            VALUES 
                (TRIM($1), decode(md5(TRIM($1)), 'hex'))
            ON CONFLICT (url_hash)
            DO NOTHING
            RETURNING 
                id,
                url,
                url_hash,
                is_secure
        )
        SELECT 
            id,
            url,
            url_hash,
            is_secure
        FROM ins
        UNION
        SELECT 
            id,
            url,
            url_hash,
            is_secure
        FROM domains 
        WHERE url_hash = decode(md5(TRIM($1)), 'hex')
        """,
        url
    )
    return Domain(**dict(r))


async def get_domain_id(url: str, conn: Connection, is_secure: bool = True) -> int:
    domain_id: int = await conn.fetchval(
        """
        WITH ins AS (
            INSERT INTO domains (
                url, 
                url_hash,
                is_secure
            )
            VALUES 
                (TRIM($1), decode(md5(TRIM($1)), 'hex'), $2)
            ON CONFLICT (url_hash)
            DO NOTHING
            RETURNING id
        )
        SELECT 
            id 
        FROM 
            ins
        UNION
        SELECT 
            id 
        FROM 
            domains 
        WHERE 
            url_hash = decode(md5(TRIM($1)), 'hex')
        """,
        url,
        is_secure
    )
    return domain_id


async def is_safe_domain(url: str, conn: Connection) -> bool:
    r = await conn.fetchrow(
        """
            SELECT 
                is_secure 
            FROM 
                domains 
            WHERE 
                url_hash = decode(md5(TRIM($1)), 'hex')
            """,
        url
    )
    return r['is_secure'] if r else None


async def create_domain(domain: DomainCreate, conn: Connection) -> Domain:
    r = await conn.fetchrow(
        """
            INSERT INTO domains (
                url,
                url_hash,
                is_secure
            )
            VALUES (
                $1,
                decode(md5(TRIM($1)), 'hex'),
                $2
            )
            ON CONFLICT 
                (url_hash)
            DO UPDATE SET
                is_secure = EXCLUDED.is_secure
            RETURNING
                id,
                url,
                url_hash,
                is_secure
        """,
        str(domain.url),
        domain.is_secure
    )
    return Domain(**dict(r))

async def upsert_domain(domain_id: int, is_secure: bool, conn: Connection):
    await conn.execute(
        """
        UPDATE
            domains
        SET
            is_secure = $1
        WHERE
            id = $2        
        """,
        is_secure,
        domain_id
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
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Domain]:
    if url:
        total = await conn.fetchval(
            """
            SELECT 
                COUNT(*) 
            FROM 
                domains
            WHERE 
                url ILIKE $1
            """,
            f"%{url}%"            
        )
        rows = await conn.fetch(
            """
            SELECT
                id,
                url,
                url_hash,
                similarity(url, $1) AS score,
                is_secure
            FROM 
                domains
            WHERE 
                url ILIKE $1
            ORDER BY 
                score DESC
            LIMIT 
                $2
            OFFSET 
                $3
            """,
            f"%{url}%",
            limit,
            offset
        )
        return Pagination(
            total=total,
            limit=limit,
            offset=offset,
            results=[Domain(**dict(r)) for r in rows]
        )

    total = await conn.fetchval(
        """
        SELECT
            COUNT(*) as total
        FROM
            domains
        """        
    )

    rows = await conn.fetch(
        """
        SELECT
            id,
            url,
            url_hash,
            is_secure
        FROM 
            domains
        LIMIT 
            $1
        OFFSET 
            $2
        """,
        limit,
        offset
    )    
    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[Domain(**dict(r)) for r in rows]
    )


async def update_domain(domain: DomainUpdate, conn: Connection) -> None:
    await conn.execute(
        """
            UPDATE 
                domains
            SET
                is_secure = $1
            WHERE
                id = $2
        """,
        domain.is_secure,
        domain.id
    )