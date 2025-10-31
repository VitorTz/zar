from src.schemas.dashboard import Dashboard
from asyncpg import Connection
from src.db import db_count
import json


async def refresh_dashboard(conn: Connection):
    await conn.execute("SELECT * FROM refresh_dashboard_stats()")


async def get_dashboard(conn: Connection) -> Dashboard:
    total_urls: int = await db_count('urls', conn)
    row = await conn.fetchrow("SELECT * FROM mv_dashboard;")
    if not row:
        raise ValueError("No dashboard data found")
    
    data = dict(row)
    
    json_fields = [
        "users", "urls", "clicks", "analytics", "top_urls",
        "geography", "client_info", "tags", "domains",
        "daily_growth", "sessions", "conversion",
    ]

    for field in json_fields:
        value = data.get(field)
        if isinstance(value, str):
            data[field] = json.loads(value)

    return Dashboard(**data, total_urls=total_urls)