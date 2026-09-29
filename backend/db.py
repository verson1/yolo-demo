"""Small MySQL access layer. Database setup is documented in README.md."""

from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from config import DB_CONFIG


@contextmanager
def connection():
    conn = pymysql.connect(**DB_CONFIG, cursorclass=DictCursor, autocommit=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_one(sql, params=()):
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def fetch_all(sql, params=()):
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
