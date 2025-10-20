from src.perf.system_monitor import get_monitor
from src.schemas.client_info import ClientInfo
from fastapi import Request
from pathlib import Path
from asyncpg import Connection
from urllib.parse import urlparse
from src.s3 import S3
import ipaddress
import socket
import uuid
import aiohttp
import segno
import random
import string
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
