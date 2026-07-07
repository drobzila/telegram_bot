from database.db import get_connection


def enable_sync(user_id, videos_per_day, times):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # تحويل القيم لـ TRUE واستخدام ON CONFLICT للـ PostgreSQL
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


def disable_sync(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # تعديل القيمة المنطقية إلى FALSE والمعامل إلى %s
            cur.execute("""
                UPDATE youtube_settings
                SET enabled = FALSE
                WHERE user_id = %s
            """, (user_id,))


def get_sync_settings(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM youtube_settings
                WHERE user_id = %s
            """, (user_id,))
            
            row = cur.fetchone()
            return row


def is_sync_enabled(user_id):
    settings = get_sync_settings(user_id)
    
    # في psycopg عند جلب البيانات كـ Dictionary أو Tuple:
    # نقوم بالتحقق من القيمة المنطقية المعادّة مباشرة من الـ Database
    if settings:
        # إذا كان الصف عبارة عن dict أو يدعم المفاتيح النصية
        try:
            return bool(settings["enabled"])
        except TypeError:
            # إذا كان الصف Tuple عادي (حسب إعداد الـ row_factory لديك)
            # ترتيب الحقول في الـ Schema: user_id (0), enabled (1)
            return bool(settings[1])
            
    return False
