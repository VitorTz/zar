from asyncpg import Connection
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from src.schemas.user import User
from src.tables import dashboard
from src.tables import users as users_table
from src import util


async def get_urls_ordered_by_popularity(limit: int, offset: int, conn: Connection):
    total, results = await dashboard.get_urls_ordered_by_popularity(limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }

    return JSONResponse(response)


async def get_daily_metrics(limit: int, offset: int, conn: Connection):
    total, results = await dashboard.get_daily_metrics(limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    
    util.print_dict(response)
    return JSONResponse(response)


async def get_dashboard_metrics(conn: Connection) -> JSONResponse:
    data: dict = await dashboard.get_dashboard_data(conn)
    return JSONResponse(data)


async def get_user_stats(user: User, conn: Connection):
    data: dict | None = await users_table.get_user_stats(user.id, conn)
    if data is None:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(data)