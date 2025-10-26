from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TimePerfCreate(BaseModel):

    perf_type: str
    execution_time: float
    perf_subtype: Optional[str] = None
    created_at: Optional[datetime] = None
    notes: Optional[str] = None


class TimePerfResponse(BaseModel):

    id: int
    perf_type: str
    perf_subtype: Optional[str]
    execution_time: float
    notes: Optional[str] = None
    created_at: Optional[datetime]


class TimePerfStats(BaseModel):
    total_records: int
    avg_exec_time: float
    min_exec_time: float
    max_exec_time: float


class TimePerfGroupedStats(BaseModel):
    perf_type: str
    perf_subtype: Optional[str]
    count: int
    avg_exec_time: float
    min_exec_time: float
    max_exec_time: float