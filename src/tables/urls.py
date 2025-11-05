from src.schemas.user import User
from src.schemas.urls import URLCreate, UrlRedirect, URLResponse, UrlStats, UserURLResponse
from src.schemas.pagination import Pagination
from src.schemas.domain import Domain
from fastapi.exceptions import HTTPException
from fastapi import status, Request
from typing import Optional
from user_agents import parse
from src.globals import Globals
from src.constants import Constants
from asyncpg import Connection
import asyncpg
import json


async def url_exists(url_id: int, conn: Connection) -> bool:
    r = await conn.fetchval("SELECT id FROM urls WHERE id = $1", url_id)
    return r is not None


async def user_has_access_to_url(user_id: str, url_id: int, conn: Connection) -> bool:
    result = await conn.fetchval(
        """
        SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN TRUE
                WHEN COUNT(*) FILTER (WHERE user_id = $2) > 0 THEN TRUE  -- specific user has access
                ELSE FALSE
            END AS has_access
        FROM user_urls
        WHERE url_id = $1;
        """,
        url_id,
        user_id,
    )

    return bool(result)


async def user_url_exists(user_id: str, url_id: int, conn: Connection) -> bool:
    r = await conn.fetchval(
        "SELECT id FROM user_urls WHERE user_id = $1 AND url_id = $2", 
        user_id,
        url_id
    )
    return r is not None


async def get_redirect_url(short_code: str, conn: Connection) -> Optional[UrlRedirect]:
    r = await conn.fetchrow(
        """
            SELECT
                urls.id,
                urls.original_url                
            FROM
                urls
            WHERE
                short_code = TRIM($1)
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
    total: int = await conn.fetchval("SELECT COUNT(*) FROM urls")    
    rows = await conn.fetch(
        """
        SELECT
            u.id,
            u.title,
            u.descr,
            u.domain_id,
            uu.user_id,
            u.original_url,
            u.short_code,
            u.clicks,
            COALESCE(uu.is_favorite, FALSE) AS is_favorite,
            u.created_at            
        FROM 
            urls u
        LEFT JOIN (
            SELECT DISTINCT ON (url_id) *
            FROM 
                user_urls
            ORDER BY 
                url_id, 
                id DESC
        ) uu ON uu.url_id = u.id
        ORDER BY 
            u.id
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
        results=[
            URLResponse(
                **dict(row),
                short_url=f"{base_url}/{row['short_code']}"
            )
            for row in rows
        ]
    )


async def create_url(
    domain: Domain,
    url: URLCreate,
    user: Optional[User],
    base_url: str,
    conn: Connection
) -> URLResponse:
    try:
        async with conn.transaction():
            r = await conn.fetchrow(
                """
                    INSERT INTO urls (
                        domain_id,
                        original_url,
                        original_url_hash,
                        title,
                        descr
                    )
                    VALUES (
                        $1, 
                        $2,
                        decode(md5(TRIM($2)), 'hex'),
                        $3,
                        $4                        
                    )
                    RETURNING
                        id,
                        domain_id,
                        title,
                        descr,
                        short_code,
                        original_url,
                        created_at                        
                """,
                domain.id,
                str(url.url),
                url.title,
                url.descr
            )
            
            if user:
                await conn.execute(
                    """
                        INSERT INTO user_urls (
                            url_id,
                            user_id,
                            is_favorite
                        )
                        VALUES 
                            ($1, $2, $3)
                        ON CONFLICT 
                        DO NOTHING
                    """,
                    r["id"],
                    user.id,
                    url.is_favorite or False
                )

        return URLResponse(
            **dict(r),
            user_id=user.id if user else None,
            is_favorite=url.is_favorite or False,
            short_url=f"{base_url}/{r['short_code']}"
        )
    except asyncpg.exceptions.CheckViolationError:        
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid URL: {url.url}")
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"URL already exists: {url.url}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def update_url_clicks(url_id: int, conn: Connection):
    await conn.execute("SELECT increment_url_clicks($1)", url_id)


async def get_user_urls(
    user_id: str, 
    limit: int, 
    offset: int, 
    base_url: str, 
    conn: Connection
) -> Pagination[UserURLResponse]:
    total: int = await conn.fetchval(
        """
            SELECT 
                COUNT(*) AS total 
            FROM 
                user_urls
            JOIN
                urls ON urls.id = user_urls.url_id
            WHERE 
                user_id = $1
        """, 
        user_id
    )

    rows = await conn.fetch(
        """
            SELECT
                urls.id,
                domains.id AS domain_id,
                urls.title,
                urls.descr,
                urls.original_url,
                urls.short_code,
                urls.clicks,
                user_urls.is_favorite,
                urls.created_at,
                COALESCE(
                    jsonb_agg(
                        DISTINCT jsonb_build_object(
                            'id', url_tags.id,
                            'name', url_tags.name,
                            'descr', url_tags.descr,
                            'color', url_tags.color,
                            'user_id', url_tags.user_id,
                            'created_at', url_tags.created_at
                        )
                    ) FILTER (WHERE url_tags.id IS NOT NULL),
                    '[]'::jsonb
                ) AS tags
            FROM
                user_urls
            JOIN
                urls ON urls.id = user_urls.url_id
            JOIN
                domains ON domains.id = urls.domain_id
            LEFT JOIN
                url_tag_relations utr ON utr.url_id = urls.id
            LEFT JOIN
                url_tags ON url_tags.id = utr.tag_id
            WHERE
                user_urls.user_id = $1
            GROUP BY
                urls.id, domains.id, user_urls.is_favorite, user_urls.id
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

    rows = [dict(row) for row in rows]
    for row in rows:        
        row['tags'] = json.loads(row["tags"])

    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[
            UserURLResponse(**row, short_url=f"{base_url}/{row['short_code']}", user_id=user_id) for row in rows
        ]
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
    if ip_address:
        try:
            response = Globals.geoip_reader.get_all(ip_address)
            country_code = response.country_short if response.country_short and response.country_short.strip() != '-' else None
        except Exception as e:
            print(e)
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

    if not r: return None

    data = dict(r)
    for key in ("browsers", "operating_systems", "device_types", "countries"):
        val = data.get(key)
        if isinstance(val, str):
            try:
                data[key] = [x for x in json.loads(val) if x]
            except json.JSONDecodeError:
                data[key] = []
    return UrlStats(**data)


async def delete_url(url_id: int, conn: Connection):
    await conn.execute("DELETE FROM urls WHERE id = $1", url_id)