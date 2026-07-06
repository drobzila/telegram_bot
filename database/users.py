from database.db import get_connection


def register_user(user):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users
        (telegram_id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM users
        WHERE telegram_id=?
    """, (telegram_id,)).fetchone()

    conn.close()
    return row


def user_exists(telegram_id):
    return get_user(telegram_id) is not None


def count_users():
    conn = get_connection()

    count = conn.execute("""
        SELECT COUNT(*)
        FROM users
    """).fetchone()[0]

    conn.close()
    return count


def list_users():
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM users
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()
    return rows


def update_drive_folder(telegram_id, folder_id):
    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET drive_folder=?
        WHERE telegram_id=?
    """, (
        folder_id,
        telegram_id
    ))

    conn.commit()
    conn.close()


def update_youtube_status(telegram_id, connected):
    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET youtube_connected=?
        WHERE telegram_id=?
    """, (
        int(connected),
        telegram_id
    ))

    conn.commit()
    conn.close()


def set_default_visibility(telegram_id, visibility):
    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET default_visibility=?
        WHERE telegram_id=?
    """, (
        visibility,
        telegram_id
    ))

    conn.commit()
    conn.close()


def delete_user(telegram_id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM users
        WHERE telegram_id=?
    """, (telegram_id,))

    conn.commit()
    conn.close()
