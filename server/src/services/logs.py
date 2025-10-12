from fastapi import Request
from fastapi.responses import JSONResponse, Response
from src.tables import logs as logs_table
from src.perf.system_monitor import get_monitor
from src.db import get_db_pool
from asyncpg import Connection
from datetime import datetime
import traceback


async def log_and_build_response(
    request: Request,
    exc: Exception,
    error_level: str,
    status_code: int,
    detail: dict | str
) -> JSONResponse:
    get_monitor().increment_error()
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            
    conn = None
    try:
        pool = get_db_pool()
        if pool is not None:
            conn = await pool.acquire()
            await logs_table.log_error(
                error_level=error_level,
                message=str(exc),
                path=str(request.url.path),
                method=request.method,
                status_code=status_code,
                stacktrace=tb,
                conn=conn
            )
    except Exception as e:
        print(f"Failed to acquire DB connection for logging: {e}")
        await logs_table.log_error(
            error_level=error_level,
            message=str(exc),
            path=str(request.url.path),
            method=request.method,
            status_code=status_code,
            stacktrace=tb,
            conn=None
        )
    finally:
        if conn is not None:
            try:
                await pool.release(conn)
            except Exception as e:
                print(f"Failed to release DB connection: {e}")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": str(detail),
            "path": str(request.url.path),
            "timestamp": str(datetime.now())
        }
    )

async def get_logs(method: str | None, sort_by: str, sort_order: str, limit: int, offset: int, conn: Connection) -> JSONResponse:
    total, results = await logs_table.get_logs(method, sort_by, sort_order, limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return JSONResponse(content=response)


async def delete_logs(interval_minutes: int | None, conn: Connection) -> Response:
    deleted_logs = await logs_table.delete_logs(interval_minutes, conn)
    return JSONResponse(
        content={
            "deleted": deleted_logs
        }
    )


async def log_stats(conn: Connection) -> JSONResponse:
    return await logs_table.get_log_stats(conn)
