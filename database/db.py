import os
from pathlib import Path

from psycopg import connect
from psycopg.rows import dict_row

from config import DATABASE_URL

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL غير مضبوط.")
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
                youtube_connected BOOLEAN DEFAULT FALSE,
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
            CREATE TABLE IF NOT EXISTS oauth_states (
                state TEXT PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

            # Migrate older databases where youtube_connected was INTEGER.
            cursor.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'users'
                      AND column_name = 'youtube_connected'
                      AND data_type = 'integer'
                ) THEN
                    ALTER TABLE users
                    ALTER COLUMN youtube_connected TYPE BOOLEAN
                    USING (youtube_connected <> 0);
                END IF;
            END $$;
            """)

            # Migrate legacy oauth_tokens.telegram_id -> oauth_tokens.user_id.
            cursor.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'oauth_tokens' AND column_name = 'telegram_id'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'oauth_tokens' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE oauth_tokens ADD COLUMN user_id INTEGER;
                    UPDATE oauth_tokens ot
                    SET user_id = u.id
                    FROM users u
                    WHERE u.telegram_id = ot.telegram_id;
                    DELETE FROM oauth_tokens WHERE user_id IS NULL;
                    ALTER TABLE oauth_tokens ALTER COLUMN user_id SET NOT NULL;
                    ALTER TABLE oauth_tokens ADD CONSTRAINT oauth_tokens_user_id_unique UNIQUE (user_id);
                    ALTER TABLE oauth_tokens
                        ADD CONSTRAINT oauth_tokens_user_id_fkey
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                    ALTER TABLE oauth_tokens DROP COLUMN telegram_id;
                END IF;
            END $$;
            """)

            # Remove stale OAuth states after restarts/deploys.
            cursor.execute("DELETE FROM oauth_states WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '15 minutes'")

        conn.commit()
