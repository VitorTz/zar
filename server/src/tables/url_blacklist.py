from asyncpg import Connection


async def is_url_in_blacklist(url: str, conn: Connection) -> bool:
    r = await conn.fetchrow(
        "SELECT id FROM url_blacklist WHERE url = LOWER(TRIM($1))",
        url
    )
    return r is not None


async def add_url_to_blacklist(url: str, conn: Connection):
    await conn.execute(
        """
            INSERT INTO url_blacklist (
                url
            )
            VALUES
                (LOWER(TRIM($1)))
            ON CONFLICT
                (url)
            DO NOTHING
        """,
        url
    )