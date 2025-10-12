from dotenv import load_dotenv
import os


load_dotenv()


class CacheSettings:
    """Configurações centralizadas do sistema de cache"""
    
    # Configurações básicas do Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT"))
    REDIS_DB: int = int(os.getenv("REDIS_DB"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Configurações de TTL (Time To Live)
    DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL"))
    MIN_TTL: int = 30  # TTL mínimo
    MAX_TTL: int = 3600  # TTL máximo (1 hora)
    
    # Configurações de chave
    CACHE_PREFIX: str = os.getenv("CACHE_PREFIX")
    MAX_KEY_LENGTH: int = 250
    
    # Configurações de tamanho
    MAX_RESPONSE_SIZE: int = int(os.getenv("CACHE_MAX_RESPONSE_SIZE"))
    
    # TTL específicos por rota (em segundos)
    ROUTE_TTL: dict[str, int] = {
        "/public/geo": int(os.getenv("CACHE_TTL_PUBLIC_GEO")),
        "/public": int(os.getenv("CACHE_TTL_PUBLIC")),
        "/manager/places": int(os.getenv("CACHE_TTL_MANAGER_PLACES")),
        "/manager/employees": int(os.getenv("CACHE_TTL_MANAGER_EMPLOYEES")),
        "/admin": int(os.getenv("CACHE_TTL_ADMIN"))
    }
    
    # Rotas que nunca devem ser cacheadas
    NO_CACHE_PATHS: list[str] = [
        "/favicon.ico",
        "/static",
        "/admin",
        "/manager/auth"
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
