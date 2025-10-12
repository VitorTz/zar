from src.perf.system_monitor import get_monitor
from src.schemas.client_info import ClientInfo
from src.constants import Constants
from src.globals import Globals
from fastapi import Request
from pathlib import Path
from typing import Any
from asyncpg import Connection
from PIL import Image
from src.s3 import S3
import httpx
import uuid
import segno
import random
import string
import asyncio
import time
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


def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


def load_json(path: Path) -> Any:
    with open(path, "r") as file:
        return json.load(file)


def save_json(path: Path, obj: Any):
    with open(path, "w+") as file:
        json.dump(obj, file, indent=4)
    

def title(text: str) -> str:    
    words: list[str] = text.split()
    result: list[str] = []

    for i, word in enumerate(words):
        if word.lower() in Constants.TITLE_IGNORE and i != 0:
            result.append(word.lower())
        else:
            result.append(word.capitalize())

    return ' '.join(result)


def normalize_phone(phone: str) -> str:
    if not phone: return None
    phone1 = ''
    for i in phone:
        if i.isdigit():
            phone1 += i
    if phone1.startswith("55"):
        phone1 = phone1[2:]
    return phone1


def delete_file(path: Path) -> None:
    try:
        os.remove(str(path))
    except Exception:
        pass


def coalesce(a: Any | None, b: Any | None) -> Any:
    if a: return a
    return b


def normalize_employee_sort_by(sort_by: str) -> str:
    sort_by = sort_by.strip().lower()
    if sort_by not in Constants.VALID_EMPLOYEE_SORT_BY:
        return Constants.DEFAULT_EMPLOYEE_SORT_BY
    return sort_by


def normalize_rate_limit_sort_by(sort_by: str) -> str:
    sort_by = sort_by.strip().lower()
    if sort_by not in Constants.VALID_RATE_LIMIT_SORT_BY:
        return Constants.VALID_RATE_LIMIT_SORT_BY
    return sort_by


def normalize_sort_order(sort_order: str) -> str:
    sort_order = sort_order.strip().lower()
    if sort_order not in ("asc", "desc"):
        return "asc"
    return sort_order


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


def make_ping_response(request: Request, start: float):
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "status": "ok",
        "latency_ms": round(elapsed, 3),
        "client": request.client.host,
    }


async def normalize_image(
    path: Path, 
    max_width: int = 1080, 
    quality: int = 90, 
    format: str = "WEBP"
) -> Path:
    output = path.with_suffix(f".{format.lower()}")
    
    with Image.open(path) as img:
        w, h = img.size
        if w > max_width:
            new_h = int(h * max_width / w)
            img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
        img.save(output, format=format, quality=quality)
    
    if path.suffix != output.suffix:
        os.remove(str(path))

    return output


def generate_short_code(length: int = 7):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def print_dict(data: dict) -> None:
    print(json.dumps(data, indent=4, ensure_ascii=False))


def extract_base_url(request: Request) -> str:
    return str(request.base_url).rstrip('/')


async def create_qrcode(data: str):
    qrcode = segno.make(data)
    random_id = str(uuid.uuid4())
    path = Path(f'tmp/{random_id}.png')
    qrcode.save(path, scale=10)
    url = await S3().upload_qrcode(path, random_id)
    os.remove(str(path))
    return url


async def is_url_safe(url: str) -> bool:
    cache_key = f"safe_browsing:{url}"
    
    cached = await Globals.redis_client.get(cache_key)
    if cached is not None:
        return cached == "safe"
    
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
                return False

            await Globals.redis_client.setex(cache_key, Constants.SAFE_CACHE_TTL, "safe")
            return True

    except httpx.RequestError as e:
        print(e)
        return False