from fastapi import Request
from fastapi.responses import JSONResponse, Response
from src.tables import logs as logs_table
from src.perf.system_monitor import get_monitor
from src.db import get_db_pool
from asyncpg import Connection
from datetime import datetime, timezone, timedelta
from src.constants import Constants
import traceback
from typing import Literal


async def log_and_build_response(
    request: Request,
    exc: Exception,
    error_level: Literal['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
    status_code: int,
    detail: dict | str
) -> JSONResponse:
    get_monitor().increment_error()
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        
    metadata = {
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "referer": request.headers.get("referer"),
        "content_type": request.headers.get("content-type"),            
        "query_params": dict(request.query_params) if request.query_params else None,
        "path_params": dict(request.path_params) if request.path_params else None,
        "request_id": request.headers.get("x-request-id"),
        "exception_type": type(exc).__name__,
        "exception_module": type(exc).__module__,
        "timestamp_ms": int(datetime.now().timestamp() * 1000),
        "host": request.url.hostname,
        "scheme": request.url.scheme,
        "server": request.headers.get("host"),
        "auth_header_present": "authorization" in request.headers,
        "response_detail": str(detail) if isinstance(detail, str) else detail,
        "correlation_id": request.state.correlation_id if hasattr(request.state, 'correlation_id') else None,
    }
        
    metadata = {k: v for k, v in metadata.items() if v is not None}
    
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
                metadata=metadata,
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
            metadata=metadata,
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
            "status_code": status_code,
            "timestamp": str(datetime.now())
        }
    )


async def log_rate_limit_violation(
    request: Request,
    identifier: str,
    attempts: int,
    ttl: int
):
    conn = None
    try:
        pool = get_db_pool()
        if pool is None:
            print(f"[WARN] DB pool not available for rate limit logging")
            return
        
        conn = await pool.acquire()

        window_start = datetime.now(timezone.utc) - timedelta(seconds=Constants.WINDOW - ttl)        
        ip_address = identifier.split(":")[-1] if ":" in identifier else identifier
        
        await logs_table.create_rate_limit_log(
            ip_address,
            str(request.url.path),
            request.method,
            attempts,
            window_start,
            conn
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to log rate limit violation: {e}")
    finally:
        if conn is not None:
            try:
                await pool.release(conn)
            except Exception as e:
                print(f"[ERROR] Failed to release DB connection: {e}")



async def get_logs(limit: int, offset: int, conn: Connection):
    total, results = await logs_table.get_logs(limit=limit, offset=offset, conn=conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return JSONResponse(response)


async def delete_logs(interval_minutes: int | None, conn: Connection) -> Response:
    deleted_logs = await logs_table.delete_logs(interval_minutes, conn)
    return JSONResponse({"deleted": deleted_logs})


async def log_stats(conn: Connection) -> JSONResponse:
    return await logs_table.get_log_stats(conn)


async def get_rate_limit_violations(
    hours: int,
    min_attempts: int,
    limit: int,
    offset: int,
    conn: Connection,
    ip_address: str = None
) -> list[dict]:    
    total, results = await logs_table.get_rate_limit_violations(hours, min_attempts, limit, offset, conn, ip_address)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return JSONResponse(content=response)


async def cleanup_old_rate_limit_logs(hours: int, conn: Connection) -> int:
    total: int = await logs_table.delete_old_rate_limit_logs(hours, conn)
    return JSONResponse({"deleted": total})