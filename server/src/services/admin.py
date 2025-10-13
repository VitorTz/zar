from src.tables import users as users_table
from src.tables import urls as urls_table
from src.tables import logs as logs_table
from fastapi.responses import JSONResponse, Response
from fastapi import status
from asyncpg import Connection


async def get_users(limit: int, offset: int, conn: Connection):
    total, results = await users_table.get_users(limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return JSONResponse(response)


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


async def delete_user(user_id: str, conn: Connection):
    await users_table.delete_user(user_id, conn)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def delete_all_users(conn: Connection):
    await users_table.delete_all_users(conn)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def delete_all_urls(conn: Connection):
    await urls_table.delete_all_urls(conn)
    return Response(status_code=status.HTTP_204_NO_CONTENT)