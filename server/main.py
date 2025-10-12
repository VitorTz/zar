from fastapi import FastAPI, Request, status
from fastapi.responses import Response, FileResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware
from src.constants import Constants
from src.cache.config import CacheSettings
from src.services import logs as log_service
from src import util
from src.db import db_init, db_close
from src.perf.system_monitor import get_monitor
from src.globals import Globals
from src import middleware
from src.routes import shortener
from src.routes import admin
from src.routes import auth
from src.routes import user
from src.routes import metrics
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
    print("🚀 Starting ZAR API...")
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

    print("👋 Shutting down ZAR API...")



app = FastAPI(
    title=os.getenv("API_NAME"), 
    description=os.getenv("API_DESCR"),
    version=os.getenv("API_VERSION"),
    lifespan=lifespan
)


app.include_router(shortener.router, tags=["shorten"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])


templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


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


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join("static", "favicon.ico")
    return FileResponse(favicon_path)



########################## MIDDLEWARES ##########################
#################################################################

@app.middleware("http")
async def http_middleware(request: Request, call_next):
    if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
        response = await call_next(request)
        return response
    
    monitor = get_monitor()
    start_time = time.perf_counter()

    # Check body size
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

    # Continue request
    response: Response = await call_next(request)

    # Add rate limit headers
    remaining = max(Constants.MAX_REQUESTS - current, 0)
    response.headers["X-RateLimit-Limit"] = str(Constants.MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(ttl)

    # Existing security + monitoring
    middleware.add_security_headers(request, response)
    response_time_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
    monitor.increment_request(response_time_ms)

    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return await log_service.log_and_build_response(
        request=request,
        exc=exc,
        error_level="WARNING" if exc.status_code < 500 else "ERROR",
        status_code=exc.status_code,
        detail=exc.detail
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await log_service.log_and_build_response(
        request=request,
        exc=exc,
        error_level="WARNING",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith(("/openapi.json", "/docs", "/redoc")):
        raise exc
    return await log_service.log_and_build_response(
        request=request,
        exc=exc,
        error_level="CRITICAL",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )

