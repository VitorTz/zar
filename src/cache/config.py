from dotenv import load_dotenv
from src.constants import Constants
import os


load_dotenv()


REDIS_URL = os.getenv("REDIS_URL") if Constants.IS_PRODUCTION else os.getenv("REDIS_URL_DEV")


class CacheSettings:

    REDIS_URL: str = REDIS_URL
    
    # TTL
    DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL"))
    MIN_TTL: int = 30
    MAX_TTL: int = 3600
        
    CACHE_PREFIX: str = os.getenv("CACHE_PREFIX")
    MAX_KEY_LENGTH: int = 250    
    
    # TTL específicos por rota (em segundos)
    ROUTE_TTL: dict[str, int] = {
        "/admin": int(os.getenv("CACHE_TTL_ADMIN"))
    }
    
    # Rotas que nunca devem ser cacheadas
    NO_CACHE_PATHS: list[str] = [
        "/favicon.ico",
        "/static",
        "/admin",
        "/auth"
    ]
    
    # Parâmetros sensíveis que impedem cache
    SENSITIVE_PARAMS: list[str] = [
        "password",
        "token",
        "key", 
        "secret",
        "auth",
        "session"
    ]
    
    # Headers sensíveis que não devem ser cacheados
    SENSITIVE_HEADERS: list[str] = [
        "set-cookie",
        "authorization", 
        "x-api-key",
        "x-auth-token",
        "cookie"
    ]
    
    # Headers que devem ser considerados na chave do cache
    CACHE_KEY_HEADERS: list[str] = [
        "accept-language",
        "user-agent",
        "accept"
    ]
    
    # Configurações de ambiente
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE") == "1"
    CACHE_DEBUG: bool = os.getenv("CACHE_DEBUG") == "1"
    LOG_CACHE_STATS: bool = os.getenv("LOG_CACHE_STATS") == "1"
    
    # Configurações de performance
    CACHE_CLEANUP_INTERVAL: int = int(os.getenv("CACHE_CLEANUP_INTERVAL"))
    MAX_CONCURRENT_CACHE_OPS: int = int(os.getenv("MAX_CONCURRENT_CACHE_OPS"))
