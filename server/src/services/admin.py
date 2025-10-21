from src.schemas.domain import DomainCreate, DomainDelete
from src.tables import users as users_table
from src.tables import domains as domains_table
from src.tables import urls as urls_table
from fastapi.responses import JSONResponse
from src.services import domain as domain_service
from asyncpg import Connection
from typing import Optional


async def get_users(limit: int, offset: int, conn: Connection):
    total, results = await users_table.get_users(limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return JSONResponse(response)


async def delete_user(user_id: str, conn: Connection):
    await users_table.delete_user(user_id, conn)


async def delete_all_users(conn: Connection):
    await users_table.delete_all_users(conn)


async def delete_all_urls(conn: Connection):
    await urls_table.delete_all_urls(conn)


async def delete_expired_urls(conn: Connection):
    await urls_table.delete_all_urls(conn)


async def soft_delete_expired_urls(conn: Connection):
    await urls_table.soft_delete_expired_urls(conn)


async def get_domains(q: Optional[str], is_secure: bool, limit: int, offset: int, conn: Connection):
    total, results = await domains_table.get_domains(q, is_secure, limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return response


async def create_domain(domain: DomainCreate, conn: Connection):
    await domain_service.create_domain(domain, conn)


async def delete_domain(domain: DomainDelete, conn: Connection):
    await domain_service.delete_domain(domain, conn)
