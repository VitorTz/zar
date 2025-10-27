from src.perf.system_monitor import get_monitor
from src.schemas.client_info import ClientInfo
from src.cache.config import CacheSettings
from src.globals import Globals
from fastapi import Request
from pathlib import Path
from asyncpg import Connection
from src.s3 import S3
from datetime import datetime, timezone
from typing import Optional, Any
from urllib.parse import urlparse
import redis.asyncio as redis
import uuid
import segno
import asyncio
import json
import os


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
            
    return request.client.host


async def execute_sql_file(file: Path, conn: Connection) -> None:
    try:
        with open(file, "r", encoding="utf-8") as f:
            sql_commands = f.read()
        await conn.execute(sql_commands)
    except Exception as e:
        print(f"[EXCEPTION WHEN OPEN COMMANDS] [{file}] | {e}")


async def periodic_update():
    while True:
        get_monitor().update_history()
        await asyncio.sleep(300)


def get_client_info(request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    device_name = None
    if user_agent:
        if "Windows" in user_agent:
            device_name = "Windows PC"
        elif "Macintosh" in user_agent:
            device_name = "Mac"
        elif "Linux" in user_agent:
            device_name = "Linux"
        elif "iPhone" in user_agent:
            device_name = "iPhone"
        elif "Android" in user_agent:
            device_name = "Android"

    return ClientInfo(
        client_ip=client_ip, 
        user_agent=user_agent, 
        device_name=device_name
    )


def print_dict(data: dict) -> None:
    print(json.dumps(data, indent=4, ensure_ascii=False))


def extract_base_url(request: Request) -> str:
    return str(request.base_url).rstrip('/')


def seconds_until(target: datetime) -> int:
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = (target - now).total_seconds()
    return int(diff) if diff > 0 else 0


def datetime_has_expired(expires_at: Optional[datetime]) -> bool:
    if expires_at and isinstance(expires_at, datetime):
        return expires_at < datetime.now(timezone.utc)
    return False


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


def extract_domain(url: str) -> str:
    parsed = urlparse(url.strip())
    
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid domain in URL: {url}")
    
    domain = f"{parsed.scheme}://{parsed.netloc}/"
    return domain


def coalesce(a: Optional[Any], b: Optional[Any]) -> Any:
    if a: return a
    return b


def minutes_since(target_datetime: datetime, reference_time: Optional[datetime] = None) -> float:    
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
        
    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
        
    difference = reference_time - target_datetime
    return difference.total_seconds() / 60