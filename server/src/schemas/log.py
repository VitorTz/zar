from pydantic import BaseModel
from typing import Optional, List


class Log(BaseModel):

    id: int
    level: str
    message: str
    path: str
    method: str
    status_code: int
    user_id: Optional[str] = None
    stacktrace: str
    metadata: dict
    created_at: str


class LogPagination(BaseModel):

    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[Log]


class RateLimitLog(BaseModel):

    ip_address: str
    path: str
    method: str
    total_attempts: int
    violation_count: int
    first_violation: str
    last_violation: str
    

class RateLimitLogPagination(BaseModel):

    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[RateLimitLog]