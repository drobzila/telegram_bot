import os
from pathlib import Path
import psycopg  # أو psycopg2 حسب المكتبة المستخدمة في مشروعك
from psycopg import connect
from psycopg.rows import dict_row
from config import DATABASE_URL

# إعداد المسارات (يمكنك الإبقاء عليها إذا كنت تحتاجها لأمور أخرى، 
# ولكن في PostgreSQL لن تحتاج لإنشاء ملف bot.db محلياً)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def get_connection():
    return connect(
        DATABASE_URL,
        row_factory=dict_row,
        autocommit=False,
    )

def initialize_database():
    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'ar',
                is_admin INTEGER DEFAULT 0,
                youtube_connected INTEGER DEFAULT 0,
                drive_folder TEXT,
                default_visibility TEXT DEFAULT 'private',
                state TEXT DEFAULT 'IDLE',
                state_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename TEXT,
                title TEXT,
                description TEXT,
                thumbnail_file_id TEXT,
                telegram_file_id TEXT,
                drive_file_id TEXT,
                youtube_video_id TEXT,
                status TEXT DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_at TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_settings (
                user_id INTEGER PRIMARY KEY,
                enabled BOOLEAN DEFAULT FALSE,
                videos_per_day INTEGER,
                times TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS upload_queue (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                video_path TEXT,
                title TEXT,
                description TEXT,
                privacy TEXT,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_drive_deletions (
                id SERIAL PRIMARY KEY,
                drive_file_id TEXT NOT NULL,
                file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

        conn.commit()
