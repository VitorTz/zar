from fastapi import APIRouter, Depends, Query, Request, status
from src.security import get_user_from_token
from src.schemas.user import User
from src.schemas.urls import URLDelete, CreateFavoriteURL, UserURLResponse
from src.schemas.pagination import Pagination
from src.services import user as user_service
from asyncpg import Connection
from src.db import get_db


router = APIRouter()


@router.get("/url", response_model=Pagination[UserURLResponse])
async def get_user_urls(
    request: Request,
    limit: int = Query(default=64, le=64, ge=0),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_user_from_token), 
    conn: Connection = Depends(get_db)
):
    return await user_service.get_user_urls(user.id, request, limit, offset, conn)


@router.put("/url/favorite", status_code=status.HTTP_201_CREATED)
async def set_favorite_url(
    url: CreateFavoriteURL,
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await user_service.set_user_favorite_url(user, url, conn)


@router.delete("/url")
async def delele_user_url(
    url: URLDelete, 
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await user_service.delete_user_url(user, url, conn)
