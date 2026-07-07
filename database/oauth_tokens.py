from database.db import get_connection


def save_token(telegram_id, access_token, refresh_token, expires_at):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO oauth_tokens (
                    telegram_id,
                    access_token,
                    refresh_token,
                    expires_at
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at
            """, (
                telegram_id,
                access_token,
                refresh_token,
                expires_at,
            ))


def get_token(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM oauth_tokens
                WHERE telegram_id = %s
            """, (telegram_id,))
            return cur.fetchone()