from pydantic import BaseModel, HttpUrl
from typing import List


class Domain(BaseModel):

    id: int
    url: str
    url_hash: bytes
    is_secure: bool


class DomainCreate(BaseModel):

    url: HttpUrl
    is_secure: bool


class DomainDelete(BaseModel):

    id: int


class DomainUpdate(BaseModel):
    
    id: int
    is_secure: bool


class DomainPagination(BaseModel):

    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[Domain]