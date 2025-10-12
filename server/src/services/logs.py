from fastapi import Request
from fastapi.responses import JSONResponse, Response
from src.tables import logs as logs_table
from src.perf.system_monitor import get_monitor
from src.db import get_db_pool
from asyncpg import Connection
from datetime import datetime, timezone, timedelta
from src.constants import Constants
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
        
        await conn.execute(
            """
            INSERT INTO rate_limit_logs (
                ip_address, 
                path, 
                method, 
                attempts, 
                window_start,
                last_attempt_at
            )
            VALUES 
                ($1, $2, $3, $4, $5, NOW())
            ON CONFLICT 
                (ip_address, path, method, window_start)
            DO UPDATE SET
                attempts = rate_limit_logs.attempts + 1,
                last_attempt_at = NOW()
            """,
            ip_address,
            str(request.url.path),
            request.method,
            attempts,
            window_start
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to log rate limit violation: {e}")
    finally:
        if conn is not None:
            try:
                await pool.release(conn)
            except Exception as e:
                print(f"[ERROR] Failed to release DB connection: {e}")



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


async def get_rate_limit_violations(
    ip_address: str = None,
    hours: int = 24,
    min_attempts: int = 10
) -> list[dict]:    
    conn = None
    try:
        pool = get_db_pool()
        if pool is None:
            return []
        
        conn = await pool.acquire()
        
        query = """
        SELECT 
            ip_address,
            path,
            method,
            SUM(attempts) as total_attempts,
            COUNT(*) as violation_count,
            MIN(created_at) as first_violation,
            MAX(last_attempt_at) as last_violation
        FROM rate_limit_logs
        WHERE last_attempt_at > NOW() - INTERVAL '%s hours'
        """
        
        params = [hours]
        
        if ip_address:
            query += " AND ip_address = $2"
            params.append(ip_address)
        
        query += """
        GROUP BY ip_address, path, method
        HAVING SUM(attempts) >= $%d
        ORDER BY total_attempts DESC
        LIMIT 100
        """ % (len(params) + 1)
        
        params.append(min_attempts)
        
        rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        print(f"[ERROR] Failed to get rate limit violations: {e}")
        return []
    finally:
        if conn is not None:
            try:
                await pool.release(conn)
            except Exception as e:
                print(f"[ERROR] Failed to release DB connection: {e}")


async def cleanup_old_rate_limit_logs(days_to_keep: int = 30) -> int:
    conn = None
    try:
        pool = get_db_pool()
        if pool is None:
            return 0
        
        conn = await pool.acquire()
        
        result = await conn.execute(
            """
            DELETE FROM rate_limit_logs
            WHERE last_attempt_at < NOW() - INTERVAL '%s days'
            """,
            days_to_keep
        )
        
        # Parse "DELETE X" response
        deleted_count = int(result.split()[-1]) if result else 0
        
        print(f"[INFO] Cleaned up {deleted_count} old rate limit logs")
        return deleted_count
        
    except Exception as e:
        print(f"[ERROR] Failed to cleanup rate limit logs: {e}")
        return 0
    finally:
        if conn is not None:
            try:
                await pool.release(conn)
            except Exception as e:
                print(f"[ERROR] Failed to release DB connection: {e}")