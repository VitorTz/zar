from asyncpg import Connection
from fastapi.responses import JSONResponse
from src.schemas.user import User


async def get_urls_ordered_by_popularity(limit: int, offset: int, conn: Connection):
    r = await conn.fetchrow("SELECT COUNT(*) AS total FROM v_popular_urls;")
    total = dict(r)['total']

    r = await conn.fetch(
        """
            SELECT
                short_code,
                original_url,
                title,
                clicks,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(last_clicked_at, 'DD-MM-YYYY HH24:MI:SS') as last_clicked_at,
                unique_visitors,
                countries_reached
            FROM
                v_popular_urls
            LIMIT
                $1
            OFFSET
                $2;
        """,
        limit,
        offset
    )
    results = [dict(i) for i in r]
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }

    return JSONResponse(response)


async def get_daily_metrics(limit: int, offset: int, conn: Connection):
    r = await conn.fetchrow("SELECT COUNT(*) AS total FROM v_daily_analytics;")
    total = dict(r)['total']

    r = await conn.fetch("SELECT * FROM v_daily_analytics LIMIT $1 OFFSET $2;", limit, offset)
    results = [dict(i) for i in r]
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }

    return JSONResponse(response)


async def get_dashboard_metrics(conn: Connection) -> JSONResponse:
    await conn.execute("SELECT * FROM refresh_dashboard_stats();")
    r = await conn.fetchrow(
        """
            SELECT
                *
            FROM
                mv_dashboard_stats;
        """
    )
    result = dict(r)
    return JSONResponse(result)


async def get_user_stats(user: User, conn: Connection):
    r = await conn.fetchrow("SELECT * FROM v_user_stats WHERE id = $1;", user.id)
    return dict(r) if r is not None else None