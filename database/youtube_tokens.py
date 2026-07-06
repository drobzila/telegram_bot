import sqlite3

DB_NAME = "database/database.db"


def save_token(user_id, refresh_token):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO youtube_tokens(user_id, refresh_token)
        VALUES(?, ?)
    """, (user_id, refresh_token))

    conn.commit()
    conn.close()


def get_token(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT refresh_token FROM youtube_tokens WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None
