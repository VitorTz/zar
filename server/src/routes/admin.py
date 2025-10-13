
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from src.db import get_db, db_count, db_version
from src.schemas.user import UserPagination, UseDelete
from src.schemas.urls import UrlPagination
from src.schemas.admin import HealthReport
from src.schemas.log import LogPagination, RateLimitLogPagination
from src.security import require_admin
from src.services import admin as admin_service
from src.services import urls as urls_service
from src.services import logs as log_service
from src.services import perf as perf_service
from datetime import datetime
from asyncpg import Connection
from src.perf.system_monitor import get_monitor


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/health", response_model=HealthReport)
async def health_check(conn: Connection = Depends(get_db)):
    version: str = await db_version(conn)
    total_urls: int = await db_count("urls", conn)
    monitor = get_monitor()    
    return JSONResponse(
        content={
            "status": "healthy",
            "database": "connected",
            "postgres_version": version,
            "total_urls": total_urls,
            "now": str(datetime.now()),
            "memory": monitor.get_memory_info(),
            "cpu": monitor.get_cpu_info(),
            "disk": monitor.get_disk_info()
        }
    )


@router.get("/logs", response_model=LogPagination)
async def get_logs(
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_logs(limit, offset, conn)


@router.get("/logs/rate", response_model=RateLimitLogPagination)
async def get_rate_limit_logs(
    ip_address: str | None = Query(default=None),
    min_attempts: int = Query(default=10, ge=0),
    hours: int = Query(default=10, ge=0),
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await log_service.get_rate_limit_violations(
        hours, 
        min_attempts, 
        limit, 
        offset, 
        conn, 
        ip_address
    )


@router.get("/users", response_model=UserPagination)
async def get_users(
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_users(limit, offset, conn)


@router.delete("/users")
async def delete_user(user: UseDelete, conn: Connection = Depends(get_db)):
    return await admin_service.delete_user(user.user_id, conn)


@router.delete("/users/all")
async def delete_all_users(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_users(conn)


@router.get("/urls", response_model=UrlPagination)
async def get_urls(
    request: Request, 
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await urls_service.get_urls(request, limit, offset, conn)


@router.delete("/urls/all")
async def delete_all_urls(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_urls(conn)


@router.get("/report/full")
async def get_full_metrics_report():
    report: dict = await perf_service.generate_full_report()
    return JSONResponse(report)


@router.get("/report/html")
async def get_full_metrics_report():
    return await perf_service.generate_metric_html_report()