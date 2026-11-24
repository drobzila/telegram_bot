"""Optional PostgreSQL connectivity check; never print connection credentials."""

import sys

import psycopg

from config import DATABASE_URL


def main():
    if not DATABASE_URL:
        print("DATABASE_URL is not configured.", file=sys.stderr)
        return 2

    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        print("PostgreSQL connection successful.")
        return 0
    except psycopg.Error as exc:
        print(f"PostgreSQL connection failed ({type(exc).__name__}).", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
