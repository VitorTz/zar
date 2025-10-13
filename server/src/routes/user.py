from src.security import get_user_from_token
from src.schemas.user import User, UserStats
from src.schemas.urls import UrlPagination, URLDelete, CreateFavoriteURL, URLResponse, UrlShortCode
from fastapi import APIRouter, Depends, Query, Request
from asyncpg import Connection
from src.db import get_db
from src.services import user as user_service
from src.services import dashboard as metrics_service


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


@router.put("/url/favorite", response_model=URLResponse)
async def set_favorite_url(
    url: CreateFavoriteURL,
    request: Request,
    user: User | None = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await user_service.set_user_favorite_url(user, url, request, conn)


@router.post("/url")
async def assign_url_to_user(
    url: UrlShortCode,
    user: User | None = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await user_service.assign_url_to_user(user, url, conn)


@router.delete("/url")
async def delele_user_url(
    url: URLDelete, 
    user: User | None = Depends(get_user_from_token), 
    conn: Connection = Depends(get_db)
):
    return await user_service.delete_user_url(user, url, conn)


@router.get("/metrics", response_model=UserStats)
async def get_user_stats(
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await metrics_service.get_user_stats(user, conn)