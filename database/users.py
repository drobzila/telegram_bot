from database.db import get_connection


def register_user(user):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # استبدال INSERT OR IGNORE بـ ON CONFLICT DO NOTHING الخاص بـ Postgres
            cur.execute("""
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_id) DO NOTHING
            """, (user.id, user.username, user.first_name))


def get_user(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))
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
            cur.execute("""
                SELECT *
                FROM users
                ORDER BY created_at DESC
            """)
            return cur.fetchall()


def update_drive_folder(telegram_id, folder_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET drive_folder = %s
                WHERE telegram_id = %s
            """, (folder_id, telegram_id))


def update_youtube_status(telegram_id, connected):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # تمرير القيمة كـ Boolean مباشرة للبايثون ومكتبة الاتصال تتكفل بالباقي
            cur.execute("""
                UPDATE users
                SET youtube_connected = %s
                WHERE telegram_id = %s
            """, (bool(connected), telegram_id))


def set_default_visibility(telegram_id, visibility):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET default_visibility = %s
                WHERE telegram_id = %s
            """, (visibility, telegram_id))


def delete_user(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))


def set_youtube_connected(telegram_id):
    print("set_youtube_connected called")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name='users'
                AND column_name='youtube_connected'
            """)
            print(cur.fetchone())

            cur.execute("""
                UPDATE users
                SET youtube_connected = TRUE
                WHERE telegram_id = %s
            """, (telegram_id,))

def is_youtube_connected(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT youtube_connected
                FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))
            row = cur.fetchone()
            
            if row:
                return bool(row["youtube_connected"])
            return False
def get_user_id(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id
                FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))
            row = cur.fetchone()
            return row["id"] if row else None
