from src.schemas.user import User, UserLoginData
from src.schemas.urls import URLResponse
from asyncpg import Connection
from uuid import UUID
from datetime import datetime


async def get_user(user_id: str | UUID, conn: Connection) -> User | None:
    r = await conn.fetchrow(
        """
            SELECT
                id::text,
                email,
                is_active,
                is_verified,
                TO_CHAR(last_login_at, 'DD-MM-YYYY HH24:MI:SS') as last_login_at,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') as updated_at
            FROM
                users
            WHERE
                id = $1
        """,
        user_id
    )

    return User(**dict(r)) if r is not None else None


async def get_users(limit: int, offset: int, conn: Connection) -> tuple[int, list[dict]]:
    total: int = await conn.fetchval("SELECT COUNT(*) AS total FROM users")
    
    r = await conn.fetch(
        """
            SELECT
                id::text,
                email,
                is_active,
                is_verified,
                TO_CHAR(last_login_at, 'DD-MM-YYYY HH24:MI:SS') as last_login_at,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') as updated_at
            FROM
                users
            LIMIT 
                $1
            OFFSET
                $2
        """,
        limit,
        offset
    )

    return total, [dict(i) for i in r]


async def get_user_by_refresh_token(refresh_token: str, conn: Connection) -> User | None:
    r = await conn.fetchrow(
        """
            SELECT
                id::text,
                email,
                is_active,
                is_verified,
                TO_CHAR(last_login_at, 'DD-MM-YYYY HH24:MI:SS') as last_login_at,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') as updated_at
            FROM
                users u
            JOIN
                user_session_tokens rt ON rt.user_id = u.id
            WHERE
                rt.refresh_token = $1
        """,
        refresh_token
    )
    return User(**dict(r)) if r is not None else None


async def update_user_session_token(user_id: str, refresh_token: str, expires_at: datetime, conn: Connection):
    await conn.execute(
        """
            UPDATE
                user_session_tokens
            SET
                expires_at = $1,
                revoked = FALSE,
                revoked_at = NULL,
                last_used_at = NOW()
            WHERE
                user_id = $2 AND
                refresh_token = $3
        """,
        expires_at,
        user_id,
        refresh_token
    )


async def get_user_login_data(email: str, conn: Connection) -> UserLoginData:
    r = await conn.fetchrow(
        """
            SELECT
                u.id::text,
                u.email,
                u.p_hash,
                ul.attempts as login_attempts,
                ul.last_failed_login,
                ul.locked_until
            FROM
                users u
            JOIN
                user_login_attempts ul ON ul.user_id = u.id
            WHERE
                email = $1
        """,
        email.lower().strip()
    )

    return UserLoginData(**dict(r)) if r is not None else None


async def create_user(email: str, p_hash: bytes, conn: Connection) -> User:
    r = await conn.fetchrow(
        """
            INSERT INTO users (
                email,
                p_hash
            )
            VALUES  
                (LOWER(TRIM($1)), $2)
            RETURNING
                id::text,
                email,
                is_active,
                is_verified,
                TO_CHAR(last_login_at, 'DD-MM-YYYY HH24:MI:SS') as last_login_at,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') as updated_at
        """,
        email,
        p_hash
    )

    return User(**dict(r)) if r is not None else None


async def user_email_exists(email: str, conn: Connection) -> bool:
    r = await conn.fetchrow("SELECT id FROM users WHERE email = LOWER(TRIM($1))", email)
    return r is not None


async def update_user_login_attempts(
    user_id: str | UUID, 
    failed_login_attempts: int, 
    last_failed_login: datetime, 
    locked_until: datetime, 
    conn: Connection
) -> None:
    if failed_login_attempts == 0:
        await conn.execute(
            """
                UPDATE 
                    user_login_attempts
                SET
                    attempts = $1,
                    last_failed_login = $2,
                    locked_until = $3,
                    last_successful_login = NOW()
                WHERE
                    user_id = $4
            """,
            failed_login_attempts, 
            last_failed_login, 
            locked_until, 
            user_id
        )
        return
      
    await conn.execute(
        """
            UPDATE 
                user_login_attempts
            SET
                attempts = $1,
                last_failed_login = $2,
                locked_until = $3                
            WHERE
                user_id = $4
        """,
        failed_login_attempts, 
        last_failed_login, 
        locked_until, 
        user_id
    )


async def create_user_session_token(
    user_id: str,
    refresh_token: str,
    expires_at: datetime,
    device_name: str | None,
    device_ip: str | None,
    user_agent: str | None,
    conn: Connection
) -> bool:
    await conn.execute(
        """
            INSERT INTO user_session_tokens (
                user_id,
                refresh_token,
                expires_at,
                device_name,
                device_ip,
                user_agent
            )
            VALUES 
                ($1, $2, $3, $4, $5, $6)
            ON CONFLICT
                (user_id, device_ip, user_agent)
            DO UPDATE SET
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at,
                device_name = EXCLUDED.device_name,
                last_used_at = NOW()
        """,
        user_id, 
        refresh_token, 
        expires_at,
        device_name,
        device_ip,
        user_agent
    )


async def get_user_sessions(user_id: str | UUID, limit: int, offset: int, conn: Connection) -> tuple[int, list[dict]]:
    total: int = await conn.fetchval(
        "SELECT COUNT(*) AS total FROM user_session_tokens WHERE user_id = $1", 
        user_id
    )

    r = await conn.fetch(
        """
            SELECT
                user_id::text
                TO_CHAR(issued_at, 'DD-MM-YYYY HH24:MI:SS') as issued_at,
                TO_CHAR(expires_at, 'DD-MM-YYYY HH24:MI:SS') as expires_at,
                revoked,
                TO_CHAR(revoked_at, 'DD-MM-YYYY HH24:MI:SS') as revoked_at,
                device_name,
                device_ip::text,
                user_agent,
                TO_CHAR(last_used_at, 'DD-MM-YYYY HH24:MI:SS') as last_used_at
            FROM
                user_session_tokens
            WHERE
                user_id = $1
            ORDER BY
                issued_at DESC
            LIMIT
                $2
            OFFSET
                $3
        """,
        user_id,
        limit,
        offset
    )

    return total, [dict(i) for i in r]


async def delete_user_session_token(refresh_token: str, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                user_session_tokens
            WHERE
                refresh_token = $1
        """,        
        refresh_token
    )


async def delete_all_user_session_tokens(user_id: str, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                user_session_tokens
            WHERE
                user_id = $1
        """,        
        user_id
    )



async def delete_user(user_id: str | UUID, conn: Connection):
    await conn.execute("DELETE FROM users WHERE id = $1", user_id)


async def delete_all_users(conn: Connection):
    await conn.execute("DELETE FROM users")


async def update_user_last_login_at(user_id: str, conn: Connection):
    await conn.execute(
        """
            UPDATE 
                users
            SET
                last_login_at = NOW()
            WHERE
                id = $1
        """,
        user_id
    )

async def delete_user_url(user_id: str, short_code: str, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                urls
            WHERE
                user_id = $1 AND
                short_code = $2
        """,
        user_id,
        short_code
    )



async def assign_url_to_user(url: URLResponse, user_id: str, conn: Connection):
    if url.user_id is None:
        await conn.execute(
            """
                UPDATE 
                    urls
                SET
                    user_id = $1,
                    is_favorite = FALSE,
                    expires_at = NULL
                WHERE
                    short_code = $2
            """,
            user_id,
            url.short_code
        )


async def set_user_favorite_url(user_id: str, short_code: str, is_favorite: bool, conn: Connection):
    await conn.execute(
        """
            UPDATE 
                urls
            SET
                is_favorite = $1
            WHERE
                user_id = $2 AND
                short_code = $3
        """,
        is_favorite,
        user_id,
        short_code
    )


async def get_user_stats(user_id: str, conn: Connection) -> dict | None:
    r = await conn.fetchrow(
        """
            SELECT 
                id::text,
                email,
                TO_CHAR(member_since, 'DD-MM-YYYY HH24:MI:SS') as member_since,
                total_urls,
                favorite_urls,
                total_clicks,
                TO_CHAR(last_url_created, 'DD-MM-YYYY HH24:MI:SS') as last_url_created,
                TO_CHAR(last_click_received, 'DD-MM-YYYY HH24:MI:SS') as last_click_received
            FROM 
                v_user_stats 
            WHERE 
                id = $1;
        """, 
        user_id
    )
    return dict(r) if r else None