from asyncpg import Connection
from typing import Literal, Optional
from datetime import datetime, timedelta


async def log_error(
    error_level: str,
    message: str,
    path: str,
    method: str,
    status_code: int,
    stacktrace: str,
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
                    stacktrace
                )
                VALUES 
                    ($1, $2, $3, $4, $5, $6);
                """,
                error_level,
                message,
                path,
                method,
                status_code,
                stacktrace
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
    level: Literal['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
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
                ($1, $2, $3, $4, $5, $6);
        """,
        level,
        message,
        path,
        method,
        status_code,
        stacktrace
    )
    

async def get_logs(
    method: str | None,
    sort_by: str,
    sort_order: str,
    limit: int,
    offset: int,
    conn: Connection
) ->  tuple[int, list[dict]]:
    where_clause: list[str] = []
    params: list[str] = []

    if method is not None:
        where_clause.append("method = $1")
        params.append(method)

    
    if params:
        where_clause = "WHERE " + " AND ".join(where_clause)
        r = await conn.fetchrow(f"SELECT count(*) as total FROM logs {where_clause};", *params)
        total = dict(r)['total']
    else:
        where_clause = ''
        r = await conn.fetchrow(f"SELECT count(*) as total FROM logs;")
        total = dict(r)['total']

    params.extend([limit, offset])
    r = await conn.fetch(
        f"""
            SELECT 
                log_id,
                level,
                message,
                path,
                method,
                status_code,
                stacktrace,
                to_char(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at
            FROM 
                logs
            {where_clause}
            ORDER BY 
                {sort_by} {sort_order}
            LIMIT ${len(params) - 1}
            OFFSET ${len(params)}
        """,
        *params
    )

    return total, [dict(i) for i in r]


async def delete_logs(
    interval_minutes: int | None,
    conn: Connection
) -> int:
    r = await conn.fetchrow("SELECT count(*) as total FROM logs;")
    t1 = dict(r)['total']
    if interval_minutes is None:
        await conn.execute("DELETE FROM logs;")
    else:
        await conn.execute(
            f"""
                DELETE FROM 
                    logs
                WHERE
                    created_at < NOW() - INTERVAL '{interval_minutes} minutes';
            """
        )
    r = await conn.fetchrow("SELECT count(*) as total FROM logs;")
    t2 = dict(r)['total']
    return t1 - t2
        

async def get_filtered_logs(
    limit: int,
    offset: int,
    level: Optional[str],
    method: Optional[str],
    status_group: Optional[str],
    search: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    conn: Connection
) -> tuple[int, list[dict]]:
    where_clauses = []
    params = []
    param_count = 1
    
    if level:
        where_clauses.append(f"level = ${param_count}")
        params.append(level.upper())
        param_count += 1
    
    if method:
        where_clauses.append(f"method = ${param_count}")
        params.append(method.upper())
        param_count += 1
    
    if status_group:
        if status_group == '2xx':
            where_clauses.append(f"status_code >= 200 AND status_code < 300")
        elif status_group == '3xx':
            where_clauses.append(f"status_code >= 300 AND status_code < 400")
        elif status_group == '4xx':
            where_clauses.append(f"status_code >= 400 AND status_code < 500")
        elif status_group == '5xx':
            where_clauses.append(f"status_code >= 500 AND status_code < 600")
    
    if search:
        where_clauses.append(f"message ILIKE ${param_count}")
        params.append(f"%{search}%")
        param_count += 1
    
    if date_from:
        try:
            dt = datetime.strptime(date_from, '%d-%m-%Y')
            where_clauses.append(f"created_at >= ${param_count}")
            params.append(dt)
            param_count += 1
        except ValueError:
            pass
    
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%d-%m-%Y') + timedelta(days=1)
            where_clauses.append(f"created_at < ${param_count}")
            params.append(dt)
            param_count += 1
        except ValueError:
            pass
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Query de contagem
    count_query = f"SELECT COUNT(*) as total FROM logs WHERE {where_sql}"
    r = await conn.fetchrow(count_query, *params)
    total = dict(r)['total']
    
    # Query de dados
    params.append(limit)
    params.append(offset)
    data_query = f"""
        SELECT
            log_id,
            level,
            message,
            path,
            method,
            status_code,
            stacktrace,
            to_char(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at
        FROM 
            logs
        WHERE 
            {where_sql}
        ORDER BY 
            log_id DESC
        LIMIT 
            ${param_count}
        OFFSET 
            ${param_count + 1}
    """
    
    r = await conn.fetch(data_query, *params)
    
    return total, [dict(i) for i in r]


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
        ORDER BY date DESC;
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
        ORDER BY hour DESC;
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