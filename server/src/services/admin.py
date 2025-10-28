from src.schemas.domain import (
    DomainCreate, 
    DomainDelete, 
    Domain, 
    DomainUpdate
)
from src.schemas.admin import (
    HealthReport, 
    MemoryInfo, 
    CpuInfo, 
    DiskInfo
)
from src.schemas.pagination import Pagination
from src.schemas.user import UserSession
from src.tables import users as users_table
from src.tables import domains as domains_table
from src.tables import urls as urls_table
from src.services import domain as domain_service
from fastapi.exceptions import HTTPException
from fastapi import status
from asyncpg import Connection
from typing import Optional
from src.db import db_count, db_version
from src.migrate import db_migrate
from src.perf.system_monitor import get_monitor
from datetime import datetime


async def get_system_health(conn: Connection):
    version: str = await db_version(conn)
    total_urls: int = await db_count("urls", conn)
    monitor = get_monitor() 
    return HealthReport(
        status="healthy",
        database="connected",
        postgres_version=version,
        total_urls=total_urls,
        now=datetime.now(),
        memory=MemoryInfo(**monitor.get_memory_info()),
        cpu=CpuInfo(**monitor.get_cpu_info()),
        disk=DiskInfo(**monitor.get_disk_info())
    )


async def get_users(limit: int, offset: int, conn: Connection):
    return await users_table.get_users(limit, offset, conn)
    

async def delete_user(user_id: str, conn: Connection):
    await users_table.delete_user(user_id, conn)


async def delete_all_users(conn: Connection):
    await users_table.delete_all_users(conn)


async def delete_all_urls(conn: Connection):
    await urls_table.delete_all_urls(conn)


async def delete_expired_urls(conn: Connection):
    await urls_table.delete_expired_urls(conn)


async def soft_delete_expired_urls(conn: Connection):
    await urls_table.soft_delete_expired_urls(conn)


async def get_domains(q: Optional[str], is_secure: Optional[bool], limit: int, offset: int, conn: Connection):
    return await domains_table.get_domains(q, is_secure, limit, offset, conn)


async def create_domain(domain: DomainCreate, conn: Connection) -> Domain:
    return await domain_service.create_domain(domain, conn)


async def delete_domain(domain: DomainDelete, conn: Connection):
    await domain_service.delete_domain(domain, conn)


async def update_domain(domain: DomainUpdate, conn: Connection) -> Domain:
    domain: Optional[Domain] = await domain_service.update_domain(domain, conn)
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return domain


async def delete_all_user_sessions(conn: Connection) -> None:
    await users_table.delete_sessions(conn)

async def get_user_sessions(limit: int, offset: int, conn: Connection) -> Pagination[UserSession]:
    return await users_table.get_sessions(limit, offset, conn)


async def cleanup_expired_sessions(conn: Connection) -> None:
    await users_table.cleanup_expired_sessions(conn)

async def reset_database(conn: Connection) -> None:
    statements = [
        "DROP TABLE IF EXISTS users CASCADE;",
        "DROP TABLE IF EXISTS user_session_tokens CASCADE;",
        "DROP TABLE IF EXISTS user_login_attempts CASCADE;",
        "DROP TABLE IF EXISTS domains CASCADE;",
        "DROP TABLE IF EXISTS urls CASCADE;",
        "DROP TABLE IF EXISTS user_urls CASCADE;",
        "DROP TABLE IF EXISTS url_tags CASCADE;",
        "DROP TABLE IF EXISTS url_tag_relations CASCADE;",
        "DROP TABLE IF EXISTS url_analytics CASCADE;",
        "DROP TABLE IF EXISTS logs CASCADE;",
        "DROP TABLE IF EXISTS time_perf CASCADE;",
        "DROP TABLE IF EXISTS rate_limit_logs CASCADE;",
        "DROP MATERIALIZED VIEW IF EXISTS mv_dashboard CASCADE;",
        "DROP FUNCTION IF EXISTS increment_url_clicks CASCADE;"
    ]

    for stmt in statements:
        await conn.execute(stmt)

    await db_migrate(conn)