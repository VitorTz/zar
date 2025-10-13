from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import Request, status
from asyncpg import Connection
from src.schemas.urls import URLCreate
from src.schemas.url_stats import URLStatsResponse
from src.schemas.user import User
from src.services import url_blacklist as url_blacklis_service
from src.tables import urls as urls_table
from src.globals import Globals
from user_agents import parse
from src import util
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


async def shorten(url: URLCreate, request: Request, conn: Connection, user: User | None = None):    
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
    
    return JSONResponse(url_response)


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


async def redirect_from_short_code(short_code: str, request: Request, conn: Connection):
    original_url: str = await urls_table.get_original_url(short_code, conn)
    
    if original_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL não encontrada")
    
    await register_click_event(short_code, request, conn)
    await urls_table.update_clicks(short_code, conn)

    return RedirectResponse(url=original_url)


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