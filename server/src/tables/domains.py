from asyncpg import Connection


async def get_domain_id(url: str, conn: Connection, is_secure: bool = True) -> int:
    domain_id: int = conn.fetchval(
        """
            WITH ins AS (
                INSERT INTO domains (
                    url, 
                    url_hash,
                    is_secure
                )
                VALUES 
                    (TRIM($1), decode(md5(TRIM($2)), 'hex'), $3)
                ON CONFLICT
                    (url_hash)
                DO NOTHING
                RETURNING 
                    id
            )
            SELECT 
                id FROM ins UNION
            SELECT 
                id 
            FROM
                domains 
            WHERE 
                url_hash = decode(md5(TRIM($2)), 'hex')
        """,
        url,
        url,
        is_secure
    )
    return domain_id