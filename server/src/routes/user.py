from src.security import get_user_from_token
from src.schemas.user import User
from src.schemas.urls import UrlPagination, URLDelete
from fastapi import APIRouter, Depends, Query, Request
from asyncpg import Connection
from src.db import get_db
from src.services import user as user_service


router = APIRouter()


@router.get("/urls", response_model=UrlPagination)
async def get_user_urls(
    request: Request,
    limit: int = Query(default=64, le=64, ge=0),
    offset: int = Query(default=0, ge=0),
    user: User | None = Depends(get_user_from_token), 
    conn: Connection = Depends(get_db)
):
    return await user_service.get_user_urls(user.id, request, limit, offset, conn)


@router.delete("/url")
async def delele_user_url(
    url: URLDelete, 
    user: User | None = Depends(get_user_from_token), 
    conn: Connection = Depends(get_db)
):
    return await user_service.delete_user_url(user, url, conn)