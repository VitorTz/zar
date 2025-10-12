
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from src.db import get_db, db_count, db_version
from src.schemas.user import UserPagination, UseDelete
from src.schemas.urls import UrlPagination
from src.schemas.admin import HealthReport
from src.security import require_admin
from src.services import admin as admin_service
from src.services import urls as urls_service
from datetime import datetime
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/health", response_model=HealthReport)
async def health_check(conn: Connection = Depends(get_db)):
    version: str = await db_version(conn)
    total_urls: int = await db_count("urls", conn)
    return JSONResponse(
        content={
            "status": "healthy",
            "database": "connected",
            "postgres_version": version,
            "total_urls": total_urls,
            "now": (datetime.now())
        }
    )    


@router.get("/users", response_model=UserPagination)
async def get_users(
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_users(limit, offset, conn)


@router.delete("/users")
async def delete_user(user: UseDelete, conn: Connection = Depends(get_db)):
    return await admin_service.delete_user(user.user_id, conn)


@router.delete("/users/all")
async def delete_all_users(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_users(conn)


@router.get("/urls", response_model=UrlPagination)
async def get_urls(
    request: Request, 
    limit: int = Query(default=64, ge=0, le=64), 
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await urls_service.get_urls(request, limit, offset, conn)


@router.delete("/urls/all")
async def delete_all_urls(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_urls(conn)