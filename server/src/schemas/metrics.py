from pydantic import BaseModel
from typing import Optional, List


class UrlAnalytic(BaseModel):

    url_id: str
    date: str
    clicks: int
    unique_visitors: int
    countries: int
    device_types: List[str]


class UrlAnalyticPagination(BaseModel):

    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[UrlAnalytic]


class PopularUrl(BaseModel):

    id: str
    short_code: str
    original_url: str
    clicks: int
    created_at: str
    unique_clicks: int


class DashboardStats(BaseModel):

    total_urls: int
    total_users: int
    total_clicks: int
    clicks_last_24h: int
    urls_created_last_week: int
    last_updated: str


class UserStats(BaseModel):

    id: str
    email: str
    member_since: str
    total_urls: int
    favorite_urls: int
    total_clicks: int
    last_url_created: Optional[str]