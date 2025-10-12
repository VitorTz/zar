from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi import Request, status
from asyncpg import Connection
from src.schemas.urls import URLResponse, URLStats
from src.schemas.user import User
from src.tables import urls as urls_table
from src.globals import Globals
from user_agents import parse
from src import util
from uuid import UUID


async def get_urls(request: Request, limit: int, offset: int, conn: Connection):
    base_url = str(request.base_url).rstrip('/')
    total: int = await urls_table.count_urls(conn)    
    results = await urls_table.get_url_pages(base_url, limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return response


async def shorten(original_url: str, request: Request, conn: Connection, user: User | None = None):
    base_url = util.extract_base_url(request)
    r: dict | None = await urls_table.get_url_from_original_url(original_url, conn)

    if r:
        if user is not None:
            await urls_table.create_user_url(user.id, r['id'], conn)

        return URLResponse(
            id=r['id'],
            original_url=r['original_url'],
            short_url=f"{base_url}/{r['short_code']}",
            short_code=r['short_code'],
            clicks=r['clicks'],
            qr_code_url=r['qr_code_url']
        )
    
    new_url: dict = await urls_table.create_url(original_url, conn)

    if user is not None:
        await urls_table.create_user_url(user.id, new_url['id'], conn)

    return URLResponse(
        id=new_url['id'],
        original_url=new_url['original_url'],
        short_url=f"{base_url}/{new_url['short_code']}",
        short_code=new_url['short_code'],
        clicks=new_url['clicks'],
        qr_code_url=new_url['qr_code_url']
    )


async def log_click_event(url_id: UUID, request: Request, conn: Connection):    
    user_agent_string = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_string)
    
    ip_address = request.client.host
    
    # Geolocalização do IP
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
        url_id,
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
    url: dict = await urls_table.get_url(short_code, conn)
    
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL não encontrada")
    
    await log_click_event(url['id'], request, conn)
    await urls_table.update_clicks(url['id'], conn)

    return RedirectResponse(url=url['original_url'])


async def get_short_code_stats(short_code: str, conn: Connection):
    url: dict | None = await urls_table.get_url(short_code, conn)

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL não encontrada")
    
    return URLStats(
        id=url['id'],
        original_url=url['original_url'],
        short_code=url['short_code'],
        clicks=url['clicks'],
        created_at=url['created_at'],
        qr_code_url=url['qr_code_url']
    )


