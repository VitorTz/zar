from fastapi import APIRouter, Depends, status
from src.schemas.dashboard import Dashboard
from src.services import dashboard as dashboard_service
from src.db import get_db
from src.security import require_admin
from asyncpg import Connection


router = APIRouter()


@router.get("/data", response_model=Dashboard)
async def get_dashboard(conn: Connection = Depends(get_db)):
    return await dashboard_service.get_dashboard(conn)


@router.put(
    "/refresh", 
    response_model=Dashboard, 
    status_code=status.HTTP_201_CREATED, 
    dependencies=[Depends(require_admin)]
)
async def refresh_dashboard(conn: Connection = Depends(get_db)):
    return await dashboard_service.refresh_dashboard(conn)