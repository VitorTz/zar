from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Tuple, List


class ProcessMemoryInfo(BaseModel):
    rss_bytes: int
    vms_bytes: int
    rss_mb: float
    vms_mb: float
    percent: float
    peak_mb: float


class SystemMemoryInfo(BaseModel):
    total_mb: float
    available_mb: float
    used_mb: float
    percent: float


class PythonMemoryInfo(BaseModel):
    objects_count: int
    gc_collected: int
    gc_enabled: bool
    gc_thresholds: Tuple[int, int, int]
    gc_count: Tuple[int, int, int]


class MemoryInfo(BaseModel):
    process: ProcessMemoryInfo
    system: SystemMemoryInfo
    python: PythonMemoryInfo
    history_stats: Dict[str, Any]


class ProcessCpuInfo(BaseModel):
    percent: float
    user_time: float
    system_time: float
    peak_percent: float
    num_threads: int

class LoadAverageInfo(BaseModel):
    _1min: float
    _5min: float
    _15min: float

    class Config:
        fields = {
            "_1min": "1min",
            "_5min": "5min",
            "_15min": "15min"
        }

class SystemCpuInfo(BaseModel):
    percent_total: float
    percent_per_core: List[float]
    core_count_logical: int
    core_count_physical: int
    frequency_current_mhz: float
    frequency_min_mhz: float
    frequency_max_mhz: float
    load_average: LoadAverageInfo


class CpuInfo(BaseModel):
    process: ProcessCpuInfo
    system: SystemCpuInfo
    history_stats: Dict[str, Any]


class DiskUsageInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float

class DiskIOInfo(BaseModel):
    read_mb: float
    write_mb: float
    read_count: int
    write_count: int

class DiskInfo(BaseModel):
    usage: DiskUsageInfo
    io: DiskIOInfo


class HealthReport(BaseModel):
        
    status: str
    database: str
    postgres_version: str
    total_urls: int
    now: datetime
    memory: MemoryInfo
    cpu: CpuInfo
    disk: DiskInfo