from fastapi import APIRouter, Request, Depends, Form, Cookie, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.security import get_user_from_token_if_exists
from src.schemas.urls import URLResponse, URLCreate
from src.schemas.user import User
from src.services import urls as url_service
from asyncpg import Connection
from src.db import get_db
from typing import Optional


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/", response_model=URLResponse)
async def shorten_url(
    url: URLCreate, 
    request: Request,
    refresh_token: Optional[str] = Cookie(default=None),
    user: Optional[User] = Depends(get_user_from_token_if_exists),
    conn: Connection = Depends(get_db)
):      
    return await url_service.shorten(url, refresh_token, request, conn, user)


@router.get("/{short_code}")
async def redirect_from_short_code(
    short_code: str,
    request: Request,
    conn: Connection = Depends(get_db)
):
    return await url_service.redirect_from_short_code(short_code, request, conn)


@router.post("/{short_code}/verify")
async def verify_password(
    short_code: str,
    request: Request,
    password: str = Form(...),
    conn: Connection = Depends(get_db)
):    
    return await url_service.verify_password_and_redirect(short_code, password, request, conn)


@router.get("/{short_code}/stats")
async def get_url_stats(short_code: str, conn: Connection = Depends(get_db)):
    await url_service.get_url_stats(short_code, conn)


@router.get("/expired", response_class=HTMLResponse, summary="Página para URL Expirada")
async def show_expired_page(request: Request, expired_at: str = Query()):
    context = {
        "request": request,
        "expired_at": expired_at
    }
    return templates.TemplateResponse("expired.html", context)