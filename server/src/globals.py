from fastapi.security import OAuth2PasswordBearer
from src.cache.cache import RedisCache
from src.cache.config import CacheSettings
import geoip2.database
import redis.asyncio as redis


class Globals:
    
    oauth2_admin_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/admin-login")
    redis_client = redis.Redis(host=CacheSettings.REDIS_HOST, port=CacheSettings.REDIS_PORT, decode_responses=True)
    cache_service = RedisCache(redis_client)
    geoip_reader = geoip2.database.Reader('res/GeoLite2-City.mmdb')