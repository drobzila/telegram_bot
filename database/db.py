from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "bot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
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

    CREATE TABLE IF NOT EXISTS oauth_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER UNIQUE NOT NULL,

        access_token TEXT,

        refresh_token TEXT,

        expires_at TEXT,

        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS videos (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

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
 
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,

        value TEXT
    );
    """)

    conn.commit()

    # في حال كانت قاعدة البيانات قد أُنشئت قبل إضافة الأعمدة
    columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)")
    ]

    if "state" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN state TEXT DEFAULT 'IDLE'"
        )

    if "state_data" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN state_data TEXT"
        )

    conn.commit()
    conn.close()
