from src.schemas.metrics import DashboardStats, UrlAnalyticPagination, UserStats
from src.schemas.user import User
from src.schemas.urls import UrlPopularPagination
from src.services import metrics as metrics_service
from src.security import get_user_from_token
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from asyncpg import Connection
from src.services import perf
from src.db import get_db


router = APIRouter()


@router.get("/urls/popular", response_model=UrlPopularPagination)
async def get_popular_urls(
    limit: int = Query(default=64, le=64, ge=1),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await metrics_service.get_urls_ordered_by_popularity(limit, offset, conn)


@router.get("/daily", response_model=UrlAnalyticPagination)
async def get_daily_analytics(
    limit: int = Query(default=64, le=64, ge=1),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await metrics_service.get_daily_metrics(limit, offset, conn)


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(conn: Connection = Depends(get_db)):
    return await metrics_service.get_dashboard_metrics(conn)


@router.get("/user", response_model=UserStats)
async def get_user_stats(
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await metrics_service.get_user_stats(user, conn)