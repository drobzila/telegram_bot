from database.db import get_connection


def save_token(user_id, access_token, refresh_token, expires_at):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM oauth_tokens WHERE user_id=?",
        (user_id,),
    )

    cur.execute(
        """
        INSERT INTO oauth_tokens(
            user_id,
            access_token,
            refresh_token,
            expires_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            access_token,
            refresh_token,
            expires_at,
        ),
    )

    conn.commit()
    conn.close()


def get_token(user_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM oauth_tokens
        WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()

    conn.close()

    return row
