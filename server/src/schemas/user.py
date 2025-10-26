from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class User(BaseModel):

    id: UUID
    email: str
    last_login_at: Optional[datetime] = None
    created_at: datetime


class UserLoginData(BaseModel):

    id: UUID
    email: str
    p_hash: bytes
    login_attempts: int
    last_login_at: Optional[datetime] = None
    last_failed_login: Optional[datetime] = None
    locked_until: Optional[datetime] = None
    created_at: datetime


class UserCreate(BaseModel):

    email: EmailStr
    password: str


class UserLogin(BaseModel):

    email: EmailStr
    password: str


class UserLoginAttempt(BaseModel):

    user_id: str
    attempts: int
    last_failed_login: Optional[datetime]
    locked_until: Optional[datetime]


class UserSession(BaseModel):

    user_id: UUID
    issued_at: datetime
    expires_at: datetime
    revoked: bool
    revoked_at: Optional[datetime] = None
    device_name: Optional[str] = None
    device_ip: str
    user_agent: Optional[str] = None
    last_used_at: datetime


class UserSessionPagination(BaseModel):
    
    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[UserSession]


class UserPagination(BaseModel):
    
    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[User]


class UserDelete(BaseModel):

    user_id: str


class UserStats(BaseModel):

    id: str
    email: str
    member_since: str
    total_urls: int
    favorite_urls: int
    total_clicks: int
    last_url_created: Optional[str]