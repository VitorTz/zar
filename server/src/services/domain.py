from src.constants import Constants
from src.globals import Globals
from asyncpg import Connection
from src.schemas.domain import DomainCreate, DomainDelete
from src.tables import domains as domains_table
from src.tables import urls as urls_table
import httpx


async def create_domain(domain: DomainCreate, conn: Connection):
    await domains_table.create_domain(str(domain.url), domain.is_secure, conn)
    if not domain.is_secure:
        await urls_table.delete_urls_by_domain(conn)


async def delete_domain(domain: DomainDelete, conn: Connection):
    await domains_table.delete_domain_by_id(domain.id, conn)


async def is_secure_domain(url: str, conn: Connection) -> bool:
    cache_key = f"safe_browsing:{url}"
    
    # Short time storage
    cached = await Globals.redis_client.get(cache_key)
    if cached is not None:
        return cached == "safe"
    
    # Long time storage
    if await domains_table.is_safe_domain(url, conn):
        return False
    
    body = {
        "client": {"clientId": "fastapi-url-shortener", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(Constants.SAFE_BROWSING_URL, json=body)
            resp.raise_for_status()
            data = resp.json()

            if data.get("matches"):
                await Globals.redis_client.setex(cache_key, Constants.SAFE_CACHE_TTL, "unsafe")
                await domains_table.create_domain(url, False, conn)
                return False

            await Globals.redis_client.setex(cache_key, Constants.SAFE_CACHE_TTL, "safe")
            return True
    except httpx.RequestError:
        return False