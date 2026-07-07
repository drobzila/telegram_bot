from database.db import get_connection

def create_video(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO videos (user_id)
                VALUES (%s)
                RETURNING id
            """, (user_id,))
            
            row = cur.fetchone()
            return row["id"] if row else None


def get_video(video_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM videos
                WHERE id = %s
            """, (video_id,))
            return cur.fetchone()


def update_video(video_id, **kwargs):
    if not kwargs:
        return

    fields = []
    values = []

    for key, value in kwargs.items():
        fields.append(f"{key} = %s")
        values.append(value)

    values.append(video_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE videos
                SET {', '.join(fields)}
                WHERE id = %s
            """, values)
