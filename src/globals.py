from fastapi.security import OAuth2PasswordBearer
from src.cache.cache import RedisCache
from src.cache.config import CacheSettings
import redis.asyncio as redis
import IP2Location


# Yanille uses the IP2Location LITE database for <a href="https://lite.ip2location.com">IP geolocation</a>.


class Globals:
    
    oauth2_admin_scheme = OAuth2PasswordBearer(tokenUrl="/admin/admin-login")
    redis_client = redis.from_url(CacheSettings.REDIS_URL, decode_responses=True)
    cache_service = RedisCache(redis_client)
    geoip_reader = IP2Location.IP2Location("res/IP2LOCATION-LITE-DB1.BIN")