from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional


class Domain(BaseModel):

    id: int
    url: str
    url_hash: bytes
    is_secure: bool

    @field_validator("url_hash", mode="before")
    def decode_bytes(cls, v):
        if isinstance(v, (bytes, bytearray)):
            return v.hex()
        return v


class DomainCreate(BaseModel):

    url: HttpUrl
    is_secure: Optional[bool] = True


class DomainDelete(BaseModel):

    id: int


class DomainUpdate(BaseModel):
    
    id: int
    is_secure: bool
