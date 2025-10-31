from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from uuid import UUID



class URLCreate(BaseModel):

    url: HttpUrl
    title: Optional[str] = None
    descr: Optional[str] = None
    is_favorite: Optional[bool] = False


class UrlShortCode(BaseModel):

    short_code: str


class URLDelete(BaseModel):

    id: int


class CreateFavoriteURL(BaseModel):

    url_id: int
    is_favorite: bool


class URLResponse(BaseModel):
    
    id: int
    title: Optional[str]
    descr: Optional[str]
    domain_id: int
    user_id: Optional[UUID] = None
    original_url: str
    short_url: str
    short_code: str
    clicks: int = 0
    is_favorite: Optional[bool] = False
    created_at: datetime


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
    original_url: str


class UrlStats(BaseModel):
    url_id: int
    total_clicks: int
    unique_visitors: int
    first_click: Optional[datetime]
    last_click: Optional[datetime]
    clicks_today: int
    browsers: Optional[List[str]] = []
    operating_systems: Optional[List[str]] = []
    device_types: Optional[List[str]] = []
    countries: Optional[List[str]] = []


class UrlTag(BaseModel):

    id: int
    user_id: UUID
    name: str
    color: str
    descr: Optional[str] = None
    created_at: datetime


class UrlTagCreate(BaseModel):

    name: str
    color: Optional[str] = "#d8775a"
    descr: Optional[str] = None


class UrlTagUpdate(BaseModel):
    
    id: int
    name: Optional[str] = None
    color: Optional[str] = None
    descr: Optional[str] = None


class UrlTagId(BaseModel):

    id: int

class UrlTagDelete(BaseModel):
    
    id: int    


class UrlTagRelation(BaseModel):

    url_id: int
    tag_id: int
    created_at: datetime


class UrlTagRelationCreate(BaseModel):

    url_id: int
    tag_id: int

class UrlTagRelationDelete(BaseModel):

    url_id: int
    tag_id: int


class UserURLResponse(BaseModel):
    
    id: int
    title: Optional[str]
    descr: Optional[str]
    domain_id: int
    user_id: Optional[UUID] = None
    tags: List[UrlTag]
    original_url: str
    short_url: str
    short_code: str
    clicks: int = 0
    is_favorite: Optional[bool] = False
    created_at: datetime
