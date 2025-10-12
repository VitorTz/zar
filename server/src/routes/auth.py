from fastapi import APIRouter, Depends, Request, Query, Cookie
from fastapi.responses import JSONResponse
from src.db import get_db
from src.schemas.user import User, UserLogin, UserSessionPagination, UserCreate
from src.security import get_user_from_token
from src.services import auth as auth_service
from asyncpg import Connection


router = APIRouter()


@router.get("/me", response_model=User)
async def get_manager(
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
) -> JSONResponse:
    return await auth_service.get_user(user.id, conn)


@router.post("/login", response_model=User)
async def login(
    user_login: UserLogin,
    request: Request,
    conn: Connection = Depends(get_db)
) -> User:
    return await auth_service.login(user_login, request, conn)


@router.get("/sessions", response_model=UserSessionPagination)
async def get_manager_active_sessions(
    limit: int = Query(default=64, le=64, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await auth_service.get_user_sessions(user, limit, offset, conn)


@router.post("/refresh", response_model=User)
async def refresh_token_manager(refresh_token: str | None = Cookie(default=None), conn: Connection = Depends(get_db)):
    return await auth_service.refresh_access_token(refresh_token, conn)


@router.post("/signup")
async def signup(manager_signup: UserCreate, conn: Connection = Depends(get_db)):
    return await auth_service.signup(manager_signup, conn)


@router.post("/logout")
async def logout(refresh_token: str | None = Cookie(default=None), conn: Connection = Depends(get_db)):
    return await auth_service.logout(refresh_token, conn)


@router.post("/logoutall")
async def logout(user: User = Depends(get_user_from_token), conn: Connection = Depends(get_db)):
    return await auth_service.logout_all(user, conn)