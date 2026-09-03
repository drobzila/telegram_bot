from config import OWNER_USERNAME
from database.db import get_connection


def register_user(user):
    username = (user.username or "").lstrip("@").strip().lower() or None
    is_owner = bool(username and username == OWNER_USERNAME)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (telegram_id, username, first_name, is_admin)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    is_admin = CASE
                        WHEN EXCLUDED.is_admin = 1 THEN 1
                        ELSE users.is_admin
                    END
            """, (user.id, username, user.first_name, int(is_owner)))
        conn.commit()


def get_user(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            return cur.fetchone()


def user_exists(telegram_id):
    return get_user(telegram_id) is not None


def count_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS count FROM users")
            row = cur.fetchone()
            return row["count"] if row else 0


def list_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            return cur.fetchall()


def update_drive_folder(telegram_id, folder_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET drive_folder = %s WHERE telegram_id = %s",
                (folder_id, telegram_id),
            )
        conn.commit()


def update_youtube_status(telegram_id, connected):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET youtube_connected = %s WHERE telegram_id = %s",
                (bool(connected), telegram_id),
            )
        conn.commit()


def set_default_visibility(telegram_id, visibility):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET default_visibility = %s WHERE telegram_id = %s",
                (visibility, telegram_id),
            )
        conn.commit()


def delete_user(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE telegram_id = %s", (telegram_id,))
        conn.commit()


def set_youtube_connected(telegram_id, connected=True):
    update_youtube_status(telegram_id, connected)


def is_youtube_connected(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT youtube_connected FROM users WHERE telegram_id = %s",
                (telegram_id,),
            )
            row = cur.fetchone()
            return bool(row["youtube_connected"]) if row else False


def get_user_id(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
            row = cur.fetchone()
            return row["id"] if row else None


def is_admin(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT is_admin FROM users WHERE telegram_id = %s", (telegram_id,))
            row = cur.fetchone()
            return bool(row["is_admin"]) if row else False
