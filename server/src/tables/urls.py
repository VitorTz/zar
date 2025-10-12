from asyncpg import Connection
from src.util import generate_short_code, create_qrcode
from typing import Optional


async def count_urls(conn: Connection) -> int:
    r = await conn.fetchrow("SELECT COUNT(*) AS total FROM urls;")
    return dict(r)['total']


async def get_url(short_code: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
            SELECT
                id::text,
                original_url,
                short_code,
                clicks,
                qr_code_url,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at
            FROM
                urls
            WHERE
                short_code = $1;
        """,
        short_code.strip()
    )
    return dict(r) if r is not None else None


async def get_url_pages(base_url: str, limit: int, offset: int, conn: Connection) -> dict | None:
    r = await conn.fetch(
        """
            SELECT
                id::text,
                original_url,
                short_code,
                clicks,
                qr_code_url,
                ($3 || '/' || short_code) AS short_url,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at
            FROM
                urls
            LIMIT 
                $1
            OFFSET 
                $2;
        """,
        limit,
        offset,
        base_url
    )
    return [dict(i) for i in r]


async def get_url_from_original_url(original_url: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
            SELECT 
                id::text, 
                original_url, 
                short_code, 
                clicks,
                qr_code_url
            FROM 
                urls 
            WHERE 
                original_url = LOWER(TRIM($1));
        """,
        original_url
    )
    return dict(r) if r is not None else None


async def get_original_url_from_short_code(short_code: str, conn: Connection) -> str | None:
    r = await conn.fetchrow(
        """
            SELECT                
                original_url
            FROM 
                urls 
            WHERE 
                short_code = $1;
            """,
        short_code.strip()
    )
    return dict(r)['original_url'] if r is not None else None


async def create_url(original_url: str, conn: Connection) -> dict | None:
    qrcode_url = await create_qrcode(original_url)
    while True:
        try:
            r = await conn.fetchrow(
                """
                    INSERT INTO urls (
                        original_url,
                        short_code,
                        qr_code_url
                    )
                    VALUES
                        (LOWER(TRIM($1)), $2, $3)
                    RETURNING
                        id::text,
                        original_url,
                        short_code,
                        clicks,
                        qr_code_url;
                """,
                original_url,
                generate_short_code(),
                qrcode_url
            )
            return dict(r) if r is not None else None
        except Exception:
            pass
    



async def create_user_url(user_id: str, url_id: str, conn: Connection):
    await conn.execute(
        """
            INSERT INTO user_urls (
                user_id,
                url_id
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (user_id, url_id)
            DO NOTHING;
        """,
        user_id,
        url_id
    )


async def update_clicks(url_id: str, conn: Connection):
    await conn.execute(
        """
            UPDATE 
                urls
            SET
                clicks = clicks + 1
            WHERE
                id = $1;
        """,
        url_id
    )


async def get_user_urls(user_id: str, limit: int, offset: int, base_url: str, conn: Connection) -> tuple[int, list[dict]]:
    r = await conn.fetchrow("SELECT COUNT(*) AS total FROM user_urls WHERE user_id = $1;", user_id)
    total = r["total"]

    r = await conn.fetch(
        """
            SELECT
                urls.id::text,
                urls.original_url,
                urls.short_code,
                urls.clicks,
                qr_code_url,
                ($4 || '/' || urls.short_code) AS short_url
            FROM
                user_urls
            JOIN
                urls ON urls.id = user_urls.url_id
            WHERE
                user_urls.user_id = $1
            ORDER BY
                user_urls.is_favorite DESC, 
                urls.created_at DESC
            LIMIT
                $2
            OFFSET
                $3;
        """,
        user_id,
        limit,
        offset,
        base_url
    )

    results = [dict(row) for row in r]
    return total, results


async def create_url_analytic(
    url_id: str,
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
                ($1, $2, $3, $4, $5, $6, $7, $8, $9);
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
    await conn.execute("DELETE FROM urls;")