from database.db import get_connection
from database.users import get_user_id


def _resolve_user_id(telegram_id):
    user_id = get_user_id(telegram_id)
    if user_id is None:
        raise ValueError("المستخدم غير موجود في قاعدة البيانات.")
    return user_id


def save_token(telegram_id, access_token, refresh_token, expires_at):
    user_id = _resolve_user_id(telegram_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO oauth_tokens (
                    user_id,
                    access_token,
                    refresh_token,
                    expires_at
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = COALESCE(EXCLUDED.refresh_token, oauth_tokens.refresh_token),
                    expires_at = EXCLUDED.expires_at
            """, (user_id, access_token, refresh_token, expires_at))
        conn.commit()


def get_token(telegram_id):
    user_id = get_user_id(telegram_id)
    if user_id is None:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT access_token, refresh_token, expires_at
                FROM oauth_tokens
                WHERE user_id = %s
            """, (user_id,))
            return cur.fetchone()


def delete_token(telegram_id):
    user_id = get_user_id(telegram_id)
    if user_id is None:
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM oauth_tokens WHERE user_id = %s", (user_id,))
        conn.commit()
