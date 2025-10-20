from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from src.db import get_db, db_count, db_version
from src.schemas.user import UserPagination, UseDelete
from src.schemas.urls import UrlBlackListCreate, UrlBlackListDelete, UrlBlacklistPagination
from src.schemas.log import LogPagination, RateLimitLogPagination
from src.schemas.admin import HealthReport
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


@router.get("/users", response_model=UserPagination)
async def get_users(
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_users(limit, offset, conn)


@router.delete("/users", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: UseDelete, conn: Connection = Depends(get_db)):
    return await admin_service.delete_user(user.user_id, conn)


@router.delete("/users/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_users(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_users(conn)


@router.get("/urls", status_code=status.HTTP_200_OK)
async def get_urls(
    request: Request, 
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await urls_service.get_urls(request, limit, offset, conn)


@router.delete("/urls/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_urls(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_urls(conn)


@router.delete("/urls/expired", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expired_urls(conn: Connection = Depends(get_db)):
    return await admin_service.delete_expired_urls(conn)


@router.delete("/urls/expired/soft", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_expired_urls(conn: Connection = Depends(get_db)):
    return await admin_service.soft_delete_expired_urls(conn)


@router.get("/report", status_code=status.HTTP_200_OK)
async def get_full_metrics_report():
    content = await perf_service.generate_full_report()
    return JSONResponse(content)


@router.get("/report/html", status_code=status.HTTP_200_OK)
async def get_full_metrics_report():
    return await perf_service.generate_metric_html_report()


## LOGS

@router.get("/logs", response_model=LogPagination)
async def get_logs(
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await log_service.get_logs(limit, offset, conn)


@router.get("/logs/ratelimit", response_model=RateLimitLogPagination)
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



# BLACKLIST

@router.get("/url/blacklist", response_model=UrlBlacklistPagination)
async def get_blacklist_urls(
    q: str = Query(default=None),
    limit: int = Query(default=64, ge=1, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_blacklist_urls(q, limit, offset, conn)


@router.post("/url/blacklist", status_code=status.HTTP_201_CREATED)
async def add_url_to_blacklist(
    url: UrlBlackListCreate,
    conn: Connection = Depends(get_db)
):
    await admin_service.add_to_blacklist_url(url, conn)


@router.delete("/url/blacklist", status_code=status.HTTP_204_NO_CONTENT)
async def remove_url_from_blacklist(
    url: UrlBlackListDelete, 
    conn: Connection = Depends(get_db)
):
    await admin_service.remove_url_from_blacklist(url, conn)
