from src.db import get_db_pool, db_init, db_close, db_count
from asyncpg import Connection
from src.security import sha256_bytes
import asyncio
import json


async def main():
    await db_init()
    pool = get_db_pool()
    conn: Connection = await pool.acquire()
        
    
    with open("/mnt/HD/verified_online.json", "r") as file:
        data = json.load(file)
    
    params = [x['url'] for x in data]
    t = 0
    t1 = await db_count('url_blacklist', conn)
    for url in params:
        await conn.execute(
            """
                INSERT INTO url_blacklist (
                    url, 
                    url_hash
                )
                VALUES 
                    ($1, $2)
                ON CONFLICT 
                    (url_hash) 
                DO NOTHING
            """, 
            url, 
            sha256_bytes(url)
        )
        print(t)
        t += 1
        
    t2 = await db_count('url_blacklist', conn)
    print(t1)
    print(t2)

    await pool.release(conn)
    await db_close()


if __name__ == "__main__":
    asyncio.run(main())
