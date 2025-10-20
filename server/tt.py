from src.db import db_instance
from psycopg.rows import dict_row
import psycopg



POPULATE = """
INSERT INTO domains 
    (url, url_hash, is_secure)
VALUES
    ('https://short.ly', decode(md5('https://short.ly'), 'hex'), TRUE),
    ('https://zar.io', decode(md5('https://zar.io'), 'hex'), TRUE)
ON CONFLICT
    (url_hash)
DO NOTHING;

INSERT INTO urls 
    (p_hash, domain_id, title, clicks, last_clicked_at, qrcode_url, expires_at)
VALUES
    (decode(md5('https://example.com'), 'hex'), 1, 'Example Website', 25, NOW() - INTERVAL '2 hours', 'https://cdn.short.ly/qrcodes/abcd1234.png', NOW() + INTERVAL '30 days'),
    (decode(md5('https://postgresql.org'), 'hex'), 2, 'PostgreSQL Official', 13, NOW() - INTERVAL '1 day', 'https://cdn.zar.io/qrcodes/xyz9876.png', NULL),
    (decode(md5('https://github.com'), 'hex'), 1, 'GitHub', 54, NOW() - INTERVAL '3 hours', 'https://cdn.short.ly/qrcodes/mnop4567.png', NOW() + INTERVAL '15 days');


"""


def show_table(cur: psycopg.Cursor, table: str):
    cur.execute(f"SELECT * FROM {table};")
    r = cur.fetchall()
    for i in r:
        print(i)


def main():
    conn: psycopg.Connection = db_instance()
    cur: psycopg.Cursor = conn.cursor()
    cur.row_factory = dict_row

    cur.execute(POPULATE)
    conn.commit()

    show_table(cur, 'domains')
    show_table(cur, 'urls') 

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
