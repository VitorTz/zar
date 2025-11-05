from fastapi import APIRouter, Depends, Query, Request, status
from src.schemas.urls import URLDelete
from src.schemas.pagination import Pagination
from src.schemas.urls import URLResponse
from src.security import require_admin
from src.services import admin as admin_service
from src.services import urls as urls_service
from asyncpg import Connection
from src.db import get_db


router = APIRouter(prefix="/urls", dependencies=[Depends(require_admin)], tags=["admin_urls"])


@router.get("/", response_model=Pagination[URLResponse])
async def get_urls(
    request: Request,
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await urls_service.get_urls(request, limit, offset, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(url: URLDelete, conn: Connection = Depends(get_db)):
    await urls_service.delete_url(url, conn)
    

@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_urls(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_urls(conn)
