from src.schemas.time_perf import TimePerfCreate, TimePerfResponse, TimePerfStats, TimePerfGroupedStats
from src.schemas.pagination import Pagination
from typing import List, Optional
from asyncpg import Connection


async def create_time_perf(time_perf: TimePerfCreate, conn: Connection):
    await conn.execute(
        """
            INSERT INTO time_perf (
                perf_type,
                perf_subtype,
                execution_time,
                notes
            )
            VALUES
                ($1, $2, $3, $4)
        """,
        time_perf.perf_type,
        time_perf.perf_subtype,
        time_perf.execution_time,
        time_perf.notes
    )


async def get_time_perf(limit: int, offset: int, conn: Connection) -> Pagination[TimePerfCreate]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM time_perf")
    rows = await conn.fetch("SELECT * FROM time_perf LIMIT $1 OFFSET $2", limit, offset)
    return Pagination(
        total=total,
        offset=offset,
        limit=limit,
        results=[TimePerfResponse(**dict(row)) for row in rows]
    )


async def get_time_perf_globals_stats(conn: Connection) -> TimePerfStats:
    row = await conn.fetchrow(
        """
            SELECT 
                COUNT(*) AS total_records,
                COALESCE(AVG(execution_time), 0::FLOAT) AS avg_exec_time,
                COALESCE(MIN(execution_time), 0::FLOAT) AS min_exec_time,
                COALESCE(MAX(execution_time), 0::FLOAT) AS max_exec_time
            FROM 
                time_perf
        """
    )
    return TimePerfStats(**dict(row))


async def get_time_perf_grouped_stats(conn: Connection) -> List[TimePerfGroupedStats]:
    rows = await conn.fetch(
        """
            SELECT 
                perf_type,
                perf_subtype,
                COUNT(*) AS count,
                AVG(execution_time) AS avg_exec_time,
                MIN(execution_time) AS min_exec_time,
                MAX(execution_time) AS max_exec_time
            FROM 
                time_perf
            GROUP BY 
                perf_type, 
                perf_subtype
            ORDER BY 
                avg_exec_time DESC
        """
    )
    return [TimePerfGroupedStats(**dict(row)) for row in rows]


async def delete_time_perf(conn: Connection):
    await conn.execute("DELETE FROM time_perf")