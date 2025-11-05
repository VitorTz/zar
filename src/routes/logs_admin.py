from fastapi import APIRouter, Depends, Query
from typing import Optional, Literal
from src.security import require_admin
from src.db import get_db
from src.schemas.pagination import Pagination
from src.schemas.log import Log, RateLimitViolation, DeletedLogs
from src.services import logs as log_service
from asyncpg import Connection


router = APIRouter(prefix="/logs", dependencies=[Depends(require_admin)], tags=["admin_logs"])


@router.get("/", response_model=Pagination[Log])
async def get_logs(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await log_service.get_logs(limit, offset, conn)


@router.delete("/", response_model=DeletedLogs)
async def delete_logs(
    interval_minutes: Optional[int] = Query(default=None),
    method: Optional[Literal["GET", "PUT", "POST", "DELETE"]] = Query(default=None),
    conn: Connection = Depends(get_db)
):
    return await log_service.delete_logs(interval_minutes, method, conn)


@router.get("/ratelimit", response_model=Pagination[RateLimitViolation])
async def get_rate_limit_logs(
    ip_address: Optional[str] = Query(default=None),
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