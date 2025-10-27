from src.schemas.urls import UrlTagCreate, UrlTag, URLResponse, UrlTagUpdate
from src.schemas.user import User
from src.schemas.pagination import Pagination
from typing import Optional
from asyncpg import Connection
from src import util


async def create_tag(user: User, tag: UrlTagCreate, conn: Connection):
    row = await conn.fetchrow(
        """
        INSERT INTO url_tags (
            user_id, 
            name, 
            color, 
            descr
        )
        VALUES 
            ($1, TRIM($2), $3, TRIM($4))
        RETURNING 
            id, 
            user_id, 
            name, 
            color, 
            descr, 
            created_at
        """,
        user.id,
        tag.name,
        tag.color,
        tag.descr
    )
    
    return UrlTag(**dict(row))


async def get_tag_by_id(tag_id: int, conn: Connection) -> Optional[UrlTag]:
    row = await conn.fetchrow(
        """
            SELECT
                id,
                user_id,
                name,
                color,
                descr,
                created_at
            FROM
                url_tags
            WHERE
                id = $1
        """,
        tag_id
    )
    return UrlTag(**dict(row)) if row else None


async def update_tag(user: User, tag: UrlTagUpdate, conn: Connection) -> UrlTag:
    old_tag: Optional[UrlTag] = await get_tag_by_id(tag.id, conn)
    if not old_tag: return

    old_tag.name = util.coalesce(tag.name, old_tag.name)
    old_tag.color = util.coalesce(tag.color, old_tag.color)
    old_tag.descr = util.coalesce(tag.descr, old_tag.descr)
    
    await conn.execute(
        """
            UPDATE
                url_tags
            SET
                name = $1,
                color = $2,
                descr = $3
            WHERE
                id = $4
                AND user_id = $5
        """,
        old_tag.name,
        old_tag.color,
        old_tag.descr,
        tag.id,
        user.id
    )
    return old_tag


async def get_user_tags(user: User, limit: int, offset: int, conn: Connection) -> Pagination[UrlTag]:
    total: int = await conn.fetchval(
        "SELECT COUNT(*) AS total FROM url_tags WHERE user_id = $1",
        user.id
    )
    rows = await conn.fetch(
        """
            SELECT
                id,
                user_id,
                name,
                color,
                descr,
                created_at
            FROM
                url_tags
            WHERE
                user_id = $1
            LIMIT
                $2
            OFFSET
                $3
        """,
        user.id,
        limit,
        offset
    )
    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[UrlTag(**dict(row)) for row in rows]
    )


async def get_tag_urls(
    base_url: str,
    tag_id: int,
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[URLResponse]:
    total = await conn.fetchval(
        """
            SELECT 
                COUNT(*) AS total
            FROM 
                url_tag_relations utr
            JOIN 
                urls u ON u.id = utr.url_id
            WHERE 
                utr.tag_id = $1
        """,
        tag_id
    )

    rows = await conn.fetch(
        """
        SELECT
            u.id,
            u.domain_id,
            uu.user_id,
            u.original_url,
            u.short_code,
            u.clicks,
            COALESCE(uu.is_favorite, FALSE) AS is_favorite,
            u.created_at,
            u.expires_at
        FROM 
            urls u
        JOIN
            url_tag_relations utr ON utr.url_id = u.id
        LEFT JOIN (
            SELECT DISTINCT ON (url_id) *
            FROM 
                user_urls
            ORDER BY 
                url_id, 
                id DESC
        ) uu ON uu.url_id = u.id
        WHERE
            utr.tag_id = $1
        ORDER BY 
            u.id
        LIMIT
            $2
        OFFSET
            $3
        """,
        tag_id,
        limit,
        offset
    )

    return Pagination[URLResponse](
        total=total,
        limit=limit,
        offset=offset,
        results=[URLResponse(**dict(row), short_url=f"{base_url}/api/v1/{row['short_code']}") for row in rows],
    )


async def add_url_to_tag(url_id: int, tag_id: int, conn: Connection):
    await conn.execute(
        """
            INSERT INTO url_tag_relations (
                url_id,
                tag_id
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (url_id, tag_id)
            DO NOTHING
        """,
        url_id,
        tag_id
    )


async def remove_url_from_tag(url_id: int, tag_id: int, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                url_tag_relations
            WHERE
                url_id = $1
                AND tag_id = $2
            DO NOTHING
        """,
        url_id,
        tag_id
    )


async def delete_user_tag(user_id: str, tag_id: int, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                url_tags
            WHERE
                id = $1
                AND user_id = $2
        """,
        tag_id,
        user_id
    )


async def delete_tag(tag_id: int, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                url_tags
            WHERE
                id = $1
        """,
        tag_id
    )


async def create_tag_relation(url_id: int, tag_id: int, conn: Connection):
    await conn.execute(
        """
            INSERT INTO url_tag_relations (
                url_id,
                tag_id
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (url_id, tag_id)
            DO NOTHING
        """,
        url_id,
        tag_id
    )


async def delete_tag_relation(url_id: int, tag_id: int, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                url_tag_relations
            WHERE
                url_id = $1
                AND tag_id = $2
        """,
        url_id,
        tag_id
    )


async def user_has_access_to_tag(user_id: str, tag_id: int, conn: Connection) -> bool:
    r = await conn.fetchval(
        "SELECT id FROM url_tags WHERE user_id = $1 AND id = $2",
        user_id,
        tag_id
    )
    return bool(r)


async def clear_tag(tag_id: int, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                url_tag_relations
            WHERE
                tag_id = $1
        """,
        tag_id
    )