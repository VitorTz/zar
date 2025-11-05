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
from src.schemas.user import UserSession, User
from src.tables import users as users_table
from src.tables import domains as domains_table
from src.tables import urls as urls_table
from src.services import domain as domain_service
from fastapi.exceptions import HTTPException
from fastapi import status
from asyncpg import Connection
from typing import Optional
from src.db import db_count, db_version, db_reset
from src.migrate import db_migrate
from src.perf.system_monitor import get_monitor
from datetime import datetime


async def get_system_health(conn: Connection) -> HealthReport:
    version: str = await db_version(conn)
    total_urls: int = await db_count("urls", conn)
    total_users: int = await db_count("users", conn)
    total_domains: int = await db_count("domains", conn)
    monitor = get_monitor()
    return HealthReport(
        status="healthy",
        database="connected",
        postgres_version=version,
        total_urls=total_urls,
        total_users=total_users,
        total_domains=total_domains,
        now=datetime.now(),
        memory=MemoryInfo(**monitor.get_memory_info()),
        cpu=CpuInfo(**monitor.get_cpu_info()),
        disk=DiskInfo(**monitor.get_disk_info())
    )


async def get_users(limit: int, offset: int, conn: Connection) -> Pagination[User]:
    return await users_table.get_users(limit, offset, conn)
    

async def delete_user(user_id: str, conn: Connection):
    await users_table.delete_user(user_id, conn)


async def delete_all_users(conn: Connection):
    await users_table.delete_all_users(conn)


async def get_domains(
    q: Optional[str], 
    is_secure: Optional[bool], 
    limit: int, 
    offset: int, 
    conn: Connection
) -> Pagination[Domain]:
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
    await db_reset(db_migrate, conn)


async def delete_all_urls(conn: Connection) -> None:
    await urls_table.delete_all_urls(conn)