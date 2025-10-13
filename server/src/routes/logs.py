from fastapi import APIRouter, Query, Depends
from src.schemas.log import LogPagination, RateLimitLogPagination
from asyncpg import Connection
from src.db import get_db
from src.services import logs as log_service
from src.security import require_admin


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/logs", response_model=LogPagination)
async def get_logs(
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await log_service.get_logs(limit, offset, conn)


@router.get("/rate-limit-log", response_model=RateLimitLogPagination)
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

