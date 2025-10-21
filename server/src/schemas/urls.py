from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime


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


class URLResponse(BaseModel):
    
    id: int
    user_id: Optional[str] = None
    original_url: str
    short_url: str
    short_code: str
    clicks: int
    has_password: bool
    qrcode_url: str
    title: Optional[str] = None
    is_favorite: bool = False
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


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

