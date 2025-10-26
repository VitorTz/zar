from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from src.security import require_admin
from src.db import get_db
from src.schemas.reports import SystemReport
from src.schemas.admin import HealthReport
from src.services import admin as admin_service
from src.services import perf as perf_service
from asyncpg import Connection
import random


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/health", response_model=HealthReport)
async def health_check(conn: Connection = Depends(get_db)):
    return await admin_service.get_system_health(conn)

@router.get("/report", response_model=SystemReport)
async def get_full_metrics_report():
    return await perf_service.generate_full_report()

@router.get("/report/html")
async def get_full_metrics_report_html():
    return await perf_service.generate_metric_html_report()

@router.api_route("/crash", methods=["GET", "POST", "PUT", "DELETE"])
async def crash(
    message: Optional[str] = Query(default="Manual crash triggered."),
    code: Optional[int] = Query(default=500, ge=100, le=599),
    randomize: Optional[bool] = Query(default=False),
    probability: Optional[float] = Query(default=1.0, ge=0.0, le=1.0)
):
    if randomize and random.random() > probability:
        return {"status": "ok", "detail": "Crash evitado por probabilidade"}
    raise HTTPException(status_code=code, detail=message)

