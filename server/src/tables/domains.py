from src.schemas.domain import Domain, DomainCreate, DomainUpdate
from src.schemas.pagination import Pagination
from asyncpg import Connection
from typing import Optional
from src import util

async def get_domain_by_id(id: int, conn: Connection) -> Optional[Domain]:
    row = await conn.fetchrow(
        """
            SELECT
                id,
                url,
                url_hash,
                is_secure
            FROM
                domains
            WHERE
                id = $1
        """,
        id
    )
    return Domain(**dict(row)) if row else None

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
            ON CONFLICT 
                (url_hash)
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
        FROM 
            domains 
        WHERE 
            url_hash = decode(md5(TRIM($1)), 'hex')
        """,
        util.extract_domain(url)
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
        util.extract_domain(str(domain.url)),
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
    is_secure: Optional[bool],
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Domain]:
    filters = []
    params = []
    param_index = 1

    if url:
        filters.append(f"url ILIKE ${param_index}")
        params.append(f"%{url}%")
        param_index += 1

    if is_secure is not None:
        filters.append(f"is_secure = ${param_index}")
        params.append(is_secure)
        param_index += 1

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    total = await conn.fetchval(
        f"""
            SELECT 
                COUNT(*) 
            FROM 
                domains
            {where_clause}
        """,
        *params
    )

    rows = await conn.fetch(
        f"""
            SELECT
                id,
                url,
                url_hash,
                is_secure
            FROM 
                domains
            {where_clause}
            ORDER BY 
                id DESC
            LIMIT 
                ${param_index}
            OFFSET 
                ${param_index + 1}
        """,
        *params, 
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