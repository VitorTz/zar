from src.schemas.dashboard import DashboardStats, DashboardRefreshResponse
from fastapi import APIRouter, Depends, status, Request, Query
from src.schemas.urls import UrlAnalyticPagination, UrlPopularPagination
from src.db import get_db
from asyncpg import Connection
from src.services import dashboard as dashboard_service
from src.security import require_admin


router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardStats,
    status_code=status.HTTP_200_OK,
    summary="Obter estatísticas do dashboard",
    description="Retorna todas as estatísticas agregadas do dashboard a partir da materialized view"
)
async def get_dashboard_stats(request: Request, conn: Connection = Depends(get_db)):
    return await dashboard_service.get_dashboard_stats(request, conn)


@router.post(
    "/refresh",
    response_model=DashboardRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar materialized view do dashboard",
    description="Força atualização da materialized view com estatísticas mais recentes"
)
async def refresh_dashboard_stats(conn: Connection = Depends(get_db), is_admin: bool = Depends(require_admin)):
    return await dashboard_service.dashboard_refresh(conn)


@router.get(
    "/stats/summary",
    status_code=status.HTTP_200_OK,
    summary="Obter resumo simplificado do dashboard",
    description="Retorna apenas as métricas principais do dashboard"
)
async def get_dashboard_summary(conn: Connection = Depends(get_db)):    
    return await dashboard_service.dashboard_summary(conn)
                

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Verificar status do dashboard",
    description="Verifica se a materialized view está disponível e atualizada"
)
async def dashboard_health(conn: Connection = Depends(get_db), is_admin: bool = Depends(require_admin)):    
    return await dashboard_service.dashboard_health(conn)


@router.get("/popular/urls", response_model=UrlPopularPagination)
async def get_popular_urls(
    request: Request,
    limit: int = Query(default=10, le=64, ge=1),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await dashboard_service.get_urls_ordered_by_popularity(request, limit, offset, conn)


@router.get("/daily", response_model=UrlAnalyticPagination)
async def get_daily_analytics(
    limit: int = Query(default=64, le=64, ge=1),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    
    return await dashboard_service.get_daily_metrics(limit, offset, conn)
