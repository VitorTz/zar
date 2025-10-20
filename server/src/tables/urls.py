from asyncpg import Connection
from src.schemas.user import User
from src.schemas.urls import URLCreate
from src.tables import domains as domains_table
from fastapi.exceptions import HTTPException
from fastapi import status
from typing import Optional
import json
import asyncpg


async def count_urls(conn: Connection) -> int:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls")
    return total


async def get_redirect_url(short_code: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
            SELECT
                domains.url as original_url,
                urls.p_hash,
                urls.expires_at
            FROM
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            WHERE
                short_code = TRIM($1)
        """,
        short_code
    )
    return dict(r) if r else None

async def get_original_url(short_code: str, conn: Connection) -> str | None:
    r = await conn.fetchrow(
        """
            SELECT 
                domains.url as original_url
            FROM 
                urls 
            JOIN
                domains ON domains.id = urls.domain_id
            WHERE 
                short_code = TRIM($1)
        """,
        short_code
    )
    return r["original_url"] if r else None


async def get_url(short_code: str, base_url: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
        SELECT
            id,
            user_id::text,
            domains.url as original_url,
            ($1 || '/' || short_code) AS short_url,
            short_code,
            clicks,
            title,
            qrcode_url,
            is_favorite,
            (p_hash IS NOT NULL) AS has_password,
            TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
            TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
        FROM
            urls
        JOIN
            domains ON domains.id = urls.domain_id
        WHERE
            short_code = TRIM($2)
        """,
        base_url,
        short_code
    )
    return dict(r) if r else None


async def get_url_stats(short_code: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
        SELECT
            id,
            short_code,
            total_clicks,
            unique_visitors,
            TO_CHAR(first_click, 'DD-MM-YYYY HH24:MI:SS') AS first_click,
            TO_CHAR(last_click, 'DD-MM-YYYY HH24:MI:SS') AS last_click,
            timeline,
            devices,
            browsers,
            top_countries,
            top_cities,
            operating_systems,
            top_referers
        FROM 
            vw_url_stats
        WHERE 
            short_code = $1
        """,
        short_code
    )

    if not r:
        return None

    data = dict(r)
    
    json_fields = [
        "timeline",
        "devices",
        "browsers",
        "top_countries",
        "top_cities",
        "operating_systems",
        "top_referers",
    ]

    for f in json_fields:
        v = data.get(f)
        if isinstance(v, str):
            try:
                data[f] = json.loads(v)
            except json.JSONDecodeError:
                data[f] = None

    return data


async def get_url_pages(base_url: str, user_id: str | None, limit: int, offset: int, conn: Connection) -> tuple[int, list[dict]]:

    if user_id is None:
        total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls")
        r = await conn.fetch(
            """
                SELECT
                    id,
                    user_id::text,
                    domains.url as original_url,
                    p_hash,
                    ($1 || '/' || short_code) AS short_url,
                    short_code,
                    clicks,
                    title,
                    qrcode_url,
                    (p_hash IS NOT NULL) AS has_password,
                    (FALSE) as is_favorite,
                    TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                    TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
                FROM
                    urls
                JOIN
                    domains ON domains.id = urls.domain_id
                LIMIT
                    $2
                OFFSET 
                    $3
            """,
            base_url,
            limit,
            offset
        )
        return total, [dict(i) for i in r]
    
    total: int = await conn.fetchval(
        """
            SELECT 
                COUNT(*) AS total 
            FROM 
                urls 
            JOIN 
                user_urls ON user_urls.url_id = urls.id
            WHERE
                user_urls.user_id = $1
        """,
        user_id
    )
    r = await conn.fetch(
        """
            SELECT
                id,
                user_id::text,
                domains.url as original_url,
                p_hash,
                ($1 || '/' || short_code) AS short_url,
                short_code,
                clicks,
                title,
                qrcode_url,
                (p_hash IS NOT NULL) AS has_password,
                (FALSE) as is_favorite,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            FROM
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            JOIN 
                user_urls ON user_urls.url_id = urls.id
            WHERE
                user_urls.user_id = $2
            LIMIT 
                $3
            OFFSET 
                $4
        """,
        base_url,
        user_id,
        limit,
        offset
    )
    return total, [dict(i) for i in r]



async def get_anonymous_url(original_url: str, base_url: str, title: Optional[str], conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
            SELECT
                urls.id,
                user_id::text,
                domains.url as original_url,
                ($1 || '/' || short_code) AS short_url,
                short_code,
                clicks,
                qrcode_url,
                (p_hash IS NOT NULL) AS has_password,
                is_favorite,
                title,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            FROM 
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            WHERE
                user_id IS NULL AND
                domains.url_hash = decode(md5(TRIM($2)), 'hex') AND
                p_hash IS NULL AND
                title = $3 AND
                (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """,
        base_url,
        original_url,
        title
    )
    return dict(r) if r else None


async def get_user_url(original_url: str, base_url: str, user_id: str, title: Optional[str], conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
        SELECT
            urls.id,
            user_id::text,
            domains.url as original_url,
            ($1 || '/' || short_code) AS short_url,
            short_code,
            clicks,
            (p_hash IS NOT NULL) AS has_password,
            qrcode_url,
            is_favorite,
            title,
            TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
            TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
        FROM 
            urls
        JOIN
            domains ON domains.id = urls.domain_id
        WHERE
            user_id = $2 AND 
            domains.url_hash = decode(md5(TRIM($3)), 'hex') AND
            (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP) AND
            title = $4
        """,
        base_url,
        user_id,
        original_url,
        title
    )
    return dict(r) if r else None


async def set_url_qrcode(url_id: int, qrcode_url: str, conn: Connection):
    await conn.execute(
        """
            UPDATE
                urls
            SET
                qrcode_url = $1
            WHERE
                url_id = $2
        """,
        qrcode_url,
        url_id
    )


async def create_anonymous_url(url: URLCreate, base_url: str, conn: Connection):
    try:
        r = await conn.fetchrow(
            """
                INSERT INTO urls (
                    p_hash,
                    domain_id,
                    title,
                    expires_at
                )
                VALUES
                    (decode(md5(TRIM($1), 'hex')::bytea, $2, TRIM($3), $4)
                RETURNING
                    id,
                    user_id::text,
                    original_url,
                    ($5 || '/' || short_code) AS short_url,
                    short_code,
                    clicks,
                    qrcode_url,
                    (p_hash IS NOT NULL) AS has_password,
                    is_favorite,
                    title,
                    TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                    TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            """,
            url.password,
            await domains_table.get_domain_id(str(url.url), conn),
            url.title,
            url.expires_at,
            base_url
        )
        return dict(r) if r else None
    except asyncpg.exceptions.CheckViolationError as e:
        raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_400_BAD_REQUEST)
    except asyncpg.exceptions.UniqueViolationError as e:
        print(e) # short code collision (should be impossible)
        raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_409_CONFLICT)
    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def create_user_url(url: URLCreate, user: User, base_url: str, conn: Connection):        
    try:
        r = await conn.fetchrow(
            """
                INSERT INTO urls (
                    user_id,
                    p_hash,
                    domain_id,
                    expires_at,
                    is_favorite,
                    title
                )
                VALUES
                    ($1, decode(md5(TRIM($2), 'hex')::bytea, $3, $4, $5, $6)
                RETURNING
                    id,
                    user_id::text,
                    original_url,
                    ($7 || '/' || short_code) AS short_url,
                    short_code,
                    clicks,
                    qrcode_url,
                    (p_hash IS NOT NULL) AS has_password,
                    is_favorite,
                    title,
                    TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                    TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            """,
            user.id,
            url.password,
            await domains_table.get_domain_id(str(url.url), conn),
            url.expires_at,
            url.is_favorite,
            url.title,
            base_url
        )
        return dict(r) if r else None
    except asyncpg.exceptions.CheckViolationError as e:
        raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_400_BAD_REQUEST)
    except asyncpg.exceptions.UniqueViolationError as e:
        print(e) # short code collision (should be impossible)
        raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_409_CONFLICT)
    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_clicks(short_code: str, conn: Connection):
    await conn.execute("SELECT increment_url_clicks($1)", short_code)


async def get_user_urls(user_id: str, limit: int, offset: int, base_url: str, conn: Connection) -> tuple[int, list[dict]]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls WHERE user_id = $1", user_id)

    r = await conn.fetch(
        """
            SELECT
                urls.id,
                users.user_id::text,
                domains.url as original_url,
                ($1 || '/' || urls.short_code) AS short_url,
                urls.short_code,
                urls.clicks,
                urls.qrcode_url,
                (urls.p_hash IS NOT NULL) AS has_password,
                urls.is_favorite,
                urls.title,
                TO_CHAR(urls.created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(urls.expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            FROM
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            JOIN
                users ON users.url_id = urls.id
            WHERE
                users.id = $2
            ORDER BY
                urls.is_favorite DESC,
                urls.created_at DESC
            LIMIT
                $3
            OFFSET
                $4
        """,
        base_url,
        user_id,
        limit,
        offset        
    )
    
    return total, [dict(row) for row in r]


async def get_url_id_by_short_code(short_code: str, conn: Connection) -> int | None:
    return await conn.fetchval("SELECT short_code FROM urls WHERE short_code = TRIM($1)", short_code)


async def create_url_analytic(
    short_code: str,
    ip_address: str,
    country_code: Optional[str],
    city: Optional[str],
    user_agent: str,
    referer: str,
    device_type: str,
    browser: str,
    os: str,
    conn: Connection
):
    url_id: int | None = await get_url_id_by_short_code(short_code, conn)
    if url_id is None: return
    await conn.execute(
        """
            INSERT INTO url_analytics (
                url_id,
                ip_address,
                country_code,
                city,
                user_agent,
                referer,
                device_type,
                browser,
                os
            )
            VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        url_id,
        ip_address,
        country_code,
        city,
        user_agent,
        referer,
        device_type,
        browser,
        os
    )


async def delete_all_urls(conn: Connection):
    await conn.execute("DELETE FROM urls")


async def delete_expired_urls(conn: Connection) -> None:
    await conn.execute(
        """
            DELETE FROM 
                urls
            WHERE 
                expires_at IS NOT NULL AND 
                expires_at < NOW();
        """
    )


async def soft_delete_expired_urls(conn: Connection) -> None:
    await conn.execute(
        """
        UPDATE 
            urls
        SET 
            is_active = FALSE,
            updated_at = NOW()
        WHERE 
            expires_at IS NOT NULL AND 
            expires_at < NOW() AND 
            is_active = TRUE;
    """)