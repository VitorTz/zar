from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional


class ReportPeriod(BaseModel):
    uptime: str
    uptime_seconds: float


class ExecutiveSummary(BaseModel):
    health_status: str
    overall_score: int
    key_findings: List[str]
    recommendations: List[str]


class ProcessIdentification(BaseModel):
    pid: int
    name: str
    status: str
    threads: int
    file_descriptors: int


class ProcessUptime(BaseModel):
    seconds: float
    formatted: str
    started_at: datetime


class RequestsMetrics(BaseModel):
    total: int
    errors: int
    error_rate_percent: float
    requests_per_second: float


class ResponseTimes(BaseModel):
    min: float
    max: float
    avg: float
    current: float


class ProcessMetrics(BaseModel):
    identification: ProcessIdentification
    uptime: ProcessUptime
    requests: RequestsMetrics
    response_times: ResponseTimes


class MemoryProcess(BaseModel):
    rss_bytes: int
    vms_bytes: int
    rss_mb: float
    vms_mb: float
    percent: float
    peak_mb: float


class MemorySystem(BaseModel):
    total_mb: float
    available_mb: float
    used_mb: float
    percent: float


class MemoryPython(BaseModel):
    objects_count: int
    gc_collected: int
    gc_enabled: bool
    gc_thresholds: List[int]
    gc_count: List[int]


class Trends(BaseModel):
    min: float
    max: float
    avg: float
    current: float


class Analysis(BaseModel):
    status: str
    usage_level: Optional[str] = None
    details: str


class MemoryMetrics(BaseModel):
    process: MemoryProcess
    system: MemorySystem
    python: MemoryPython
    trends: Trends
    analysis: Analysis


class CPUProcess(BaseModel):
    percent: float
    user_time: float
    system_time: float
    peak_percent: float
    num_threads: int


class CPULoadAverage(BaseModel):
    _1min: float
    _5min: float
    _15min: float

    class Config:
        fields = {"_1min": "1min", "_5min": "5min", "_15min": "15min"}


class CPUSystem(BaseModel):
    percent_total: float
    percent_per_core: List[float]
    core_count_logical: int
    core_count_physical: int
    frequency_current_mhz: float
    frequency_min_mhz: float
    frequency_max_mhz: float
    load_average: CPULoadAverage


class CPUMetrics(BaseModel):
    process: CPUProcess
    system: CPUSystem
    trends: Trends
    analysis: Analysis


class DiskUsage(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


class DiskIO(BaseModel):
    read_mb: float
    write_mb: float
    read_count: int
    write_count: int


class DiskAnalysis(BaseModel):
    status: str
    free_space_gb: float


class DiskMetrics(BaseModel):
    usage: DiskUsage
    io: DiskIO
    analysis: DiskAnalysis


class NetworkIO(BaseModel):
    bytes_sent_mb: float
    bytes_recv_mb: float
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int


class NetworkConnections(BaseModel):
    active: int


class NetworkAnalysis(BaseModel):
    total_traffic_mb: float
    error_rate: float


class NetworkMetrics(BaseModel):
    io: NetworkIO
    connections: NetworkConnections
    analysis: NetworkAnalysis


class HistoricalPoint(BaseModel):
    timestamp: float
    value: float


class HistoricalData(BaseModel):
    memory: List[HistoricalPoint]
    cpu: List[HistoricalPoint]
    response_time: List[HistoricalPoint]


class Metadata(BaseModel):
    monitoring_interval_seconds: int
    history_size: int
    cache_ttl_seconds: float


class SystemReport(BaseModel):
    generated_at: datetime
    report_period: ReportPeriod
    executive_summary: ExecutiveSummary
    process_metrics: ProcessMetrics
    memory_metrics: MemoryMetrics
    cpu_metrics: CPUMetrics
    disk_metrics: DiskMetrics
    network_metrics: NetworkMetrics
    historical_data: HistoricalData
    metadata: Metadata
