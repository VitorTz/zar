from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class ExpiredUrl(BaseModel):

    original_url: str
    expires_at: datetime
    

class URLCreate(BaseModel):

    url: HttpUrl
    title: Optional[str] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_favorite: Optional[bool] = False


class UrlShortCode(BaseModel):

    short_code: str


class URLDelete(BaseModel):

    short_code: str


class CreateFavoriteURL(BaseModel):

    short_code: str
    is_favorite: bool


class URLAdminResponse(BaseModel):

    id: int
    domain_id: int
    user_id: Optional[UUID] = None
    original_url: str
    p_hash: Optional[bytes] = None
    short_url: str
    short_code: str
    clicks: int
    title: Optional[str] = None
    has_password: bool
    is_favorite: bool
    created_at: datetime
    expires_at: Optional[datetime] = None


class URLResponse(BaseModel):
    
    id: int
    domain_id: int
    user_id: Optional[str] = None
    original_url: str
    short_url: str
    short_code: str
    clicks: int = 0
    has_password: bool
    title: Optional[str] = None
    is_favorite: Optional[bool] = False
    created_at: datetime
    expires_at: Optional[datetime] = None


class UrlPagination(BaseModel):

    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[URLResponse]


class UrlPopular(BaseModel):

    short_code: str
    short_url: str
    original_url: str
    title: Optional[str]
    clicks: int
    created_at: str
    last_clicked_at: str
    unique_visitors: int
    countries_reached: int


class UrlPopularPagination(BaseModel):

    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[UrlPopular]



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


class UrlRedirect(BaseModel):

    id: int
    p_hash: Optional[bytes]
    original_url: str
    expires_at: Optional[datetime] = None


class UrlStats(BaseModel):
    url_id: int
    total_clicks: int
    unique_visitors: int
    first_click: Optional[datetime]
    last_click: Optional[datetime]
    clicks_today: int
    browsers: Optional[List[str]]
    operating_systems: Optional[List[str]]
    device_types: Optional[List[str]]
    countries: Optional[List[str]]