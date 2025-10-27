from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from src.security import require_admin
from src.db import get_db
from src.schemas.pagination import Pagination
from src.schemas.domain import DomainCreate, DomainDelete, DomainUpdate, Domain
from src.services import admin as admin_service
from asyncpg import Connection


router = APIRouter(prefix="/domains", dependencies=[Depends(require_admin)], tags=["admin_domains"])


@router.get("/", response_model=Pagination[Domain])
async def get_domains(
    q: Optional[str] = Query(default=None),
    is_secure: Optional[bool] = Query(default=None),
    limit: int = Query(default=64, ge=1, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await admin_service.get_domains(q, is_secure, limit, offset, conn)


@router.post("/", response_model=Domain, status_code=status.HTTP_201_CREATED)
async def create_domain(domain: DomainCreate, conn: Connection = Depends(get_db)):
    return await admin_service.create_domain(domain, conn)


@router.put("/", status_code=status.HTTP_201_CREATED)
async def update_domain(domain: DomainUpdate, conn: Connection = Depends(get_db)):
    await admin_service.update_domain(domain, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(domain: DomainDelete, conn: Connection = Depends(get_db)):
    await admin_service.delete_domain(domain, conn)
