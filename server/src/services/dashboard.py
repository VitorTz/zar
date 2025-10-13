from asyncpg import Connection
from fastapi import status, Request
from src.schemas.dashboard import DashboardRefreshResponse, DashboardStats
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from src.schemas.user import User
from src.tables import dashboard
from src.tables import users as users_table
from decimal import Decimal
from src import util


async def get_urls_ordered_by_popularity(request: Request, limit: int, offset: int, conn: Connection):
    base_url: str = util.extract_base_url(request)
    total, results = await dashboard.get_urls_ordered_by_popularity(base_url, limit, offset, conn)
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
    total, results = await dashboard.get_daily_metrics(limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    
    return JSONResponse(response)


async def get_dashboard_stats(conn: Connection) -> JSONResponse:
    r = await conn.fetchrow(
        """
            SELECT 
                *
            FROM
                mv_dashboard_stats
            LIMIT 
                1
        """
    )
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard stats not available. Please refresh the materialized view."
        )
    
    stats_dict = dict(r)
    
    # Converter Decimal para float
    if isinstance(stats_dict.get('avg_clicks_per_url'), Decimal):
        stats_dict['avg_clicks_per_url'] = float(stats_dict['avg_clicks_per_url'])
    
    return DashboardStats(**stats_dict)


async def get_user_stats(user: User, conn: Connection):
    data: dict | None = await users_table.get_user_stats(user.id, conn)
    if data is None:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(data)


async def dashboard_health(conn: Connection):
    r = await conn.fetchrow(
       """
        SELECT 
            last_updated,
            EXTRACT(EPOCH FROM (NOW() - last_updated)) / 60 as minutes_since_update
        FROM mv_dashboard_stats
        LIMIT 1;
        """ 
    )
    
    if not r:
        return {
            "status": "unavailable",
            "message": "Dashboard stats not initialized",
            "action": "Run refresh endpoint to initialize"
        }
    
    minutes_old = float(r['minutes_since_update'])
    is_fresh = minutes_old <= 15
    
    return {
        "status": "healthy" if is_fresh else "stale",
        "last_updated": r['last_updated'],
        "minutes_since_update": round(minutes_old, 2),
        "is_fresh": is_fresh,
        "message": "Dashboard is up to date" if is_fresh else "Dashboard data is stale, consider refreshing"
    }


async def dashboard_summary(conn: Connection):
    r = await conn.fetchrow(
        """
        SELECT 
            total_urls,
            total_clicks,
            total_users,
            clicks_last_24h,
            clicks_last_7d,
            unique_visitors_24h,
            active_sessions,
            last_updated_formatted
        FROM 
            mv_dashboard_stats
        LIMIT 
            1;
        """
    )
    
    if not r:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard stats not available"
        )
    
    return dict(r)


async def dashboard_refresh(conn: Connection):
    r = await conn.fetchrow("SELECT * FROM refresh_dashboard_stats();")

    return DashboardRefreshResponse(
        success=True,
        execution_time_ms=float(r['execution_time_ms']),
        last_updated=r['last_updated'],
        message=f"Dashboard stats refreshed successfully in {r['execution_time_ms']}ms"
    )