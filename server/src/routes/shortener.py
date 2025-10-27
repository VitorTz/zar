from fastapi import APIRouter, Request, Depends, Cookie
from src.security import get_user_from_token_if_exists
from src.schemas.urls import URLResponse, URLCreate, UrlStats
from src.schemas.user import User
from src.services import urls as url_service
from asyncpg import Connection
from src.db import get_db
from typing import Optional


router = APIRouter()


@router.post("/", response_model=URLResponse)
async def shorten_url(
    url: URLCreate, 
    request: Request,
    refresh_token: Optional[str] = Cookie(default=None),
    user: Optional[User] = Depends(get_user_from_token_if_exists),
    conn: Connection = Depends(get_db)
):      
    return await url_service.shorten(url, refresh_token, user, request, conn)


@router.get("/{short_code}")
async def redirect_from_short_code(
    short_code: str,
    request: Request,
    conn: Connection = Depends(get_db)
):
    return await url_service.redirect_from_short_code(short_code, request, conn)


@router.get("/{short_code}/stats", response_model=UrlStats)
async def get_url_stats(short_code: str, conn: Connection = Depends(get_db)):
    return await url_service.get_url_stats(short_code, conn)
