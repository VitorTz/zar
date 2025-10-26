from fastapi import FastAPI, Request, status
from fastapi.responses import Response, FileResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware
from src.constants import Constants
from src.cache.config import CacheSettings
from src.services import logs as log_service
from src.db import db_init, db_close
from src.perf.system_monitor import get_monitor
from src.globals import Globals
from src import middleware
from src.routes import shortener
from src.routes import admin
from src.routes import users_admin
from src.routes import auth
from src.routes import logs_admin
from src.routes import urls_admin
from src.routes import time_perf_admin
from src.routes import domains_admin
from src.routes import user
from src import util
import redis.asyncio as redis
import time
import contextlib
import asyncio
import os


async def init_redis_cache():
    if CacheSettings.CACHE_DEBUG:
        print(f"[CACHE CONFIG] Redis: {CacheSettings.REDIS_HOST}:{CacheSettings.REDIS_PORT}")
        print(f"[CACHE CONFIG] Default TTL: {CacheSettings.DEFAULT_TTL}s")
        print(f"[CACHE CONFIG] Cache Enabled: {CacheSettings.ENABLE_CACHE}")
        print(f"[CACHE CONFIG] Route TTLs: {CacheSettings.ROUTE_TTL}")
        print(f"[CACHE CONFIG] No-cache paths: {len(CacheSettings.NO_CACHE_PATHS)} paths")
    try:
        await Globals.redis_client.ping()
        health = await Globals.cache_service.health_check()
        if health["status"] == "healthy":
            print("[REDIS CONNECTED]")
            print("[CACHE SERVICE READY]")
        else:
            print(f"[CACHE SERVICE WARNING]: {health}")
    except redis.RedisError as e:
        print(f"[REDIS ERROR]: {e}")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Starting {Constants.API_NAME}]")
    # System Monitor
    task = asyncio.create_task(util.periodic_update())

    # Dir
    Constants.TMP_DIR.mkdir(exist_ok=True)
    Constants.LOG_DIR.mkdir(exist_ok=True)

    # Database
    await db_init()
    
    # Redis
    await init_redis_cache()

    yield
    
    # SystemMonitor
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    # Database
    await db_close()    
    
    # Redis
    await Globals.redis_client.aclose()

    print(f"[Shutting down {Constants.API_NAME}]")



app = FastAPI(    
    title=Constants.API_NAME, 
    description=Constants.API_DESCR,
    version=Constants.API_VERSION,
    lifespan=lifespan    
)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return { "status": "ok" }


@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join("static", "favicon.ico")
    return FileResponse(favicon_path)


app.include_router(shortener.router, prefix='/api/v1', tags=["shorten"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(users_admin.router, prefix="/api/v1/admin", tags=["admin_users"])
app.include_router(urls_admin.router, prefix="/api/v1/admin", tags=["admin_urls"])
app.include_router(logs_admin.router, prefix="/api/v1/admin", tags=["admin_logs"])
app.include_router(time_perf_admin.router, prefix="/api/v1/admin", tags=["admin_time_perf"])
app.include_router(domains_admin.router, prefix="/api/v1/admin", tags=["admin_domains"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


########################## MIDDLEWARES ##########################
#################################################################

@app.middleware("http")
async def http_middleware(request: Request, call_next):
    if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
        response = await call_next(request)
        return response
    
    monitor = get_monitor()
    start_time = time.perf_counter()
    
    # Body size check
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > Constants.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request entity too large. Max allowed: {Constants.MAX_BODY_SIZE} bytes"
            )
    else:
        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > Constants.MAX_BODY_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request entity too large. Max allowed: {Constants.MAX_BODY_SIZE} bytes"
                )
        request._body = body
    
    # Rate limit check
    identifier = util.get_client_identifier(request)
    key = f"rate_limit:{identifier}"
    
    pipe = Globals.redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, Constants.WINDOW)
    results = await pipe.execute()
    
    current = results[0]
    ttl = await Globals.redis_client.ttl(key)
    
    if current > Constants.MAX_REQUESTS:
        await log_service.log_rate_limit_violation(
            request=request,
            identifier=identifier,
            attempts=current,
            ttl=ttl
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too many requests",
                "message": f"Rate limit exceeded. Try again in {ttl} seconds.",
                "retry_after": ttl,
                "limit": Constants.MAX_REQUESTS,
                "window": Constants.WINDOW
            },
            headers={
                "Retry-After": str(ttl),
                "X-RateLimit-Limit": str(Constants.MAX_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(ttl)
            }
        )
    
    # Headers
    response: Response = await call_next(request)
        
    remaining = max(Constants.MAX_REQUESTS - current, 0)
    response.headers["X-RateLimit-Limit"] = str(Constants.MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(ttl)
        
    middleware.add_security_headers(request, response)
    response_time_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
    
    # System Monitor
    monitor.increment_request(response_time_ms)

    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return await log_service.log_and_build_response(
        request=request,
        exc=exc,
        error_level="WARN" if exc.status_code < 500 else "ERROR",
        status_code=exc.status_code,
        detail=exc.detail
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await log_service.log_and_build_response(
        request=request,
        exc=exc,
        error_level="WARN",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return await log_service.log_and_build_response(
        request=request,
        exc=exc,
        error_level="FATAL",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )

