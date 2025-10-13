from pydantic import BaseModel, Field, validator
from typing import Any, Optional
from datetime import datetime
import json


class TopURL(BaseModel):
    short_code: str
    title: Optional[str] = None
    clicks: int
    original_url: str


class TopCountry(BaseModel):
    country_code: str
    clicks: int


class TopTag(BaseModel):
    tag_name: str
    usage_count: int
    tag_color: str


class TimelineEntry(BaseModel):
    date: str
    new_urls: int
    new_users: int
    total_clicks: int


class DashboardStats(BaseModel):
    total_urls: int
    favorite_urls: int
    custom_alias_urls: int
    protected_urls: int
    expiring_urls: int
    urls_created_last_24h: int
    urls_created_last_7d: int
    urls_created_last_30d: int
    total_clicks: int
    avg_clicks_per_url: float
    max_clicks_single_url: int

    total_users: int
    verified_users: int
    new_users_last_7d: int
    new_users_last_30d: int
    users_active_last_24h: int
    users_active_last_7d: int

    clicks_last_hour: int
    clicks_last_24h: int
    clicks_last_7d: int
    clicks_last_30d: int
    unique_visitors_24h: int
    unique_visitors_7d: int
    countries_reached_30d: int

    active_sessions: int
    users_with_active_sessions: int
    sessions_active_last_hour: int

    total_tags: int
    top_tags: Any
    top_urls: Any
    device_distribution: Any
    top_countries: Any
    growth_timeline: Any

    last_updated: datetime
    last_updated_formatted: str

    @validator(
        "top_tags",
        "top_urls",
        "device_distribution",
        "top_countries",
        "growth_timeline",
        pre=True,
    )
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "total_urls": 3,
                "favorite_urls": 1,
                "custom_alias_urls": 0,
                "protected_urls": 0,
                "expiring_urls": 0,
                "urls_created_last_24h": 3,
                "urls_created_last_7d": 3,
                "urls_created_last_30d": 3,
                "total_clicks": 5,
                "avg_clicks_per_url": 1.67,
                "max_clicks_single_url": 3,
                "total_users": 1,
                "verified_users": 0,
                "new_users_last_7d": 1,
                "new_users_last_30d": 1,
                "users_active_last_24h": 1,
                "users_active_last_7d": 1,
                "clicks_last_hour": 0,
                "clicks_last_24h": 5,
                "clicks_last_7d": 5,
                "clicks_last_30d": 5,
                "unique_visitors_24h": 1,
                "unique_visitors_7d": 1,
                "countries_reached_30d": 0,
                "active_sessions": 1,
                "users_with_active_sessions": 1,
                "sessions_active_last_hour": 0,
                "total_tags": 0,
                "top_tags": [],
                "top_urls": [
                    {
                        "short_code": "eT3oZiK",
                        "clicks": 3,
                        "title": None,
                        "original_url": "https://www.reddit.com/"
                    }
                ],
                "device_distribution": {"desktop": 5},
                "top_countries": [],
                "growth_timeline": [
                    {"date": "2025-10-13", "new_urls": 1, "new_users": 1, "total_clicks": 3}
                ],
                "last_updated": "2025-10-13T18:31:36.215426+00:00",
                "last_updated_formatted": "13-10-2025 15:31:36"
            }
        }


class DashboardRefreshResponse(BaseModel):
    success: bool
    execution_time_ms: float
    last_updated: datetime
    message: str
