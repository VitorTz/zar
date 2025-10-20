from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi import Request, status
from asyncpg import Connection
from urllib.parse import urlparse
from src.schemas.urls import URLCreate
from src.schemas.url_stats import URLStatsResponse
from src.schemas.user import User
from src.services import url_blacklist as url_blacklist_service
from src.tables import urls as urls_table
from src.tables import users as users_table
from src import security
from src.globals import Globals
from user_agents import parse
from src import util
from datetime import datetime, timezone
import bcrypt
import aiohttp
import json


async def get_urls(request: Request, limit: int, offset: int, conn: Connection):
    base_url: str = util.extract_base_url(request)
    total, results = await urls_table.get_url_pages(base_url, limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return response


async def shorten(url: URLCreate, refresh_token: str | None, request: Request, conn: Connection, user: User | None = None):
    base_url: str = util.extract_base_url(request)
    original_url = str(url.url)
    # Security
    if not await url_blacklist_service.url_is_in_blacklist(original_url, conn):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL potencialmente maliciosa!.")    

    # Update user session
    access_token = None
    expires_at = None
    if not user and refresh_token:
        user: User | None = await users_table.get_user_by_refresh_token(refresh_token, conn)
        if user:
            access_token, _, expires_at = security.create_session_token(user.id)
            await users_table.update_user_session_token(
                user.id,
                refresh_token,
                expires_at,
                conn        
            )         
    
    # Fetch existing url
    is_new_url = False
    if url.expires_at or url.password:
        is_new_url = True
    elif not user:
        url_response: dict | None = await urls_table.get_anonymous_url(original_url, base_url, url.title, conn)
        is_new_url = url_response is None
    else:
        url_response: dict | None = await urls_table.get_user_url(original_url, base_url, user.id, url.title, conn)
        is_new_url = url_response is None
    
    # Create url
    if is_new_url and user is None:
        url_response: dict = await urls_table.create_anonymous_url(url, base_url, conn)
    elif is_new_url and user is not None:
        url_response: dict = await urls_table.create_user_url(url, user, base_url, conn)
        
    if is_new_url or not url_response['qrcode_url']:
        qrcode_url: str = await util.create_qrcode(url_response['short_url'])
        await urls_table.set_url_qrcode(url_response['short_code'], qrcode_url, conn)
        url_response['qrcode_url'] = qrcode_url
    
    # Response
    response = JSONResponse(url_response)
    if access_token and refresh_token:
        security.set_access_cookie(response, access_token, refresh_token)
    return response


async def register_click_event(short_code: str, request: Request, conn: Connection):    
    user_agent_string = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_string)
    
    ip_address = request.client.host
    
    # GEO
    country_code = None
    city = None
    if Globals.geoip_reader and ip_address:
        try:
            response = Globals.geoip_reader.city(ip_address)
            country_code = response.country.iso_code
            city = response.city.name
        except Exception:
            pass
    
    if user_agent.is_mobile:
        device_type = 'mobile'
    elif user_agent.is_tablet:
        device_type = 'tablet'
    elif user_agent.is_pc:
        device_type = 'desktop'
    elif user_agent.is_bot:
        device_type = 'bot'
    else:
        device_type = 'unknown'    

    await urls_table.create_url_analytic(
        short_code,
        ip_address,
        country_code,
        city,
        user_agent_string[:255] if user_agent_string else None,
        request.headers.get("referer"),
        device_type,
        user_agent.browser.family,
        user_agent.os.family,
        conn
    )


def url_has_expired(url: dict) -> bool:
    if url.get('expires_at') and isinstance(url['expires_at'], datetime):
        if url['expires_at'] < datetime.now(timezone.utc):
            return True
    return False
        

async def redirect_from_short_code(short_code: str, request: Request, conn: Connection):
    url: dict | None = await urls_table.get_redirect_url(short_code, conn)

    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL não encontrada")
    
    if url_has_expired(url):
        return RedirectResponse(
            url=f"/url/expired/?original_url={url['original_url']}&expired_at={url['expires_at']}",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
    
    if url['p_hash']:
        return HTMLResponse(content=get_password_page_html(short_code))    
    
    await register_click_event(short_code, request, conn)
    await urls_table.update_clicks(short_code, conn)
    
    return RedirectResponse(url=url['original_url'], status_code=status.HTTP_307_TEMPORARY_REDIRECT)


async def fetch_page_metadata(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5, allow_redirects=True) as resp:
                html = await resp.text(errors="ignore")
                title = ""
                favicon = ""

                # Extrai <title>
                start = html.find("<title>")
                end = html.find("</title>")
                if start != -1 and end != -1:
                    title = html[start + 7:end].strip()

                # Extrai favicon
                icon_pos = html.find('rel="icon"')
                if icon_pos != -1:
                    href_start = html.rfind('href="', 0, icon_pos)
                    href_end = html.find('"', href_start + 6)
                    if href_start != -1 and href_end != -1:
                        favicon = html[href_start + 6:href_end]
                        if favicon.startswith("/"):
                            parsed = urlparse(url)
                            favicon = f"{parsed.scheme}://{parsed.netloc}{favicon}"

                return {
                    "title": title or "(sem título)",
                    "favicon": favicon or "https://www.google.com/s2/favicons?domain=" + urlparse(url).netloc,
                    "status": resp.status,
                }
    except Exception:
        return {"title": "(indisponível)", "favicon": "", "status": "erro"}
    

async def verify_password_and_redirect(
    short_code: str, 
    password: str, 
    request: Request, 
    conn: Connection
):
    url: dict | None = await urls_table.get_redirect_url(short_code, conn)
    
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL não encontrada")
        
    if url_has_expired(url):
        return RedirectResponse(
            url=f"/url/expired/?original_url={url['original_url']}&expired_at={url['expires_at']}"
        )
        
    if not url['p_hash']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta URL não requer senha")
        
    password_correct = bcrypt.checkpw(
        password.encode('utf-8'),
        url['p_hash']
    )
    
    if not password_correct:        
        return HTMLResponse(
            content=get_password_page_html(short_code, error=True),
            status_code=401
        )
    
    await register_click_event(short_code, request, conn)
    await urls_table.update_clicks(short_code, conn)
    
    return RedirectResponse(
        url=url['original_url'],
        status_code=status.HTTP_303_SEE_OTHER
    )


async def get_url_stats(short_code: str, conn: Connection):
    result = await conn.fetchrow(
        '''
        SELECT
            short_code,
            total_clicks,
            unique_visitors,
            TO_CHAR(first_click, 'DD-MM-YYYY HH24:MI:SS') AS first_click,
            TO_CHAR(last_click, 'DD-MM-YYYY HH24:MI:SS') AS last_click,
            timeline,
            devices,
            browsers,
            top_countries,
            top_cities,
            operating_systems,
            top_referers
        FROM 
            vw_url_stats
        WHERE 
            short_code = $1
        ''',
        short_code
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statistics not found for URL: {short_code}"
        )
    
    # Converter para dict
    data = dict(result)
        
    json_fields = [
        "timeline", "devices", "browsers", 
        "top_countries", "top_cities", 
        "operating_systems", "top_referers"
    ]
    
    for field in json_fields:
        value = data.get(field)
        if isinstance(value, str):
            try:
                data[field] = json.loads(value)
            except json.JSONDecodeError:
                data[field] = [] if field in ["timeline", "top_countries", "top_cities", "top_referers"] else {}
    
    return URLStatsResponse(**data)


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