from src.schemas.domain import DomainCreate, DomainDelete, Domain, DomainUpdate
from src.schemas.admin import HealthReport, MemoryInfo, CpuInfo, DiskInfo
from src.tables import users as users_table
from src.tables import domains as domains_table
from src.tables import urls as urls_table
from src.services import domain as domain_service
from asyncpg import Connection
from typing import Optional
from src.db import db_count, db_version
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


async def get_domains(q: Optional[str], limit: int, offset: int, conn: Connection):
    return await domains_table.get_domains(q, limit, offset, conn)


async def create_domain(domain: DomainCreate, conn: Connection) -> Domain:
    return await domain_service.create_domain(domain, conn)


async def delete_domain(domain: DomainDelete, conn: Connection):
    await domain_service.delete_domain(domain, conn)


async def update_domain(domain: DomainUpdate, conn: Connection) -> None:
    await domain_service.update_domain(domain, conn)