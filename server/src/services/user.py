from asyncpg import Connection
from src.schemas.user import User
from src.schemas.urls import URLDelete
from src.tables import users as users_table
from src.tables import urls as urls_table
from fastapi.responses import Response
from fastapi import status, Request 
from src import util



async def delete_user_url(user: User, url: URLDelete, conn: Connection):
    await users_table.delete_user_url(user.id, url.url_id, conn)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def get_user_urls(user_id: str, request: Request, limit: int, offset: int, conn: Connection):
    total, results = await urls_table.get_user_urls(user_id, limit, offset, util.extract_base_url(request), conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return response


async def assign_url_to_user(user_id: str, url_id: str, conn: Connection):
    await users_table.assign_url_to_user(user_id, url_id, conn)
    return Response()