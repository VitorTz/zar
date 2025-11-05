from src.tables import time_perf as time_perf_table
from src.schemas.pagination import Pagination
from src.schemas.time_perf import (
    TimePerfResponse, 
    TimePerfGroupedStats, 
    TimePerfStats
)
from typing import List
from asyncpg import Connection


async def get_time_perf(
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[TimePerfResponse]:
    return await time_perf_table.get_time_perf(limit, offset, conn)


async def get_time_perf_globals_stats(conn: Connection) -> TimePerfStats:
    return await time_perf_table.get_time_perf_globals_stats(conn)


async def get_time_perf_grouped_stats(conn: Connection) -> List[TimePerfGroupedStats]:
    return await time_perf_table.get_time_perf_grouped_stats(conn)


async def delete_time_perf(conn: Connection):
    await time_perf_table.delete_time_perf(conn)