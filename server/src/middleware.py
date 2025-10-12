from fastapi import Request, status
from fastapi.responses import Response
from fastapi.exceptions import HTTPException
from src.constants import Constants
from src.globals import Globals


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
            
    return request.client.host


async def check_rate_limit(request: Request):
    identifier = get_client_identifier(request)
    
    key = f"rate_limit:{identifier}"
        
    pipe = Globals.redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, Constants.WINDOW)
    results = await pipe.execute()
    
    current = results[0]
    
    if current > Constants.MAX_REQUESTS:       
        ttl = await Globals.redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too many requests",
                "message": f"Rate limit exceeded. Try again in {ttl} seconds.",
                "retry_after": ttl,
                "limit": Constants.MAX_REQUESTS,
                "window": Constants.WINDOW
            },
            headers={"Retry-After": str(ttl)}
        )


def add_security_headers(request: Request, response: Response) -> None:
    is_api_endpoint = request.url.path.startswith("/api/")
    
    # =========================================================================
    # HEADERS SEMPRE INCLUÍDOS
    # =========================================================================    
    response.headers["X-Content-Type-Options"] = "nosniff"    
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"    
    response.headers["Permissions-Policy"] = Constants.PERMISSIONS_POLICY_HEADER
    
    # =========================================================================
    # HSTS - APENAS EM PRODUÇÃO COM HTTPS
    # =========================================================================
    if Constants.IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = ("max-age=31536000; includeSubDomains; preload")
    
    # =========================================================================
    # CONTENT SECURITY POLICY
    # =========================================================================
    
    # Para API pura (sem frontend)
    if is_api_endpoint:
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none';"
        )
    else:
        # Para páginas HTML/frontend
        response.headers["Content-Security-Policy"] = Constants.CONTENT_SECURITY_HEADER
    
    # =========================================================================
    # CACHE CONTROL - BASEADO NO TIPO DE CONTEÚDO
    # =========================================================================
    is_sensitive = any(request.url.path.startswith(path) for path in Constants.SENSITIVE_PATHS)
    
    if is_sensitive or is_api_endpoint:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    else:
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-cache"


async def check_body_stream(request: Request):        
    content_length = request.headers.get("content-length")
    if content_length:
        content_length = int(content_length)
        if content_length > Constants.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request entity too large. Maximum size allowed: {Constants.MAX_BODY_SIZE} bytes"
            )
        
    if hasattr(request, '_body'):
        body_size = len(request._body) if request._body else 0
        if body_size > Constants.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request entity too large. Maximum size allowed: {Constants.MAX_BODY_SIZE} bytes"
            )
    else:
        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > Constants.MAX_BODY_SIZE:
                raise HTTPException(
                status_code=413,
                detail=f"Request entity too large. Maximum size allowed: {Constants.MAX_BODY_SIZE} bytes"
            )        
        request._body = body


async def check_request(request: Request):
    await check_rate_limit(request)    
    await check_body_stream(request)    