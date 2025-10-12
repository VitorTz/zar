from fastapi import APIRouter, Request, Depends, Query
from src.security import get_user_from_token_if_exists
from src.schemas.urls import URLResponse, URLStats, URLCreate, UrlPagination
from src.schemas.user import User
from src.db import get_db
from src.services import urls as url_service
from asyncpg import Connection


router = APIRouter()


@router.post("/", response_model=URLResponse)
async def shorten_url(
    url_data: URLCreate, 
    request: Request, 
    user: User | None = Depends(get_user_from_token_if_exists),
    conn: Connection = Depends(get_db)
):
    return await url_service.shorten(str(url_data.url), request, conn, user)


@router.get("/{short_code}")
async def redirect_from_short_code(
    short_code: str,
    request: Request,
    conn: Connection = Depends(get_db)
):
    return await url_service.redirect_from_short_code(short_code, request, conn)


@router.get("/stats/{short_code}", response_model=URLStats)
async def get_url_stats(
    short_code: str,
    conn: Connection = Depends(get_db)
):
    return await url_service.get_short_code_stats(short_code, conn)


@router.get("/pagination/urls", response_model=UrlPagination)
async def get_urls(
    request: Request,
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await url_service.get_urls(request, limit, offset, conn)
    