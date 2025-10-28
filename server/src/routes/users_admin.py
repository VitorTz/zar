from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.db import get_db
from src.schemas.user import User, UserDelete
from src.schemas.pagination import Pagination
from src.services import admin as admin_service
from src.schemas.user import UserSession
from asyncpg import Connection


router = APIRouter(prefix='/users', dependencies=[Depends(require_admin)])


@router.get("/", response_model=Pagination[User])
async def get_users(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_users(limit, offset, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: UserDelete, conn: Connection = Depends(get_db)):
    return await admin_service.delete_user(user.user_id, conn)


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_users(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_users(conn)


@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_sessions(conn: Connection = Depends(get_db)):
    return await admin_service.delete_all_user_sessions(conn)


@router.get("/sessions", status_code=status.HTTP_200_OK, response_model=Pagination[UserSession])
async def get_sessions(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_user_sessions(limit, offset, conn)


@router.delete("/sessions/expired", status_code=status.HTTP_204_NO_CONTENT)
async def cleanup_expired_sessions(conn: Connection = Depends(get_db)):
    await admin_service.cleanup_expired_sessions(conn)
