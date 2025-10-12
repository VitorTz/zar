from fastapi import APIRouter, Depends
from asyncpg import Connection
from src.schemas.metrics import DashboardStats, PopularUrl, UrlAnalytic, UserStats
from src.schemas.user import User
from src.security import get_user_from_token
from src.db import get_db
from typing import List


router = APIRouter()


@router.get("/urls/popular", response_model=List[PopularUrl])
async def get_popular_urls(conn: Connection = Depends(get_db)):
    r = await conn.fetch(
        """
            SELECT
                *
            FROM
                v_popular_urls;
        """
    )
    return [dict(i) for i in r]


@router.get("/daily", response_model=List[UrlAnalytic])
async def get_daily_analytics(conn: Connection = Depends(get_db)):
    r = await conn.fetch("SELECT * FROM v_daily_analytics;")
    return [dict(i) for i in r]



@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(conn: Connection = Depends(get_db)):
    await conn.execute("SELECT * FROM refresh_dashboard_stats();")
    r = await conn.fetchrow(
        """
            SELECT
                *
            FROM
                mv_dashboard_stats;
        """
    )
    return dict(r)


@router.get("/user", response_model=UserStats)
async def get_user_stats(
    user: User = Depends(get_user_from_token), 
    conn: Connection = Depends(get_db)
):
    
    r = await conn.fetchrow("SELECT * FROM v_user_stats WHERE id = $1;", user.id)
    return dict(r) if r is not None else None