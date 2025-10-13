from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class User(BaseModel):

    id: str
    email: str
    last_login_at: Optional[str] = None
    is_active: bool
    is_verified: bool
    updated_at: str
    created_at: str


class UserLoginData(BaseModel):

    id: str
    email: str
    p_hash: bytes
    login_attempts: int
    last_failed_login: Optional[datetime]
    locked_until: Optional[datetime]


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

    user_id: str
    issued_at: str
    expires_at: str
    revoked: bool
    revoked_at: Optional[str]
    device_name: Optional[str]
    device_ip: str
    user_agent: Optional[str]
    last_used_at: str


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


class UseDelete(BaseModel):

    user_id: str


class UserStats(BaseModel):

    id: str
    email: str
    member_since: str
    total_urls: int
    favorite_urls: int
    total_clicks: int
    last_url_created: Optional[str]