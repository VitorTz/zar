from src.schemas.user import User
from src.schemas.urls import URLCreate, UrlRedirect, URLResponse, UrlStats
from src.schemas.pagination import Pagination
from src.schemas.domain import Domain
from fastapi.exceptions import HTTPException
from fastapi import status, Request
from typing import Optional
from user_agents import parse
from src.globals import Globals
from asyncpg import Connection
import asyncpg
import json


async def url_exists(url_id: int, conn: Connection) -> bool:
    r = await conn.fetchval("SELECT id FROM urls WHERE id = $1", url_id)
    return r is not None


async def get_redirect_url(short_code: str, conn: Connection) -> Optional[UrlRedirect]:
    r = await conn.fetchrow(
        """
            SELECT
                urls.id,
                urls.original_url,
                urls.expires_at
            FROM
                urls
            WHERE
                short_code = TRIM($1) AND
                is_active = TRUE
        """,
        short_code
    )
    return UrlRedirect(**dict(r)) if r else None


async def get_url_id_by_short_code(short_code: str, conn: Connection) -> Optional[int]:
    return await conn.fetchval(
        """
            SELECT 
                id 
            FROM 
                urls 
            WHERE 
                short_code = TRIM($1)
        """, 
        short_code
    )


async def get_url_id(short_code: str, conn: Connection) -> Optional[int]:
    url_id: Optional[int] = await conn.fetchval(
        """
            SELECT
                urls.id,
            FROM
                urls
            WHERE
                short_code = TRIM($1)
        """,
        short_code
    )
    return url_id
    


async def get_urls(base_url: str, limit: int, offset: int, conn: Connection) -> Pagination[URLResponse]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls")
    rows = await conn.fetch(
        """
            SELECT
                urls.id,
                urls.domain_id,
                urls.original_url,
                urls.original_url_hash,
                user_urls.user_id,
                urls.short_code,
                urls.clicks,
                COALESCE(user_urls.is_favorite, FALSE) AS is_favorite,
                urls.created_at,
                urls.expires_at
            FROM 
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            LEFT JOIN
                user_urls ON user_urls.url_id = urls.id                            
            ORDER BY 
                urls.created_at DESC
        """
    )
    
    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[URLResponse(**dict(row), short_url=f"{base_url}/api/v1/{row['short_code']}") for row in rows]
    )


async def get_anonymous_url(domain: Domain, base_url: str, url: URLCreate, conn: Connection) -> Optional[URLResponse]:
    r = await conn.fetchrow(
        """
            SELECT 
                urls.id,
                urls.domain_id,
                urls.original_url,
                urls.short_code,
                urls.clicks,
                urls.created_at,
                urls.expires_at
            FROM 
                urls
            JOIN 
                domains ON domains.id = urls.domain_id
            LEFT JOIN 
                user_urls ON user_urls.url_id = urls.id
            WHERE
                urls.domain_id = $1
                AND urls.original_url_hash = decode(md5(TRIM($2)), 'hex')
                AND user_urls.url_id IS NULL
                AND urls.expires_at IS NULL
                AND urls.is_active = TRUE
        """,
        domain.id,
        str(url.url)
    )

    return URLResponse(
        **dict(r), 
        short_url=f"{base_url}/api/v1/{r['short_code']}"
    ) if r else None


async def get_user_url(domain: Domain, base_url: str, url: URLCreate, user_id: str, conn: Connection) -> Optional[URLResponse]:
    r = await conn.fetchrow(
        """
            SELECT
                urls.id,
                urls.domain_id,
                user_urls.user_id,
                urls.original_url,
                urls.short_code,
                urls.clicks,
                user_urls.is_favorite,
                urls.created_at,
                urls.expires_at
            FROM 
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            JOIN
                user_urls ON user_urls.url_id = urls.id AND user_urls.user_id = $1
            WHERE
                urls.original_url_hash = decode(md5(TRIM($2)), 'hex')
                AND domains.id = $3
                AND urls.expires_at IS NULL
                AND urls.is_active = TRUE
                AND (urls.expires_at IS NULL OR urls.expires_at = $4::TIMESTAMPTZ)
        """,
        user_id,
        str(url.url),
        domain.id,
        url.expires_at
    )

    return URLResponse(
        **dict(r),
        short_url=f"{base_url}/api/v1/{r['short_code']}"
    ) if r else None


async def get_url_if_exists(domain: Domain, url: URLCreate, base_url: str, user: Optional[User], conn: Connection) -> URLResponse:
    if user: return await get_user_url(domain, base_url, url, user.id, conn)
    return await get_anonymous_url(domain, base_url, url, conn)


async def create_anonymous_url(domain: Domain, url: URLCreate, base_url: str, conn: Connection) -> URLResponse:
    try:
        r = await conn.fetchrow(
            """
                INSERT INTO urls (
                    domain_id,
                    original_url,
                    original_url_hash,
                    expires_at
                )
                VALUES (
                    $1,                    
                    $2,
                    decode(md5(TRIM($2)), 'hex'),
                    $3
                )
                RETURNING
                    id,
                    domain_id,
                    short_code,
                    original_url,
                    created_at,
                    expires_at
            """,
            domain.id,
            str(url.url),
            url.expires_at
        )
    
        return URLResponse(
            **dict(r),
            short_url=f"{base_url}/api/v1/{r['short_code']}"
        )
    except asyncpg.exceptions.CheckViolationError:
        raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_400_BAD_REQUEST)
    except asyncpg.exceptions.UniqueViolationError as e:
        raise HTTPException(detail=f"Invalid url! {url.url}", status_code=status.HTTP_409_CONFLICT)
    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def create_user_url(
    domain: Domain,
    url: URLCreate,
    user: User,
    base_url: str,
    conn: Connection
) -> URLResponse:
    if user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID is required.")
    
    try:
        async with conn.transaction():
            r = await conn.fetchrow(
                """
                    INSERT INTO urls (
                        domain_id,
                        original_url,
                        original_url_hash,
                        expires_at
                    )
                    VALUES (
                        $1, 
                        $2,
                        decode(md5(TRIM($2)), 'hex'),
                        $3
                    )
                    RETURNING
                        id,
                        domain_id,
                        short_code,
                        original_url,
                        created_at,
                        expires_at
                """,
                domain.id,
                str(url.url),
                url.expires_at
            )

            await conn.execute(
                """
                    INSERT INTO user_urls (
                        url_id,
                        user_id,
                        is_favorite
                    )
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                """,
                r["id"],
                user.id,
                url.is_favorite or False
            )

            return URLResponse(
                **dict(r),
                user_id=user.id,
                is_favorite=url.is_favorite or False,
                short_url=f"{base_url}/api/v1/{r['short_code']}"
            )
    except asyncpg.exceptions.CheckViolationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid URL: {url.url}")
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"URL already exists: {url.url}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

async def create_url(
    domain: Domain,
    url: URLCreate,
    user: Optional[User],
    base_url: str,
    conn: Connection
) -> URLResponse:
    if user:
        return await create_user_url(domain, url, user, base_url, conn)
    return await create_anonymous_url(domain, url, base_url, conn)


async def update_url_clicks(url_id: int, conn: Connection):
    await conn.execute("SELECT increment_url_clicks($1)", url_id)


async def get_user_urls(
    user_id: str, 
    limit: int, 
    offset: int, 
    base_url: str, 
    conn: Connection
) -> Pagination[URLResponse]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM user_urls WHERE user_id = $1", user_id)

    rows = await conn.fetch(
        """
            SELECT
                urls.id,
                domains.id as domain_id,
                urls.original_url,
                urls.short_code,
                urls.clicks,
                user_urls.is_favorite,
                urls.created_at,
                urls.expires_at
            FROM
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            JOIN
                user_urls ON user_urls.url_id = urls.id
            WHERE
                user_urls.user_id = $1
            ORDER BY
                user_urls.is_favorite DESC,
                user_urls.id DESC
            LIMIT
                $2
            OFFSET
                $3
        """,
        user_id,
        limit,
        offset        
    )

    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[URLResponse(**dict(row), short_url=f"{base_url}/api/v1/{row['short_code']}", user_id=user_id) for row in rows]
    )


async def create_url_analytic(
    url_id: int,
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


async def add_click_event(url_id: int, request: Request, conn: Connection):
    user_agent_string = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_string)
    
    ip_address = request.client.host
    
    # GEO
    country_code = None
    city = None
    if Globals.geoip_reader and ip_address:
        try:
            response = Globals.geoip_reader.city(ip_address)
            country_code = response.country.iso_code
            city = response.city.name
        except Exception:
            pass
    
    if user_agent.is_mobile:
        device_type = 'mobile'
    elif user_agent.is_tablet:
        device_type = 'tablet'
    elif user_agent.is_pc:
        device_type = 'desktop'
    elif user_agent.is_bot:
        device_type = 'bot'
    else:
        device_type = 'unknown'

    await conn.execute("SELECT increment_url_clicks($1)", url_id)
    await create_url_analytic(
        url_id,
        ip_address,
        country_code,
        city,
        user_agent_string[:255] if user_agent_string else None,
        request.headers.get("referer"),
        device_type,
        user_agent.browser.family,
        user_agent.os.family,
        conn
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
            is_active = FALSE            
        WHERE 
            expires_at IS NOT NULL AND 
            expires_at < NOW() AND 
            is_active = TRUE;
    """)
    

async def delete_unsafe_urls(conn: Connection):
    await conn.execute(
        """
        DELETE FROM 
            urls
        USING 
            domains
        WHERE 
            domains.id = urls.domain_id AND
            domains.is_secure = FALSE
        """
    )


async def delete_urls_by_domain(domain: Domain, conn: Connection) -> None:
    await conn.execute(
        """
        DELETE FROM
            urls
        WHERE
            domain_id = $1
        """,
        domain.id
    )


async def get_url_stats(url_id: int, conn: Connection) -> Optional[UrlStats]:
    r = await conn.fetchrow(
        """
            SELECT 
                url_id,
                COUNT(*) AS total_clicks,
                COUNT(DISTINCT ip_address) AS unique_visitors,
                MIN(clicked_at) AS first_click,
                MAX(clicked_at) AS last_click,
                COUNT(*) FILTER (WHERE DATE(clicked_at) = CURRENT_DATE) AS clicks_today,
                COALESCE(jsonb_agg(DISTINCT browser), '[]'::jsonb) AS browsers,
                COALESCE(jsonb_agg(DISTINCT os), '[]'::jsonb) AS operating_systems,
                COALESCE(jsonb_agg(DISTINCT device_type), '[]'::jsonb) AS device_types,
                COALESCE(jsonb_agg(DISTINCT country_code), '[]'::jsonb) AS countries
            FROM 
                url_analytics
            WHERE 
                url_id = $1
            GROUP BY 
                url_id;
        """,
        url_id
    )

    if not r:
        return None

    data = dict(r)
    for key in ("browsers", "operating_systems", "device_types", "countries"):
        val = data.get(key)
        if isinstance(val, str):
            try:
                data[key] = [x for x in json.loads(val) if x]
            except json.JSONDecodeError:
                data[key] = []
    return UrlStats(**data)