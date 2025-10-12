from pydantic import BaseModel


class HealthReport(BaseModel):
        
    status: str
    database: str
    postgres_version: str
    total_urls: int
    now: str
