from asyncpg import Connection
from src.util import generate_short_code
from src.schemas.user import User
from src.schemas.urls import URLCreate
from src.security import hash_password
from fastapi.exceptions import HTTPException
from fastapi import status
from typing import Optional
import json
import asyncpg


async def count_urls(conn: Connection) -> int:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls")
    return total


async def get_original_url(short_code: str, conn: Connection) -> str | None:
    r = await conn.fetchrow(
        "SELECT original_url FROM urls WHERE short_code = TRIM($1)",
        short_code
    )
    return r["original_url"] if r else None


async def get_url(short_code: str, base_url: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
        SELECT
            user_id::text,
            original_url,
            ($1 || '/' || short_code) AS short_url,
            short_code,
            clicks,
            qrcode_url,
            is_favorite,
            TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
            TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
        FROM
            urls
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


async def get_url_pages(base_url: str, limit: int, offset: int, conn: Connection) -> tuple[int, list[dict]]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls")    

    r = await conn.fetch(
        """
            SELECT
                user_id::text,
                original_url,
                ($1 || '/' || short_code) AS short_url,
                short_code,
                clicks,
                qrcode_url,
                is_favorite,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            FROM
                urls
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


async def get_anonymous_url(original_url: str, base_url: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
            SELECT
                user_id::text,
                original_url,
                ($1 || '/' || short_code) AS short_url,
                short_code,
                clicks,
                qrcode_url,
                is_favorite,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            FROM 
                urls
            WHERE
                user_id IS NULL AND 
                original_url = TRIM($2)
        """,
        base_url,
        original_url
    )
    return dict(r) if r else None


async def get_user_url(original_url: str, base_url: str, user_id: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
        SELECT
            user_id::text,
            original_url,
            ($1 || '/' || short_code) AS short_url,
            short_code,
            clicks,
            qrcode_url,
            is_favorite,
            TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
            TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
        FROM 
            urls
        WHERE
            user_id = $2 AND 
            original_url = TRIM($3)
        """,
        base_url,
        user_id,
        original_url
    )
    return dict(r) if r else None


async def set_url_qrcode(short_code: str, qrcode_url: str, conn: Connection):
    await conn.execute(
        """
            UPDATE
                urls
            SET
                qrcode_url = $1
            WHERE
                short_code = TRIM($2)
        """,
        qrcode_url,
        short_code
    )


async def create_anonymous_url(url: URLCreate, base_url: str, conn: Connection):
    while True:
        try:
            r = await conn.fetchrow(
                """
                    INSERT INTO urls (
                        short_code,
                        original_url                        
                    )
                    VALUES
                        ($1, LOWER(TRIM($2)))
                    RETURNING
                        user_id::text,
                        original_url,
                        ($3 || '/' || short_code) AS short_url,
                        short_code,
                        clicks,
                        qrcode_url,
                        is_favorite,
                        TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                        TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
                """,
                generate_short_code(),
                str(url.url),
                base_url
            )
            return dict(r) if r else None
        except asyncpg.exceptions.CheckViolationError as e:
            raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_400_BAD_REQUEST)
        except asyncpg.exceptions.UniqueViolationError as e:
            pass # short code collision
        except Exception as e:
            raise HTTPException(detail=f"{e}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def create_user_url(url: URLCreate, user: User, base_url: str, conn: Connection):
    while True:
        try:
            r = await conn.fetchrow(
                """
                    INSERT INTO urls (
                        short_code,
                        user_id,
                        p_hash,
                        original_url,
                        expires_at,
                        is_favorite
                    )
                    VALUES
                        ($1, $2, $3, LOWER(TRIM($4)), $5, $6)
                    RETURNING
                        user_id::text,
                        original_url,
                        ($7 || '/' || short_code) AS short_url,
                        short_code,
                        clicks,
                        qrcode_url,
                        is_favorite,
                        TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                        TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
                """,
                generate_short_code(),
                user.id,
                hash_password(url.password),
                str(url.url),
                url.expires_at,
                url.is_favorite,
                base_url
            )
            return dict(r) if r else None
        except asyncpg.exceptions.CheckViolationError as e:
            raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_400_BAD_REQUEST)
        except asyncpg.exceptions.UniqueViolationError as e:
            pass # short code collision
        except Exception as e:
            raise HTTPException(detail=f"{e}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_clicks(short_code: str, conn: Connection):
    await conn.execute("SELECT increment_url_clicks($1)", short_code)


async def get_user_urls(user_id: str, limit: int, offset: int, base_url: str, conn: Connection) -> tuple[int, list[dict]]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls WHERE user_id = $1", user_id)

    r = await conn.fetch(
        """
            SELECT
                user_id::text,
                urls.original_url,
                ($1 || '/' || urls.short_code) AS short_url,
                urls.short_code,
                urls.clicks,
                urls.qrcode_url,
                urls.is_favorite,
                TO_CHAR(urls.created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(urls.expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            FROM
                urls
            JOIN
                users ON urls.user_id = users.id
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

    results = [dict(row) for row in r]
    return total, results


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
    await conn.execute(
        """
            INSERT INTO url_analytics (
                short_code,
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
        short_code,
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