from src.schemas.urls import (
    URLCreate, 
    UrlRedirect, 
    UrlStats, 
    URLResponse, 
    URLDelete
)
from src.schemas.pagination import Pagination
from src.schemas.user import User
from src.schemas.token import SessionToken
from src.schemas.domain import Domain
from src.services import domain as domain_service
from src.tables import urls as urls_table
from src.tables import users as users_table
from src.tables import domains as domains_table
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import Request, status
from asyncpg import Connection
from src import security
from typing import Optional
from src import util


async def get_urls(
    request: Request, 
    limit: int, 
    offset: int, 
    conn: Connection
) -> Pagination[URLResponse]:
    return await urls_table.get_urls(
        util.extract_base_url(request),
        limit, 
        offset, 
        conn
    )


async def shorten(url: URLCreate, request: Request, conn: Connection, refresh_token: Optional[str], user: Optional[User]) -> JSONResponse:    
    domain: Domain = await domains_table.get_domain(str(url.url), conn)
    
    if not domain.is_secure or not await domain_service.is_safe_domain(request, domain, conn):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This domain is potentially malicious.")
    
    base_url: str = util.extract_base_url(request)
    url_response: URLResponse = await urls_table.create_url(domain, url, user, base_url, conn)

    response = JSONResponse(content=url_response.model_dump(mode="json"))
    if not user and refresh_token:
        user = await users_table.get_user_by_refresh_token(refresh_token, conn)
        if user:
            session_token: SessionToken = security.create_session_token(user.id)
            await users_table.update_user_session_token(user.id, session_token.refresh_token, conn)
            security.set_session_token_cookie(response, session_token)
            return response

    return response
        

async def redirect_from_short_code(
    short_code: str, 
    request: Request, 
    conn: Connection
) -> RedirectResponse:
    url: Optional[UrlRedirect] = await urls_table.get_redirect_url(short_code, conn)

    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found.")

    await urls_table.add_click_event(url.id, request, conn)
    
    return RedirectResponse(url=url.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


async def get_url_stats(short_code: str, conn: Connection) -> UrlStats:
    url_id = await urls_table.get_url_id_by_short_code(short_code, conn)
    if url_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The URL with short code {short_code} was not found or has no statistics yet."
        )
    
    url_stats: Optional[UrlStats] = await urls_table.get_url_stats(url_id, conn)
    if url_stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The URL with short code {short_code} was not found or has no statistics yet."
        )
    return url_stats


async def delete_url(url: URLDelete, conn: Connection):
    await urls_table.delete_url(url.id, conn)