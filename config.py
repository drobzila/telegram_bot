import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

PORT = int(os.getenv("PORT", "8080"))

ADMIN_IDS = [
    int(admin_id)
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip()
]

# Telegram username of the bot owner. The user is promoted automatically
# when they register/start the bot, and existing matching users are promoted
# during database initialization.
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "safiazri").lstrip("@").strip().lower()

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BASE_URL = os.getenv("BASE_URL")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL")
