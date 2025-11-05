from datetime import datetime, date
from pydantic import BaseModel
from typing import List


class UserStats(BaseModel):
    total: int
    new_30d: int
    new_7d: int
    active_30d: int
    active_7d: int
    active_24h: int


class UrlStats(BaseModel):
    total: int    
    new_30d: int
    new_7d: int
    new_24h: int
    avg_clicks: float
    median_clicks: float


class ClickStats(BaseModel):
    total: int
    last_30d: int
    last_7d: int
    last_24h: int


class AnalyticsStats(BaseModel):
    total_records: int
    records_30d: int
    records_7d: int
    records_24h: int
    unique_visitors_all_time: int
    unique_visitors_30d: int
    countries_reached: int


class TopUrl(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime


class TopCountry(BaseModel):
    country_code: str
    clicks: int
    percentage: float


class Geography(BaseModel):
    top_countries: List[TopCountry]


class DeviceBreakdown(BaseModel):
    mobile: int
    desktop: int
    tablet: int
    other: int


class BrowserStat(BaseModel):
    browser: str
    count: int


class ClientInfo(BaseModel):
    devices: DeviceBreakdown
    browsers: List[BrowserStat]


class TopTag(BaseModel):
    name: str
    usage_count: int


class TagStats(BaseModel):
    total_tags: int
    urls_with_tags: int
    avg_tags_per_url: float
    top_tags: List[TopTag]


class TopDomain(BaseModel):
    domain: str
    url_count: int
    total_clicks: int


class DomainStats(BaseModel):
    total_domains: int
    top_domains: List[TopDomain]


class DailyGrowthItem(BaseModel):
    date: date
    new_urls: int
    new_users: int
    clicks: int


class SessionStats(BaseModel):
    total: int
    active: int
    revoked: int
    users_with_sessions: int
    avg_duration_hours: float


class ConversionStats(BaseModel):
    urls_with_clicks: int
    total_urls_30d: int
    conversion_rate: float
    urls_10plus_rate: float


class Dashboard(BaseModel):
    
    total_urls: int
    last_updated: datetime
    users: UserStats
    urls: UrlStats
    clicks: ClickStats
    analytics: AnalyticsStats
    top_urls: List[TopUrl]
    geography: Geography
    client_info: ClientInfo
    tags: TagStats
    domains: DomainStats
    daily_growth: List[DailyGrowthItem]
    sessions: SessionStats
    conversion: ConversionStats
