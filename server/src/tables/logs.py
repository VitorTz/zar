from asyncpg import Connection
from typing import Literal
import json


async def log_error(
    error_level: str,
    message: str,
    path: str,
    method: str,
    status_code: int,
    stacktrace: str,
    metadata: dict,
    conn: Connection = None
):
    try:
        if conn is not None:
            await conn.execute(
                """
                INSERT INTO logs (
                    level, 
                    message, 
                    path, 
                    method, 
                    status_code, 
                    stacktrace,
                    metadata
                )
                VALUES 
                    ($1, $2, $3, $4, $5, $6, $7)
                """,
                error_level,
                message,
                path,
                method,
                status_code,
                stacktrace,
                json.dumps(metadata)
            )
        else:
            print(
                f"[{error_level}] {method} {path} - {status_code}\n",
                f"Message: {message}\n",
                f"Stacktrace: {stacktrace}"
            )
    except Exception as e:
        print(
            f"Failed to log to database: {e}\n",
            f"Original error: [{error_level}] {method} {path} - {status_code}\n",
            f"{message}\n{stacktrace}"
        )


async def create_log(
    level: Literal['INFO', 'WARN', 'ERROR', 'FATAL', 'DEBUG'],
    message: str,
    path: str | None,
    method: Literal['POST', 'PUT', 'GET', 'DELETE'],
    status_code: int | None,
    stacktrace: str | None,
    conn: Connection
) -> None:
    await conn.execute(
        """
            INSERT INTO logs (
                level,
                message,
                path,
                method,
                status_code,
                stacktrace
            )
            VALUES
                ($1, $2, $3, $4, $5, $6)
        """,
        level,
        message,
        path,
        method,
        status_code,
        stacktrace
    )
    

async def get_logs(
    limit: int,
    offset: int,
    conn: Connection
) ->  tuple[int, list[dict]]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM logs")

    r = await conn.fetch(
        f"""
            SELECT 
                id,
                level,
                message,
                path,
                method,
                status_code,
                user_id,
                stacktrace,
                metadata,
                to_char(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at
            FROM 
                logs
            ORDER BY 
                created_at DESC
            LIMIT $1
            OFFSET $2
        """,
        limit,
        offset
    )    

    return total, [dict(i) for i in r]


async def delete_logs(
    interval_minutes: int | None,
    conn: Connection
) -> int:
    t1: int = await conn.fetchval("SELECT count(*) as total FROM logs")

    if interval_minutes is None:
        await conn.execute("DELETE FROM logs")
    else:
        await conn.execute(
            f"""
                DELETE FROM 
                    logs
                WHERE
                    created_at < NOW() - INTERVAL '{interval_minutes} minutes'
            """
        )
    t2: int = await conn.fetchval("SELECT count(*) as total FROM logs")

    return t1 - t2
        

async def get_log_stats(conn: Connection) -> dict:
    # Estatísticas por nível
    level_stats = await conn.fetch("""
        SELECT 
            level, 
            COUNT(*) as count
        FROM 
            logs
        GROUP BY 
            level
        ORDER BY 
            count DESC
    """)
    
    # Estatísticas por status code
    status_stats = await conn.fetch("""
        SELECT 
            CASE 
                WHEN status_code >= 200 AND status_code < 300 THEN '2xx'
                WHEN status_code >= 300 AND status_code < 400 THEN '3xx'
                WHEN status_code >= 400 AND status_code < 500 THEN '4xx'
                WHEN status_code >= 500 AND status_code < 600 THEN '5xx'
                ELSE 'Other'
            END as status_group,
            COUNT(*) as count
        FROM logs
        WHERE status_code IS NOT NULL
        GROUP BY status_group
        ORDER BY status_group
    """)
    
    # Estatísticas por método HTTP
    method_stats = await conn.fetch("""
        SELECT method, COUNT(*) as count
        FROM logs
        WHERE method IS NOT NULL
        GROUP BY method
        ORDER BY count DESC
    """)
    
    # Logs por dia (últimos 7 dias)
    daily_stats = await conn.fetch("""
        SELECT 
            TO_CHAR(created_at, 'YYYY-MM-DD') AS date,
            COUNT(*) AS count
        FROM logs
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY date
        ORDER BY date DESC
    """)
    
    # Logs por hora (últimas 24 horas)
    hourly_stats = await conn.fetch("""
        SELECT 
            TO_CHAR(created_at, 'YYYY-MM-DD HH24:00') AS hour,
            COUNT(*) AS count
        FROM 
            logs
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY hour
        ORDER BY hour DESC
    """)
    
    # Top 10 endpoints com mais erros
    error_endpoints = await conn.fetch(
        """
            SELECT 
                path,
                COUNT(*) as count
            FROM logs
            WHERE level = 'ERROR'
            GROUP BY path
            ORDER BY count DESC
            LIMIT 10
        """
    )

    return {
        "by_level": [dict(row) for row in level_stats],
        "by_status": [dict(row) for row in status_stats],
        "by_method": [dict(row) for row in method_stats],
        "by_day": [dict(row) for row in daily_stats],
        "by_hour": [dict(row) for row in hourly_stats],
        "error_endpoints": [dict(row) for row in error_endpoints]
    }


async def get_rate_limit_violations(
    hours: int,
    min_attempts: int,
    limit: int,
    offset: int,
    conn: Connection,
    ip_address: str | None = None,
) -> tuple[int, list[dict]]:
    if ip_address:
        r = await conn.fetch(
            f"""
                WITH filtered AS (
                    SELECT
                        ip_address,
                        path,
                        method,
                        attempts,
                        created_at,
                        last_attempt_at
                    FROM 
                        rate_limit_logs
                    WHERE 
                        ip_address = $1 AND
                        last_attempt_at > NOW() - ($2 || ' hours')::interval
                )
                SELECT
                    ip_address,
                    path,
                    method,
                    SUM(attempts) AS total_attempts,
                    COUNT(*) AS violation_count,
                    TO_CHAR(MIN(created_at), 'DD-MM-YYYY HH24:MI:SS') AS first_violation,
                    TO_CHAR(MAX(last_attempt_at), 'DD-MM-YYYY HH24:MI:SS') AS last_violation,
                    COUNT(*) OVER() AS total_matching_records
                FROM 
                    filtered
                GROUP BY 
                    ip_address, path, method
                HAVING 
                    SUM(attempts) >= $3
                ORDER BY 
                    total_attempts DESC
                LIMIT $4
                OFFSET $5
            """,
            ip_address,
            str(hours),
            min_attempts,
            limit,
            offset
        )
    else:
        r = await conn.fetch(
            """
                WITH filtered AS (
                    SELECT
                        ip_address,
                        path,
                        method,
                        attempts,
                        created_at,
                        last_attempt_at
                    FROM 
                        rate_limit_logs
                    WHERE 
                        last_attempt_at > NOW() - ($1 || ' hours')::interval
                )
                SELECT
                    ip_address,
                    path,
                    method,
                    SUM(attempts) AS total_attempts,
                    COUNT(*) AS violation_count,
                    TO_CHAR(MIN(created_at), 'DD-MM-YYYY HH24:MI:SS') AS first_violation,
                    TO_CHAR(MAX(last_attempt_at), 'DD-MM-YYYY HH24:MI:SS') AS last_violation,
                    COUNT(*) OVER() AS total_matching_records
                FROM filtered
                GROUP BY ip_address, path, method
                HAVING SUM(attempts) >= $2
                ORDER BY total_attempts DESC
                LIMIT $3
                OFFSET $4;
            """,
            str(hours),
            min_attempts,
            limit,
            offset
        )

    results = [dict(r) for r in r]
    total = results[0]['total_matching_records'] if results else 0
    for row in results:
        row.pop('total_matching_records', None)        
    
    return total, results


async def delete_old_rate_limit_logs(hours: int, conn: Connection) -> int:
    t1: int = await conn.fetchval("SELECT COUNT(*) AS total FROM rate_limit_logs")
    
    await conn.execute(
        """
            DELETE FROM
                rate_limit_logs                
            WHERE
                last_attempt_at > NOW() - ($1 || ' hours')::interval
        """,
        str(hours)
    )

    t2: int = await conn.fetchval("SELECT COUNT(*) AS total FROM rate_limit_logs")

    return t1 - t2



async def create_rate_limit_log(
    ip_address: str,
    path: str,
    method: str,
    attempts: str,
    window_start,    
    conn: Connection
):
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
        path,
        method,
        attempts,
        window_start
    )