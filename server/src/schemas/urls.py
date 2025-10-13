from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime


class URLCreate(BaseModel):

    url: HttpUrl
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
    
    user_id: Optional[str] = None
    original_url: str
    short_url: str
    short_code: str
    clicks: int
    qrcode_url: str
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