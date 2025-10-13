from src.globals import Globals
from asyncpg import Connection
from src.constants import Constants
from src.tables import url_blacklist as url_blacklist_table
import httpx


async def is_valid_url(url: str, conn: Connection) -> bool:
    cache_key = f"safe_browsing:{url}"
    
    # Short time storage
    cached = await Globals.redis_client.get(cache_key)
    if cached is not None:
        return cached == "safe"
    
    # Long time storage
    if await url_blacklist_table.is_url_in_blacklist(url, conn):
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
                await url_blacklist_table.add_url_to_blacklist(url, conn)
                return False

            await Globals.redis_client.setex(cache_key, Constants.SAFE_CACHE_TTL, "safe")
            return True
    except httpx.RequestError:
        return False