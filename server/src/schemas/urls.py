from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List


class URLCreate(BaseModel):

    url: HttpUrl


class URLDelete(BaseModel):

    url_id: str


class URLResponse(BaseModel):

    id: str
    original_url: str
    short_url: str
    short_code: str
    clicks: int
    qr_code_url: str


class URLStats(BaseModel):

    id: str
    original_url: str
    short_code: str
    clicks: int
    created_at: str
    qr_code_url: str


class UrlPagination(BaseModel):

    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[URLResponse]