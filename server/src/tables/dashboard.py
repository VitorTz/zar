from asyncpg import Connection


async def get_dashboard_data(conn: Connection) -> dict:
    await conn.execute("SELECT refresh_dashboard_stats()")
    r = await conn.fetchrow("SELECT * FROM mv_dashboard_stats")
    return dict(r)


async def get_daily_metrics(limit: int, offset: int, conn: Connection) -> tuple[int, list[dict[str]]]:
    rows = await conn.fetch(
        """
        SELECT 
            *, 
            COUNT(*) OVER() AS total_count
        FROM 
            v_daily_analytics
        ORDER BY 
            date DESC
        LIMIT
            $1 
        OFFSET 
            $2
        """,
        limit, offset
    )
    total = rows[0]['total_count'] if rows else 0
    return total, [dict(r) for r in rows]


async def get_urls_ordered_by_popularity(limit: int, offset: int, conn: Connection) -> tuple[int, list[dict[str]]]:
    rows = await conn.fetch(
        """
            SELECT
                short_code,
                original_url,
                title,
                clicks,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(last_clicked_at, 'DD-MM-YYYY HH24:MI:SS') as last_clicked_at,
                unique_visitors,
                countries_reached,
                COUNT(*) OVER() AS total_count
            FROM
                v_popular_urls
            LIMIT
                $1
            OFFSET
                $2
        """,
        limit,
        offset
    )

    total = rows[0]['total_count'] if rows else 0
    return total, [dict(r) for r in rows]