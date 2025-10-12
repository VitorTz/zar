from datetime import datetime, timezone, timedelta
from fastapi.exceptions import HTTPException
from fastapi.responses import Response
from fastapi import Depends, Cookie, Request
from passlib.context import CryptContext
from src.constants import Constants
from src.db import get_db
from src.schemas.user import User, UserLoginAttempt
from src.tables import users as users_table
from src.globals import Globals
from fastapi import status
from jose import jwt, JWTError
from asyncpg import Connection
import uuid


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def check_admin_token(token: str):
    try:
        payload = jwt.decode(token, Constants.SECRET_KEY, algorithms=[Constants.ALGORITHM])
        admin_password: str = payload.get("sub")
        if admin_password != Constants.ADMIN_PASSWORD:
            return False
    except Exception:        
        return False
    return True


def require_admin(token: str = Depends(Globals.oauth2_admin_scheme)):
    if not check_admin_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return True


def create_new_refresh_token_expires_time() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=Constants.REFRESH_TOKEN_EXPIRE_DAYS)


def create_refresh_token() -> tuple[str, datetime]:
    token = str(uuid.uuid4())
    expires = create_new_refresh_token_expires_time()
    return token, expires


def hash_password(password: str) -> bytes:
    return pwd_context.hash(password.strip()).encode()


def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    return pwd_context.verify(plain_password.strip(), hashed_password.decode())


def create_access_token(manager_id: str | uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + (timedelta(minutes=Constants.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(
        {"sub": str(manager_id), "exp": expire}, 
        Constants.SECRET_KEY,
        algorithm=Constants.ALGORITHM
    )


def create_session_token(manager_id: str | uuid.UUID) -> tuple[str, str, datetime]:
    access_token = create_access_token(manager_id)
    refresh_token, expires_at = create_refresh_token()
    return access_token, refresh_token, expires_at


def create_admin_token() -> str:
    data = {"sub": Constants.ADMIN_PASSWORD}
    to_encode = data.copy()
    return jwt.encode(to_encode, Constants.SECRET_KEY, algorithm=Constants.ALGORITHM)


def check_user_login_attempts(lock: UserLoginAttempt):
    now = datetime.now(timezone.utc)
    if lock.locked_until and lock.locked_until > now:
        raise HTTPException(status_code=403, detail=f"Account locked until {lock.locked_until}")
    

async def get_user_from_token(
    access_token: str | None = Cookie(default=None),
    conn: Connection = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if access_token is None: 
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            access_token,
            Constants.SECRET_KEY,
            algorithms=[Constants.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None: 
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    manager: User | None = await users_table.get_user(user_id, conn)
    
    if manager is None:
        raise credentials_exception
    
    return manager


async def get_user_from_token_if_exists(
    access_token: str | None = Cookie(default=None),
    conn: Connection = Depends(get_db)
) -> User | None:
    if access_token is None: 
        return None
    
    try:
        payload = jwt.decode(
            access_token,
            Constants.SECRET_KEY,
            algorithms=[Constants.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id: return await users_table.get_user(user_id, conn)
    except JWTError:
        return None


def set_access_cookie(response: Response, access_token: str, refresh_token: str):
    if Constants.IS_PRODUCTION:
        samesite_policy = "none"
        secure_policy = True 
    else:
        samesite_policy = "lax"
        secure_policy = False
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_policy,
        samesite=samesite_policy,
        path="/",
        max_age=Constants.REFRESH_TOKEN_EXPIRE_DAYS
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_policy,
        samesite=samesite_policy,
        path="/",
        max_age=Constants.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )