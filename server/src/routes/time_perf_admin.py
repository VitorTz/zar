from fastapi import APIRouter, Depends, Query
from typing import List
from src.security import require_admin
from src.db import get_db
from src.schemas.pagination import Pagination
from src.schemas.time_perf import TimePerfResponse, TimePerfStats, TimePerfGroupedStats
from src.services import time_perf as time_perf_service
from asyncpg import Connection


router = APIRouter(prefix="/time_perf", dependencies=[Depends(require_admin)], tags=["admin_time_perf"])


@router.get("/", response_model=Pagination[TimePerfResponse])
async def get_time_perf(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await time_perf_service.get_time_perf(limit, offset, conn)


@router.get("/stats", response_model=TimePerfStats)
async def get_time_perf_globals_stats(conn: Connection = Depends(get_db)):
    return await time_perf_service.get_time_perf_globals_stats(conn)


@router.get("/stats/grouped", response_model=List[TimePerfGroupedStats])
async def get_time_perf_grouped_stats(conn: Connection = Depends(get_db)):
    return await time_perf_service.get_time_perf_grouped_stats(conn)