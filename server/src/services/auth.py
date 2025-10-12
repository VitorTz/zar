from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import HTTPException
from fastapi import status, Request
from asyncpg import Connection, UniqueViolationError
from src.schemas.user import User, UserLogin, UserLoginData, UserCreate
from src.schemas.client_info import ClientInfo
from src.tables import users as users_table
from datetime import datetime, timezone, timedelta
from src.constants import Constants
from src import security
from uuid import UUID
from src import util


async def get_user(user_id: str | UUID, conn: Connection) -> JSONResponse:
    try:
        manager: User | None = await users_table.get_user(user_id, conn)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}")
    if manager is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(content=manager.model_dump())



async def login(user_login: UserLogin, request: Request, conn: Connection):
    now: datetime = datetime.now(timezone.utc)
    
    # Retrive user with email = user_login.email
    user_login_data: UserLoginData | None = await users_table.get_user_login_data(user_login.email, conn)
    if user_login_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Check if account is locked    
    if user_login_data.locked_until and user_login_data.locked_until > now:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account locked until {user_login_data.locked_until}")

    # Verify password
    if not security.verify_password(user_login.password, user_login_data.p_hash):
        await users_table.update_user_login_attempts(
            user_login_data.id, 
            user_login_data.login_attempts + 1, 
            now, 
            locked_until,
            conn
        )
        if user_login_data.login_attempts + 1 >= Constants.MAX_FAILED_ATTEMPTS:
            locked_until = now + timedelta(minutes=Constants.LOCK_TIME_MINUTES)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account locked until {locked_until}")
                
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Reset login attempts
    await users_table.update_user_login_attempts(
        user_login_data.id,
        0,
        None,
        None,
        conn        
    )
    
    # Create unique access token
    access_token, refresh_token, expires_at = security.create_session_token(user_login_data.id)
    client_info: ClientInfo = util.get_client_info(request)
    await users_table.create_user_session_token(
        user_login_data.id,
        refresh_token,
        expires_at,
        client_info.device_name,
        client_info.client_ip,
        client_info.user_agent,
        conn        
    )

    # Fetch user
    user: User = await users_table.get_user(user_login_data.id, conn)
    await users_table.update_user_last_login_at(user.id, conn)

    # Response
    response = JSONResponse(user.model_dump())
    security.set_access_cookie(response, access_token, refresh_token)
    return response


async def get_user_sessions(user: User, limit: int, offset: int, conn: Connection):
    total, results = await users_table.get_user_sessions(user.id, limit, offset, conn)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": results
    }
    return JSONResponse(response)


async def refresh_access_token(token: str | None, conn: Connection):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user: User | None = await users_table.get_user_by_refresh_token(token, conn)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    access_token, _, expires_at = security.create_session_token(user.id)
    await users_table.update_user_session_token(
        user.id,
        token,
        expires_at,
        conn        
    )

    user: User = await users_table.get_user(user.id, conn)
    response = JSONResponse(user.model_dump_json())
    security.set_access_cookie(response, access_token, token)

    return response


async def signup(manager_signup: UserCreate, conn: Connection):
    try:
        await users_table.create_user(
            manager_signup.email,
            security.hash_password(manager_signup.password),
            conn
        )
        return Response(status_code=status.HTTP_201_CREATED)
    except UniqueViolationError:
        raise HTTPException(status_code=409, detail="Email already registered")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}")


async def logout(refresh_token: str | None, conn: Connection):
    if refresh_token is None:
        await users_table.delete_user_session_token(refresh_token, conn)
    
    response = Response(status_code=status.HTTP_200_OK)
    security.set_access_cookie(response, '', '')
    return response


async def logout_all(user: User, conn: Connection):
    await users_table.delete_all_user_session_tokens(user.id, conn)
    response = Response(status_code=status.HTTP_200_OK)
    security.set_access_cookie(response, '', '')
    return response