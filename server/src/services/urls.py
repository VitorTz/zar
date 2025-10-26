from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi import Request, status
from asyncpg import Connection
from src.schemas.urls import URLCreate, UrlRedirect, URLResponse, UrlStats, URLAdminResponse
from src.schemas.pagination import Pagination
from src.schemas.user import User
from src.schemas.token import SessionToken
from src.schemas.domain import Domain
from src.services import domain as domain_service
from src.tables import urls as urls_table
from src.tables import users as users_table
from src.tables import domains as domains_table
from src import security
from typing import Optional
from src import util


async def get_urls(
    request: Request, 
    limit: int, 
    offset: int, 
    conn: Connection
) -> Pagination[URLAdminResponse]:
    return await urls_table.get_url_pages(
        util.extract_base_url(request), 
        None,
        limit, 
        offset, 
        conn
    )


async def shorten(url: URLCreate, refresh_token: Optional[str], request: Request, conn: Connection, user: Optional[User] = None) -> JSONResponse:
    base_url: str = util.extract_base_url(request)
    domain: Domain = await domains_table.get_domain(str(url.url), conn)

    if not domain.is_secure or not await domain_service.is_safe_domain(request, domain, conn):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL potencialmente maliciosa!.")

    if user is None:
        url_response = await urls_table.get_anonymous_url(domain, base_url, conn)
    else:
        url_response = await urls_table.get_user_url(domain, base_url, user.id, url.title, conn)

    if url_response is None:
        if user:
            url_response = await urls_table.create_user_url(domain, url, user, base_url, conn)
        else:
            url_response = await urls_table.create_anonymous_url(domain, url, base_url, conn)
    
    response = url_response

    if not user and refresh_token:
        user = await users_table.get_user_by_refresh_token(refresh_token, conn)
        if user:
            session_token: SessionToken = security.create_session_token(user.id)
            await users_table.update_user_session_token(user.id, session_token, conn)
            response = JSONResponse(content=url_response.model_dump(mode="json"))
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL não encontrada")
    
    if util.datetime_has_expired(url.expires_at):
        return RedirectResponse(
            url=f"/url/expired/?original_url={url.original_url}&expired_at={url.expires_at}",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
    
    if url.p_hash:
        return HTMLResponse(content=get_password_page_html(short_code))    
    
    await urls_table.add_click_event(url.id, request, conn)
    
    return RedirectResponse(
        url=url.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


async def verify_password_and_redirect(
    short_code: str, 
    password: str, 
    request: Request, 
    conn: Connection
) -> RedirectResponse:
    url: Optional[UrlRedirect] = await urls_table.get_redirect_url(short_code, conn)
    
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL não encontrada")
        
    if util.datetime_has_expired(url.expires_at):
        return RedirectResponse(
            url=f"/url/expired/?original_url={url['original_url']}&expired_at={url['expires_at']}"
        )
        
    if not url.p_hash:
        await urls_table.add_click_event(url.id, request, conn)
        return RedirectResponse(
            url=url.original_url,
            status_code=status.HTTP_303_SEE_OTHER
        )    

    if not security.verify_password(password, url.p_hash):
        return HTMLResponse(
            content=get_password_page_html(short_code, error=True),
            status_code=401
        )
    
    await urls_table.add_click_event(url.id, request, conn)

    return RedirectResponse(
        url=url.original_url, 
        status_code=status.HTTP_303_SEE_OTHER
    )


async def get_url_stats(short_code: str, conn: Connection) -> UrlStats:
    url_id = await urls_table.get_url_id_by_short_code(short_code, conn)
    if url_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with short code {short_code} has no statistics yet."
        )
    
    url_stats: Optional[UrlStats] = await urls_table.get_url_stats(url_id, conn)
    if url_stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with short code {short_code} has no statistics yet."
        )
    return url_stats


def get_password_page_html(short_code: str, error: bool = False) -> str:
    error_message = """
        <div style="background-color: #fee; border: 1px solid #fcc; color: #c33; padding: 12px; border-radius: 6px; margin-bottom: 20px;">
            ❌ Senha incorreta. Tente novamente.
        </div>
    """ if error else ""
    
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>URL Protegida - Senha Necessária</title>
        <style>
            :root {{
                --background-color: #F8F9FA;
                --surface-color: #fff;
                --primary-color: #d8775a;
                --text-primary: #1e1e1e;
                --text-secondary: #a0a0a0;
                --danger-color: #cf6679;
                --border-color: #2c2c2c;
            }}
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                margin: 0;
                font-family: 'Inter', sans-serif;
                background-color: var(--background-color);
                color: var(--text-primary);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                padding: 1rem;
                box-sizing: border-box;
            }}
            
            .container {{
                background-color: var(--surface-color);
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                max-width: 400px;
                width: 100%;
            }}
            
            .lock-icon {{
                font-size: 48px;
                text-align: center;
                margin-bottom: 20px;
            }}
            
            h1 {{
                font-size: 24px;
                color: var(--text-primary);
                text-align: center;
                margin-bottom: 10px;
            }}
            
            .subtitle {{
                color: var(--text-primary);
                text-align: center;
                margin-bottom: 30px;
                font-size: 14px;
            }}
            
            .form-group {{
                margin-bottom: 20px;
            }}
            
            label {{
                display: block;
                color: #555;
                font-weight: 500;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            
            input[type="password"] {{
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }}
            
            input[type="password"]:focus {{
                outline: none;
                border-color: var(--primary-color);
            }}
            
            button {{
                width: 100%;
                padding: 14px;
                background: var(--primary-color);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            }}
            
            button:active {{
                transform: translateY(0);
            }}
            
            .short-code {{
                background: var(--background-color);
                padding: 8px 12px;
                border-radius: 6px;
                font-family: monospace;
                font-size: 16px;
                text-align: center;
                margin-bottom: 20px;
                color: var(--text-primary);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="short-code">/{short_code}</div>
            
            {error_message}
            
            <form method="POST" action="/{short_code}/verify">
                <div class="form-group">
                    <label for="password">Digite a senha:</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        required 
                        autofocus
                        placeholder="••••••••"
                    >
                </div>
                
                <button type="submit">Acessar URL</button>
            </form>
        </div>
    </body>
    </html>
    """