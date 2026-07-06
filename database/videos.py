from database.db import get_connection


def create_video(user_id):
    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO videos(user_id)
        VALUES(?)
        """,
        (user_id,)
    )

    conn.commit()

    video_id = cursor.lastrowid

    conn.close()

    return video_id


def get_video(video_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM videos
        WHERE id=?
        """,
        (video_id,)
    ).fetchone()

    conn.close()

    return row


def update_video(video_id, **kwargs):

    if not kwargs:
        return

    conn = get_connection()

    fields = []

    values = []

    for key, value in kwargs.items():
        fields.append(f"{key}=?")
        values.append(value)

    values.append(video_id)

    conn.execute(
        f"""
        UPDATE videos
        SET {', '.join(fields)}
        WHERE id=?
        """,
        values
    )

    conn.commit()

    conn.close()
