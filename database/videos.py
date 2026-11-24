from database.db import get_connection

VIDEO_UPDATE_FIELDS = {
    "filename",
    "title",
    "description",
    "thumbnail_file_id",
    "telegram_file_id",
    "drive_file_id",
    "youtube_video_id",
    "status",
    "uploaded_at",
}


def create_video(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO videos (user_id)
                VALUES (%s)
                RETURNING id
                """,
                (user_id,),
            )
            row = cur.fetchone()
            return row["id"] if row else None


def get_video(video_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM videos
                WHERE id = %s
                """,
                (video_id,),
            )
            return cur.fetchone()


def update_video(video_id, **kwargs):
    if not kwargs:
        return

    invalid_fields = set(kwargs) - VIDEO_UPDATE_FIELDS
    if invalid_fields:
        raise ValueError(
            "Unsupported video field(s): " + ", ".join(sorted(invalid_fields))
        )

    assignments = [f"{field} = %s" for field in kwargs]
    values = list(kwargs.values())
    values.append(video_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE videos
                SET {", ".join(assignments)}
                WHERE id = %s
                """,
                values,
            )
