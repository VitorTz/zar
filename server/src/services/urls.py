from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi import Request, status
from asyncpg import Connection
from src.schemas.urls import URLCreate
from src.schemas.url_stats import URLStatsResponse
from src.schemas.user import User
from src.services import url_blacklist as url_blacklis_service
from src.tables import urls as urls_table
from src.tables import users as users_table
from src import security
import bcrypt
from src.globals import Globals
from user_agents import parse
from src import util
from datetime import datetime, timezone
import json


async def get_urls(request: Request, limit: int, offset: int, conn: Connection):
    base_url = str(request.base_url).rstrip('/')
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

    # Create url
    base_url: str = util.extract_base_url(request)
    original_url = str(url.url)

    if not await url_blacklis_service.is_valid_url(original_url, conn):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL maliciosa detectada pela Google Safe Browsing API.")

    if not user:
        url_response: dict | None = await urls_table.get_anonymous_url(original_url, base_url, conn)
    else:
        url_response: dict | None = await urls_table.get_user_url(original_url, base_url, user.id, conn)
    
    is_new_url = url_response is None
    
    if is_new_url and user is None:
        url_response: dict = await urls_table.create_anonymous_url(url, base_url, conn)
    elif is_new_url and user is not None:
        url_response: dict = await urls_table.create_user_url(url, user, base_url, conn)
        
    if is_new_url:
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
        return RedirectResponse(url=f"/url/expired/?original_url={url['original_url']}&expired_at={url['expires_at']}")
    
    if url['p_hash']:
        return HTMLResponse(content=get_password_page_html(short_code))    
    
    await register_click_event(short_code, request, conn)
    await urls_table.update_clicks(short_code, conn)

    return RedirectResponse(url=url['original_url'])


async def verify_password_and_redirect(
    short_code: str, 
    password: str, 
    request: Request, 
    conn: Connection
):
    """Verifica a senha e redireciona se estiver correta"""
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
    return RedirectResponse(url=url['original_url'])


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
    """Retorna o HTML da página de verificação de senha"""
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
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            
            .container {{
                background: white;
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
                color: #333;
                text-align: center;
                margin-bottom: 10px;
            }}
            
            .subtitle {{
                color: #666;
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
                border-color: #667eea;
            }}
            
            button {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                background: #f5f5f5;
                padding: 8px 12px;
                border-radius: 6px;
                font-family: monospace;
                font-size: 14px;
                text-align: center;
                margin-bottom: 20px;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="lock-icon">🔒</div>
            <h1>URL Protegida</h1>
            <p class="subtitle">Esta URL requer uma senha para acesso</p>
            
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