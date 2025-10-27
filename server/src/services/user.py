from src.schemas.user import User
from src.schemas.urls import URLDelete, CreateFavoriteURL, URLCreate, URLResponse
from src.schemas.pagination import Pagination
from src.tables import users as users_table
from src.tables import urls as urls_table
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import status, Request 
from asyncpg import Connection
from typing import Optional
from src import util


async def delete_user_url(user: User, url: URLDelete, conn: Connection):
    await users_table.delete_user_url(user.id, url.short_code, conn)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def get_user_urls(user_id: str, request: Request, limit: int, offset: int, conn: Connection) -> Pagination[URLResponse]:
    return await urls_table.get_user_urls(user_id, limit, offset, util.extract_base_url(request), conn)


async def set_user_favorite_url(user: User, url: CreateFavoriteURL, conn: Connection):        
    if not await urls_table.url_exists(url.url_id, conn):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Url não encontrada")
    await users_table.set_user_favorite_url(user.id, url.url_id, url.is_favorite, conn)    
