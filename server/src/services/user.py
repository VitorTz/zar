from asyncpg import Connection
from src.schemas.user import User
from src.schemas.urls import URLDelete, CreateFavoriteURL, URLResponse, UrlShortCode
from src.tables import users as users_table
from src.tables import urls as urls_table
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import HTTPException
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


async def assign_url_to_user(user: User, url: UrlShortCode, conn: Connection):
    await users_table.assign_url_to_user(user.id, url.short_code, conn)
    return Response()


async def set_user_favorite_url(user: User, url: CreateFavoriteURL, base_url: str, conn: Connection):
    url_response: URLResponse | None = await urls_table.get_url(url.short_code, base_url, conn)
    if url_response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Url não encontrada!')
    
    await users_table.set_user_favorite_url(user.id, url.short_code, url.is_favorite, conn)    

    return JSONResponse(url_response.model_dump())