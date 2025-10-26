from src.schemas.user import User
from src.schemas.urls import URLCreate, UrlRedirect, URLAdminResponse, URLResponse, UrlStats
from src.schemas.pagination import Pagination
from src.schemas.domain import Domain
from fastapi.exceptions import HTTPException
from fastapi import status, Request
from typing import Optional
from user_agents import parse
from src.globals import Globals
from asyncpg import Connection
import asyncpg


async def count_urls(conn: Connection) -> int:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls")
    return total


async def get_redirect_url(short_code: str, conn: Connection) -> Optional[UrlRedirect]:
    r = await conn.fetchrow(
        """
            SELECT
                urls.id,
                urls.p_hash,
                domains.url as original_url,
                urls.expires_at
            FROM
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            WHERE
                short_code = TRIM($1) AND
                is_active = TRUE

        """,
        short_code
    )
    return UrlRedirect(**dict(r)) if r else None


async def get_original_url(short_code: str, conn: Connection) -> Optional[str]:
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


async def get_url_id_by_short_code(short_code: str, conn: Connection) -> Optional[int]:
    return await conn.fetchval("SELECT id FROM urls WHERE short_code = $1", short_code)


async def get_url(short_code: str, base_url: str, conn: Connection) -> Optional[URLResponse]:
    r = await conn.fetchrow(
        """
            SELECT
                id,
                domains.id as domain_id,
                domains.url as original_url,
                short_code,
                clicks,
                title,
                is_favorite,
                (p_hash IS NOT NULL) AS has_password,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at
            FROM
                urls
            JOIN
                domains ON domains.id = urls.domain_id
            WHERE
                short_code = TRIM($1)
        """,
        short_code
    )
    return URLResponse(
        **dict(r),
        short_url=f"{base_url}/api/v1/{r['short_code']}"
    ) if r else None


async def get_url_pages(base_url: str, user_id: str | None, limit: int, offset: int, conn: Connection) -> Pagination[URLAdminResponse]:
    if user_id is None:
        total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls")
        rows = await conn.fetch(
            """
                SELECT
                    urls.id,
                    domains.id as domain_id,
                    domains.url as original_url,
                    urls.p_hash,
                    urls.short_code,
                    urls.clicks,
                    urls.title,
                    (urls.p_hash IS NOT NULL) AS has_password,
                    (FALSE) as is_favorite,
                    urls.created_at,
                    urls.expires_at
                FROM
                    urls
                JOIN
                    domains ON domains.id = urls.domain_id
                LIMIT
                    $1
                OFFSET 
                    $2
            """,
            limit,
            offset
        )        

        return Pagination[URLAdminResponse](
            total=total,
            limit=limit,
            offset=offset,
            results=[URLAdminResponse(**dict(row), short_url=f"{base_url}/api/v1/{row['short_code']}") for row in rows]
        )
    
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
                urls.id,
                user_urls.user_id,
                domains.id as domain_id,
                domains.url as original_url,
                urls.p_hash,
                urls.short_code,
                urls.clicks,
                urls.title,
                (urls.p_hash IS NOT NULL) AS has_password,
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
            LIMIT 
                $2
            OFFSET 
                $3
        """,
        user_id,
        limit,
        offset
    )
    return Pagination[URLAdminResponse](
        total=total,
        limit=limit,
        offset=offset,
        results=[URLAdminResponse(**dict(i), short_url=f"{base_url}/api/v1/{r['short_code']}") for i in r]
    )    



async def get_anonymous_url(domain: Domain, base_url: str, conn: Connection) -> Optional[URLResponse]:
    r = await conn.fetchrow(
        """
            SELECT 
                u.id,
                u.short_code,
                u.clicks,
                u.title,
                u.created_at,
                u.expires_at
            FROM 
                urls u
            JOIN 
                domains d ON d.id = u.domain_id
            LEFT JOIN 
                user_urls uu ON uu.url_id = u.id
            WHERE
                u.domain_id = $1
                AND uu.url_id IS NULL
                AND u.p_hash IS NULL
                AND u.expires_at IS NULL
                AND u.title IS NULL
                AND u.is_active = TRUE;
        """,
        domain.id
    )

    return URLResponse(
        **dict(r), 
        short_url=f"{base_url}/api/v1/{r['short_code']}",
        original_url=domain.url,
        has_password=False,
        domain_id=domain.id
    ) if r else None


async def get_user_url(domain: Domain, base_url: str, user_id: str, title: Optional[str], conn: Connection) -> Optional[URLResponse]:
    r = await conn.fetchrow(
        """
            SELECT
                urls.id,
                user_urls.user_id,
                urls.short_code,
                urls.clicks,
                (urls.p_hash IS NOT NULL) AS has_password,
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
                user_urls.user_id = $1 AND
                domains.id = $2 AND
                urls.title = $3 AND
                (urls.expires_at IS NULL OR urls.expires_at > CURRENT_TIMESTAMP) AND
                is_active = TRUE
        """,
        user_id,
        domain.id,
        title
    )

    return URLResponse(
        **dict(r),
        short_url=f"{base_url}/api/v1/{r['short_code']}",
        original_url=domain.url,
        title=title,
        domain_id=domain.id
    ) if r else None


async def create_anonymous_url(domain: Domain, url: URLCreate, base_url: str, conn: Connection) -> URLResponse:
    try:
        r = await conn.fetchrow(
            """
                INSERT INTO urls (
                    p_hash,
                    domain_id,
                    title,
                    expires_at
                )
                VALUES (
                    decode(md5(TRIM($1)), 'hex'),
                    $2,
                    TRIM($3),
                    $4
                )
                RETURNING
                    id,
                    short_code,
                    title,
                    (urls.p_hash IS NOT NULL) AS has_password,
                    created_at,
                    expires_at
            """,
            url.password,
            domain.id,
            url.title,
            url.expires_at
        )
    
        return URLResponse(
            **dict(r),
            original_url=domain.url,
            is_favorite=url.is_favorite,
            short_url=f"{base_url}/api/v1/{r['short_code']}",
            domain_id=domain.id
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
                        p_hash,
                        domain_id,
                        expires_at,
                        title
                    )
                    VALUES (
                        decode(md5(TRIM($1)), 'hex')::bytea, 
                        $2, 
                        $3, 
                        TRIM($4)
                    )
                    RETURNING
                        id,
                        short_code,
                        created_at
                """,
                url.password,
                domain.id,
                url.expires_at,
                url.title
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
                original_url=domain.url,
                expires_at=url.expires_at,
                has_password=url.password is not None,
                is_favorite=url.is_favorite or False,
                title=url.title,
                short_url=f"{base_url}/api/v1/{r['short_code']}",
                domain_id=domain.id
            )
    except asyncpg.exceptions.CheckViolationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid URL: {url.url}")
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"URL already exists: {url.url}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

async def update_clicks(url_id: int, conn: Connection):
    await conn.execute("SELECT increment_url_clicks($1)", url_id)


async def get_user_urls(
    user_id: str, 
    limit: int, 
    offset: int, 
    base_url: str, 
    conn: Connection
) -> Pagination[URLResponse]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM urls WHERE user_id = $1", user_id)

    rows = await conn.fetch(
        """
            SELECT
                urls.id,
                domains.id as domain_id,
                domains.url as original_url,
                urls.short_code,
                urls.clicks,
                (urls.p_hash IS NOT NULL) AS has_password,
                user_urls.is_favorite,
                urls.title,
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
                json_agg(DISTINCT browser) AS browsers,
                json_agg(DISTINCT os) AS operating_systems,
                json_agg(DISTINCT device_type) AS device_types,
                json_agg(DISTINCT country_code) AS countries
            FROM 
                url_analytics
            WHERE 
                url_id = $1
            GROUP BY 
                url_id;
        """,
        url_id
    )
    return UrlStats(**dict(r)) if r else None