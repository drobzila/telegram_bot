from database.db import get_connection


def add_to_queue(user_id, video_path, title, description, privacy, scheduled_time):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO upload_queue (
                    user_id, video_path, title, description, privacy, scheduled_time
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, video_path, title, description, privacy, scheduled_time))


def get_waiting_videos():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM upload_queue
                WHERE status = 'waiting'
            """)
            return cur.fetchall()


def mark_uploaded(video_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE upload_queue
                SET status = 'uploaded'
                WHERE id = %s
            """, (video_id,))
