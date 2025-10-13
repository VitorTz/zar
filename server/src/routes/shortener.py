from fastapi import APIRouter, Request, Depends, Query, status
from src.security import get_user_from_token_if_exists
from src.schemas.urls import URLResponse, URLCreate, UrlPagination
from src.schemas.url_stats import URLStatsResponse, URLStatsNotFound
from src.schemas.user import User
from src.db import get_db
from src.services import urls as url_service
from asyncpg import Connection


router = APIRouter()


@router.post("/url", response_model=URLResponse)
async def shorten_url(
    url: URLCreate, 
    request: Request, 
    user: User | None = Depends(get_user_from_token_if_exists),
    conn: Connection = Depends(get_db)
):    
    return await url_service.shorten(url, request, conn, user)


@router.get("/{short_code}")
async def redirect_from_short_code(
    short_code: str,
    request: Request,
    conn: Connection = Depends(get_db)
):
    return await url_service.redirect_from_short_code(short_code, request, conn)


@router.get(
    "/url/{short_code}/stats",
    response_model=URLStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter estatísticas detalhadas da URL",
    description="Retorna analytics completos dos últimos 30 dias para uma URL específica",
    responses={
        404: {
            "model": URLStatsNotFound,
            "description": "URL não encontrada"
        }
    }
)
async def get_url_stats_endpoint(short_code: str, conn: Connection = Depends(get_db)): 
    return await url_service.get_url_stats(short_code, conn)


@router.get("/url/urls", response_model=UrlPagination)
async def get_urls(
    request: Request,
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await url_service.get_urls(request, limit, offset, conn)