from src.schemas.urls import UrlBlackListCreate, UrlBlackListDelete
from src.tables import users as users_table
from src.tables import url_blacklist as url_blacklist_table
from src.tables import urls as urls_table
from fastapi.responses import JSONResponse
from asyncpg import Connection
from typing import Optional


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


async def delete_user(user_id: str, conn: Connection):
    await users_table.delete_user(user_id, conn)


async def delete_all_users(conn: Connection):
    await users_table.delete_all_users(conn)


async def delete_all_urls(conn: Connection):
    await urls_table.delete_all_urls(conn)


async def delete_expired_urls(conn: Connection):
    await urls_table.delete_all_urls(conn)


async def soft_delete_expired_urls(conn: Connection):
    await urls_table.soft_delete_expired_urls(conn)


async def get_blacklist_urls(q: Optional[str], limit: int, offset: int, conn: Connection):
    total, results = await url_blacklist_table.get_blacklist(q, limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return response


async def add_to_blacklist_url(url: UrlBlackListCreate, conn: Connection):
    await url_blacklist_table.add_url_to_blacklist(str(url.url), conn)
    await url_blacklist_table.delete_blacklisted_urls(str(url.url), conn)


async def remove_url_from_blacklist(url: UrlBlackListDelete, conn: Connection):
    await url_blacklist_table.remove_url_from_blacklist(str(url.url), conn)

