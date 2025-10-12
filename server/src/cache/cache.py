from typing import Optional, Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from src.cache.config import CacheSettings
import redis.asyncio as redis
import json
import hashlib
import time
import asyncio


class RedisCache:

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        
    def generate_cache_key(self, request: Request) -> str:
        """Gera uma chave única para o cache baseada na URL e query parameters."""
        url_path = str(request.url.path)
        query_params = str(request.url.query)
        
        # Incluir alguns headers relevantes para diferenciação
        headers_to_include = ["authorization", "accept-language", "user-agent"]
        header_values = []
        for header in headers_to_include:
            if header in request.headers:
                # Limitar tamanho do header para evitar chaves muito longas
                header_value = request.headers[header][:50]
                header_values.append(f"{header}:{header_value}")
        
        # Criar string única
        cache_string = f"{url_path}?{query_params}|{','.join(header_values)}"
        
        # Hash para evitar chaves muito longas
        if len(cache_string) > CacheSettings.MAX_KEY_LENGTH:
            cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
            return f"{CacheSettings.CACHE_PREFIX}{cache_hash}"
        
        return f"{CacheSettings.CACHE_PREFIX}{cache_string.replace(' ', '_').replace('/', ':')}"

    def get_cache_ttl(self, request: Request) -> int:
        """Determina o TTL baseado na rota."""
        path = request.url.path
        
        # Verifica TTL específico para a rota
        for route_prefix, ttl in CacheSettings.ROUTE_TTL.items():
            if path.startswith(route_prefix):
                return ttl
        
        return CacheSettings.DEFAULT_TTL

    async def get_cached_response(self, cache_key: str) -> Optional[JSONResponse]:
        """Recupera resposta do cache."""
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                
                # Verificar se o cache não expirou manualmente
                cached_at = data.get("cached_at", 0)
                if time.time() - cached_at > CacheSettings.DEFAULT_TTL * 2:  # Dupla verificação
                    await self.redis_client.delete(cache_key)
                    return None
                
                return JSONResponse(
                    content=data["content"],
                    status_code=data["status_code"],
                    headers=data.get("headers", {}),
                    media_type=data.get("media_type", "application/json")
                )
        except (json.JSONDecodeError, KeyError, redis.RedisError) as e:
            print(f"Error retrieving cache: {e}")
            # Remover cache corrompido
            try:
                await self.redis_client.delete(cache_key)
            except:
                pass
        return None

    async def set_cached_response(self, cache_key: str, response: Response, ttl: int):
        """Armazena resposta no cache."""
        try:
            # Só cachear respostas de sucesso
            if response.status_code < 200 or response.status_code >= 300:
                return
            
            # Verificar tamanho da resposta (não cachear respostas muito grandes)
            response_body = None
            if hasattr(response, 'body') and response.body:
                if isinstance(response.body, bytes):
                    if len(response.body) > 1024 * 1024:  # 1MB limite
                        return
                    response_body = response.body.decode('utf-8')
                else:
                    response_body = str(response.body)
                    if len(response_body) > 1024 * 1024:  # 1MB limite
                        return
            elif hasattr(response, 'content') and response.content:
                response_body = response.content
                if len(str(response_body)) > 1024 * 1024:  # 1MB limite
                    return
            
            if response_body:
                try:
                    # Tentar parsear como JSON
                    if isinstance(response_body, str):
                        try:
                            content = json.loads(response_body)
                        except json.JSONDecodeError:
                            content = response_body
                    else:
                        content = response_body
                        
                    # Filtrar headers sensíveis
                    safe_headers = {}
                    sensitive_headers = ['set-cookie', 'authorization', 'x-api-key']
                    for key, value in dict(response.headers).items():
                        if key.lower() not in sensitive_headers:
                            safe_headers[key] = value
                            
                    cache_data = {
                        "content": content,
                        "status_code": response.status_code,
                        "headers": safe_headers,
                        "media_type": getattr(response, 'media_type', 'application/json'),
                        "cached_at": time.time()
                    }
                    
                    await self.redis_client.setex(
                        cache_key, 
                        ttl, 
                        json.dumps(cache_data, ensure_ascii=False, separators=(',', ':'))
                    )
                except Exception as e:
                    print(f"Error serializing cache data: {e}")
        except Exception as e:
            print(f"Error setting cache: {e}")

    def should_cache_request(self, request: Request) -> bool:
        """Determina se a requisição deve ser cacheada."""
        # Só cachear métodos GET
        if request.method != "GET":
            return False
            
        # Não cachear se tem parâmetros sensíveis
        query_lower = str(request.url.query).lower()
        sensitive_params = ['password', 'token', 'key', 'secret']
        if any(param in query_lower for param in sensitive_params):
            return False
            
        # Não cachear rotas específicas
        for path in CacheSettings.NO_CACHE_PATHS:
            if request.url.path.startswith(path):
                return False
                
        # Não cachear se tem header no-cache
        cache_control = request.headers.get("cache-control", "").lower()
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
            
        # Não cachear requests com authorization (podem ser específicos do usuário)
        if request.headers.get("authorization"):
            # Exceto para rotas públicas
            if not request.url.path.startswith("/public/"):
                return False
                
        return True

    async def cache_middleware(self, request: Request, call_next):
        """Middleware para gerenciar cache."""
        # Verificar se deve cachear
        if not self.should_cache_request(request):
            response = await call_next(request)
            response.headers["X-Cache"] = "BYPASS"
            return response
        
        # Gerar chave do cache
        cache_key = self.generate_cache_key(request)
        
        # Tentar recuperar do cache
        cached_response = await self.get_cached_response(cache_key)
        if cached_response:
            # Adicionar headers indicando que veio do cache
            cached_response.headers["X-Cache"] = "HIT"
            cached_response.headers["X-Cache-Key"] = cache_key.split(":")[-1][:20]  # Só os últimos 20 chars
            return cached_response
        
        # Executar requisição normal
        response = await call_next(request)
        
        # Cachear a resposta se apropriado
        if isinstance(response, (JSONResponse, Response)) and response.status_code == 200:
            ttl = self.get_cache_ttl(request)
            # Executar cache em background para não afetar a resposta
            asyncio.create_task(self.set_cached_response(cache_key, response, ttl))
            
        # Adicionar headers indicando que não veio do cache
        response.headers["X-Cache"] = "MISS"
        response.headers["X-Cache-Key"] = cache_key.split(":")[-1][:20]  # Só os últimos 20 chars
        
        return response

    async def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalida cache baseado em um padrão."""
        try:
            keys = await self.redis_client.keys(f"{CacheSettings.CACHE_PREFIX}*{pattern}*")
            if keys:
                await self.redis_client.delete(*keys)
                return len(keys)
        except redis.RedisError as e:
            print(f"Error invalidating cache: {e}")
        return 0

    async def clear_all_cache(self) -> int:
        """Limpa todo o cache."""
        try:
            keys = await self.redis_client.keys(f"{CacheSettings.CACHE_PREFIX}*")
            if keys:
                await self.redis_client.delete(*keys)
                return len(keys)
        except redis.RedisError as e:
            print(f"Error clearing cache: {e}")
        return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        try:
            keys = await self.redis_client.keys(f"{CacheSettings.CACHE_PREFIX}*")
            total_keys = len(keys)
            
            # Estatísticas por tipo de rota
            route_stats = {}
            for key in keys:
                # Extrair informação da rota da chave
                try:
                    key_info = await self.redis_client.get(key)
                    if key_info:
                        data = json.loads(key_info)
                        # Estimar rota baseado na chave (simplificado)
                        route_type = "unknown"
                        if "public" in key:
                            route_type = "public"
                        elif "admin" in key:
                            route_type = "admin"
                        elif "manager" in key:
                            route_type = "manager"
                        
                        if route_type not in route_stats:
                            route_stats[route_type] = 0
                        route_stats[route_type] += 1
                except:
                    continue
            
            # Informações sobre o Redis
            info = await self.redis_client.info()
            memory_used = info.get('used_memory_human', 'N/A')
            
            return {
                "total_cached_keys": total_keys,
                "route_stats": route_stats,
                "memory_used": memory_used,
                "cache_prefix": CacheSettings.CACHE_PREFIX,
                "default_ttl": CacheSettings.DEFAULT_TTL,
                "route_ttl_config": CacheSettings.ROUTE_TTL
            }
        except redis.RedisError as e:
            print(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Verifica a saúde do sistema de cache."""
        try:
            # Teste de ping
            ping_result = await self.redis_client.ping()
            
            # Teste de escrita/leitura
            test_key = f"{CacheSettings.CACHE_PREFIX}health_check"
            await self.redis_client.setex(test_key, 10, "test_value")
            test_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            return {
                "status": "healthy",
                "ping": ping_result,
                "write_test": test_value == "test_value"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
        