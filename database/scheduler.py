from database.db import get_connection


def enable_sync(user_id, videos_per_day, times):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # تعديل الاستعلام ليتوافق مع PostgreSQL واستبدال ? بـ %s
            cur.execute("""
                INSERT INTO youtube_settings (user_id, enabled, videos_per_day, times)
                VALUES (%s, TRUE, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    enabled = EXCLUDED.enabled,
                    videos_per_day = EXCLUDED.videos_per_day,
                    times = EXCLUDED.times
            """, (
                user_id,
                videos_per_day,
                ",".join(times) if isinstance(times, list) else times
            ))


def get_settings(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM youtube_settings
                WHERE user_id = %s
            """, (user_id,))
            return cur.fetchone()
